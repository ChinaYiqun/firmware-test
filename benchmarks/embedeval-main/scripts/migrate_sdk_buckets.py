"""Migrate cases/ into per-SDK bucket directories.

Driven by ``cases/SDK_LAYOUT.yaml``. For each case:

  1. ``git mv`` the case directory under ``cases/<sdk>/<case-id>/``.
     If the manifest entry has ``rename_to:``, the destination ID is changed
     as part of the move (only ``boot-002 -> boot-uboot-001`` at present).
  2. Rewrite ``metadata.yaml`` to add ``sdk: <bucket>`` (and the new ``id:``
     if renamed). Full-file rewrite with PyYAML to avoid Edit-tool corruption
     on WSL2/NTFS.
  3. Patch ``results/test_tracker.json`` for any renamed IDs.

Usage::

    python scripts/migrate_sdk_buckets.py --cases cases/ \\
        --manifest cases/SDK_LAYOUT.yaml [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("migrate_sdk_buckets")

VALID_SDKS = {"zephyr", "embedded-linux", "freertos", "esp-idf", "stm32-hal"}


def load_manifest(manifest_path: Path) -> dict[str, dict[str, str]]:
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "cases" not in data:
        raise ValueError(f"Manifest {manifest_path} missing 'cases' key")
    cases = data["cases"]
    if not isinstance(cases, dict):
        raise ValueError("'cases' must be a mapping")
    for case_id, entry in cases.items():
        if "sdk" not in entry:
            raise ValueError(f"Manifest entry {case_id} missing 'sdk'")
        if entry["sdk"] not in VALID_SDKS:
            raise ValueError(
                f"Manifest entry {case_id} has invalid sdk: {entry['sdk']}"
            )
    return cases


def _git_root(path: Path) -> Path:
    """Resolve the git working-tree root containing ``path``.

    Needed because the script can run against either the public or the
    private cases repo; ``git mv`` must execute inside the correct repo's
    worktree or it fails with "not under version control".
    """
    out = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
        check=True,
        capture_output=True,
        text=True,
    )
    return Path(out.stdout.strip())


def run_git_mv(src: Path, dst: Path, dry_run: bool) -> None:
    logger.info("  git mv %s %s", src, dst)
    if dry_run:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    cwd = _git_root(src)
    subprocess.run(["git", "mv", str(src), str(dst)], check=True, cwd=cwd)


def rewrite_metadata(
    metadata_path: Path, sdk: str, new_id: str | None, dry_run: bool
) -> None:
    raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Invalid metadata at {metadata_path}")
    if new_id:
        raw["id"] = new_id
    raw["sdk"] = sdk
    # Preserve a stable key order: id, category, difficulty, title,
    # description, tags, platform, sdk, then the rest.
    ordered_keys = [
        "id",
        "category",
        "difficulty",
        "title",
        "description",
        "tags",
        "platform",
        "sdk",
    ]
    ordered: dict[str, Any] = {}
    for k in ordered_keys:
        if k in raw:
            ordered[k] = raw[k]
    for k, v in raw.items():
        if k not in ordered:
            ordered[k] = v

    new_text = yaml.safe_dump(ordered, sort_keys=False, width=120, allow_unicode=True)
    logger.info(
        "  rewrite %s (sdk=%s%s)",
        metadata_path,
        sdk,
        f", id={new_id}" if new_id else "",
    )
    if dry_run:
        return
    # Atomic write: write to a sibling temp file then rename, so a crash
    # mid-write can't leave a partially-written metadata.yaml that the
    # dst.exists() guard on re-run would then skip.
    tmp = metadata_path.with_suffix(metadata_path.suffix + ".tmp")
    tmp.write_text(new_text, encoding="utf-8")
    tmp.replace(metadata_path)


def patch_tracker(tracker_path: Path, renames: dict[str, str], dry_run: bool) -> None:
    if not tracker_path.is_file():
        logger.info("tracker not found: %s (skipping)", tracker_path)
        return
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    results = data.get("results", {})
    changed = False
    for model_key, per_model in results.items():
        if not isinstance(per_model, dict):
            continue
        for old_id, new_id in renames.items():
            if old_id in per_model:
                per_model[new_id] = per_model.pop(old_id)
                per_model[new_id]["case_id"] = new_id
                logger.info("  tracker[%s]: %s -> %s", model_key, old_id, new_id)
                changed = True
    if not changed:
        logger.info("tracker: no renamed IDs present")
        return
    if dry_run:
        return
    tracker_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def migrate(
    cases_dir: Path,
    manifest: dict[str, dict[str, str]],
    dry_run: bool,
    tracker_path: Path,
) -> None:
    renames: dict[str, str] = {}
    for case_id, entry in sorted(manifest.items()):
        src = cases_dir / case_id
        if not src.is_dir():
            logger.warning("  missing case dir: %s (skipping)", src)
            continue
        sdk = entry["sdk"]
        new_id = entry.get("rename_to")
        dst_id = new_id or case_id
        dst = cases_dir / sdk / dst_id
        if dst.exists():
            logger.warning("  destination exists, skipping: %s", dst)
            continue
        run_git_mv(src, dst, dry_run)
        metadata_path = dst / "metadata.yaml"
        # Dry-run: metadata file is still at src/metadata.yaml (no mv happened)
        if dry_run:
            metadata_path = src / "metadata.yaml"
        if metadata_path.is_file():
            rewrite_metadata(metadata_path, sdk, new_id, dry_run)
        else:
            logger.warning("  no metadata.yaml after move: %s", metadata_path)
        if new_id:
            renames[case_id] = new_id

    patch_tracker(tracker_path, renames, dry_run)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", type=Path, default=Path("cases"))
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Path to SDK layout manifest (default: <cases>/SDK_LAYOUT.yaml)",
    )
    parser.add_argument(
        "--tracker",
        type=Path,
        default=None,
        help="Path to test_tracker.json to patch for renamed IDs "
        "(default: <cases>/../results/test_tracker.json)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    manifest_path = args.manifest or (args.cases / "SDK_LAYOUT.yaml")
    tracker_path = args.tracker or (args.cases.parent / "results" / "test_tracker.json")

    manifest = load_manifest(manifest_path)
    logger.info("Loaded %d entries from %s", len(manifest), manifest_path)
    logger.info("Tracker target: %s", tracker_path)
    migrate(args.cases, manifest, args.dry_run, tracker_path)
    if args.dry_run:
        logger.info("Dry run complete — no files modified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
