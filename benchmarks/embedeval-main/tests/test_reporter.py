"""Tests for EmbedEval reporter."""

import json
from pathlib import Path

from embedeval.models import (
    BenchmarkReport,
    CaseCategory,
    CategoryScore,
    CheckDetail,
    EvalResult,
    LayerResult,
    ModelScore,
    OverallScore,
    TokenUsage,
)
from embedeval.reporter import (
    generate_json,
    generate_leaderboard,
    generate_per_check_metrics,
)


def _make_report() -> BenchmarkReport:
    """Create a sample benchmark report."""
    return BenchmarkReport(
        version="0.1.0",
        date="2026-03-23",
        models=[
            ModelScore(
                model="gpt-4",
                pass_at_1=0.8,
                pass_at_5=0.95,
                total_cases=10,
                passed_cases=8,
                layer_pass_rates={
                    "static_analysis": 1.0,
                    "compile_gate": 0.9,
                    "runtime_execution": 0.85,
                    "static_heuristic": 0.8,
                    "test_quality_proof": 0.8,
                },
            ),
            ModelScore(
                model="claude-3",
                pass_at_1=0.7,
                pass_at_5=0.9,
                total_cases=10,
                passed_cases=7,
                layer_pass_rates={
                    "static_analysis": 0.95,
                    "compile_gate": 0.85,
                    "runtime_execution": 0.8,
                    "static_heuristic": 0.7,
                    "test_quality_proof": 0.7,
                },
            ),
        ],
        categories=[
            CategoryScore(
                category=CaseCategory.KCONFIG,
                pass_at_1=0.9,
                total_cases=5,
                passed_cases=4,
            ),
            CategoryScore(
                category=CaseCategory.BLE,
                pass_at_1=0.4,
                total_cases=5,
                passed_cases=2,
            ),
        ],
        overall=OverallScore(
            total_cases=10,
            total_models=2,
            best_model="gpt-4",
            best_pass_at_1=0.8,
        ),
    )


class TestGenerateJson:
    """Tests for JSON report generation."""

    def test_creates_valid_json(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "results" / "report.json"
        generate_json(report, output)

        assert output.exists()
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["version"] == "0.1.0"

    def test_json_contains_models(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "report.json"
        generate_json(report, output)

        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data["models"]) == 2
        assert data["models"][0]["model"] == "gpt-4"

    def test_json_contains_categories(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "report.json"
        generate_json(report, output)

        data = json.loads(output.read_text(encoding="utf-8"))
        assert len(data["categories"]) == 2

    def test_json_contains_overall(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "report.json"
        generate_json(report, output)

        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["overall"]["best_model"] == "gpt-4"

    def test_creates_parent_directories(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "deep" / "nested" / "report.json"
        generate_json(report, output)
        assert output.exists()


class TestGenerateLeaderboard:
    """Tests for Markdown leaderboard generation."""

    def test_creates_markdown_file(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)
        assert output.exists()

    def test_contains_header(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "# EmbedEval Leaderboard" in content

    def test_contains_schema_version_comment(self, tmp_path: Path) -> None:
        """REQ-05: SCHEMA_VERSION marker must be present for consumers."""
        from embedeval.reporter import LEADERBOARD_SCHEMA_VERSION

        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert f"<!-- SCHEMA_VERSION: {LEADERBOARD_SCHEMA_VERSION} -->" in content

    def test_schema_version_precedes_sections(self, tmp_path: Path) -> None:
        """Schema version comment must appear before any table header so
        consumers that parse the first N lines see it."""
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        version_idx = content.find("SCHEMA_VERSION:")
        first_section_idx = content.find("## ")
        assert version_idx != -1
        assert first_section_idx != -1
        assert version_idx < first_section_idx

    def test_contains_model_table(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "## Model Comparison" in content
        assert "| Model |" in content
        assert "gpt-4" in content
        assert "claude-3" in content

    def test_contains_category_heatmap(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "## Category Results" in content
        assert "kconfig" in content
        assert "PASS" in content
        assert "FAIL" in content

    def test_pass_fail_icons(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "PASS" in content
        assert "FAIL" in content

    def test_multiple_reports(self, tmp_path: Path) -> None:
        report1 = _make_report()
        report2 = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report1, report2], output)

        content = output.read_text(encoding="utf-8")
        assert content.count("gpt-4") >= 2

    def test_empty_reports(self, tmp_path: Path) -> None:
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([], output)

        content = output.read_text(encoding="utf-8")
        assert "# EmbedEval Leaderboard" in content

    def test_contains_layer_heatmap(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "## Layer Pass Rate Heatmap" in content
        assert "L0 Static" in content
        assert "L1 Build" in content
        assert "L2 Runtime" in content
        assert "L3 Heuristic" in content
        assert "L4 Mutation" in content
        assert "100%" in content
        assert "90%" in content

    def test_layer_heatmap_shows_all_models(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        # Both models should appear in the layer heatmap
        lines = content.split("\n")
        heatmap_lines = []
        in_heatmap = False
        for line in lines:
            if "## Layer Pass Rate Heatmap" in line:
                in_heatmap = True
                continue
            if in_heatmap and line.startswith("## "):
                break
            if (
                in_heatmap
                and line.startswith("|")
                and "Model" not in line
                and "---" not in line
            ):
                heatmap_lines.append(line)
        assert len(heatmap_lines) == 2
        assert any("gpt-4" in line for line in heatmap_lines)
        assert any("claude-3" in line for line in heatmap_lines)

    def test_contains_failure_distribution(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "## Failure Distribution" in content
        assert "| Layer | Failures | % of Total |" in content
        assert "L0 Static" in content
        assert "L1 Build" in content

    def test_failure_distribution_percentages(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        # L0 Static has lowest failures (0.0 + 0.05 = 0.05)
        # so it should have lowest % of total
        assert "% |" in content

    def test_contains_category_breakdown(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "## Category Breakdown" in content
        assert "| Category | Pass@1 | Cases |" in content
        assert "kconfig" in content
        assert "ble" in content

    def test_category_breakdown_values(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        # kconfig has pass_at_1=0.9 -> 90%, 5 cases
        assert "90%" in content
        assert "| 5 |" in content
        # ble has pass_at_1=0.4 -> 40%, 5 cases
        assert "40%" in content

    def test_layer_heatmap_missing_layers(self, tmp_path: Path) -> None:
        """Test that missing layers show '-' in the heatmap."""
        report = BenchmarkReport(
            version="0.1.0",
            date="2026-03-23",
            models=[
                ModelScore(
                    model="partial-model",
                    pass_at_1=0.5,
                    pass_at_5=0.7,
                    total_cases=5,
                    passed_cases=3,
                    layer_pass_rates={
                        "static_analysis": 0.9,
                        "compile_gate": 0.8,
                    },
                ),
            ],
            categories=[],
            overall=OverallScore(
                total_cases=5,
                total_models=1,
                best_model="partial-model",
                best_pass_at_1=0.5,
            ),
        )
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        # Missing layers should show "-"
        lines = content.split("\n")
        heatmap_lines = [
            l for l in lines if "partial-model" in l and "L0 Static" not in l
        ]
        # Find the line in the layer heatmap section (not Model Comparison)
        # The heatmap line should contain "-" for missing layers
        model_line = [l for l in heatmap_lines if "90%" in l][0]
        parts = [p.strip() for p in model_line.split("|") if p.strip()]
        dash_cells = [p for p in parts if p == "-"]
        assert len(dash_cells) == 3

    def test_empty_reports_still_has_all_sections(self, tmp_path: Path) -> None:
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([], output)

        content = output.read_text(encoding="utf-8")
        assert "## Model Comparison" in content
        assert "## Category Results" in content
        assert "## Layer Pass Rate Heatmap" in content
        assert "## Failure Distribution" in content
        assert "## Category Breakdown" in content


class TestComparabilityWarning:
    """Tests for leaderboard comparability warning when models have different case sets."""

    def test_no_warning_when_same_cases(self, tmp_path: Path) -> None:
        report = _make_report()
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "Warning" not in content
        assert "comparable" not in content.lower().split("pass@1 (quality)")[0]

    def test_warning_and_comparable_column_when_different_cases(self, tmp_path: Path) -> None:
        report = BenchmarkReport(
            version="0.1.0",
            date="2026-03-31",
            models=[
                ModelScore(
                    model="sonnet",
                    pass_at_1=0.55,
                    pass_at_1_comparable=0.60,
                    pass_at_5=0.70,
                    total_cases=227,
                    passed_cases=125,
                    comparable_cases=179,
                    layer_pass_rates={"static_analysis": 0.9},
                ),
                ModelScore(
                    model="haiku",
                    pass_at_1=0.34,
                    pass_at_1_comparable=0.34,
                    pass_at_5=0.50,
                    total_cases=179,
                    passed_cases=61,
                    comparable_cases=179,
                    layer_pass_rates={"static_analysis": 0.8},
                ),
            ],
            categories=[],
            overall=OverallScore(
                total_cases=227,
                total_models=2,
                best_model="sonnet",
                best_pass_at_1=0.55,
                common_cases=179,
                case_set_warning="Models tested on different case sets: haiku=179, sonnet=227. Use comparable scores for fair comparison.",
            ),
        )
        output = tmp_path / "LEADERBOARD.md"
        generate_leaderboard([report], output)

        content = output.read_text(encoding="utf-8")
        assert "Warning" in content
        assert "pass@1 (comparable)" in content
        assert "Common" in content
        assert "60.0%" in content
        assert "179" in content


def _make_result(
    case_id: str,
    category: CaseCategory,
    model: str,
    details: list[CheckDetail],
    passed: bool = True,
) -> EvalResult:
    return EvalResult(
        case_id=case_id,
        category=category,
        model=model,
        attempt=1,
        generated_code="int main(){return 0;}",
        layers=[
            LayerResult(
                layer=0,
                name="static_analysis",
                passed=all(d.passed for d in details),
                details=details,
                duration_seconds=0.01,
            )
        ],
        passed=passed,
        duration_seconds=0.1,
        token_usage=TokenUsage(input_tokens=10, output_tokens=10, total_tokens=20),
        cost_usd=0.0,
    )


def _cd(name: str, passed: bool) -> CheckDetail:
    return CheckDetail(
        check_name=name,
        passed=passed,
        expected="x",
        actual="x" if passed else "y",
        check_type="exact_match",
    )


class TestGeneratePerCheckMetrics:
    """REQ-04: per-(TC, check_name, model) metrics emission."""

    def test_requires_at_least_one_output(self, tmp_path: Path) -> None:
        import pytest

        with pytest.raises(ValueError):
            generate_per_check_metrics({"m": []}, output_json=None, output_md=None)

    def test_rows_grouped_by_tc_check_model(self, tmp_path: Path) -> None:
        results = {
            "sonnet": [
                _make_result("a-1", CaseCategory.KCONFIG, "sonnet", [_cd("c1", True)]),
                _make_result("a-1", CaseCategory.KCONFIG, "sonnet", [_cd("c1", False)]),
                _make_result("a-2", CaseCategory.KCONFIG, "sonnet", [_cd("c1", True)]),
            ],
            "haiku": [
                _make_result("a-1", CaseCategory.KCONFIG, "haiku", [_cd("c1", False)]),
            ],
        }
        rows = generate_per_check_metrics(results, output_json=tmp_path / "m.json")
        # 3 distinct (case, check, model) combos: (a-1,c1,sonnet), (a-2,c1,sonnet), (a-1,c1,haiku)
        assert len(rows) == 3
        keys = {(r["case_id"], r["check_name"], r["model"]) for r in rows}
        assert keys == {("a-1", "c1", "sonnet"), ("a-2", "c1", "sonnet"), ("a-1", "c1", "haiku")}
        sonnet_a1 = next(
            r for r in rows
            if r["case_id"] == "a-1" and r["model"] == "sonnet"
        )
        assert sonnet_a1["samples"] == 2
        assert sonnet_a1["passed"] == 1
        assert sonnet_a1["pass_rate"] == 0.5

    def test_sort_order_worst_first(self, tmp_path: Path) -> None:
        results = {
            "sonnet": [
                _make_result("a-1", CaseCategory.KCONFIG, "sonnet", [_cd("strict", False)]),
                _make_result("a-2", CaseCategory.KCONFIG, "sonnet", [_cd("easy", True)]),
            ],
        }
        rows = generate_per_check_metrics(results, output_json=tmp_path / "m.json")
        # strict (0.0 pass_rate) must come before easy (1.0 pass_rate).
        assert rows[0]["check_name"] == "strict"
        assert rows[-1]["check_name"] == "easy"

    def test_skips_l4_mutation_checks(self, tmp_path: Path) -> None:
        """L4 synthetic mutation_* checks measure benchmark self-test,
        not model behavior — must not pollute per-check metrics."""
        details = [
            _cd("real_check", True),
            CheckDetail(
                check_name="mutation_missing_volatile",
                passed=True,
                expected="x",
                actual="x",
                check_type="mutation",
            ),
        ]
        results = {
            "sonnet": [_make_result("a-1", CaseCategory.KCONFIG, "sonnet", details)],
        }
        rows = generate_per_check_metrics(results, output_json=tmp_path / "m.json")
        assert len(rows) == 1
        assert rows[0]["check_name"] == "real_check"

    def test_json_schema_version(self, tmp_path: Path) -> None:
        import json as _json

        from embedeval.reporter import PER_CHECK_METRICS_SCHEMA_VERSION

        out = tmp_path / "m.json"
        generate_per_check_metrics(
            {"sonnet": [_make_result("a", CaseCategory.KCONFIG, "sonnet", [_cd("c", True)])]},
            output_json=out,
        )
        data = _json.loads(out.read_text())
        assert data["schema_version"] == PER_CHECK_METRICS_SCHEMA_VERSION
        assert "rows" in data and "generated" in data

    def test_markdown_contains_schema_version(self, tmp_path: Path) -> None:
        out = tmp_path / "m.md"
        generate_per_check_metrics(
            {"sonnet": [_make_result("a", CaseCategory.KCONFIG, "sonnet", [_cd("c", True)])]},
            output_md=out,
        )
        content = out.read_text()
        assert "<!-- SCHEMA_VERSION:" in content
        assert "a" in content and "c" in content and "sonnet" in content

    def test_empty_results(self, tmp_path: Path) -> None:
        import json as _json

        out = tmp_path / "empty.json"
        rows = generate_per_check_metrics({"sonnet": []}, output_json=out)
        assert rows == []
        # Hiloop contract: the file must be written even when rows is
        # empty — a consumer walking runs/*/per_check_metrics.json should
        # not silently skip empty runs.
        assert out.exists(), "JSON must be written even when rows is empty"
        data = _json.loads(out.read_text())
        assert data["rows"] == []
        assert data["schema_version"] == 1
        assert "generated" in data
