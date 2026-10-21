"""Full public EmbedEval, OpenCode only, L0/L3 only. No installation or embedded keys."""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import getpass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import uuid

import yaml
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ENGINE_FILE = ROOT / "experiments/2026-10-20-opus5-harness-comparison/run_benchmark.py"
spec = importlib.util.spec_from_file_location("firmware_pilot_engine", ENGINE_FILE)
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)
CONSOLE = Console(legacy_windows=False)
TERMINAL = {"scored_pass", "scored_fail", "timeout", "no_submission"}
SCORING = threading.Lock()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalize_token(value):
    value = value.strip()
    if len(value) > 1 and (value[0], value[-1]) in {('"', '"'), ("'", "'"), ("“", "”"), ("‘", "’")}:
        value = value[1:-1].strip()
    if not re.fullmatch(r"sk-or-v1-[A-Za-z0-9_-]{20,}", value):
        raise RuntimeError("Invalid OpenRouter key format. Paste only the sk-or-v1-... key, "
                           "without JSON field names, commas, newlines or extra quotes. The value was not logged.")
    return value


def dump(path, value):
    # A status reader or antivirus can briefly hold a Windows file without delete sharing.
    for retry in range(25):
        try:
            engine.dump(path, value)
            return
        except PermissionError:
            if retry == 24:
                raise
            time.sleep(.02 * (retry + 1))


def inventory():
    """Select by available checks, not by generated results or reference pass/fail."""
    from embedeval.evaluator import _run_static_checks, _run_behavioral
    cases, excluded, reference_results, hashes = [], [], [], {}
    names = set()
    for path in sorted((ROOT / "benchmarks/embedeval-main/cases").rglob("metadata.yaml")):
        directory = path.parent
        metadata = yaml.safe_load(path.read_text(encoding="utf-8"))
        missing = [name for name in ("prompt.md", "checks/static.py", "checks/behavior.py", "reference/main.c")
                   if not (directory / name).is_file()]
        if missing:
            excluded.append({"case_id": metadata["id"], "missing": missing})
            continue
        if metadata["id"] in names or not re.fullmatch(r"[A-Za-z0-9_-]+", metadata["id"]):
            raise RuntimeError("Duplicate or unsafe case ID")
        names.add(metadata["id"])
        case = {"id": metadata["id"], "path": directory.relative_to(ROOT).as_posix(),
                "title": metadata.get("title", metadata["id"]), "sdk": metadata.get("sdk", "unknown"),
                "category": metadata["category"], "difficulty": metadata["difficulty"]}
        cases.append(case)
        code = (directory / "reference/main.c").read_text(encoding="utf-8")
        try:
            layers = [_run_static_checks(directory, code), _run_behavioral(directory, code)]
            passed = bool(all(layer.passed and layer.details and not layer.error for layer in layers))
            reference_results.append({"case_id": case["id"], "passed": passed,
                                      "layers": [layer.model_dump(mode="json") for layer in layers]})
        except Exception as exc:
            reference_results.append({"case_id": case["id"], "passed": False, "error": str(exc)})
        for item in sorted(directory.rglob("*")):
            if item.is_file() and "__pycache__" not in item.parts:
                hashes[item.relative_to(ROOT).as_posix()] = sha(item)
    for item in sorted((ROOT / "benchmarks/embedeval-main/src/embedeval").rglob("*.py")):
        hashes[item.relative_to(ROOT).as_posix()] = sha(item)
    manifest = {"benchmark": "EmbedEval", "selection": "All public cases with L0 and L3 checks; no sampling",
                "cases": cases, "excluded": excluded,
                "difficulty": dict(Counter(case["difficulty"] for case in cases)),
                "sdk": dict(Counter(case["sdk"] for case in cases)),
                "source_sha256": hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()}
    health = {"checked_at": datetime.now(timezone.utc).isoformat(),
              "reference_passed": sum(row["passed"] for row in reference_results),
              "reference_total": len(reference_results), "cases": reference_results}
    dump(HERE / "cases.json", manifest)
    dump(HERE / "environment-check.json", health)
    return manifest, health


def latest_results(run):
    """Artifact JSON is the recovery source even if the DB write was interrupted."""
    attempts, latest = [], {}
    for path in (run / "tasks").glob("*/*/result.json"):
        row = read(path)
        row["artifact_directory"] = path.parent.relative_to(run).as_posix()
        attempts.append(row)
    attempts.sort(key=lambda row: (row["started_at"], row["attempt_id"]))
    for row in attempts:
        latest[row["case_id"]] = row
    return attempts, latest


def select_pending(cases, latest):
    return [case for case in cases if latest.get(case["id"], {}).get("status") not in TERMINAL]


@contextmanager
def run_lock(run):
    # Never overwrite the locked byte: Windows raises even on writing a locked file.
    path = run / ".lock"
    if not path.exists():
        path.write_bytes(b"0")
    handle = path.open("r+b")
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield
    finally:
        handle.close()


def confirm(total, done, pending, concurrency, dry):
    message = (f"模型：qwen/qwen3.8-27b\n框架：仅 OpenCode\n评分：仅 L0 + L3 静态检查\n\n"
               f"总题数：{total}\n已完成（本次跳过）：{done}\n本次待跑 / 重试：{pending}\n"
               f"并发数：{concurrency}\n\n"
               + ("离线模拟，不请求模型 API。\n" if dry else
                  "会使用 OpenRouter API 额度；首次含少量工具预检请求。\n")
               + "\n确认开始 / 继续运行吗？")
    try:
        import tkinter as tk
        from tkinter import messagebox
        window = tk.Tk()
        window.withdraw()
        window.attributes("-topmost", True)
        try:
            return messagebox.askyesno("Firmware 评测：确认待跑题数", message,
                                      parent=window, default="no", icon="question")
        finally:
            window.destroy()
    except Exception:
        CONSOLE.print(message, markup=False)
        return input("Type YES to start: ").strip() == "YES"


def token_usage(events, status):
    steps = [event["part"] for event in events if event.get("type") == "step_finish"]
    if not steps:
        return {"coverage": "unknown", "input": None, "output_including_reasoning": None,
                "cache_read": None, "cache_write": None, "reasoning": None, "total": None}
    sums = {key: sum(step.get("tokens", {}).get(key, 0) for step in steps)
            for key in ("input", "output", "reasoning", "total")}
    sums["output_including_reasoning"] = sums.pop("output") + sums["reasoning"]
    sums["cache_read"] = sum(step.get("tokens", {}).get("cache", {}).get("read", 0) for step in steps)
    sums["cache_write"] = sum(step.get("tokens", {}).get("cache", {}).get("write", 0) for step in steps)
    sums["coverage"] = "complete" if status.startswith("scored_") or status == "no_submission" else "partial"
    return sums


def task(case, run, config, binary):
    attempt = uuid.uuid4().hex
    folder = run / "tasks" / case["id"] / attempt
    folder.mkdir(parents=True)
    result = {"case_id": case["id"], "attempt_id": attempt, "harness": "opencode",
              "model": config["model"], "status": "running", "passed": False,
              "started_at": datetime.now(timezone.utc).isoformat(),
              "artifact_directory": folder.relative_to(run).as_posix()}
    dump(folder / "result.json", result)
    if engine.STOP.is_set():
        result["status"] = "cancelled"
    else:
        engine.EVENTS.put(f"START {case['id']} ({case['sdk']}, {case['difficulty']})")
        stage = "generation"
        try:
            original = (ROOT / case["path"] / "prompt.md").read_text(encoding="utf-8")
            # Some tasks request Kconfig, devicetree, BitBake, etc. Do not force C.
            prompt = original + (
                "\n\nSubmission instruction: follow the requested language and content format exactly. "
                "Write the entire requested answer as text to submission/answer.txt using file tools, "
                "instead of returning the answer only in chat. This is a collection filename; do not "
                "change the requested content into C merely because of a filename. "
                "Do not access paths outside this task workspace.\n")
            (folder / "prompt.md").write_text(prompt, encoding="utf-8")
            if config["dry_run"]:
                submission = folder / "workspace/submission/answer.txt"
                submission.parent.mkdir(parents=True)
                submission.write_text("OFFLINE INVALID FIXTURE\n", encoding="utf-8")
                time.sleep(.02)
                result.update(status="completed", duration_seconds=.02, cost_usd=None)
            else:
                result.update(engine.execute("opencode", folder, prompt, config, {"opencode": binary}))
            submission = folder / "workspace/submission/answer.txt"
            if result["status"] == "completed":
                if submission.is_symlink() or not submission.is_file() or not submission.stat().st_size:
                    result["status"] = "no_submission"
                else:
                    stage = "evaluation"
                    from embedeval.evaluator import _run_static_checks, _run_behavioral
                    code = submission.read_text(encoding="utf-8-sig")
                    with SCORING:
                        layer0 = _run_static_checks(ROOT / case["path"], code)
                        layers = [layer0]
                        if layer0.passed:
                            layers.append(_run_behavioral(ROOT / case["path"], code))
                    healthy = all(layer.details and not layer.error for layer in layers)
                    passed = bool(healthy and all(layer.passed for layer in layers))
                    evaluation = {"scope": "L0+L3", "passed": passed,
                                  "layers": [layer.model_dump(mode="json") for layer in layers],
                                  "not_evaluated": ["L1 compile", "L2 runtime", "L4 mutation"]}
                    dump(folder / "evaluation.json", evaluation)
                    result.update(passed=passed, submission_sha256=sha(submission),
                                  status=("scored_pass" if passed else "scored_fail") if healthy else "evaluator_error")
            events = read(folder / "trace.json") if (folder / "trace.json").is_file() else []
            result["tokens"] = token_usage(events, result["status"])
            result["cost_usd"] = None  # custom-provider zero is not a real invoice
        except Exception as exc:
            result.update(status="evaluator_error" if stage == "evaluation" else "infra_error",
                          error=engine.clean(str(exc)))
    result["ended_at"] = datetime.now(timezone.utc).isoformat()
    dump(folder / "result.json", result)
    return result


def persist_report(run, config, db, runtime_status):
    attempts, latest = latest_results(run)
    for row in attempts:
        db.execute("INSERT OR REPLACE INTO attempts VALUES (?, ?, ?)",
                   (row["attempt_id"], row["case_id"], json.dumps(row, ensure_ascii=False)))
    db.commit()
    counts = Counter(row["status"] for row in latest.values())
    total = len(config["cases"])
    finished = sum(row["status"] not in {"running", "cancelled"} for row in latest.values())
    passed = counts["scored_pass"]
    scored = counts["scored_pass"] + counts["scored_fail"]
    summary = {"model": config["model"], "harness": "opencode", "scope": "L0+L3 only",
               "dry_run": config["dry_run"], "runtime_status": runtime_status,
               "planned": total, "finished": finished, "passed": passed, "scored": scored,
               "progress_percent": round(100 * finished / total, 2), "status_counts": dict(counts),
               "retryable_cases": [c["id"] for c in select_pending(config["cases"], latest)],
               "observed_tokens": sum((r.get("tokens") or {}).get("total") or 0 for r in latest.values()),
               "observed_tokens_all_attempts": sum((r.get("tokens") or {}).get("total") or 0 for r in attempts),
               "usage_coverage": dict(Counter((r.get("tokens") or {}).get("coverage", "unknown") for r in latest.values())),
               "cost_usd": None}
    dump(run / "summary.json", summary)
    title = "OFFLINE DRY RUN - not model results" if config["dry_run"] else "Qwen / OpenCode - public EmbedEval static run"
    lines = ["# " + title, "", f"Model: `{config['model']}`; L0/L3 only. No compilation or runtime tests.",
             "", f"Progress: {finished}/{total} ({summary['progress_percent']}%). Runtime: {runtime_status}.",
             f"Passed/planned: {passed}/{total}. Passed/scored: {passed}/{scored}.",
             "", "Token totals are observed records, possibly incomplete; unknown is not zero cost.",
             "", "| Case | SDK | Difficulty | Status | Seconds | Observed tokens | Artifact |",
             "|---|---|---|---|---:|---:|---|"]
    rows = []
    for case in config["cases"]:
        row = latest.get(case["id"], {})
        usage = row.get("tokens") or {}
        tokens = usage.get("total")
        shown = "unknown" if tokens is None else (">= " if usage.get("coverage") == "partial" else "") + str(tokens)
        artifact = row.get("artifact_directory", "")
        lines.append(f"| {case['id']} | {case['sdk']} | {case['difficulty']} | {row.get('status', 'pending')} | "
                     f"{row.get('duration_seconds', '')} | {shown} | "
                     + (f"[result]({artifact}/result.json) |" if artifact else " |"))
        rows.append({"case_id": case["id"], "sdk": case["sdk"], "difficulty": case["difficulty"],
                     "status": row.get("status", "pending"), "passed": row.get("passed"),
                     "seconds": row.get("duration_seconds"), "tokens": tokens,
                     "token_coverage": usage.get("coverage", "unknown"), "artifact": artifact})
    report = run / "report.md"
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (run / "tasks.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-only", action="store_true", help="Refresh case inventory and reference checks; no API")
    parser.add_argument("--dry-run", action="store_true", help="Offline invalid fixture; no API")
    parser.add_argument("--new-run", action="store_true", help="Create a new experiment rather than auto-resume")
    parser.add_argument("--resume", type=Path, help="Explicit run directory")
    parser.add_argument("--yes", action="store_true", help="Explicitly bypass the confirmation dialog")
    parser.add_argument("--limit", type=int, help="Smoke-test subset; changes configuration and needs a new run")
    parser.add_argument("--concurrency", type=int, choices=range(1, 9), default=2)
    parser.add_argument("--timeout", type=int, default=600)
    args = parser.parse_args()
    if args.new_run and args.resume:
        parser.error("--new-run and --resume are mutually exclusive")
    if args.timeout < 1 or (args.limit is not None and args.limit < 1):
        parser.error("timeout/limit must be positive")
    manifest, health = inventory()
    CONSOLE.print(f"Public cases with both checks: {len(manifest['cases'])}. "
                  f"Reference checks: {health['reference_passed']}/{health['reference_total']}.")
    if health["reference_passed"] != health["reference_total"]:
        raise RuntimeError("Reference checks failed; no API calls. Inspect environment-check.json.")
    if args.prepare_only:
        return 0
    cases = manifest["cases"][:args.limit] if args.limit else manifest["cases"]
    experiment = read(HERE / "experiment.json")
    config = {"model": experiment["model"], "base_url": experiment["base_url"],
              "harness": "opencode", "cases": cases, "source_sha256": manifest["source_sha256"],
              "runner_sha256": sha(Path(__file__)), "engine_sha256": sha(ENGINE_FILE),
              "timeout_seconds": args.timeout, "concurrency": args.concurrency,
              "dry_run": args.dry_run, "scoring": "L0+L3", "submission": "submission/answer.txt",
              "repetitions": 1, "external_retries": 0, "reasoning_parameters": "OpenCode defaults"}
    binary = None
    if not args.dry_run:
        binary = engine.executable("opencode")
        config["opencode_version"] = subprocess.check_output([binary, "--version"], timeout=30).decode().strip()
    pointer = HERE / ("latest-dry-run.json" if args.dry_run else "latest-run.json")
    if args.resume:
        run = args.resume.resolve()
    elif pointer.is_file() and not args.new_run:
        run = HERE / read(pointer)["run"]
    else:
        run = HERE / "runs" / (("dry-" if args.dry_run else "run-") + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    # Run paths must remain within this experiment; do not mix with the pilot.
    if not run.resolve().is_relative_to((HERE / "runs").resolve()):
        raise RuntimeError("Resume path is outside this experiment's runs directory")
    existed = (run / "config.json").is_file()
    upgrade_unstarted = False
    if existed:
        previous_config = read(run / "config.json")
        changed = {key for key in set(previous_config) | set(config) if previous_config.get(key) != config.get(key)}
        if changed:
            # A preflight-only run has no scored/model-task attempts to mix. Keep its
            # original code/config revision and retry with the repaired parser.
            upgrade_unstarted = (changed <= {"runner_sha256", "engine_sha256"}
                                 and not list(run.glob("tasks/*/*/result.json"))
                                 and not (run / "preflight-passed.json").exists())
            if not upgrade_unstarted:
                raise RuntimeError("Configuration/source/version changed; resume refused. Restore the settings or use --new-run.")
    if args.resume and not existed:
        raise RuntimeError("The requested resume run has no config.json")
    run.mkdir(parents=True, exist_ok=True)
    with run_lock(run):
        _, latest = latest_results(run)
        pending = select_pending(cases, latest)
        done = len(cases) - len(pending)
        CONSOLE.print(f"Run: {run}\nTotal {len(cases)} | Already finished {done} | Pending/retry {len(pending)} | Concurrency {args.concurrency}")
        if not pending:
            CONSOLE.print("Nothing to resume. Use --new-run only if you intend to repeat all tasks.")
            return 0
        if not args.yes and not confirm(len(cases), done, len(pending), args.concurrency, args.dry_run):
            CONSOLE.print("Cancelled before model requests.")
            return 0
        if not existed or upgrade_unstarted:
            if upgrade_unstarted:
                archive = run / "config-revisions" / uuid.uuid4().hex[:8]
                archive.mkdir(parents=True)
                for name in ("config.json", "frozen-runner.py", "frozen-engine.py"):
                    if (run / name).exists():
                        shutil.copyfile(run / name, archive / name)
                CONSOLE.print("Preflight-only run: original configuration archived; retrying with repaired runner.")
            dump(run / "config.json", config)
            shutil.copyfile(Path(__file__), run / "frozen-runner.py")
            shutil.copyfile(ENGINE_FILE, run / "frozen-engine.py")
        dump(pointer, {"run": run.relative_to(HERE).as_posix()})
        db = sqlite3.connect(run / "results.sqlite")
        db.execute("CREATE TABLE IF NOT EXISTS attempts (attempt_id TEXT PRIMARY KEY, case_id TEXT, payload TEXT)")
        try:
            persist_report(run, config, db, "preflight" if not args.dry_run else "running")
            if not args.dry_run:
                # API keys are intentionally never read from the previous experiment.
                engine.TOKEN = normalize_token(os.environ.get("OPENROUTER_API_KEY") or os.environ.get("BENCH_ANTHROPIC_TOKEN")
                                               or getpass.getpass("OpenRouter API Key (hidden): "))
                if not (run / "preflight-passed.json").is_file():
                    try:
                        engine.preflight(run, config, {"opencode": binary})
                    except Exception:
                        persist_report(run, config, db, "preflight_failed")
                        raise
            random.Random(42).shuffle(pending)
            interrupted = False
            pool = ThreadPoolExecutor(max_workers=args.concurrency)
            jobs = set()
            todo = iter(pending)

            def fill():
                while len(jobs) < args.concurrency and not engine.STOP.is_set():
                    case = next(todo, None)
                    if case is None:
                        break
                    jobs.add(pool.submit(task, case, run, config, binary))

            try:
                with (run / "run.log").open("a", encoding="utf-8") as log, Progress(
                    TextColumn("L0/L3"), BarColumn(), TextColumn("{task.percentage:>5.1f}%"),
                    TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), TimeRemainingColumn(),
                    console=CONSOLE) as progress:
                    bar = progress.add_task("Cases", total=len(cases), completed=done)
                    fill()
                    while jobs:
                        finished_jobs, jobs = wait(jobs, timeout=.25, return_when=FIRST_COMPLETED)
                        while not engine.EVENTS.empty():
                            line = engine.EVENTS.get_nowait()
                            line = engine.clean(line)
                            log.write(datetime.now().isoformat() + " " + line + "\n")
                            log.flush()
                            progress.console.print(line, markup=False)
                        for future in finished_jobs:
                            row = future.result()
                            persist_report(run, config, db, "running")
                            line = f"DONE {row['case_id']}: {row['status']} ({row.get('duration_seconds', 0):.1f}s)"
                            log.write(line + "\n")
                            log.flush()
                            progress.console.print(line, markup=False)
                            progress.advance(bar)
                        fill()
            except KeyboardInterrupt:
                interrupted = True
                engine.STOP.set()
                CONSOLE.print("Stopping active processes; results are preserved for the next start.")
                with engine.LOCK:
                    for proc in list(engine.ACTIVE):
                        engine.kill(proc)
            finally:
                pool.shutdown(wait=True, cancel_futures=True)
                summary = persist_report(run, config, db, "interrupted" if interrupted else "finished")
            CONSOLE.print(f"Finished {summary['finished']}/{len(cases)}. Passed {summary['passed']}. "
                          f"Retryable cases on next start: {len(summary['retryable_cases'])}.\nReport: {run / 'report.md'}")
            return 130 if interrupted else (1 if summary["retryable_cases"] else 0)
        finally:
            db.close()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        CONSOLE.print("Error: " + engine.clean(str(exc)), markup=False)
        sys.exit(1)
