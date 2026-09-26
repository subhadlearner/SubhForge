"""Offline checks for the POC runner; these never call Claude or spend tokens."""

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import run_poc


def fake_success() -> subprocess.CompletedProcess[str]:
    payload = {
        "is_error": False,
        "structured_output": {
            "handoff_id": "HO-007",
            "status": "COMPLETED",
            "verdict_token": "OPUS_MATERIAL_FINDINGS",
            "findings": [{
                "id": "F-1",
                "severity": "HIGH",
                "claim": "A timeout skips the required denial audit",
                "evidence_refs": ["contract.md:AC-1 — invariant", "artifact.md:step 3 — timeout"],
                "recommendation": "Emit the audit event for a timeout",
            }],
        },
        "modelUsage": {"claude-opus-5-5": {"inputTokens": 100}},
        "usage": {"input_tokens": 100, "output_tokens": 50},
    }
    return subprocess.CompletedProcess([], 0, stdout=json.dumps(payload), stderr="")


class HandoffPocTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.handoff_patch = mock.patch.object(run_poc, "HANDOFFS", Path(self.temp.name))
        self.handoff_patch.start()

    def tearDown(self):
        self.handoff_patch.stop()
        self.temp.cleanup()

    def test_subscription_routing_refuses_api_key_without_printing_value(self):
        with self.assertRaisesRegex(ValueError, "ANTHROPIC_API_KEY") as caught:
            run_poc.check_routing_environment({"ANTHROPIC_API_KEY": "secret-test-value"})
        self.assertNotIn("secret-test-value", str(caught.exception))

    def test_detects_rate_limit_without_requiring_real_quota_exhaustion(self):
        self.assertEqual(
            run_poc.classify_failure(1, "", "HTTP 429: rate limit exceeded"),
            "QUOTA_OR_RATE_LIMIT",
        )
        self.assertEqual(
            run_poc.classify_failure(1, "", "usage limit reached; resets at 5pm"),
            "QUOTA_OR_RATE_LIMIT",
        )

    def test_rejects_malformed_or_inaccurate_findings(self):
        with self.assertRaises(ValueError):
            run_poc.parse_result('{"result":"unstructured"}')
        bad = fake_success()
        payload = json.loads(bad.stdout)
        payload["structured_output"]["findings"][0]["evidence_refs"] = ["artifact.md"]
        with self.assertRaisesRegex(ValueError, "cites both"):
            run_poc.parse_result(json.dumps(payload))

    def test_five_invocations_return_canonical_and_per_run_files(self):
        out = io.StringIO()
        with mock.patch.object(run_poc, "preflight"), mock.patch.object(
            run_poc, "invoke", return_value=fake_success()
        ) as invoke, mock.patch.object(
            sys, "argv", ["run_poc.py", "--runs", "5"]
        ), contextlib.redirect_stdout(out):
            self.assertEqual(run_poc.main(), 0)
        self.assertEqual(invoke.call_count, 5)
        self.assertIn("POC_RESULT: 5/5 valid runs", out.getvalue())
        canonical = run_poc.HANDOFFS / "HO-007.result.json"
        self.assertTrue(canonical.is_file())
        result = json.loads(canonical.read_text(encoding="utf-8"))
        self.assertEqual(result["model"], "claude-opus-5-5")
        self.assertEqual(result["usage"]["input_tokens"], 100)
        self.assertIn(" — ", result["findings"][0]["evidence_refs"][0])
        for index in range(1, 6):
            self.assertTrue((run_poc.HANDOFFS / f"HO-007.run-{index}.result.json").is_file())

    def test_failed_second_run_does_not_leave_a_canonical_success(self):
        quota = subprocess.CompletedProcess([], 1, stdout="", stderr="HTTP 429: rate limit")
        out = io.StringIO()
        with mock.patch.object(run_poc, "preflight"), mock.patch.object(
            run_poc, "invoke", side_effect=[fake_success(), quota]
        ), mock.patch.object(
            sys, "argv", ["run_poc.py", "--runs", "5"]
        ), contextlib.redirect_stdout(out):
            self.assertEqual(run_poc.main(), 1)
        self.assertIn("QUOTA_OR_RATE_LIMIT", out.getvalue())
        self.assertFalse((run_poc.HANDOFFS / "HO-007.result.json").exists())

    def test_invocation_is_opus_and_read_only(self):
        with mock.patch.object(run_poc, "run_command", return_value=fake_success()) as command:
            run_poc.invoke("claude", {}, 180)
        argv = command.call_args.args[0]
        self.assertEqual(argv[0:2], ["claude", "-p"])
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-5-5")
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Glob,Grep")
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "dontAsk")
        self.assertIn("--no-session-persistence", argv)

    def test_claude_stdout_is_decoded_as_utf8_on_windows(self):
        with mock.patch.object(run_poc.subprocess, "run", return_value=fake_success()) as process:
            run_poc.run_command(["claude", "--version"], env={}, timeout=30)
        self.assertEqual(process.call_args.kwargs["encoding"], "utf-8")

    def test_one_run_per_turn_resumes_without_repeating_paid_calls(self):
        out = io.StringIO()
        with mock.patch.object(run_poc, "preflight"), mock.patch.object(
            run_poc, "invoke", return_value=fake_success()
        ) as invoke, mock.patch.object(
            sys, "argv", ["run_poc.py"]
        ), contextlib.redirect_stdout(out):
            for _ in range(5):
                self.assertEqual(run_poc.main(), 0)
            self.assertEqual(run_poc.main(), 0)
        self.assertEqual(invoke.call_count, 5)
        self.assertIn("already complete; no new Claude call", out.getvalue())
        self.assertTrue((run_poc.HANDOFFS / "HO-007.result.json").exists())


if __name__ == "__main__":
    unittest.main()
