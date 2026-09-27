"""Tests for structured smoke orchestration state."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_state


class SmokeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"

    def test_init_and_targeted_update(self):
        created = smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        self.assertEqual("static-release-gate", created["current_stage"])
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "current_stage": "architect",
                "completed_scenarios": ["static-release-gate", "grill", "prd"],
                "context_index": {
                    "prd": "docs/prd/PRD-001.md",
                    "architecture": "docs/architecture/ARCH-001.md",
                },
            },
        )
        self.assertEqual("architect", updated["current_stage"])
        self.assertEqual("docs/prd/PRD-001.md", updated["context_index"]["prd"])
        self.assertEqual(updated, smoke_state.load(self.repo, self.run_id))



    def test_completed_scenarios_are_removed_from_pending(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "completed_scenarios": ["grill", "prd"],
                "pending_scenarios": ["static-release-gate", "prd", "architect"],
            },
        )
        self.assertEqual(["grill", "prd"], updated["completed_scenarios"])
        self.assertEqual(["static-release-gate", "architect"], updated["pending_scenarios"])

    def test_invalid_scenario_lists_fail_closed(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"completed_scenarios": "prd"},
            )



    def test_stage_metrics_persist_timing_and_context_paths(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
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
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(
                self.repo,
                self.run_id,
                {"stage_metrics": {"prd": {"elapsed_seconds": -1}}},
            )


    def test_context_index_updates_merge_without_dropping_bootstrap_context(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "context_index": {
                    "budget_started_at_utc": "2026-09-27T00:00:00+00:00",
                    "contract_parity": {"contract_equal": True},
                }
            },
        )
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {"context_index": {"discovery": "docs/discovery/full-minimal-api-discovery.md"}},
        )
        self.assertEqual(
            "2026-09-27T00:00:00+00:00",
            updated["context_index"]["budget_started_at_utc"],
        )
        self.assertEqual(
            {"contract_equal": True},
            updated["context_index"]["contract_parity"],
        )
        self.assertEqual(
            "docs/discovery/full-minimal-api-discovery.md",
            updated["context_index"]["discovery"],
        )

    def test_stage_metric_updates_merge_without_dropping_prior_stages(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
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
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
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

    def test_immutable_identity_fields_fail_closed(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(self.repo, self.run_id, {"source_commit": "other"})


if __name__ == "__main__":
    unittest.main()
