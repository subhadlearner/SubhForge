"""Tests for structured smoke orchestration state."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_segments
import smoke_state


class SmokeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"

    def init_full(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        smoke_segments.pin_qualification(
            self.repo,
            self.run_id,
            None,
            "2026-09-27T00:00:00+00:00",
            source_fingerprint="a" * 64,
        )
        return smoke_state.load(self.repo, self.run_id)

    def mark_all_segments_closed(self):
        state = smoke_state.load(self.repo, self.run_id)
        context = dict(state["context_index"])
        runtime = dict(context["segment_runtime"])
        runtime["active_segment"] = None
        runtime["active_status"] = None
        runtime["active_started_at_utc"] = None
        runtime["active_source_fingerprint"] = None
        runtime["gap"] = None
        runtime["gaps"] = []
        runtime["disqualification_reason"] = None
        closed = []
        for index, segment in enumerate(context["qualification_config"]["segments"]):
            checkpoint = segment["close_checkpoint"]
            verified = (
                segment["start_checkpoint"]
                if checkpoint == "QUALIFICATION_EVIDENCE_READY"
                else checkpoint
            )
            closed.append({
                "segment_id": segment["id"],
                "status": "COMPLETED",
                "started_at_utc": "2026-09-27T00:00:00+00:00",
                "closed_at_utc": "2026-09-27T00:10:00+00:00",
                "charged_elapsed_seconds": 600.0,
                "excluded_human_wait_seconds": 0.0,
                "configured_limit_minutes": segment["limit_minutes"],
                "assigned_scenarios": list(segment["scenarios"]),
                "completed_scenarios": list(segment["scenarios"]),
                "checkpoint": checkpoint,
                "verified_checkpoint": verified,
                "checkpoint_fingerprint": "b" * 64,
                "source_fingerprint": "a" * 64,
                "evidence_manifest": {
                    "entries": [{
                        "path": "docs/verification/smoke/fake-{}.json".format(segment["id"]),
                        "sha256": "c" * 64,
                    }],
                    "sha256": "d" * 64,
                },
                "ledger_projection_sha256": "e" * 64,
            })
        runtime["closed_segments"] = closed
        context["segment_runtime"] = runtime
        context["qualification_eligible"] = True
        state["context_index"] = context
        smoke_state._validate_full_state(state, expected_run_id=self.run_id)
        smoke_state._save(smoke_state.state_path(self.repo, self.run_id), state)

    def state_file(self):
        return self.repo / "docs/verification/smoke" / f"{self.run_id}.state.json"

    def bootstrap_context(self):
        return {
            "budget_started_at_utc": "2026-09-27T00:00:00+00:00",
            "contract_parity": {"contract_equal": True},
        }

    def advance_past_static_gate(self):
        return smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "context_index": self.bootstrap_context(),
                "completed_scenarios": ["static-release-gate"],
                "current_stage": "grill",
            },
        )

    def test_init_and_targeted_update(self):
        created = self.init_full()
        self.assertEqual("static-release-gate", created["current_stage"])
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "current_stage": "architect",
                "completed_scenarios": ["static-release-gate", "grill", "prd"],
                "context_index": {
                    **self.bootstrap_context(),
                    "prd": "docs/prd/PRD-001.md",
                    "architecture": "docs/architecture/ARCH-001.md",
                },
            },
        )
        self.assertEqual("architect", updated["current_stage"])
        self.assertEqual("docs/prd/PRD-001.md", updated["context_index"]["prd"])
        self.assertEqual(updated, smoke_state.load(self.repo, self.run_id))

    def test_unknown_update_field_fails_closed_without_persisting_typo(self):
        before = self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"current_stgae": "architect"},
            )
        self.assertEqual(before, smoke_state.load(self.repo, self.run_id))
        self.assertNotIn("current_stgae", json.loads(self.state_file().read_text()))

    def test_load_rejects_unknown_or_missing_top_level_fields(self):
        state = self.init_full()
        state["surprise"] = True
        self.state_file().write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.load(self.repo, self.run_id)

        state.pop("surprise")
        state.pop("current_stage")
        self.state_file().write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.load(self.repo, self.run_id)

    def test_segment_runtime_exact_schema_fails_closed_on_unknown_or_missing_field(self):
        original = self.init_full()

        state = json.loads(json.dumps(original))
        runtime = dict(state["context_index"]["segment_runtime"])
        runtime["surprise"] = True
        state["context_index"]["segment_runtime"] = runtime
        self.state_file().write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.load(self.repo, self.run_id)

        state = json.loads(json.dumps(original))
        runtime = dict(state["context_index"]["segment_runtime"])
        runtime.pop("disqualification_reason")
        state["context_index"]["segment_runtime"] = runtime
        self.state_file().write_text(json.dumps(state), encoding="utf-8")
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.load(self.repo, self.run_id)

    def test_invalid_profile_or_run_state_fails_closed(self):
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.init(
                self.repo,
                self.run_id,
                "UNKNOWN",
                "full-minimal-api",
                "abc123",
                "base123",
            )

        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(self.repo, self.run_id, {"state": "RUNNING"})

    def test_scenarios_are_validated_against_selected_profile(self):
        self.init_full()
        self.advance_past_static_gate()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "completed_scenarios": [
                        "static-release-gate",
                        "static-model-routing",
                    ]
                },
            )

        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "completed_scenarios": [
                    "static-release-gate",
                    "paid-claude-runtime",
                ]
            },
        )
        self.assertEqual(
            ["static-release-gate", "paid-claude-runtime"],
            updated["completed_scenarios"],
        )

    def test_no_scenario_can_complete_before_static_release_gate(self):
        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"completed_scenarios": ["prd"]},
            )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"current_scenario": "prd"},
            )

    def test_scenario_lists_must_be_unique_and_disjoint(self):
        before = self.init_full()

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"completed_scenarios": ["prd", "prd"]},
            )
        self.assertEqual(before, smoke_state.load(self.repo, self.run_id))

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "completed_scenarios": ["prd"],
                    "pending_scenarios": ["prd", "architect"],
                },
            )
        self.assertEqual(before, smoke_state.load(self.repo, self.run_id))

    def test_invalid_scenario_lists_fail_closed(self):
        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"completed_scenarios": "prd"},
            )

    def test_current_scenario_must_be_registered_and_not_completed(self):
        self.init_full()
        self.advance_past_static_gate()
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "current_scenario": "diagnose-fix-loop",
                "pending_scenarios": ["diagnose-fix-loop"],
            },
        )
        self.assertEqual("diagnose-fix-loop", updated["current_scenario"])

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"current_scenario": "static-model-routing"},
            )

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "current_scenario": "diagnose-fix-loop",
                    "completed_scenarios": [
                        "static-release-gate",
                        "diagnose-fix-loop",
                    ],
                    "pending_scenarios": [],
                },
            )

    def test_current_stage_must_be_known_workflow_stage_or_profile_scenario(self):
        self.init_full()
        self.advance_past_static_gate()

        workflow = smoke_state.set_values(
            self.repo, self.run_id, {"current_stage": "verify"}
        )
        self.assertEqual("verify", workflow["current_stage"])

        scenario = smoke_state.set_values(
            self.repo, self.run_id, {"current_stage": "static-claude-routing"}
        )
        self.assertEqual("static-claude-routing", scenario["current_stage"])

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo, self.run_id, {"current_stage": "verfiy"}
            )

    def test_stage_metrics_persist_timing_and_context_paths(self):
        self.init_full()
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "stage_metrics": {
                    "prd": {
                        "model": "openai/gpt-5.6-sol",
                        "elapsed_seconds": 142.5,
                        "context_paths": [
                            "docs/discovery/DISC-001.md",
                            "AGENTS.md",
                        ],
                        "discovery_policy": "EXACT_ONLY",
                    }
                }
            },
        )
        self.assertEqual(142.5, updated["stage_metrics"]["prd"]["elapsed_seconds"])
        self.assertEqual("EXACT_ONLY", updated["stage_metrics"]["prd"]["discovery_policy"])

    def test_invalid_stage_metrics_fail_closed(self):
        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"stage_metrics": {"prd": {"elapsed_seconds": -1}}},
            )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"stage_metrics": {"": {"elapsed_seconds": 1}}},
            )

    def test_bootstrap_context_is_write_once_and_unrelated_context_still_merges(self):
        self.init_full()
        bootstrap_context = self.bootstrap_context()
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {"context_index": bootstrap_context},
        )

        same = smoke_state.set_values(
            self.repo,
            self.run_id,
            {"context_index": bootstrap_context},
        )
        self.assertEqual(
            bootstrap_context["budget_started_at_utc"],
            same["context_index"]["budget_started_at_utc"],
        )

        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {"context_index": {"discovery": "docs/discovery/full-minimal-api-discovery.md"}},
        )
        self.assertEqual(
            bootstrap_context["contract_parity"],
            updated["context_index"]["contract_parity"],
        )
        self.assertEqual(
            "docs/discovery/full-minimal-api-discovery.md",
            updated["context_index"]["discovery"],
        )

        for malicious in (
            {"budget_started_at_utc": "2099-01-01T00:00:00+00:00"},
            {"contract_parity": {"contract_equal": False}},
        ):
            with self.assertRaises(smoke_state.SmokeStateError):
                smoke_state.set_values(
                    self.repo,
                    self.run_id,
                    {"context_index": malicious},
                )

    def test_static_gate_completion_requires_protected_bootstrap_context(self):
        self.init_full()

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "completed_scenarios": ["static-release-gate"],
                    "current_stage": "grill",
                },
            )

        completed = self.advance_past_static_gate()
        self.assertEqual("grill", completed["current_stage"])
        self.assertIn("contract_parity", completed["context_index"])
        self.assertIn("budget_started_at_utc", completed["context_index"])

    def test_current_stage_cannot_advance_before_static_gate_completion(self):
        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"current_stage": "grill"},
            )

    def test_protected_bootstrap_context_cannot_be_established_late(self):
        self.init_full()
        # Simulate a corrupt legacy record that advanced without bootstrap
        # context. Loading fails; the protected keys cannot be injected later
        # through a targeted update to make the bad history look valid.
        raw = json.loads(self.state_file().read_text(encoding="utf-8"))
        raw["current_stage"] = "grill"
        raw["completed_scenarios"] = ["static-release-gate"]
        self.state_file().write_text(json.dumps(raw), encoding="utf-8")

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.load(self.repo, self.run_id)
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"context_index": self.bootstrap_context()},
            )

    def test_bootstrap_timestamp_and_parity_shapes_fail_closed(self):
        self.init_full()
        for context in (
            {"budget_started_at_utc": "not-a-timestamp"},
            {"budget_started_at_utc": "2026-09-27T00:00:00"},
            {"contract_parity": {}},
            {"contract_parity": {"contract_equal": "yes"}},
        ):
            with self.assertRaises(smoke_state.SmokeStateError):
                smoke_state.set_values(
                    self.repo,
                    self.run_id,
                    {"context_index": context},
                )

    def test_stage_metric_updates_merge_without_dropping_prior_stages(self):
        self.init_full()
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "stage_metrics": {
                    "static-release-gate": {
                        "model": "deterministic",
                        "elapsed_seconds": 0.02,
                        "context_paths": [],
                    }
                }
            },
        )
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "stage_metrics": {
                    "grill": {
                        "model": "openai/gpt-5.6-sol",
                        "elapsed_seconds": 108.9,
                        "context_paths": ["AGENTS.md"],
                    }
                }
            },
        )
        self.assertIn("static-release-gate", updated["stage_metrics"])
        self.assertIn("grill", updated["stage_metrics"])
        self.assertEqual(108.9, updated["stage_metrics"]["grill"]["elapsed_seconds"])

    def test_nested_map_updates_reject_non_objects(self):
        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"context_index": "not-an-object"},
            )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"stage_metrics": []},
            )

    def test_blocker_and_final_result_shapes_fail_closed(self):
        self.init_full()

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo, self.run_id, {"blocker": "something failed"}
            )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo, self.run_id, {"blocker": {}}
            )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo, self.run_id, {"final_result": {}}
            )

        blocked = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "state": "BLOCKED",
                "blocker": {"code": "PERFORMANCE_BUDGET_EXCEEDED"},
            },
        )
        self.assertEqual("BLOCKED", blocked["state"])

        waiting = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "state": "WAITING_FOR_USER",
                "blocker": {"required_user_action": "Authorize the bounded waiver"},
            },
        )
        self.assertEqual("WAITING_FOR_USER", waiting["state"])

    def test_blocked_or_waiting_state_requires_blocker_details(self):
        self.init_full()
        for state in ("BLOCKED", "WAITING_FOR_USER"):
            with self.assertRaises(smoke_state.SmokeStateError):
                smoke_state.set_values(
                    self.repo,
                    self.run_id,
                    {"state": state, "blocker": None},
                )

    def test_latest_verification_and_review_shapes_are_bounded(self):
        self.init_full()
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "latest_verification": {
                    "result": "DONE",
                    "delivery_gate": "CLEAR",
                    "freshness": "MATCH",
                },
                "latest_review": "APPROVE",
            },
        )
        self.assertEqual("DONE", updated["latest_verification"]["result"])

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo, self.run_id, {"latest_verification": "DONE"}
            )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo, self.run_id, {"latest_review": 1}
            )

    def test_nonterminal_states_reject_final_result(self):
        self.init_full()
        for state, blocker in (
            ("IN_PROGRESS", None),
            ("BLOCKED", {"code": "TEST_BLOCK"}),
            ("WAITING_FOR_USER", {"required_user_action": "Confirm"}),
        ):
            with self.assertRaises(smoke_state.SmokeStateError):
                smoke_state.set_values(
                    self.repo,
                    self.run_id,
                    {
                        "state": state,
                        "blocker": blocker,
                        "final_result": "FULL_SMOKE_PASS",
                    },
                )

    def test_pass_requires_all_required_scenarios_and_matching_profile_result(self):
        self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "context_index": self.bootstrap_context(),
                    "completed_scenarios": ["static-release-gate"],
                    "current_stage": "COMPLETE",
                    "state": "PASS",
                    "final_result": "FULL_SMOKE_PASS",
                },
            )

        required, _optional, _all = smoke_state._profile_scenarios("FULL")
        completed = sorted(required)
        self.mark_all_segments_closed()
        with mock.patch.object(
            smoke_segments,
            "validate_terminal_integrity",
            return_value={"result": "PASS"},
        ):
            passed = smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "context_index": self.bootstrap_context(),
                    "completed_scenarios": completed,
                    "pending_scenarios": [],
                    "current_stage": "COMPLETE",
                    "state": "PASS",
                    "final_result": "FULL_SMOKE_PASS",
                },
            )
        self.assertEqual("PASS", passed["state"])
        self.assertEqual("FULL_SMOKE_PASS", passed["final_result"])

    def test_terminal_result_token_must_match_state_and_profile(self):
        self.init_full()
        required, _optional, _all = smoke_state._profile_scenarios("FULL")
        self.mark_all_segments_closed()
        base = {
            "context_index": self.bootstrap_context(),
            "completed_scenarios": sorted(required),
            "pending_scenarios": [],
            "current_stage": "COMPLETE",
        }

        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    **base,
                    "state": "PASS",
                    "final_result": "FAST_SMOKE_PASS",
                },
            )

        failed = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "state": "FAIL",
                "final_result": "SMOKE_FAIL",
            },
        )
        self.assertEqual("SMOKE_FAIL", failed["final_result"])

    def test_immutable_identity_fields_fail_closed(self):
        self.init_full()
        for field, value in (
            ("schema_version", 2),
            ("run_id", "SMOKE-FULL-other-20260927T000000Z-12345678"),
            ("profile", "FAST"),
            ("fixture", "other"),
            ("source_commit", "other"),
            ("baseline_head", "other"),
        ):
            with self.assertRaises(smoke_state.SmokeStateError):
                smoke_state.set_values(self.repo, self.run_id, {field: value})

    def test_invalid_update_never_partially_persists_other_valid_fields(self):
        before = self.init_full()
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {
                    "current_stage": "architect",
                    "completed_scenarios": ["prd"],
                    "pending_scenarios": ["prd"],
                },
            )
        self.assertEqual(before, smoke_state.load(self.repo, self.run_id))


if __name__ == "__main__":
    unittest.main()
