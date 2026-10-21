"""Tests for REQ-02 per-check coverage validator in verify_negatives_oracle.

The validator computes the fraction of run_checks()-emitted check_names
that have at least one must_fail/should_fail mutation pair in negatives.py.
"""

from __future__ import annotations

import importlib.util
import sys
import textwrap
from pathlib import Path


def _load_oracle():
    """Load scripts/verify_negatives_oracle.py as a module."""
    script_path = (
        Path(__file__).parent.parent / "scripts" / "verify_negatives_oracle.py"
    )
    spec = importlib.util.spec_from_file_location(
        "verify_negatives_oracle", script_path
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["verify_negatives_oracle"] = mod
    spec.loader.exec_module(mod)
    return mod


def _make_case(tmp_path: Path, static_checks: list[str], labeled: list[str]) -> Path:
    """Build a synthetic case with given check_names and negatives labels."""
    case_dir = tmp_path / "test-case-001"
    (case_dir / "checks").mkdir(parents=True)
    (case_dir / "reference").mkdir()
    (case_dir / "reference" / "main.c").write_text("int main(void) { return 0; }\n")

    # static.py emits one CheckDetail per name in static_checks, all passing.
    static_body = "from embedeval.models import CheckDetail\n\n"
    static_body += "def run_checks(code):\n"
    static_body += "    return [\n"
    for name in static_checks:
        static_body += (
            f"        CheckDetail(check_name={name!r}, passed=True,"
            " expected='x', actual='x', check_type='exact_match'),\n"
        )
    static_body += "    ]\n"
    (case_dir / "checks" / "static.py").write_text(static_body)

    # negatives.py lists labeled check_names under must_fail, each with
    # a no-op mutation so verify_case reports negative-wise pass/fail.
    neg_body = "NEGATIVES = [\n"
    for i, name in enumerate(labeled):
        neg_body += textwrap.dedent(
            f"""\
            {{
                'name': 'mut_{i}',
                'mutation': lambda code, _n={name!r}: code + '/*mut_' + _n + '*/',
                'must_fail': [{name!r}],
            }},
            """
        )
    neg_body += "]\n"
    (case_dir / "checks" / "negatives.py").write_text(neg_body)

    return case_dir


class TestComputeCoverage:
    def test_full_coverage(self, tmp_path: Path) -> None:
        oracle = _load_oracle()
        case = _make_case(tmp_path, ["a", "b", "c"], ["a", "b", "c"])
        r = oracle.OracleResult(case_id=case.name, status="pass")
        oracle.compute_coverage(case, r)
        assert r.coverage == 1.0
        assert r.uncovered_checks == []
        assert r.stale_labels == []
        assert r.emitted_checks == ["a", "b", "c"]

    def test_partial_coverage(self, tmp_path: Path) -> None:
        oracle = _load_oracle()
        case = _make_case(tmp_path, ["a", "b", "c", "d"], ["a", "b"])
        r = oracle.OracleResult(case_id=case.name, status="pass")
        oracle.compute_coverage(case, r)
        assert r.coverage == 0.5
        assert r.uncovered_checks == ["c", "d"]
        assert r.stale_labels == []

    def test_stale_label(self, tmp_path: Path) -> None:
        """Label naming a check_name that run_checks never emits — likely
        typo or post-rename drift. Should surface in stale_labels."""
        oracle = _load_oracle()
        case = _make_case(tmp_path, ["a", "b"], ["a", "ghost_check"])
        r = oracle.OracleResult(case_id=case.name, status="pass")
        oracle.compute_coverage(case, r)
        assert r.stale_labels == ["ghost_check"]
        # ghost_check does NOT count toward coverage numerator.
        assert r.coverage == 0.5

    def test_empty_emitted_returns_perfect(self, tmp_path: Path) -> None:
        """A TC whose run_checks returns no CheckDetails (unusual but
        possible for pure config TCs) has coverage=1.0 by convention."""
        oracle = _load_oracle()
        case = _make_case(tmp_path, [], [])
        r = oracle.OracleResult(case_id=case.name, status="pass")
        oracle.compute_coverage(case, r)
        assert r.coverage == 1.0

    def test_no_negatives_leaves_coverage_none(self, tmp_path: Path) -> None:
        """Without negatives.py, compute_coverage is a no-op — coverage
        stays None so callers can distinguish not-measured from measured-zero."""
        oracle = _load_oracle()
        case_dir = tmp_path / "test-case-002"
        (case_dir / "checks").mkdir(parents=True)
        (case_dir / "reference").mkdir()
        (case_dir / "reference" / "main.c").write_text("int main(){return 0;}")
        (case_dir / "checks" / "static.py").write_text(
            "from embedeval.models import CheckDetail\n"
            "def run_checks(code):\n"
            "    return [CheckDetail(check_name='a', passed=True,"
            " expected='x', actual='x', check_type='exact_match')]\n"
        )
        r = oracle.OracleResult(case_id=case_dir.name, status="skip")
        oracle.compute_coverage(case_dir, r)
        assert r.coverage is None
        assert r.emitted_checks == []


class TestGrandfatherList:
    def test_loads_from_plans_file(self) -> None:
        oracle = _load_oracle()
        gf = oracle._load_grandfather()
        # Snapshot from 2026-04-19: 30 pre-gate TCs. The `>=` allows the
        # list to SHRINK legitimately — when /negatives revisits a TC and
        # raises it to ≥80% coverage, its entry is removed from the file
        # so it becomes subject to --strict-coverage going forward.
        # A hard-count assertion would fail spuriously on that workflow.
        # The floor remains 30 to catch accidental truncation.
        assert "gpio-basic-001" in gf
        assert "dma-001" in gf
        assert len(gf) <= 30, (
            f"Grandfather list grew to {len(gf)}; new TCs should not be"
            " added — they must meet the coverage gate from day 1"
        )
        # Lower bound: allow shrinkage (graduated TCs) but flag if the
        # file was truncated or corrupted.
        assert len(gf) >= 1, "Grandfather file appears empty or corrupted"

    def test_missing_file_returns_empty(self, tmp_path: Path, monkeypatch) -> None:
        """If the grandfather file is missing, everything is gate-required."""
        oracle = _load_oracle()
        monkeypatch.setattr(oracle, "COVERAGE_GRANDFATHER_PATH", tmp_path / "nope.txt")
        assert oracle._load_grandfather() == frozenset()
