"""Verify the SDK-bucket layout introduced by PLAN-sdk-bucket-split.

Every case lives under ``cases/<sdk>/<case-id>/`` and declares the same
``sdk:`` value in its ``metadata.yaml``. These tests catch drift: if
someone adds a TC to the wrong bucket or forgets the ``sdk:`` field,
the migration invariant is violated.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
import yaml

import json

from embedeval.cli import _parse_sdk_filter
from embedeval.models import (
    CaseCategory,
    CaseMetadata,
    DifficultyTier,
    EvalPlatform,
    EvalResult,
    LayerResult,
    Sdk,
    TokenUsage,
)
from embedeval.reporter import _sdk_breakdown
from embedeval.runner import (
    Filters,
    discover_cases,
    filter_cases,
    iter_case_dirs,
    load_case_metadata,
)
from embedeval.scorer import _calculate_sdk_scores

CASES_DIR = Path(__file__).parent.parent / "cases"
MANIFEST = CASES_DIR / "SDK_LAYOUT.yaml"


def test_cases_dir_has_only_sdk_buckets() -> None:
    """Top level of cases/ must be the 5 bucket dirs plus the manifest."""
    top = {p.name for p in CASES_DIR.iterdir() if not p.name.startswith(".")}
    expected = {s.value for s in Sdk} | {"SDK_LAYOUT.yaml"}
    assert top == expected, f"unexpected entries: {top - expected}"


def test_every_case_has_sdk_matching_parent_bucket() -> None:
    """``metadata.yaml`` sdk: must match the parent bucket dir name."""
    mismatches: list[str] = []
    for case_dir, meta in discover_cases(CASES_DIR):
        bucket = case_dir.parent.name
        if meta.sdk.value != bucket:
            mismatches.append(f"{meta.id}: sdk={meta.sdk.value}, bucket={bucket}")
    assert not mismatches, "SDK field vs parent dir mismatch:\n" + "\n".join(mismatches)


def test_bucket_counts_match_manifest() -> None:
    """Per-bucket counts must match SDK_LAYOUT.yaml exactly."""
    manifest = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    expected = Counter(entry["sdk"] for entry in manifest["cases"].values())

    cases = discover_cases(CASES_DIR)
    observed = Counter(m.sdk.value for _, m in cases)

    assert dict(observed) == dict(expected), (
        f"bucket count drift — observed={observed}, expected={expected}"
    )


def test_discover_is_recursive() -> None:
    """discover_cases must walk into SDK bucket dirs, not stop at top level."""
    cases = discover_cases(CASES_DIR)
    assert len(cases) >= 180, "expected ~185 cases after migration"
    # At least one case per non-empty bucket should appear.
    seen_sdks = {m.sdk for _, m in cases}
    assert Sdk.ZEPHYR in seen_sdks
    assert Sdk.EMBEDDED_LINUX in seen_sdks
    assert Sdk.FREERTOS in seen_sdks
    assert Sdk.ESP_IDF in seen_sdks
    assert Sdk.STM32_HAL in seen_sdks


@pytest.mark.parametrize(
    "sdk,min_count",
    [
        (Sdk.ZEPHYR, 100),
        (Sdk.EMBEDDED_LINUX, 38),
        (Sdk.FREERTOS, 1),
        (Sdk.ESP_IDF, 5),
        (Sdk.STM32_HAL, 4),
    ],
)
def test_sdk_filter_returns_only_that_bucket(sdk: Sdk, min_count: int) -> None:
    cases = discover_cases(CASES_DIR)
    filtered = filter_cases(cases, Filters(sdks=[sdk]))
    assert len(filtered) >= min_count
    for _, meta in filtered:
        assert meta.sdk == sdk


def test_boot_uboot_rename_present() -> None:
    """The only ID rename (boot-002 -> boot-uboot-001) must be applied."""
    ids = {m.id for _, m in discover_cases(CASES_DIR)}
    assert "boot-uboot-001" in ids
    assert "boot-002" not in ids


def test_no_legacy_flat_case_dirs() -> None:
    """After migration, no metadata.yaml should live at cases/<id>/ directly."""
    stray: list[str] = []
    for entry in CASES_DIR.iterdir():
        if entry.is_dir() and entry.name not in {s.value for s in Sdk}:
            if (entry / "metadata.yaml").is_file():
                stray.append(entry.name)
    assert not stray, f"legacy flat case dirs remain: {stray}"


# -----------------------------------------------------------------------
# _parse_sdk_filter error + edge paths (TG-2)
# -----------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        (None, []),
        ("", []),
        (",", []),
        ("zephyr", [Sdk.ZEPHYR]),
        ("zephyr,freertos", [Sdk.ZEPHYR, Sdk.FREERTOS]),
        ("zephyr, freertos ", [Sdk.ZEPHYR, Sdk.FREERTOS]),
        ("zephyr,,freertos", [Sdk.ZEPHYR, Sdk.FREERTOS]),
        ("zephyr,", [Sdk.ZEPHYR]),
    ],
)
def test_parse_sdk_filter_happy_and_edge(raw: str | None, expected: list[Sdk]) -> None:
    assert _parse_sdk_filter(raw) == expected


def test_parse_sdk_filter_rejects_unknown() -> None:
    import typer

    with pytest.raises(typer.Exit) as exc:
        _parse_sdk_filter("RTOS")
    assert exc.value.exit_code == 1


# -----------------------------------------------------------------------
# iter_case_dirs direct test (TG-3)
# -----------------------------------------------------------------------


def test_iter_case_dirs_flat_and_bucketed(tmp_path: Path) -> None:
    """Helper must pick up both flat-legacy and SDK-bucketed cases."""
    # Flat-legacy case
    flat = tmp_path / "kconfig-999"
    flat.mkdir()
    (flat / "metadata.yaml").write_text("id: kconfig-999\n")
    # Bucketed case
    bucketed = tmp_path / "zephyr" / "threading-999"
    bucketed.mkdir(parents=True)
    (bucketed / "metadata.yaml").write_text("id: threading-999\n")
    # Bucket dir with no metadata in child — should be skipped
    (tmp_path / "zephyr" / "stub-dir").mkdir()
    # Non-dir top entry — should be skipped
    (tmp_path / "README.md").write_text("")

    names = [p.name for p in iter_case_dirs(tmp_path)]
    assert sorted(names) == ["kconfig-999", "threading-999"]


def test_iter_case_dirs_empty_root() -> None:
    assert iter_case_dirs(Path("/nonexistent-path-xyz")) == []


# -----------------------------------------------------------------------
# Sdk enum YAML round-trip (TG-1)
# -----------------------------------------------------------------------


@pytest.mark.parametrize("sdk", list(Sdk))
def test_sdk_enum_yaml_roundtrip(tmp_path: Path, sdk: Sdk) -> None:
    """Each Sdk value must load from YAML into a valid CaseMetadata."""
    case_dir = tmp_path / f"case-{sdk.value}"
    case_dir.mkdir()
    meta_text = (
        f"id: case-1\n"
        f"category: kconfig\n"
        f"difficulty: easy\n"
        f'title: "t"\n'
        f'description: "d"\n'
        f"tags: []\n"
        f"platform: native_sim\n"
        f"sdk: {sdk.value}\n"
        f"estimated_tokens: 100\n"
        f'sdk_version: "1.0"\n'
    )
    (case_dir / "metadata.yaml").write_text(meta_text)
    meta = load_case_metadata(case_dir)
    assert meta is not None
    assert meta.sdk == sdk


def test_sdk_invalid_value_fails_load(tmp_path: Path) -> None:
    case_dir = tmp_path / "bad"
    case_dir.mkdir()
    (case_dir / "metadata.yaml").write_text(
        "id: bad\ncategory: kconfig\ndifficulty: easy\n"
        'title: "t"\ndescription: "d"\ntags: []\n'
        "platform: native_sim\nsdk: RTOS\nestimated_tokens: 100\n"
        'sdk_version: "1.0"\n'
    )
    # Invalid sdk → Pydantic ValidationError → load_case_metadata returns None
    assert load_case_metadata(case_dir) is None


# -----------------------------------------------------------------------
# _calculate_sdk_scores (TG-3)
# -----------------------------------------------------------------------


def _mk_result(case_id: str, sdk: Sdk | None, passed: bool) -> EvalResult:
    return EvalResult(
        case_id=case_id,
        category=CaseCategory.KCONFIG,
        sdk=sdk,
        model="test",
        attempt=1,
        generated_code="",
        layers=[
            LayerResult(
                layer=0,
                name="static_analysis",
                passed=passed,
                details=[],
                duration_seconds=0.0,
            )
        ],
        failed_at_layer=None if passed else 0,
        passed=passed,
        duration_seconds=0.0,
        token_usage=TokenUsage(input_tokens=0, output_tokens=0, total_tokens=0),
        cost_usd=0.0,
    )


def test_calculate_sdk_scores_mixed_buckets() -> None:
    """Happy path: pass/fail counts rolled up per SDK bucket."""
    results = [
        _mk_result("a", Sdk.ZEPHYR, True),
        _mk_result("b", Sdk.ZEPHYR, False),
        _mk_result("c", Sdk.FREERTOS, True),
    ]
    scores = _calculate_sdk_scores(results)
    by_sdk = {s.sdk: s for s in scores}
    assert by_sdk[Sdk.ZEPHYR].total_cases == 2
    assert by_sdk[Sdk.ZEPHYR].passed_cases == 1
    assert by_sdk[Sdk.ZEPHYR].pass_at_1 == 0.5
    assert by_sdk[Sdk.FREERTOS].passed_cases == 1
    assert by_sdk[Sdk.FREERTOS].pass_at_1 == 1.0


def test_calculate_sdk_scores_skips_sdk_none() -> None:
    """Results with sdk=None (pre-migration tracker entries) are excluded."""
    results = [
        _mk_result("a", None, True),
        _mk_result("b", Sdk.ZEPHYR, True),
    ]
    scores = _calculate_sdk_scores(results)
    assert len(scores) == 1
    assert scores[0].sdk == Sdk.ZEPHYR


def test_calculate_sdk_scores_empty() -> None:
    assert _calculate_sdk_scores([]) == []


# -----------------------------------------------------------------------
# _sdk_breakdown reporter section (TG-4)
# -----------------------------------------------------------------------


def test_sdk_breakdown_absent_when_no_scores() -> None:
    from embedeval.models import BenchmarkReport, OverallScore

    report = BenchmarkReport(
        version="0.1.0",
        date="2026-04-19",
        models=[],
        categories=[],
        overall=OverallScore(
            total_cases=0,
            total_models=0,
            best_model="none",
            best_pass_at_1=0.0,
        ),
    )
    # No sdk_scores (default empty) → section is suppressed.
    assert _sdk_breakdown([report]) == []


def test_sdk_breakdown_present_with_thin_bucket_caveat() -> None:
    from embedeval.models import BenchmarkReport, OverallScore, SdkScore

    report = BenchmarkReport(
        version="0.1.0",
        date="2026-04-19",
        models=[],
        categories=[],
        sdk_scores=[
            SdkScore(sdk=Sdk.ZEPHYR, pass_at_1=0.5, total_cases=100, passed_cases=50),
            SdkScore(sdk=Sdk.FREERTOS, pass_at_1=1.0, total_cases=1, passed_cases=1),
        ],
        overall=OverallScore(
            total_cases=101,
            total_models=0,
            best_model="none",
            best_pass_at_1=0.5,
        ),
    )
    lines = _sdk_breakdown([report])
    text = "\n".join(lines)
    assert "## SDK Breakdown" in text
    assert "zephyr" in text
    assert "freertos" in text
    # Thin-bucket caveat only on n<8 row
    zephyr_row = next(line for line in lines if "zephyr" in line)
    freertos_row = next(line for line in lines if "freertos" in line)
    assert "thin bucket" not in zephyr_row
    assert "thin bucket (n<8)" in freertos_row


# -----------------------------------------------------------------------
# test_tracker.json rename applied (TG-7)
# -----------------------------------------------------------------------


def test_tracker_boot_uboot_rename_applied() -> None:
    """results/test_tracker.json must have boot-uboot-001 (not boot-002)."""
    tracker_path = Path(__file__).parent.parent / "results" / "test_tracker.json"
    if not tracker_path.is_file():
        pytest.skip("tracker not present")
    data = json.loads(tracker_path.read_text(encoding="utf-8"))
    for model, per_model in data.get("results", {}).items():
        if not isinstance(per_model, dict):
            continue
        assert "boot-002" not in per_model, f"stale boot-002 key under {model!r}"
        # boot-uboot-001 may or may not be present depending on whether the
        # model had ever evaluated it — but if present, the rename landed.
        if "boot-uboot-001" in per_model:
            assert per_model["boot-uboot-001"]["case_id"] == "boot-uboot-001"
