"""Health-check selected EmbedEval references using L0 and L3 only."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from embedeval.evaluator import _run_behavioral, _run_static_checks


def check(cases: list[dict], experiment_dir: Path) -> dict:
    root = experiment_dir.resolve().parents[1]
    results = []
    files = {}
    for case in cases:
        directory = root / case["path"]
        reference = directory / "reference/main.c"
        code = reference.read_text(encoding="utf-8")
        layers = [_run_static_checks(directory, code), _run_behavioral(directory, code)]
        passed = all(layer.passed and layer.details and not layer.error for layer in layers)
        results.append({"case_id": case["id"], "passed": bool(passed),
                        "errors": [layer.error for layer in layers if layer.error]})
        for path in sorted(directory.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    for path in sorted((root / "benchmarks/embedeval-main/src/embedeval").rglob("*.py")):
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"scope": "L0+L3 only", "selected": len(cases),
              "passed": sum(row["passed"] for row in results),
              "source_sha256": hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(),
              "failures": [row for row in results if not row["passed"]]}
    (experiment_dir / "environment-check.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Reference L0/L3 health: {report['passed']}/{report['selected']}")
    return report
