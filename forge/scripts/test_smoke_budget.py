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
        self.source_guard_calls = []
        self.source_fingerprint = "a" * 64

    def rooted(self, repo, run_id):
        self.rooted_calls.append((repo, run_id))

    def refuse(self, repo, run_id):
        raise smoke_handoff.SmokeHandoffError("not rooted")

    def source_matches(self, source, expected):
        self.source_guard_calls.append((source, expected))
        return {
            "source_checkout_path": str(source),
            "fingerprint": expected,
            "expected_fingerprint": expected,
            "result": "MATCH",
        }

    def source_mismatch(self, source, expected):
        self.source_guard_calls.append((source, expected))
        return {
            "source_checkout_path": str(source),
            "fingerprint": "b" * 64,
            "expected_fingerprint": expected,
            "result": "MISMATCH",
        }

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
            source_fingerprint=self.source_fingerprint,
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
            source_fingerprint=self.source_fingerprint,
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
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "architect", "openai/gpt-5.6-sol", self.started,
                source_fingerprint=self.source_fingerprint,
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
            source_fingerprint=self.source_fingerprint,
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
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        self.assertEqual([(self.repo, self.run_id)], self.rooted_calls)

    def test_unrooted_stage_start_fails_closed_without_recording(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
                source_fingerprint=self.source_fingerprint,
                rooted_guard=self.refuse,
            )
        self.assertEqual([], self._budget_file()["stage_invocations"])

    def test_unrooted_stage_end_fails_closed_and_leaves_invocation_open(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_end(
                self.repo, self.run_id, first["invocation_id"],
                self.started + dt.timedelta(seconds=5), rooted_guard=self.refuse,
            )
        self.assertIsNone(self._budget_file()["stage_invocations"][0]["ended_at_utc"])

    def test_stage_abort_closes_known_failure_and_allows_next_stage(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )

        aborted = smoke_budget.stage_abort(
            self.repo, self.run_id, first["invocation_id"],
            "CHILD_INVOCATION_FAILED",
            self.started + dt.timedelta(seconds=5),
            rooted_guard=self.rooted,
        )

        self.assertEqual(smoke_budget.INVOCATION_ABORTED, aborted["status"])
        self.assertEqual("CHILD_INVOCATION_FAILED", aborted["termination_reason"])
        self.assertEqual(5.0, aborted["elapsed_seconds"])

        second = smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol",
            self.started + dt.timedelta(seconds=6),
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        self.assertEqual("prd-002", second["invocation_id"])

    def test_source_mutation_abort_persists_restart_safe_continuation_blocker(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        active = smoke_budget.stage_start(
            self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )

        aborted = smoke_budget.stage_abort(
            self.repo, self.run_id, active["invocation_id"],
            "SOURCE_CHECKOUT_MUTATED",
            self.started + dt.timedelta(seconds=5),
            rooted_guard=self.rooted,
        )
        self.assertEqual(smoke_budget.INVOCATION_ABORTED, aborted["status"])
        blocker = self._budget_file()["continuation_blocker"]
        self.assertEqual("SOURCE_CHECKOUT_MUTATED", blocker["code"])
        self.assertEqual(active["invocation_id"], blocker["invocation_id"])

        # Simulate a crash before the orchestrator could persist its canonical
        # blocker. Both recovery and a direct new start must still fail closed.
        again = smoke_budget.recover_active(
            self.repo, self.run_id, self.repo,
            self.started + dt.timedelta(seconds=6),
            rooted_guard=self.rooted,
            source_guard=self.source_matches,
        )
        self.assertEqual("RECOVERY_BLOCKED", again["result"])
        self.assertEqual(
            "SOURCE_CHECKOUT_MUTATED",
            again["continuation_blocker"]["code"],
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "prd", "openai/gpt-5.6-sol",
                self.started + dt.timedelta(seconds=7),
                source_fingerprint=self.source_fingerprint,
                rooted_guard=self.rooted,
            )

    def test_duplicate_end_and_abort_transitions_fail_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        completed = smoke_budget.stage_start(
            self.repo, self.run_id, "verify", "deepseek/deepseek-flash", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        smoke_budget.stage_end(
            self.repo, self.run_id, completed["invocation_id"],
            self.started + dt.timedelta(seconds=1),
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_end(
                self.repo, self.run_id, completed["invocation_id"],
                self.started + dt.timedelta(seconds=2),
                rooted_guard=self.rooted,
            )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_abort(
                self.repo, self.run_id, completed["invocation_id"], "LATE_ABORT",
                self.started + dt.timedelta(seconds=2),
                rooted_guard=self.rooted,
            )

        aborted = smoke_budget.stage_start(
            self.repo, self.run_id, "fix", "deepseek/deepseek-flash",
            self.started + dt.timedelta(seconds=3),
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        smoke_budget.stage_abort(
            self.repo, self.run_id, aborted["invocation_id"], "CHILD_INVOCATION_FAILED",
            self.started + dt.timedelta(seconds=4),
            rooted_guard=self.rooted,
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_abort(
                self.repo, self.run_id, aborted["invocation_id"], "DUPLICATE_ABORT",
                self.started + dt.timedelta(seconds=5),
                rooted_guard=self.rooted,
            )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_end(
                self.repo, self.run_id, aborted["invocation_id"],
                self.started + dt.timedelta(seconds=5),
                rooted_guard=self.rooted,
            )

    def test_recover_active_marks_interrupted_without_fabricating_runtime(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        active = smoke_budget.stage_start(
            self.repo, self.run_id, "architect", "openai/gpt-5.6-sol",
            self.started + dt.timedelta(seconds=10),
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )

        recovered = smoke_budget.recover_active(
            self.repo,
            self.run_id,
            self.repo,
            self.started + dt.timedelta(minutes=10),
            rooted_guard=self.rooted,
            source_guard=self.source_matches,
        )

        self.assertTrue(recovered["recovered"])
        item = recovered["invocation"]
        self.assertEqual(active["invocation_id"], item["invocation_id"])
        self.assertEqual(smoke_budget.INVOCATION_INTERRUPTED, item["status"])
        self.assertEqual("RESUME_RECOVERY", item["termination_reason"])
        self.assertIsNone(item["ended_at_utc"])
        self.assertIsNone(item["elapsed_seconds"])
        self.assertEqual(self.source_fingerprint, item["source_fingerprint"])
        self.assertIsNotNone(item["recovered_at_utc"])
        self.assertEqual("MATCH", recovered["source_guard_result"]["result"])
        self.assertIsNone(recovered["continuation_blocker"])
        self.assertEqual(
            [(self.repo.resolve(), self.source_fingerprint)],
            self.source_guard_calls,
        )

        next_stage = smoke_budget.stage_start(
            self.repo, self.run_id, "architect", "openai/gpt-5.6-sol",
            self.started + dt.timedelta(minutes=10, seconds=1),
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        self.assertEqual("architect-002", next_stage["invocation_id"])

    def test_recover_active_is_noop_when_nothing_is_active(self):
        smoke_budget.start(self.repo, self.run_id, self.started)

        recovered = smoke_budget.recover_active(
            self.repo, self.run_id, self.repo, self.started,
            rooted_guard=self.rooted,
            source_guard=self.source_matches,
        )

        self.assertFalse(recovered["recovered"])
        self.assertEqual("NO_ACTIVE_INVOCATION", recovered["result"])
        self.assertIsNone(recovered["invocation"])

    def test_recover_active_handles_legacy_active_record(self):
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        path.write_text(
            json.dumps({
                "started_at_utc": self.started.isoformat(),
                "stage_invocations": [{
                    "invocation_id": "prd-001",
                    "stage": "prd",
                    "model": "openai/gpt-5.6-sol",
                    "source_fingerprint": self.source_fingerprint,
                    "started_at_utc": self.started.isoformat(),
                    "ended_at_utc": None,
                    "elapsed_seconds": None,
                }],
            }),
            encoding="utf-8",
        )

        recovered = smoke_budget.recover_active(
            self.repo, self.run_id, self.repo,
            self.started + dt.timedelta(seconds=20),
            rooted_guard=self.rooted,
            source_guard=self.source_matches,
        )

        self.assertTrue(recovered["recovered"])
        self.assertEqual(
            smoke_budget.INVOCATION_INTERRUPTED,
            recovered["invocation"]["status"],
        )

    def test_interrupted_source_mismatch_persists_restart_safe_blocker(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        active = smoke_budget.stage_start(
            self.repo, self.run_id, "implement", "deepseek/deepseek-flash", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )

        recovered = smoke_budget.recover_active(
            self.repo, self.run_id, self.repo,
            self.started + dt.timedelta(seconds=30),
            rooted_guard=self.rooted,
            source_guard=self.source_mismatch,
        )

        self.assertTrue(recovered["recovered"])
        self.assertEqual(
            smoke_budget.INVOCATION_INTERRUPTED,
            recovered["invocation"]["status"],
        )
        self.assertEqual("MISMATCH", recovered["source_guard_result"]["result"])
        self.assertEqual(
            "SOURCE_CHECKOUT_MUTATED",
            recovered["continuation_blocker"]["code"],
        )

        # Simulate another crash after recovery was persisted but before the
        # orchestrator could persist its canonical blocker. The next RESUME
        # must still fail closed from the budget ledger.
        again = smoke_budget.recover_active(
            self.repo, self.run_id, self.repo,
            self.started + dt.timedelta(seconds=31),
            rooted_guard=self.rooted,
            source_guard=self.source_matches,
        )
        self.assertEqual("RECOVERY_BLOCKED", again["result"])
        self.assertEqual(
            "SOURCE_CHECKOUT_MUTATED",
            again["continuation_blocker"]["code"],
        )
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "implement", "deepseek/deepseek-flash",
                self.started + dt.timedelta(seconds=32),
                source_fingerprint=self.source_fingerprint,
                rooted_guard=self.rooted,
            )

    def test_legacy_active_without_source_fingerprint_becomes_unreconstructable(self):
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        path.write_text(
            json.dumps({
                "started_at_utc": self.started.isoformat(),
                "stage_invocations": [{
                    "invocation_id": "prd-001",
                    "stage": "prd",
                    "model": "openai/gpt-5.6-sol",
                    "started_at_utc": self.started.isoformat(),
                    "ended_at_utc": None,
                    "elapsed_seconds": None,
                }],
            }),
            encoding="utf-8",
        )

        recovered = smoke_budget.recover_active(
            self.repo, self.run_id, self.repo,
            self.started + dt.timedelta(seconds=20),
            rooted_guard=self.rooted,
            source_guard=self.source_matches,
        )

        self.assertTrue(recovered["recovered"])
        self.assertEqual(
            "UNRECONSTRUCTABLE",
            recovered["source_guard_result"]["result"],
        )
        self.assertEqual(
            "INTERRUPTED_SOURCE_GUARD_UNAVAILABLE",
            recovered["continuation_blocker"]["code"],
        )
        self.assertEqual([], self.source_guard_calls)

    def test_source_guard_execution_failure_leaves_invocation_active_for_retry(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        active = smoke_budget.stage_start(
            self.repo, self.run_id, "verify", "deepseek/deepseek-flash", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )

        def broken_guard(source, expected):
            raise smoke_budget.smoke_workspace.SmokeWorkspaceError("guard unavailable")

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.recover_active(
                self.repo, self.run_id, self.repo,
                self.started + dt.timedelta(seconds=10),
                rooted_guard=self.rooted,
                source_guard=broken_guard,
            )

        item = self._budget_file()["stage_invocations"][0]
        self.assertEqual(active["invocation_id"], item["invocation_id"])
        self.assertEqual(smoke_budget.INVOCATION_ACTIVE, item["status"])
        self.assertIsNone(item["recovered_at_utc"])

    def test_multiple_active_invocations_fail_closed_without_mutation(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        data = self._budget_file()
        data["stage_invocations"] = [
            {
                "invocation_id": "prd-001",
                "stage": "prd",
                "model": "openai/gpt-5.6-sol",
                "source_fingerprint": self.source_fingerprint,
                "status": smoke_budget.INVOCATION_ACTIVE,
                "started_at_utc": self.started.isoformat(),
                "ended_at_utc": None,
                "elapsed_seconds": None,
            },
            {
                "invocation_id": "architect-001",
                "stage": "architect",
                "model": "openai/gpt-5.6-sol",
                "source_fingerprint": self.source_fingerprint,
                "status": smoke_budget.INVOCATION_ACTIVE,
                "started_at_utc": self.started.isoformat(),
                "ended_at_utc": None,
                "elapsed_seconds": None,
            },
        ]
        path.write_text(json.dumps(data), encoding="utf-8")
        before = self._budget_file()

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.recover_active(
                self.repo, self.run_id, self.repo,
                self.started + dt.timedelta(seconds=5),
                rooted_guard=self.rooted,
                source_guard=self.source_matches,
            )

        self.assertEqual(before, self._budget_file())

    def test_unrooted_abort_and_recovery_fail_without_changing_ledger(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        active = smoke_budget.stage_start(
            self.repo, self.run_id, "spec", "openai/gpt-5.6-sol", self.started,
            source_fingerprint=self.source_fingerprint,
            rooted_guard=self.rooted,
        )
        before = self._budget_file()

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_abort(
                self.repo, self.run_id, active["invocation_id"], "CHILD_FAILED",
                self.started + dt.timedelta(seconds=1),
                rooted_guard=self.refuse,
            )
        self.assertEqual(before, self._budget_file())

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.recover_active(
                self.repo, self.run_id, self.repo,
                self.started + dt.timedelta(seconds=2),
                rooted_guard=self.refuse,
                source_guard=self.source_matches,
            )
        self.assertEqual(before, self._budget_file())

    def test_stage_start_requires_sha256_source_fingerprint(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
                source_fingerprint="not-a-fingerprint",
                rooted_guard=self.rooted,
            )
        self.assertEqual([], self._budget_file()["stage_invocations"])

    def test_default_guard_fails_closed_outside_rooted_session(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        # Patch the mapping object rather than mutating os.environ: restoring a
        # mutated environment on Windows deletes empty-valued host variables.
        unmarked = {key: value for key, value in os.environ.items()
                    if key not in smoke_handoff.MARKER_ENV}
        with mock.patch.object(smoke_handoff.os, "environ", unmarked):
            with self.assertRaises(smoke_budget.BudgetError):
                smoke_budget.stage_start(
                    self.repo, self.run_id, "prd", "openai/gpt-5.6-sol", self.started,
                    source_fingerprint=self.source_fingerprint,
                )
        self.assertEqual([], self._budget_file()["stage_invocations"])


if __name__ == "__main__":
    unittest.main()
