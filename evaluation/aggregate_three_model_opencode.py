"""Rebuild OpenCode-only metrics for the three frozen model runs."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
import csv
import hashlib
import json
import statistics

from aggregate_results import percentile, usage


ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    "opus_gateway": ROOT / "experiments/2026-10-20-opus5-harness-comparison/runs/run-20261020-154313-c6793e",
    "qwen_openrouter": ROOT / "experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154440-282906",
    "qwen_local_optimized": ROOT / "experiments/2026-10-21-local-qwen38-27b-opencode/runs/run-20261021-140708-d22d11",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    groups = []
    rows = []
    expected_cases = None
    expected_source = None
    for name, run in RUNS.items():
        config = read(run / "config.json")
        assert not config["dry_run"]
        assert hashlib.sha256((run / "frozen-runner.py").read_bytes()).hexdigest() == config["runner_sha256"]
        cases = [case["id"] for case in config["subset"]["cases"]]
        if expected_cases is None:
            expected_cases, expected_source = cases, config["source_sha256"]
        assert cases == expected_cases and config["source_sha256"] == expected_source
        results = [read(path) for path in sorted(run.glob("tasks/opencode__*/*/result.json"))]
        assert len(results) == len(cases) == 10
        assert sorted(result["case_id"] for result in results) == sorted(cases)
        for result in results:
            folder = Path(result["artifact_directory"])
            assert folder.is_dir()
            events = read(folder / "trace.json")
            evaluation_path = folder / "evaluation.json"
            evaluation = read(evaluation_path) if evaluation_path.exists() else None
            layers = evaluation["layers"] if evaluation else []
            failed_checks = [f"L{layer['layer']}:{detail['check_name']}"
                             for layer in layers for detail in layer["details"] if not detail["passed"]]
            rows.append({
                "model_group": name, "case_id": result["case_id"],
                "status": result["status"], "passed": result["passed"],
                "seconds": result["duration_seconds"],
                "started_at": result["started_at"], "ended_at": result["ended_at"],
                "l0_pass": next((layer["passed"] for layer in layers if layer["layer"] == 0), None),
                "l3_pass": next((layer["passed"] for layer in layers if layer["layer"] == 3), None),
                "failed_checks": failed_checks,
                "tool_calls": sum(event.get("type") == "tool_use" for event in events),
                "response_models": sorted({event.get("message", {}).get("model") for event in events
                                           if event.get("type") == "assistant" and event.get("message", {}).get("model")}),
                "artifact_directory": folder.relative_to(ROOT).as_posix(),
                **usage(events, "opencode", result["status"]),
            })
        group_rows = [row for row in rows if row["model_group"] == name]
        times = [row["seconds"] for row in group_rows]
        start = min(datetime.fromisoformat(row["started_at"]) for row in group_rows)
        end = max(datetime.fromisoformat(row["ended_at"]) for row in group_rows)
        usage_fields = ("observed_input", "observed_cache_read", "observed_cache_write",
                        "observed_output_including_reasoning", "observed_reasoning", "observed_total")
        groups.append({
            "model_group": name, "requested_model": config["model"],
            "base_url": config["base_url"], "run": run.relative_to(ROOT).as_posix(),
            "passed": sum(row["passed"] for row in group_rows),
            "scored": sum(row["status"].startswith("scored_") for row in group_rows),
            "planned": len(group_rows),
            "status_counts": dict(Counter(row["status"] for row in group_rows)),
            "l0_passed": sum(row["l0_pass"] is True for row in group_rows),
            "l3_passed": sum(row["l3_pass"] is True for row in group_rows),
            "l3_evaluated": sum(row["l3_pass"] is not None for row in group_rows),
            "sum_seconds": sum(times), "mean_seconds": statistics.mean(times),
            "median_seconds": statistics.median(times),
            "p95_seconds": percentile(times, .95), "max_seconds": max(times),
            "tool_calls": sum(row["tool_calls"] for row in group_rows),
            "usage_coverage": dict(Counter(row["coverage"] for row in group_rows)),
            "usage_sums": {field: sum(row[field] or 0 for row in group_rows)
                           for field in usage_fields},
            "started_shanghai": start.astimezone(timezone(timedelta(hours=8))).isoformat(),
            "ended_shanghai": end.astimezone(timezone(timedelta(hours=8))).isoformat(),
            "batch_wall_seconds": (end - start).total_seconds(),
        })
    output = {"scope": "OpenCode only; original L0+L3 scores; one run per model",
              "source_sha256": expected_source, "cases": expected_cases,
              "groups": groups, "tasks": rows}
    target = ROOT / "evaluation/opencode-three-model-results.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "evaluation/opencode-three-model-results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        columns = ("model_group", "case_id", "status", "passed", "seconds", "coverage",
                   "observed_input", "observed_cache_read", "observed_cache_write",
                   "observed_output_including_reasoning", "observed_reasoning", "observed_total",
                   "tool_calls", "artifact_directory", "failed_checks")
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "failed_checks": "; ".join(row["failed_checks"])})
    print(json.dumps({"groups": groups}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
