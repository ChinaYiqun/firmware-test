"""Offline health check: dependencies and the selected reference implementations."""
import hashlib
import importlib.metadata
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def check(base_dir=None):
    HERE = Path(base_dir) if base_dir else Path(__file__).resolve().parent
    ROOT = HERE.parents[1]
    from embedeval.evaluator import _run_behavioral, _run_static_checks

    subset = json.loads((HERE / "subsets/pilot-10.json").read_text(encoding="utf-8"))
    results = []
    for case in subset["cases"]:
        directory = ROOT / case["path"]
        code = (directory / "reference/main.c").read_text(encoding="utf-8")
        layers = [_run_static_checks(directory, code), _run_behavioral(directory, code)]
        passed = all(layer.passed and layer.details and not layer.error for layer in layers)
        item = {"case_id": case["id"], "passed": bool(passed),
                "layers": [layer.model_dump(mode="json") for layer in layers]}
        results.append(item)
        print(f"{'PASS' if passed else 'FAIL'} {case['id']}")
    files = {}
    for case in subset["cases"]:
        for path in sorted((ROOT / case["path"]).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted((ROOT / "benchmarks/embedeval-main/src/embedeval").rglob("*.py")):
        files[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "packages": {name: importlib.metadata.version(name)
                     for name in ["embedeval", "pydantic", "PyYAML", "rich", "litellm"]},
        "passed": all(row["passed"] for row in results), "cases": results,
        "source_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
    }
    (HERE / "environment-check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reference health: {sum(r['passed'] for r in results)}/{len(results)}")
    return report


if __name__ == "__main__":
    sys.exit(0 if check()["passed"] else 1)
