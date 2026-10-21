#!/usr/bin/env python3
"""Mutation oracle gate for negatives.py files.

For each case with negatives.py:
  1. Read reference/main.c (or reference/*.c).
  2. Apply each NEGATIVE's mutation.
  3. Run L0 (static.py) + L3 (behavior.py) checks on mutated code.
  4. Assert each 'must_fail' check actually fails.

Exit code: 0 if all oracles pass; 1 if any case has a must_fail check
that didn't detect its seeded bug. Safe to run in CI.

Usage:
    uv run python scripts/verify_negatives_oracle.py
    uv run python scripts/verify_negatives_oracle.py --case dma-002
    uv run python scripts/verify_negatives_oracle.py --category dma
    uv run python scripts/verify_negatives_oracle.py --json report.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OracleResult:
    case_id: str
    status: str  # "pass" | "fail" | "skip"
    negatives_attempted: int = 0
    missed: list[dict[str, Any]] = field(default_factory=list)
    error: str | None = None
    # REQ-02 per-check coverage — populated by compute_coverage().
    coverage: float | None = None
    emitted_checks: list[str] = field(default_factory=list)
    labeled_checks: list[str] = field(default_factory=list)
    uncovered_checks: list[str] = field(default_factory=list)
    stale_labels: list[str] = field(default_factory=list)


# REQ-02: minimum per-check coverage fraction the /negatives gate enforces
# on newly-authored or revisited TCs. Matches the Hiloop REQ-02 ask (≥80%).
COVERAGE_MIN_DEFAULT = 0.8

# Allowlist: TCs authored before the coverage gate existed. When
# --strict-coverage is set, these are reported but do NOT cause a non-zero
# exit. New TCs (authored via /negatives after 2026-04-19) are NOT
# grandfathered.
COVERAGE_GRANDFATHER_PATH = (
    Path(__file__).parent.parent / "plans" / "coverage-grandfather.txt"
)


def _load_grandfather() -> frozenset[str]:
    if not COVERAGE_GRANDFATHER_PATH.is_file():
        return frozenset()
    entries = [
        line.strip()
        for line in COVERAGE_GRANDFATHER_PATH.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    return frozenset(entries)


def _load_module(path: Path, alias: str) -> Any:
    spec = importlib.util.spec_from_file_location(alias, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _read_reference(case_dir: Path) -> str | None:
    ref_main = case_dir / "reference" / "main.c"
    if ref_main.is_file():
        return ref_main.read_text()
    # Fallback: any .c or .bb or .conf under reference/
    ref_dir = case_dir / "reference"
    if not ref_dir.is_dir():
        return None
    for ext in ("*.c", "*.bb", "*.conf", "*.dts", "*.overlay", "*.yaml"):
        matches = sorted(ref_dir.glob(ext))
        if matches:
            return matches[0].read_text()
    return None


def verify_case(case_dir: Path) -> OracleResult:
    case_id = case_dir.name
    checks_dir = case_dir / "checks"
    neg_path = checks_dir / "negatives.py"
    static_path = checks_dir / "static.py"
    behavior_path = checks_dir / "behavior.py"

    if not neg_path.is_file():
        return OracleResult(case_id=case_id, status="skip", error="no negatives.py")

    reference = _read_reference(case_dir)
    if reference is None:
        return OracleResult(
            case_id=case_id, status="skip", error="no reference file found"
        )

    try:
        neg_mod = _load_module(neg_path, f"neg_{case_id}")
        negatives: list[dict[str, Any]] = getattr(neg_mod, "NEGATIVES", [])
    except Exception as exc:
        return OracleResult(case_id=case_id, status="fail", error=f"load: {exc}")

    if not negatives:
        return OracleResult(
            case_id=case_id, status="skip", error="NEGATIVES list empty"
        )

    static_mod = (
        _load_module(static_path, f"st_{case_id}") if static_path.is_file() else None
    )
    behavior_mod = (
        _load_module(behavior_path, f"bh_{case_id}")
        if behavior_path.is_file()
        else None
    )

    result = OracleResult(case_id=case_id, status="pass", negatives_attempted=0)

    for neg in negatives:
        if "must_fail" not in neg:
            continue  # should_fail-only subtle negatives not gated here

        name = neg.get("name", "<unnamed>")
        try:
            mutated = neg["mutation"](reference)
        except Exception as exc:
            result.missed.append(
                {
                    "negative": name,
                    "reason": f"mutation raised: {exc}",
                    "must_fail": neg["must_fail"],
                }
            )
            result.status = "fail"
            continue

        if mutated == reference:
            result.missed.append(
                {
                    "negative": name,
                    "reason": "mutation did not change reference",
                    "must_fail": neg["must_fail"],
                }
            )
            result.status = "fail"
            continue

        # Collect all check details on mutated code
        details: list[Any] = []
        if static_mod and hasattr(static_mod, "run_checks"):
            details.extend(static_mod.run_checks(mutated))
        if behavior_mod and hasattr(behavior_mod, "run_checks"):
            details.extend(behavior_mod.run_checks(mutated))

        for check_name in neg["must_fail"]:
            matching = [d for d in details if d.check_name == check_name]
            if not matching:
                result.missed.append(
                    {
                        "negative": name,
                        "must_fail_check": check_name,
                        "reason": "check not found in static.py/behavior.py",
                    }
                )
                result.status = "fail"
                continue
            if any(d.passed for d in matching):
                result.missed.append(
                    {
                        "negative": name,
                        "must_fail_check": check_name,
                        "reason": "check PASSED on mutated code (should have failed)",
                    }
                )
                result.status = "fail"

        result.negatives_attempted += 1

    return result


def compute_coverage(case_dir: Path, result: OracleResult) -> None:
    """REQ-02: populate per-check coverage fields on *result*.

    Emitted checks = union of check_names returned by static.py.run_checks
    and behavior.py.run_checks on the reference.
    Labeled checks = union of must_fail + should_fail across NEGATIVES.
    Note: should_fail entries intentionally count toward the labeled set.
    REQ-02 defines coverage = (must_fail ∪ should_fail) ∩ emitted / emitted.
    Subtle negatives (should_fail-only) are valid mutation witnesses even
    though they don't gate the oracle exit code.

    coverage = |labeled ∩ emitted| / |emitted|     (1.0 if no emitted)
    uncovered_checks = emitted - labeled          (checks with no mutation)
    stale_labels = labeled - emitted              (labels naming checks that
                                                   never run — likely typo or
                                                   post-rename drift; REQ-06).

    Exceptions from module loading or run_checks() are LOGGED, not raised.
    Coverage computation continues with whatever checks were collected so
    a single broken static.py doesn't block the oracle gate entirely.
    Inflated coverage from swallowed errors is a known risk — inspect
    stderr for WARNING lines after each run.
    """
    checks_dir = case_dir / "checks"
    neg_path = checks_dir / "negatives.py"
    if not neg_path.is_file():
        return
    reference = _read_reference(case_dir)
    if reference is None:
        return

    try:
        neg_mod = _load_module(neg_path, f"cov_neg_{case_dir.name}")
    except Exception as exc:
        logger.warning(
            "coverage: cannot load negatives.py for %s: %s", case_dir.name, exc
        )
        return
    negatives: list[dict[str, Any]] = getattr(neg_mod, "NEGATIVES", []) or []

    emitted: set[str] = set()
    for name, path in (
        ("static", checks_dir / "static.py"),
        ("behavior", checks_dir / "behavior.py"),
    ):
        if not path.is_file():
            continue
        try:
            mod = _load_module(path, f"cov_{name}_{case_dir.name}")
        except Exception as exc:
            logger.warning(
                "coverage: cannot load %s.py for %s: %s",
                name,
                case_dir.name,
                exc,
            )
            continue
        if not hasattr(mod, "run_checks"):
            continue
        try:
            emitted |= {c.check_name for c in mod.run_checks(reference)}
        except Exception as exc:
            logger.warning(
                "coverage: %s.run_checks raised on %s: %s — coverage may be"
                " inflated (failed checks not counted in emitted set)",
                name,
                case_dir.name,
                exc,
            )
            continue

    labeled: set[str] = set()
    for n in negatives:
        labeled |= set(n.get("must_fail", []) or [])
        labeled |= set(n.get("should_fail", []) or [])

    covered = labeled & emitted
    result.emitted_checks = sorted(emitted)
    result.labeled_checks = sorted(labeled)
    result.uncovered_checks = sorted(emitted - labeled)
    result.stale_labels = sorted(labeled - emitted)
    result.coverage = (len(covered) / len(emitted)) if emitted else 1.0


def iter_cases(
    cases_root: Path,
    case_filter: str | None,
    category_filter: str | None,
) -> list[Path]:
    import sys as _sys

    _src = str(Path(__file__).parent.parent / "src")
    if _src not in _sys.path:
        _sys.path.insert(0, _src)
    from embedeval.runner import iter_case_dirs  # noqa: E402

    out: list[Path] = []
    for case_dir in iter_case_dirs(cases_root):
        if case_filter and case_dir.name != case_filter:
            continue
        if category_filter and not case_dir.name.startswith(category_filter):
            continue
        out.append(case_dir)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", default="cases", help="cases root directory")
    parser.add_argument("--case", help="run a single case")
    parser.add_argument("--category", help="filter by category prefix")
    parser.add_argument("--json", help="write report as JSON to this path")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="REQ-02: compute and report per-check coverage (warn-only)",
    )
    parser.add_argument(
        "--strict-coverage",
        action="store_true",
        help="REQ-02: exit 1 if any non-grandfathered TC has coverage < threshold",
    )
    parser.add_argument(
        "--coverage-min",
        type=float,
        default=COVERAGE_MIN_DEFAULT,
        help=f"REQ-02: coverage threshold (default {COVERAGE_MIN_DEFAULT})",
    )
    args = parser.parse_args()

    cases_root = Path(args.cases).resolve()
    if not cases_root.is_dir():
        print(f"ERROR: cases dir not found: {cases_root}", file=sys.stderr)
        return 2

    want_coverage = args.coverage or args.strict_coverage
    grandfather = _load_grandfather() if args.strict_coverage else frozenset()

    results: list[OracleResult] = []
    for case_dir in iter_cases(cases_root, args.case, args.category):
        r = verify_case(case_dir)
        if want_coverage:
            compute_coverage(case_dir, r)
        results.append(r)

    # Text report
    passed = sum(1 for r in results if r.status == "pass")
    failed = sum(1 for r in results if r.status == "fail")
    skipped = sum(1 for r in results if r.status == "skip")

    # Coverage findings — only surfaced when requested.
    coverage_below: list[OracleResult] = []
    if want_coverage:
        coverage_below = [
            r
            for r in results
            if r.coverage is not None and r.coverage < args.coverage_min
        ]

    if not args.quiet:
        for r in results:
            if r.status == "fail":
                print(f"FAIL {r.case_id}")
                for m in r.missed:
                    print(f"  - {m}")
            elif r.status == "pass" and args.case:
                print(f"PASS {r.case_id} ({r.negatives_attempted} negatives)")

        print(f"\nTotal: {len(results)} | PASS={passed} FAIL={failed} SKIP={skipped}")

        if want_coverage:
            measured = [r for r in results if r.coverage is not None]
            ok = [r for r in measured if r.coverage >= args.coverage_min]
            print()
            print(
                f"Coverage (threshold {args.coverage_min:.0%}):"
                f" {len(ok)} ok,"
                f" {len(coverage_below)} below,"
                f" {len(results) - len(measured)} not measured (no negatives.py)"
            )
            for r in coverage_below:
                gf = " [grandfathered]" if r.case_id in grandfather else ""
                pct = f"{r.coverage:.0%}" if r.coverage is not None else "n/a"
                covered_n = len(set(r.labeled_checks) & set(r.emitted_checks))
                total_n = len(r.emitted_checks)
                print(
                    f"  COV {r.case_id}: {pct}"
                    f" ({covered_n}/{total_n} checks covered,"
                    f" uncovered={r.uncovered_checks}){gf}"
                )
                if r.stale_labels:
                    print(f"    stale labels: {r.stale_labels}")

    if args.json:
        Path(args.json).write_text(json.dumps([asdict(r) for r in results], indent=2))

    # Compute exit code with both conditions visible; do NOT early-return
    # on coverage alone or the oracle failure message gets masked when
    # both trip in the same run.
    exit_code = 1 if failed > 0 else 0

    if args.strict_coverage:
        blocking = [r for r in coverage_below if r.case_id not in grandfather]
        if blocking:
            if not args.quiet:
                print(
                    f"\nSTRICT COVERAGE: {len(blocking)} non-grandfathered TC(s) below threshold",
                    file=sys.stderr,
                )
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
