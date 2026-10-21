"""Offline failure-path tests. These never contact a model."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_benchmark as runner


class RunnerTests(unittest.TestCase):
    def test_opencode_file_permissions_are_scoped_to_task(self):
        with tempfile.TemporaryDirectory() as name:
            base = Path(name)
            workspace = base / "workspace"
            workspace.mkdir()
            with patch.object(runner.subprocess, "check_output", return_value=str(base).encode()):
                runner.build("opencode", workspace, base / "state",
                             {"model": "qwen/qwen3.8-27b", "base_url": "https://openrouter.ai/api"},
                             {"opencode": "not-executed"})
            config = json.loads((base / "state/opencode.json").read_text(encoding="utf-8"))
            for permissions in [config["permission"], config["agent"]["build"]["permission"]]:
                for tool in ["read", "edit"]:
                    self.assertEqual(permissions[tool]["*"], "deny")
                    self.assertEqual(permissions[tool][workspace.resolve().as_posix() + "/**"], "allow")
                    self.assertEqual(permissions[tool]["workspace/**"], "allow")
                    self.assertNotIn(base.resolve().as_posix() + "/**", permissions[tool])
                    self.assertNotIn("../*", permissions[tool])
                self.assertEqual(permissions["grep"], "deny")
                self.assertEqual(permissions["glob"], "deny")

    def test_json_scalar_and_plain_error_lines_are_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            program = ("import json,sys; sys.stdin.read(); "
                       "sys.stderr.write('Config is not valid JSON(C):\\n'); "
                       "[print(json.dumps(v),file=sys.stderr) for v in ['bench',[1,2],None,7]]; "
                       "print(json.dumps({'type':'error','message':'configuration rejected'}))")
            with patch.object(runner, "build", return_value=([sys.executable, "-c", program], os.environ.copy())):
                result = runner.execute("fake", folder, "hello", {"timeout_seconds": 5}, {})
            self.assertEqual(result["status"], "infra_error")
            events = json.loads((folder / "trace.json").read_text(encoding="utf-8"))
            self.assertTrue(all(isinstance(event, dict) for event in events))
            self.assertEqual(sum(event["type"] == "diagnostic" for event in events), 5)
            self.assertTrue(any(event["type"] == "error" for event in events))

    def test_process_redaction_and_json_error(self):
        runner.TOKEN = "private-test-credential"
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            program = "import json,sys; sys.stdin.read(); print(json.dumps({'type':'error','value':'private-test-credential'}))"
            with patch.object(runner, "build", return_value=([sys.executable, "-c", program], os.environ.copy())):
                result = runner.execute("fake", folder, "hello", {"timeout_seconds": 5}, {})
            self.assertEqual(result["status"], "infra_error")
            self.assertNotIn(runner.TOKEN, (folder / "stdout.log").read_text())
            self.assertNotIn(runner.TOKEN, (folder / "trace.json").read_text())

    def test_process_timeout_is_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            program = "import sys,time; sys.stdin.read(); time.sleep(30)"
            with patch.object(runner, "build", return_value=([sys.executable, "-c", program], os.environ.copy())):
                result = runner.execute("fake", folder, "hello", {"timeout_seconds": 0.3}, {})
            self.assertEqual(result["status"], "timeout")
            self.assertLess(result["duration_seconds"], 10)
            self.assertEqual(len(runner.ACTIVE), 0)

    def test_empty_fixture_fails_and_reference_passes(self):
        cases = json.loads((runner.HERE / "subsets/pilot-10.json").read_text(encoding="utf-8"))["cases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertFalse(runner.score(case, "int main(void) { return 0; }")["passed"])
                code = (runner.ROOT / case["path"] / "reference/main.c").read_text(encoding="utf-8")
                self.assertTrue(runner.score(case, code)["passed"])


if __name__ == "__main__":
    unittest.main()
