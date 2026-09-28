"""Tests for deterministic smoke elapsed-time budget enforcement."""

import datetime as dt
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget
import smoke_handoff


class SmokeBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"
        self.started = dt.datetime(2026, 9, 27, 0, 0, tzinfo=dt.timezone.utc)
        self.rooted_calls = []

    def rooted(self, repo, run_id):
        self.rooted_calls.append((repo, run_id))

    def refuse(self, repo, run_id):
        raise smoke_handoff.SmokeHandoffError("not rooted")

    def test_budget_boundary(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        before = smoke_budget.check(
            self.repo, self.run_id, 30,
            self.started + dt.timedelta(minutes=29, seconds=59),
        )
        self.assertEqual("WITHIN_BUDGET", before["result"])
        self.assertEqual(1.0, before["remaining_seconds"])
        at_limit = smoke_budget.check(
            self.repo, self.run_id, 30,
            self.started + dt.timedelta(minutes=30),
        )
        self.assertEqual("PERFORMANCE_BUDGET_EXCEEDED", at_limit["result"])
        self.assertEqual(0.0, at_limit["remaining_seconds"])

    def test_duplicate_start_fails_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.start(self.repo, self.run_id, self.started)

    def test_stage_timing_is_persisted_with_unique_invocation_ids(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = smoke_budget.stage_start(
            self.repo, self.run_id, "verify", "deepseek/deepseek-flash",
            self.started + dt.timedelta(seconds=10),
            rooted_guard=self.rooted,
        )
        self.assertEqual("verify-001", first["invocation_id"])
        done = smoke_budget.stage_end(
            self.repo, self.run_id, first["invocation_id"],
            self.started + dt.timedelta(seconds=85),
            rooted_guard=self.rooted,
        )
        self.assertEqual(75.0, done["elapsed_seconds"])

        second = smoke_budget.stage_start(
            self.repo, self.run_id, "verify", "deepseek/deepseek-flash",
            self.started + dt.timedelta(seconds=90),
            rooted_guard=self.rooted,
        )
        self.assertEqual("verify-002", second["invocation_id"])

        data = json.loads((self.repo / "docs/verification/smoke" /
                           f"{self.run_id}.budget.json").read_text(encoding="utf-8"))
        self.assertEqual("verify-001", data["stage_invocations"][0]["invocation_id"])
        self.assertEqual(75.0, data["stage_invocations"][0]["elapsed_seconds"])

    def test_concurrent_or_duplicate_stage_timing_fails_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "architect", "openai/gpt-5.6-sol", self.started,
                rooted_guard=self.rooted,
            )

        smoke_budget.stage_end(
            self.repo, self.run_id, first["invocation_id"],
            self.started + dt.timedelta(seconds=1),
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_end(
                self.repo, self.run_id, first["invocation_id"],
                self.started + dt.timedelta(seconds=2),
                rooted_guard=self.rooted,
            )

    def test_old_budget_file_without_stage_ledger_remains_compatible(self):
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        path.write_text(
            json.dumps({"started_at_utc": self.started.isoformat()}),
            encoding="utf-8",
        )

        result = smoke_budget.stage_start(
            self.repo, self.run_id, "grill", "openai/gpt-5.6-sol", self.started,
            rooted_guard=self.rooted,
        )
        self.assertEqual("grill-001", result["invocation_id"])

    def _budget_file(self):
        return json.loads((self.repo / "docs/verification/smoke" /
                           f"{self.run_id}.budget.json").read_text(encoding="utf-8"))

    def test_stage_start_checks_rooting_for_the_exact_run(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
            rooted_guard=self.rooted,
        )
        self.assertEqual([(self.repo, self.run_id)], self.rooted_calls)

    def test_unrooted_stage_start_fails_closed_without_recording(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
                rooted_guard=self.refuse,
            )
        self.assertEqual([], self._budget_file()["stage_invocations"])

    def test_unrooted_stage_end_fails_closed_and_leaves_invocation_open(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_end(
                self.repo, self.run_id, first["invocation_id"],
                self.started + dt.timedelta(seconds=5), rooted_guard=self.refuse,
            )
        self.assertIsNone(self._budget_file()["stage_invocations"][0]["ended_at_utc"])

    def test_default_guard_fails_closed_outside_rooted_session(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        # Patch the mapping object rather than mutating os.environ: restoring a
        # mutated environment on Windows deletes empty-valued host variables.
        unmarked = {key: value for key, value in os.environ.items()
                    if key not in smoke_handoff.MARKER_ENV}
        with mock.patch.object(smoke_handoff.os, "environ", unmarked):
            with self.assertRaises(smoke_budget.BudgetError):
                smoke_budget.stage_start(
                    self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started
                )
        self.assertEqual([], self._budget_file()["stage_invocations"])


if __name__ == "__main__":
    unittest.main()
