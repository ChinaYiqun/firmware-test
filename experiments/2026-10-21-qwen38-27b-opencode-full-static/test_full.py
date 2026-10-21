"""Offline regression tests: no API requests, no paid experiments."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from rich.console import Console
import run_full as runner


class FullRunnerTests(unittest.TestCase):
    def test_all_public_cases_have_healthy_checks(self):
        with tempfile.TemporaryDirectory() as name, patch.object(runner, "HERE", Path(name)):
            manifest, health = runner.inventory()
        self.assertEqual(len(manifest["cases"]), 219)
        self.assertEqual(health["reference_passed"], 219)
        self.assertEqual(manifest["excluded"], [])

    def test_recovery_retries_only_unfinished_or_infrastructure_errors(self):
        with tempfile.TemporaryDirectory() as name:
            run = Path(name)
            for number, status in enumerate(["scored_pass", "scored_fail", "timeout", "no_submission",
                                             "infra_error", "evaluator_error", "running", "cancelled"]):
                directory = run / "tasks" / str(number) / "attempt"
                runner.dump(directory / "result.json", {"case_id": str(number), "attempt_id": str(number),
                            "status": status, "started_at": "2026-10-21T00:00:00+00:00"})
            attempts, latest = runner.latest_results(run)
            pending = runner.select_pending([{"id": str(n)} for n in range(9)], latest)
            self.assertEqual(len(attempts), 8)
            self.assertEqual([c["id"] for c in pending], ["4", "5", "6", "7", "8"])

    def test_cancel_before_requests_and_no_auto_install(self):
        with tempfile.TemporaryDirectory() as name:
            here = Path(name)
            runner.dump(here / "experiment.json", {"model": "qwen/qwen3.8-27b", "base_url": "https://openrouter.ai/api"})
            with patch.object(runner, "HERE", here), patch.object(runner, "CONSOLE", Console(file=io.StringIO())), \
                 patch("sys.argv", ["run_full.py", "--dry-run", "--limit", "1"]), \
                 patch.object(runner, "confirm", return_value=False) as confirm, \
                 patch.object(runner.engine, "execute", side_effect=AssertionError("No API")):
                self.assertEqual(runner.main(), 0)
                confirm.assert_called_once_with(1, 0, 1, 2, True)
            self.assertFalse((here / "latest-dry-run.json").exists())
            self.assertEqual(list(here.rglob("result.json")), [])

    def test_dry_run_resume_and_config_mismatch(self):
        with tempfile.TemporaryDirectory() as name:
            here = Path(name)
            runner.dump(here / "experiment.json", {"model": "qwen/qwen3.8-27b", "base_url": "https://openrouter.ai/api"})
            with patch.object(runner, "HERE", here), patch.object(runner, "CONSOLE", Console(file=io.StringIO())), \
                 patch("sys.argv", ["run_full.py", "--dry-run", "--yes", "--limit", "3"]), \
                 patch.object(runner.engine, "execute", side_effect=AssertionError("No API")):
                self.assertEqual(runner.main(), 0)
                run = here / runner.read(here / "latest-dry-run.json")["run"]
                first, latest = runner.latest_results(run)
                self.assertEqual(len(first), 3)
                self.assertEqual(runner.main(), 0)
                second, _ = runner.latest_results(run)
                self.assertEqual(len(second), 3)
                config = runner.read(run / "config.json")
                config["model"] = "wrong-model"
                runner.dump(run / "config.json", config)
                with self.assertRaisesRegex(RuntimeError, "resume refused"):
                    runner.main()

    def test_run_lock_prevents_duplicate_writer(self):
        with tempfile.TemporaryDirectory() as name:
            run = Path(name)
            with runner.run_lock(run):
                with self.assertRaises(OSError):
                    with runner.run_lock(run):
                        self.fail("Second writer entered the same run")


if __name__ == "__main__":
    unittest.main()
