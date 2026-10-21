"""Reconstruct metrics from the two frozen runs; never changes original scores."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter
import csv
import hashlib
import json
import statistics
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUNS = {
    "opus": ROOT / "experiments/2026-10-20-opus5-harness-comparison/runs/run-20261020-154313-c6793e",
    "qwen": ROOT / "experiments/2026-10-20-qwen38-27b-harness-comparison/runs/run-20261020-154440-282906",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    index = int(position)
    return values[index] + (values[min(index + 1, len(values) - 1)] - values[index]) * (position - index)


def usage(events, harness, status):
    if harness == "opencode":
        steps = [event["part"] for event in events if event.get("type") == "step_finish"]
        if not steps:
            return {"coverage": "unknown", "observed_input": None, "observed_output_including_reasoning": None,
                    "observed_cache_read": None, "observed_cache_write": None, "observed_total": None,
                    "observed_reasoning": None, "llm_completions": 0, "client_cost_estimate_usd": None}
        inp = sum(step.get("tokens", {}).get("input", 0) for step in steps)
        out = sum(step.get("tokens", {}).get("output", 0) for step in steps)
        reasoning = sum(step.get("tokens", {}).get("reasoning", 0) for step in steps)
        cached = sum(step.get("tokens", {}).get("cache", {}).get("read", 0) for step in steps)
        written = sum(step.get("tokens", {}).get("cache", {}).get("write", 0) for step in steps)
        total = sum(step.get("tokens", {}).get("total", 0) for step in steps)
        assert total == inp + out + reasoning + cached + written
        return {"coverage": "complete" if status.startswith("scored_") else "partial",
                "observed_input": inp, "observed_output_including_reasoning": out + reasoning,
                "observed_cache_read": cached, "observed_cache_write": written, "observed_total": total,
                "observed_reasoning": reasoning, "llm_completions": len(steps),
                "client_cost_estimate_usd": None}  # custom provider cost=0 does not mean free
    finals = [event for event in events if event.get("type") == "result"]
    if not finals:
        return {"coverage": "unknown", "observed_input": None, "observed_output_including_reasoning": None,
                "observed_cache_read": None, "observed_cache_write": None, "observed_total": None,
                "observed_reasoning": None, "llm_completions": None, "client_cost_estimate_usd": None}
    final = finals[-1]
    u = final.get("usage", {})
    inp, out = u.get("input_tokens", 0), u.get("output_tokens", 0)
    cached, written = u.get("cache_read_input_tokens", 0), u.get("cache_creation_input_tokens", 0)
    return {"coverage": "complete", "observed_input": inp, "observed_output_including_reasoning": out,
            "observed_cache_read": cached, "observed_cache_write": written,
            "observed_total": inp + out + cached + written,
            "observed_reasoning": u.get("output_tokens_details", {}).get("thinking_tokens"),
            "llm_completions": None, "client_cost_estimate_usd": final.get("total_cost_usd")}


def main():
    rows, groups, batches = [], [], {}
    for model, run in RUNS.items():
        config = read(run / "config.json")
        assert not config["dry_run"]
        assert hashlib.sha256((run / "frozen-runner.py").read_bytes()).hexdigest() == config["runner_sha256"]
        records = sorted(run.glob("tasks/*/*/result.json"))
        assert len(records) == 20
        for path in records:
            result = read(path)
            events = read(path.parent / "trace.json")
            evpath = path.parent / "evaluation.json"
            evaluation = read(evpath) if evpath.exists() else None
            failing = [{"layer": layer["layer"], "check": detail["check_name"],
                        "expected": detail.get("expected"), "actual": detail.get("actual")}
                       for layer in evaluation["layers"] for detail in layer["details"] if not detail["passed"]] if evaluation else []
            models = sorted({event.get("message", {}).get("model") for event in events
                             if event.get("type") == "assistant" and event.get("message", {}).get("model")})
            calls = sum(event.get("type") == "tool_use" for event in events) if result["harness"] == "opencode" else sum(
                sum(isinstance(block, dict) and block.get("type") == "tool_use" for block in event.get("message", {}).get("content", []))
                for event in events if event.get("type") == "assistant")
            row = {"model_group": model, "requested_model": config["model"], "base_url": config["base_url"],
                   "harness": result["harness"], "case_id": result["case_id"], "status": result["status"],
                   "passed": result["passed"], "seconds": result["duration_seconds"],
                   "started_at": result["started_at"], "ended_at": result["ended_at"],
                   "tool_calls": calls, "response_models": models, "failed_checks": failing,
                   "errors": result.get("errors", []), "artifact_directory": path.parent.relative_to(ROOT).as_posix(),
                   "l0_pass": next((l["passed"] for l in evaluation["layers"] if l["layer"] == 0), None) if evaluation else None,
                   "l3_pass": next((l["passed"] for l in evaluation["layers"] if l["layer"] == 3), None) if evaluation else None,
                   **usage(events, result["harness"], result["status"])}
            rows.append(row)
        batch = [r for r in rows if r["model_group"] == model]
        start = min(datetime.fromisoformat(r["started_at"]) for r in batch)
        end = max(datetime.fromisoformat(r["ended_at"]) for r in batch)
        local = timezone(timedelta(hours=8))
        batches[model] = {"run": run.relative_to(ROOT).as_posix(), "config": config,
                          "started_shanghai": start.astimezone(local).isoformat(),
                          "ended_shanghai": end.astimezone(local).isoformat(),
                          "batch_wall_seconds": (end - start).total_seconds()}
        for harness in ["opencode", "claude-code"]:
            group = [r for r in batch if r["harness"] == harness]
            times = [r["seconds"] for r in group]
            observed_fields = ["observed_input", "observed_output_including_reasoning", "observed_cache_read",
                               "observed_cache_write", "observed_total", "observed_reasoning"]
            groups.append({"model_group": model, "harness": harness, "tasks": len(group),
                           "passed": sum(r["passed"] for r in group),
                           "scored": sum(r["status"].startswith("scored_") for r in group),
                           "status_counts": dict(Counter(r["status"] for r in group)),
                           "l0_passed": sum(r["l0_pass"] is True for r in group),
                           "l3_evaluated": sum(r["l3_pass"] is not None for r in group),
                           "l3_passed": sum(r["l3_pass"] is True for r in group),
                           "sum_seconds": sum(times), "mean_seconds": statistics.mean(times),
                           "median_seconds": statistics.median(times), "p95_seconds": percentile(times, .95),
                           "max_seconds": max(times), "tool_calls": sum(r["tool_calls"] for r in group),
                           "usage_coverage": dict(Counter(r["coverage"] for r in group)),
                           "usage_sums": {k: sum(r[k] or 0 for r in group) for k in observed_fields},
                           "client_cost_estimate_sum_usd": sum(r["client_cost_estimate_usd"] or 0 for r in group)
                           if any(r["client_cost_estimate_usd"] is not None for r in group) else None})
    metas = [yaml.safe_load(p.read_text(encoding="utf-8")) for p in (ROOT / "benchmarks/embedeval-main/cases").rglob("metadata.yaml")]
    data = {"metric_notes": {"token_total": "uncached input + cache read + cache write + output including reasoning; sums over observed requests, not unique prompt tokens",
                             "missing_usage": "null in task rows; group sums are observed lower bounds if coverage incomplete",
                             "p95": "linear interpolation at (n-1)*0.95", "time": "CLI launch-to-exit; excludes queue wait and scoring; sum is not concurrent wall time",
                             "cost": "CLI estimate only, not invoice; OpenCode custom-provider zero cost treated unknown"},
            "dataset": {"public_cases": len(metas), "sdk": dict(Counter(m.get("sdk", "unspecified") for m in metas)),
                        "difficulty": dict(Counter(m["difficulty"] for m in metas)),
                        "categories": dict(Counter(m["category"] for m in metas))},
            "batches": batches, "groups": groups, "tasks": rows}
    (ROOT / "evaluation/merged-results.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (ROOT / "evaluation/merged-results.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["model_group", "harness", "case_id", "status", "passed", "seconds", "coverage",
                  "observed_input", "observed_cache_read", "observed_cache_write", "observed_output_including_reasoning",
                  "observed_reasoning", "observed_total", "tool_calls", "base_url", "artifact_directory", "failed_checks"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "failed_checks": "; ".join(f"L{f['layer']}:{f['check']}" for f in row["failed_checks"])})
    print(json.dumps({"groups": groups, "batches": {k: {f:v for f,v in b.items() if f != "config"} for k,b in batches.items()}, "dataset": data["dataset"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
