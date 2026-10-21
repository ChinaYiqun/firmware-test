"""Local paired Harness runner. No dependency installation and no embedded keys."""
from __future__ import annotations

import argparse
import concurrent.futures as futures
import csv
import getpass
import hashlib
import json
import os
import queue
import random
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from embedeval.evaluator import _run_behavioral, _run_static_checks

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for output in (sys.stdout, sys.stderr):
    if hasattr(output, "reconfigure"):
        output.reconfigure(encoding="utf-8", errors="replace")
CONSOLE = Console(legacy_windows=False)
EVENTS = queue.Queue()
ACTIVE = set()
LOCK = threading.Lock()
STOP = threading.Event()
TOKEN = ""
HARNESS_LIMITS = {}
SCORING_LOCK = threading.Lock()


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def clean(text):
    if TOKEN:
        text = text.replace(TOKEN, "[REDACTED]")
    return re.sub(r"sk-[A-Za-z0-9_-]{16,}", "[REDACTED]", text)


def executable(name):
    shim = shutil.which(name + ".cmd") or shutil.which(name)
    if not shim:
        raise RuntimeError(f"Missing CLI: {name}")
    base = Path(shim).parent
    candidate = base / ("node_modules/opencode-ai/bin/opencode.exe" if name == "opencode"
                        else "node_modules/@anthropic-ai/claude-code/bin/claude.exe")
    if candidate.is_file():
        return str(candidate)
    if Path(shim).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        raise RuntimeError(f"Cannot locate native {name} executable beside {shim}")
    return shim


def kill(proc):
    if proc.poll() is None:
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            import signal
            os.killpg(proc.pid, signal.SIGKILL)


def score(case, code):
    # importlib-based benchmark modules share sys.modules; score serially.
    with SCORING_LOCK:
        return score_serial(case, code)


def score_serial(case, code):
    directory = ROOT / case["path"]
    layer0 = _run_static_checks(directory, code)
    layers = [layer0]
    if layer0.passed:
        layers.append(_run_behavioral(directory, code))
    # Missing check details must never count as a pass.
    healthy = all(layer.details and not layer.error for layer in layers)
    return {"passed": bool(healthy and all(layer.passed for layer in layers)),
            "healthy": bool(healthy), "scope": "L0+L3 static only",
            "layers": [layer.model_dump(mode="json") for layer in layers],
            "not_evaluated": ["L1 compile", "L2 runtime", "L4 mutation"]}


def build(harness, workspace, state, config, binaries):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("ANTHROPIC_", "CLAUDE_", "OPENCODE_", "OPENAI_"))
           and k != "BENCH_ANTHROPIC_TOKEN"}
    env.update(PYTHONIOENCODING="utf-8", NO_COLOR="1",
               ANTHROPIC_AUTH_TOKEN=TOKEN, ANTHROPIC_API_KEY=TOKEN,
               ANTHROPIC_BASE_URL=config["base_url"],
               ANTHROPIC_DEFAULT_OPUS_MODEL=config["model"],
               ANTHROPIC_DEFAULT_SONNET_MODEL=config["model"],
               ANTHROPIC_DEFAULT_HAIKU_MODEL=config["model"],
               ANTHROPIC_DEFAULT_FABLE_MODEL=config["model"],
               CLAUDE_CODE_SUBAGENT_MODEL=config["model"],
               CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1")
    state.mkdir(parents=True, exist_ok=True)
    if harness == "opencode":
        model = "bench/" + config["model"]
        native = {
            "$schema": "https://opencode.ai/config.json", "model": model,
            "small_model": model, "enabled_providers": ["bench"],
            "autoupdate": False, "snapshot": False, "share": "disabled",
            "instructions": [], "plugin": [],
            "provider": {"bench": {"npm": "@ai-sdk/anthropic", "name": "Benchmark gateway",
                "options": {"baseURL": config["base_url"].rstrip("/") + "/v1",
                            "apiKey": "{env:ANTHROPIC_API_KEY}",
                            "headers": {"Authorization": "Bearer {env:ANTHROPIC_AUTH_TOKEN}"}},
                "models": {config["model"]: {"name": config["model"]}}}},
            "permission": {"*": "deny", "read": "allow", "edit": "allow",
                           "glob": "allow", "grep": "allow", "external_directory": "deny"},
            "agent": {"build": {"permission": {"*": "deny", "read": "allow",
                "edit": "allow", "glob": "allow", "grep": "allow", "external_directory": "deny"}}},
        }
        dump(state / "opencode.json", native)
        for key, sub in [("XDG_CONFIG_HOME", "config"), ("XDG_DATA_HOME", "data"),
                         ("XDG_CACHE_HOME", "cache"), ("XDG_STATE_HOME", "state")]:
            env[key] = str(state / sub)
        env.update(OPENCODE_CONFIG=str(state / "opencode.json"),
                   OPENCODE_CONFIG_DIR=str(state / "empty-config"),
                   OPENCODE_DISABLE_PROJECT_CONFIG="true", OPENCODE_DISABLE_CLAUDE_CODE="true",
                   OPENCODE_DISABLE_DEFAULT_PLUGINS="true", OPENCODE_DISABLE_AUTOUPDATE="true")
        argv = [binaries[harness], "run", "--pure", "--format", "json", "--model", model]
    else:
        env["ANTHROPIC_API_KEY"] = ""
        native = {"permissions": {"allow": ["Read", "Write", "Edit", "Glob", "Grep"],
                                  "deny": ["Bash", "WebFetch", "WebSearch", "Agent", "Task"]},
                  "disableAllHooks": True}
        dump(state / "claude-settings.json", native)
        dump(state / "mcp.json", {"mcpServers": {}})
        env["CLAUDE_CONFIG_DIR"] = str(state / "claude-home")
        argv = [binaries[harness], "-p", "--restricted", "--model", config["model"],
                "--output-format", "stream-json", "--verbose", "--disable-slash-commands",
                "--tools", "Read,Write,Edit,Glob,Grep", "--allowedTools", "Read,Write,Edit,Glob,Grep",
                "--strict-mcp-config", "--mcp-config", str(state / "mcp.json"),
                "--settings", str(state / "claude-settings.json")]
    dump(state / "argv.json", argv)
    return argv, env


def execute(harness, folder, prompt, config, binaries):
    workspace = folder / "workspace"
    (workspace / "submission").mkdir(parents=True, exist_ok=True)
    (workspace / "task.md").write_text(prompt, encoding="utf-8")
    argv, env = build(harness, workspace, folder / "state", config, binaries)
    started = time.monotonic()
    proc = subprocess.Popen(argv, cwd=workspace, env=env, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=os.name != "nt")
    with LOCK:
        ACTIVE.add(proc)
    streams = []
    events = []

    def reader(stream, name):
        with (folder / (name + ".log")).open("w", encoding="utf-8") as log:
            for raw in iter(stream.readline, b""):
                line = clean(raw.decode("utf-8", "replace").rstrip())
                log.write(line + "\n")
                log.flush()
                try:
                    event = json.loads(line)
                    events.append(event)
                    kind = event.get("type", "event")
                    if kind in {"tool_use", "tool_result", "error", "step_finish", "result", "assistant"}:
                        EVENTS.put(f"{harness}: {kind}")
                except ValueError:
                    if line:
                        EVENTS.put(f"{harness}: {line[:180]}")
        stream.close()

    for stream, name in [(proc.stdout, "stdout"), (proc.stderr, "stderr")]:
        thread = threading.Thread(target=reader, args=(stream, name), daemon=True)
        thread.start()
        streams.append(thread)
    status = "completed"
    try:
        proc.stdin.write(prompt.encode("utf-8"))
        proc.stdin.close()
        while proc.poll() is None:
            if STOP.is_set() or time.monotonic() - started > config["timeout_seconds"]:
                status = "cancelled" if STOP.is_set() else "timeout"
                kill(proc)
                break
            time.sleep(0.2)
        proc.wait()
    except BaseException:
        kill(proc)
        raise
    finally:
        for thread in streams:
            thread.join(timeout=10)
        with LOCK:
            ACTIVE.discard(proc)
    dump(folder / "trace.json", events)
    final_errors = [e for e in events if e.get("type") == "error"
                    or (e.get("type") == "result" and e.get("is_error"))]
    if status == "completed" and (proc.returncode or final_errors):
        status = "infra_error"
    # Raw usage remains in trace; normalized units/costs are not guessed.
    usage = [e for e in events if e.get("type") in {"result", "step_finish"}]
    return {"status": status, "exit_code": proc.returncode,
            "duration_seconds": round(time.monotonic() - started, 3),
            "usage_events": usage, "token_usage": None, "cost_usd": None,
            "errors": final_errors}


def work(task, run, config, binaries, dry):
    harness, case, repeat = task
    task_id = f"{harness}__{case['id']}__{repeat}"
    folder = run / "tasks" / task_id / uuid.uuid4().hex[:8]
    folder.mkdir(parents=True)
    result = {"task_id": task_id, "harness": harness, "case_id": case["id"],
              "repeat": repeat, "started_at": datetime.now(timezone.utc).isoformat(),
              "artifact_directory": str(folder), "status": "running", "passed": False}
    dump(folder / "result.json", result)
    EVENTS.put(f"START {harness} / {case['id']} / repeat {repeat}")
    try:
        original = (ROOT / case["path"] / "prompt.md").read_text(encoding="utf-8")
        prompt = original + ("\n\nSubmission instruction: write the complete C source to "
                            "submission/main.c using file tools instead of returning it in chat. "
                            "Do not access paths outside this task workspace.\n")
        (folder / "prompt.md").write_text(prompt, encoding="utf-8")
        if dry:
            # Deliberately wrong fixture exercises scoring and reporting without a model.
            workspace = folder / "workspace/submission"
            workspace.mkdir(parents=True)
            (workspace / "main.c").write_text("int main(void) { return 0; }\n", encoding="utf-8")
            time.sleep(0.1)
            result.update(status="completed", duration_seconds=0.1, token_usage=None, cost_usd=None)
        else:
            with HARNESS_LIMITS[harness]:
                if STOP.is_set():
                    result["status"] = "cancelled"
                else:
                    result.update(execute(harness, folder, prompt, config, binaries))
        submission = folder / "workspace/submission/main.c"
        if result["status"] == "completed":
            if not submission.is_file() or submission.is_symlink() or not submission.stat().st_size:
                result["status"] = "no_submission"
            else:
                evaluation = score(case, submission.read_text(encoding="utf-8"))
                dump(folder / "evaluation.json", evaluation)
                result["passed"] = evaluation["passed"]
                result["status"] = ("scored_pass" if evaluation["passed"] else "scored_fail") if evaluation["healthy"] else "evaluator_error"
                result["submission_sha256"] = hashlib.sha256(submission.read_bytes()).hexdigest()
    except Exception as exc:
        result.update(status="infra_error", error=clean(str(exc)))
    result["ended_at"] = datetime.now(timezone.utc).isoformat()
    dump(folder / "result.json", result)
    return result


def preflight(run, config, binaries):
    """Small live tool-policy probe; never exposes a benchmark reference."""
    for harness in binaries:
        folder = run / "preflight" / harness / uuid.uuid4().hex[:8]
        folder.mkdir(parents=True)
        canary = folder / "outside-workspace.txt"
        marker = "BENCH_PRIVATE_" + uuid.uuid4().hex
        canary.write_text(marker, encoding="utf-8")
        prompt = (
            f"Tool permission test. First use the file read tool to read this absolute path: {canary}. "
            "If it is blocked, do not bypass the restriction or use another tool to read it. "
            "Then use a file write tool to create submission/main.c with exactly this content: "
            "int main(void) { return 0; }\nDo not run shell commands."
        )
        CONSOLE.print(f"Preflight: {harness} (gateway + tools + external-file denial)")
        with CONSOLE.status(f"Checking {harness}...", spinner="line"):
            result = execute(harness, folder, prompt, config, binaries)
        trace = (folder / "stdout.log").read_text(encoding="utf-8")
        submitted = folder / "workspace/submission/main.c"
        escaped = marker in trace or any(marker in p.read_text(encoding="utf-8", errors="replace")
            for p in (folder / "workspace").rglob("*") if p.is_file())
        # Require an explicit failed tool result, not just a statement that policy exists.
        events = json.loads((folder / "trace.json").read_text(encoding="utf-8"))
        denied = False
        for event in events:
            for block in event.get("message", {}).get("content", []) if isinstance(event.get("message"), dict) else []:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                    denied |= bool(re.search(r"outside|permission|denied|restricted|not allowed", str(block), re.I))
            part = event.get("part", {})
            if isinstance(part, dict) and part.get("state", {}).get("status") == "error":
                denied |= bool(re.search(r"outside|permission|denied|restricted|not allowed", str(part), re.I))
        result.update(outside_file_leaked=escaped, explicit_denial_observed=denied,
                      submission_created=submitted.is_file())
        dump(folder / "preflight.json", result)
        if result["status"] != "completed" or escaped or not denied or not submitted.is_file():
            raise RuntimeError(f"{harness} preflight failed; no scored tasks started. Inspect {folder}")
    dump(run / "preflight-passed.json", {"passed": True, "scope": "Harness policy probes, not OS sandbox"})


def main():
    global TOKEN, HERE, ROOT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Offline deliberately failing fixture; no API calls")
    parser.add_argument("--resume", type=Path, help="Resume a run directory with identical settings")
    parser.add_argument("--concurrency", type=int, default=2, choices=range(1, 5))
    parser.add_argument("--repetitions", type=int, default=1, choices=range(1, 4))
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--experiment-dir", type=Path, default=HERE)
    args = parser.parse_args()
    HERE = args.experiment_dir.resolve()
    ROOT = HERE.parents[1]
    if args.timeout <= 0:
        parser.error("timeout must be positive")
    from check_environment import check
    health = check(HERE)
    if not health["passed"]:
        raise RuntimeError("Reference checks failed; see environment-check.json")
    experiment = json.loads((HERE / "experiment.json").read_text(encoding="utf-8")) if (HERE / "experiment.json").is_file() else {}
    config = {"model": experiment.get("model", "claude-opus-5"), "base_url": experiment.get("base_url", "https://sky.tinyandbeautiful.com"),
              "timeout_seconds": args.timeout, "concurrency": args.concurrency,
              "repetitions": args.repetitions, "dry_run": args.dry_run,
              "source_sha256": health["source_sha256"], "scoring": "L0+L3",
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "external_retries": 0, "cli_internal_retries": "Harness defaults, within task timeout",
              "isolation": "Harness file-tool restrictions; no OS sandbox",
              "reasoning_parameters": "Harness defaults; not aligned"}
    for name in ["opencode", "claude-code"]:
        HARNESS_LIMITS[name] = threading.Semaphore(max(1, args.concurrency // 2))
    subset = json.loads((HERE / "subsets/pilot-10.json").read_text(encoding="utf-8"))
    config["subset"] = subset
    binaries = {}
    if not args.dry_run:
        TOKEN = os.environ.get("BENCH_ANTHROPIC_TOKEN") or os.environ.get("ANTHROPIC_AUTH_TOKEN") or getpass.getpass("API token (hidden): ")
        if not TOKEN:
            raise RuntimeError("API token required")
        for name, cli in [("opencode", "opencode"), ("claude-code", "claude")]:
            binaries[name] = executable(cli)
        config["versions"] = {name: subprocess.check_output([path, "--version"], timeout=30).decode().strip()
                              for name, path in binaries.items()}
    run = args.resume.resolve() if args.resume else HERE / "runs" / (
        ("dry-" if args.dry_run else "run-") + datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6])
    run.mkdir(parents=True, exist_ok=True)
    # OS file lock automatically releases on crashes; no stale lock blocks resuming.
    lockfile = (run / ".lock").open("a+b")
    lockfile.seek(0)
    lockfile.write(b"0")
    lockfile.flush()
    lockfile.seek(0)
    if os.name == "nt":
        import msvcrt
        msvcrt.locking(lockfile.fileno(), msvcrt.LK_NBLCK, 1)
    else:
        import fcntl
        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    if args.resume:
        if json.loads((run / "config.json").read_text(encoding="utf-8")) != config:
            raise RuntimeError("Resume rejected: configuration, versions, source or runner changed")
    else:
        dump(run / "config.json", config)
    CONSOLE.print(f"[bold]Run directory:[/] {run}")
    if not args.dry_run and not (run / "preflight-passed.json").is_file():
        preflight(run, config, binaries)
    db = sqlite3.connect(run / "results.sqlite")
    db.execute("CREATE TABLE IF NOT EXISTS attempts (task_id TEXT, payload TEXT)")
    previous = [json.loads(row[0]) for row in db.execute("SELECT payload FROM attempts ORDER BY rowid")]
    complete = {r["task_id"] for r in previous if r["status"] in {"scored_pass", "scored_fail", "no_submission", "timeout"}}
    tasks = [(h, c, r) for r in range(1, args.repetitions + 1)
             for c in subset["cases"] for h in ["opencode", "claude-code"]]
    random.Random(42).shuffle(tasks)
    pending = [t for t in tasks if f"{t[0]}__{t[1]['id']}__{t[2]}" not in complete]
    CONSOLE.print("OFFLINE FIXTURE: these are not model results" if args.dry_run else
                  "Static-only pilot. Progress logs below; raw events in each task directory.")
    pool = futures.ThreadPoolExecutor(max_workers=args.concurrency)
    jobs = {pool.submit(work, t, run, config, binaries, args.dry_run) for t in pending}
    interrupted = False
    logpath = run / "run.log"
    try:
        with logpath.open("a", encoding="utf-8") as logfile, Progress(
            SpinnerColumn(spinner_name="line"), TextColumn("{task.description}"), BarColumn(),
            TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(), console=CONSOLE) as progress:
            bar = progress.add_task("Tasks", total=len(tasks), completed=len(complete))
            while jobs:
                done, jobs = futures.wait(jobs, timeout=0.25, return_when=futures.FIRST_COMPLETED)
                while not EVENTS.empty():
                    line = EVENTS.get_nowait()
                    logfile.write(datetime.now().isoformat() + " " + line + "\n")
                    logfile.flush()
                    progress.console.print(line, markup=False)
                for job in done:
                    result = job.result()
                    db.execute("INSERT INTO attempts VALUES (?, ?)",
                               (result["task_id"], json.dumps(result, ensure_ascii=False)))
                    db.commit()
                    previous.append(result)
                    line = f"DONE {result['harness']} / {result['case_id']}: {result['status']}"
                    logfile.write(line + "\n")
                    logfile.flush()
                    progress.console.print(line, markup=False)
                    progress.advance(bar)
    except KeyboardInterrupt:
        interrupted = True
        STOP.set()
        for job in jobs:
            job.cancel()
        with LOCK:
            for proc in list(ACTIVE):
                kill(proc)
        CONSOLE.print("Interrupted. Completed results are retained; use --resume.")
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        # Recover results finalized during interruption; keep the main thread as sole DB writer.
        recorded = {r["artifact_directory"] for r in previous}
        for path in (run / "tasks").glob("*/*/result.json"):
            row = json.loads(path.read_text(encoding="utf-8"))
            if row["artifact_directory"] not in recorded and row["status"] != "running":
                db.execute("INSERT INTO attempts VALUES (?, ?)", (row["task_id"], json.dumps(row)))
                previous.append(row)
        db.commit()
        db.close()
    latest = {r["task_id"]: r for r in previous}
    rows = list(latest.values())
    summary = {"dry_run": args.dry_run, "scope": "L0+L3 static only", "planned": len(tasks),
               "completed": len(rows), "interrupted": interrupted, "harnesses": {}}
    lines = ["# " + ("OFFLINE FIXTURE — not model results" if args.dry_run else "Harness static pilot"),
             "", "Scope: L0+L3 only; L1/L2 not evaluated. Harness defaults are not parameter-aligned.",
             "", "| Harness | Passed | Scored | Planned | End-to-end pass rate |", "|---|---:|---:|---:|---:|"]
    for h in ["opencode", "claude-code"]:
        group = [r for r in rows if r["harness"] == h]
        passed = sum(r["passed"] for r in group)
        scored = sum(r["status"] in {"scored_pass", "scored_fail"} for r in group)
        n = len(tasks) // 2
        summary["harnesses"][h] = {"passed": passed, "scored": scored, "planned": n,
                                  "complete": len(group), "status_counts": {s: sum(r["status"] == s for r in group) for s in sorted({r["status"] for r in group})}}
        rate = f"{passed/n:.1%}" if len(group) == n else "provisional/incomplete"
        lines.append(f"| {h} | {passed} | {scored} | {n} | {rate} |")
    lines += ["", "| Harness | Case | Repeat | Status | Seconds |", "|---|---|---:|---|---:|"]
    for row in sorted(rows, key=lambda r: r["task_id"]):
        lines.append(f"| {row['harness']} | {row['case_id']} | {row['repeat']} | {row['status']} | {row.get('duration_seconds', '')} |")
    dump(run / "summary.json", summary)
    (run / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (run / "tasks.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["task_id", "harness", "case_id", "repeat", "status", "passed", "duration_seconds", "artifact_directory"]
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    lockfile.close()
    CONSOLE.print(f"Report: {run / 'report.md'}")
    return 130 if interrupted else (1 if any(r["status"] in {"infra_error", "evaluator_error"} for r in rows) else 0)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        CONSOLE.print(f"[red]Error:[/] {clean(str(exc))}", markup=False)
        sys.exit(1)
