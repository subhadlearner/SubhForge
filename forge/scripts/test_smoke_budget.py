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
import smoke_segments
import smoke_state


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
        self.workspace_calls = []
        self.source_fingerprint = "a" * 64
        self.verification_report = "docs/verification/VERIFY-H07-001.md"
        (self.repo / self.verification_report).write_text(
            "Verification Result: NOT_DONE\n", encoding="utf-8"
        )
        self.implementation_fingerprint = "GIT_BLOB_OID:" + ("b" * 40)
        self.failures = ["DOCS_PUBLIC_API_MISSING"]
        self.classification = "NON_CRITICAL_QUALITY_GATE"

        smoke_state.init(
            self.repo,
            self.run_id,
            "FULL",
            "full-minimal-api",
            "source123",
            "base123",
        )
        smoke_segments.pin_qualification(
            self.repo,
            self.run_id,
            None,
            self.started.isoformat(),
            source_fingerprint="a" * 64,
        )
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "context_index": {
                    "budget_started_at_utc": self.started.isoformat(),
                    "contract_parity": {"contract_equal": True},
                }
            },
        )

    def rooted(self, repo, run_id):
        self.rooted_calls.append((repo, run_id))

    def refuse(self, repo, run_id):
        raise smoke_handoff.SmokeHandoffError("not rooted")

    def workspace(self, repo, run_id):
        self.workspace_calls.append((repo, run_id))

    def refuse_workspace(self, repo, run_id):
        raise smoke_handoff.SmokeHandoffError("not a disposable smoke workspace")

    def gate_state(self, *, run_state="IN_PROGRESS", gate_id=None, **overrides):
        state = {
            "profile": "FULL",
            "current_scenario": "waive-review-loop",
            "current_stage": "waive",
            "state": run_state,
            "latest_verification": {
                "result": "NOT_DONE",
                "delivery_gate": "BLOCKED",
                "freshness": "MATCH",
            },
            "blocker": (
                {
                    "gate_type": smoke_budget.HUMAN_WAIT_WAIVER_AUTHORIZATION,
                    "gate_id": gate_id,
                }
                if run_state == "WAITING_FOR_USER" and gate_id
                else None
            ),
        }
        state.update(overrides)
        return state

    def start_state(self, repo, run_id):
        return self.gate_state()

    def _place_in_s4(self):
        state = smoke_state.load(self.repo, self.run_id)
        runtime = state["context_index"]["segment_runtime"]
        if runtime.get("active_segment") == "S4":
            return
        state = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "completed_scenarios": ["static-release-gate"],
                "pending_scenarios": ["waive-review-loop"],
                "current_stage": "waive",
                "current_scenario": "waive-review-loop",
            },
        )
        context = dict(state["context_index"])
        runtime = dict(context["segment_runtime"])
        runtime.update({
            "active_segment": "S4",
            "active_status": smoke_segments.SEGMENT_ACTIVE,
            "active_started_at_utc": self.started.isoformat(),
            "closed_segments": [],
            "gap": None,
        })
        context["segment_runtime"] = runtime
        state["context_index"] = context
        smoke_state._validate_full_state(state, expected_run_id=self.run_id)
        smoke_state._save(smoke_state.state_path(self.repo, self.run_id), state)

    def _start_wait(self, *, at=None, failures=None, state_guard=None):
        self._place_in_s4()
        return smoke_budget.human_wait_start(
            self.repo,
            self.run_id,
            smoke_budget.HUMAN_WAIT_WAIVER_AUTHORIZATION,
            self.verification_report,
            self.implementation_fingerprint,
            failures or self.failures,
            self.classification,
            at or (self.started + dt.timedelta(minutes=10)),
            rooted_guard=self.rooted,
            state_guard=state_guard or self.start_state,
        )

    def _authorize_wait(self, gate_id, *, at=None, failures=None, **overrides):
        values = {
            "decision": "ACCEPTED_TEMPORARILY",
            "verification_report": self.verification_report,
            "failures": failures or self.failures,
            "classification": self.classification,
            "justification": "Intentional documentation-only smoke-test exception.",
            "residual_risk": "One public smoke API lacks required documentation.",
            "compensating_control": "Behavioral and security checks remain passing.",
            "remediation": "Restore the required documentation after the scenario.",
            "expiry": "End of this smoke-test session.",
        }
        values.update(overrides)
        return smoke_budget.human_wait_authorize(
            self.repo,
            self.run_id,
            smoke_budget.HUMAN_WAIT_WAIVER_AUTHORIZATION,
            gate_id,
            now=at or (self.started + dt.timedelta(hours=2, minutes=10)),
            workspace_guard=self.workspace,
            state_guard=lambda repo, run_id: self.gate_state(
                run_state="WAITING_FOR_USER",
                gate_id=gate_id,
            ),
            **values,
        )

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
            self.repo, self.run_id, self.started + dt.timedelta(minutes=79, seconds=59),
        )
        self.assertEqual("WITHIN_BUDGET", before["result"])
        self.assertEqual(1.0, before["remaining_seconds"])
        at_limit = smoke_budget.check(
            self.repo, self.run_id, self.started + dt.timedelta(minutes=80),
        )
        self.assertEqual("PERFORMANCE_BUDGET_EXCEEDED", at_limit["result"])
        self.assertEqual(0.0, at_limit["remaining_seconds"])

    def test_numeric_budget_override_is_rejected(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.check(self.repo, self.run_id, 30)

    def test_duplicate_start_fails_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.start(self.repo, self.run_id, self.started)

    def test_open_human_wait_excludes_only_wait_time_from_budget(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=10))
        gate_id = opened["gate"]["gate_id"]

        during = smoke_budget.check(
            self.repo,
            self.run_id,
            self.started + dt.timedelta(hours=2, minutes=10),
        )
        self.assertEqual("WITHIN_BUDGET", during["result"])
        self.assertEqual(7800.0, during["wall_elapsed_seconds"])
        self.assertEqual(7200.0, during["excluded_human_wait_seconds"])
        self.assertEqual(600.0, during["elapsed_seconds"])
        self.assertEqual(gate_id, during["active_human_wait"]["gate_id"])

        accepted = self._authorize_wait(
            gate_id,
            at=self.started + dt.timedelta(hours=2, minutes=10),
        )
        self.assertEqual("HUMAN_AUTHORIZATION_ACCEPTED", accepted["result"])

        after = smoke_budget.check(
            self.repo,
            self.run_id,
            self.started + dt.timedelta(hours=2, minutes=15),
        )
        self.assertEqual("WITHIN_BUDGET", after["result"])
        self.assertEqual(900.0, after["elapsed_seconds"])
        self.assertEqual(2280.0, after["remaining_seconds"])
        self.assertIsNone(after["active_human_wait"])
        self.assertEqual(1, after["completed_human_wait_count"])
        self.assertEqual(
            "ACCEPTED_TEMPORARILY",
            self._budget_file()["human_wait_intervals"][0]["authorization"]["decision"],
        )

    def test_multiple_human_wait_intervals_are_summed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = self._start_wait(at=self.started + dt.timedelta(minutes=5))
        self._authorize_wait(
            first["gate"]["gate_id"],
            at=self.started + dt.timedelta(minutes=15),
        )

        second_failures = ["DOCS_SECOND_PUBLIC_API_MISSING"]
        second = self._start_wait(
            at=self.started + dt.timedelta(minutes=20),
            failures=second_failures,
        )
        self._authorize_wait(
            second["gate"]["gate_id"],
            at=self.started + dt.timedelta(minutes=50),
            failures=second_failures,
        )

        result = smoke_budget.check(
            self.repo,
            self.run_id,
            self.started + dt.timedelta(minutes=60),
        )
        self.assertEqual("WITHIN_BUDGET", result["result"])
        self.assertEqual(2400.0, result["excluded_human_wait_seconds"])
        self.assertEqual(1200.0, result["elapsed_seconds"])
        self.assertEqual(2, result["completed_human_wait_count"])

    def test_wait_start_is_idempotent_for_same_open_gate_without_restarting_clock(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = self._start_wait(at=self.started + dt.timedelta(minutes=10))
        before = self._budget_file()

        second = self._start_wait(at=self.started + dt.timedelta(minutes=20))

        self.assertEqual("HUMAN_AUTHORIZATION_WAIT_ACTIVE", second["result"])
        self.assertEqual(first["gate"]["gate_id"], second["gate"]["gate_id"])
        self.assertEqual(before, self._budget_file())
        self.assertEqual(
            (self.started + dt.timedelta(minutes=10)).isoformat(),
            second["gate"]["started_at_utc"],
        )

    def test_wait_start_rejects_non_waiver_scenario_without_mutation(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        before = self._budget_file()

        with self.assertRaises(smoke_budget.BudgetError):
            self._start_wait(
                state_guard=lambda repo, run_id: self.gate_state(
                    current_scenario="direct-fix-loop"
                )
            )

        self.assertEqual(before, self._budget_file())

    def test_wait_start_requires_failed_fresh_verification_state(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        before = self._budget_file()

        with self.assertRaises(smoke_budget.BudgetError):
            self._start_wait(
                state_guard=lambda repo, run_id: self.gate_state(
                    latest_verification={
                        "result": "DONE",
                        "delivery_gate": "CLEAR",
                        "freshness": "MATCH",
                    }
                )
            )

        self.assertEqual(before, self._budget_file())

    def test_authorization_requires_matching_waiting_blocker(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=10))
        gate_id = opened["gate"]["gate_id"]
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        before = path.read_text(encoding="utf-8")
        values = {
            "decision": "ACCEPTED_TEMPORARILY",
            "verification_report": self.verification_report,
            "failures": self.failures,
            "classification": self.classification,
            "justification": "Approved",
            "residual_risk": "Residual risk",
            "compensating_control": "Compensating control",
            "remediation": "Remediation",
            "expiry": "End of smoke run",
        }

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.human_wait_authorize(
                self.repo,
                self.run_id,
                smoke_budget.HUMAN_WAIT_WAIVER_AUTHORIZATION,
                gate_id,
                now=self.started + dt.timedelta(minutes=20),
                workspace_guard=self.workspace,
                state_guard=lambda repo, run_id: self.gate_state(
                    run_state="WAITING_FOR_USER",
                    gate_id="0" * 64,
                ),
                **values,
            )

        self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_report_content_change_produces_distinct_gate_identity(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = self._start_wait(at=self.started + dt.timedelta(minutes=5))
        first_gate_id = first["gate"]["gate_id"]
        self._authorize_wait(
            first_gate_id,
            at=self.started + dt.timedelta(minutes=10),
        )

        (self.repo / self.verification_report).write_text(
            "Verification Result: NOT_DONE\nChanged report bytes.\n",
            encoding="utf-8",
        )
        second = self._start_wait(at=self.started + dt.timedelta(minutes=15))

        self.assertNotEqual(first_gate_id, second["gate"]["gate_id"])
        smoke_budget.restore = None if False else getattr(smoke_budget, "restore", None)

    def test_report_change_after_request_blocks_authorization_without_mutation(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=5))
        gate_id = opened["gate"]["gate_id"]
        ledger_path = (
            self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        )
        before = ledger_path.read_text(encoding="utf-8")

        (self.repo / self.verification_report).write_text(
            "Verification Result: NOT_DONE\nTampered after request.\n",
            encoding="utf-8",
        )

        with self.assertRaises(smoke_budget.BudgetError):
            self._authorize_wait(
                gate_id,
                at=self.started + dt.timedelta(minutes=10),
            )

        self.assertEqual(before, ledger_path.read_text(encoding="utf-8"))

    def test_unknown_gate_and_second_different_open_gate_fail_without_mutation(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        before = self._budget_file()
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.human_wait_start(
                self.repo,
                self.run_id,
                "PAID_MODEL_APPROVAL",
                self.verification_report,
                self.implementation_fingerprint,
                self.failures,
                self.classification,
                self.started + dt.timedelta(minutes=1),
                rooted_guard=self.rooted,
            )
        self.assertEqual(before, self._budget_file())

        self._start_wait(at=self.started + dt.timedelta(minutes=10))
        before = self._budget_file()
        with self.assertRaises(smoke_budget.BudgetError):
            self._start_wait(
                at=self.started + dt.timedelta(minutes=20),
                failures=["A_DIFFERENT_FAILURE"],
            )
        self.assertEqual(before, self._budget_file())

    def test_stage_start_is_blocked_while_human_wait_is_open(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        self._start_wait(at=self.started + dt.timedelta(minutes=10))
        before = self._budget_file()

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo,
                self.run_id,
                "waive",
                "openai/gpt-5.6-luna",
                self.started + dt.timedelta(minutes=11),
                source_fingerprint=self.source_fingerprint,
                rooted_guard=self.rooted,
            )

        self.assertEqual(before, self._budget_file())

    def test_invalid_authorization_is_pure_noop_on_open_interval(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=10))
        gate_id = opened["gate"]["gate_id"]
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        before = path.read_text(encoding="utf-8")

        with self.assertRaises(smoke_budget.BudgetError):
            self._authorize_wait(
                gate_id,
                at=self.started + dt.timedelta(minutes=20),
                failures=["WRONG_FAILURE_SET"],
            )
        self.assertEqual(before, path.read_text(encoding="utf-8"))

        with self.assertRaises(smoke_budget.BudgetError):
            self._authorize_wait(
                gate_id,
                at=self.started + dt.timedelta(minutes=21),
                justification="   ",
            )
        self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_authorization_requires_validated_disposable_workspace_without_mutation(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=10))
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        before = path.read_text(encoding="utf-8")

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.human_wait_authorize(
                self.repo,
                self.run_id,
                smoke_budget.HUMAN_WAIT_WAIVER_AUTHORIZATION,
                opened["gate"]["gate_id"],
                decision="ACCEPTED_TEMPORARILY",
                verification_report=self.verification_report,
                failures=self.failures,
                classification=self.classification,
                justification="Approved",
                residual_risk="Residual risk",
                compensating_control="Compensating control",
                remediation="Remediation",
                expiry="End of smoke run",
                now=self.started + dt.timedelta(minutes=20),
                workspace_guard=self.refuse_workspace,
                state_guard=lambda repo, run_id: self.gate_state(
                    run_state="WAITING_FOR_USER",
                    gate_id=opened["gate"]["gate_id"],
                ),
            )

        self.assertEqual(before, path.read_text(encoding="utf-8"))

    def test_completed_gate_cannot_be_reopened(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=10))
        self._authorize_wait(
            opened["gate"]["gate_id"],
            at=self.started + dt.timedelta(minutes=20),
        )
        before = self._budget_file()

        with self.assertRaises(smoke_budget.BudgetError):
            self._start_wait(at=self.started + dt.timedelta(minutes=30))

        self.assertEqual(before, self._budget_file())

    def test_overlapping_persisted_wait_intervals_fail_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        first = self._start_wait(at=self.started + dt.timedelta(minutes=5))
        self._authorize_wait(
            first["gate"]["gate_id"],
            at=self.started + dt.timedelta(minutes=15),
        )
        second_failures = ["SECOND_FAILURE"]
        second = self._start_wait(
            at=self.started + dt.timedelta(minutes=20),
            failures=second_failures,
        )
        self._authorize_wait(
            second["gate"]["gate_id"],
            at=self.started + dt.timedelta(minutes=25),
            failures=second_failures,
        )

        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        data = self._budget_file()
        data["human_wait_intervals"][1]["started_at_utc"] = (
            self.started + dt.timedelta(minutes=14)
        ).isoformat()
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.check(
                self.repo,
                self.run_id,
                self.started + dt.timedelta(minutes=30),
            )

    def test_malformed_human_wait_timestamp_fails_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        opened = self._start_wait(at=self.started + dt.timedelta(minutes=5))
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        data = self._budget_file()
        data["human_wait_intervals"][0]["started_at_utc"] = None
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.check(
                self.repo,
                self.run_id,
                self.started + dt.timedelta(minutes=10),
            )

        self.assertIsNotNone(opened["gate"]["gate_id"])

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

    def test_old_budget_file_without_stage_ledger_fails_closed_for_segmented_full(self):
        path = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        path.write_text(
            json.dumps({"started_at_utc": self.started.isoformat()}),
            encoding="utf-8",
        )

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo, self.run_id, "grill", "openai/gpt-5.6-sol", self.started,
                source_fingerprint=self.source_fingerprint,
                rooted_guard=self.rooted,
            )

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
