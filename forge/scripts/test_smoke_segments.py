"""Focused H08 tests for segmented FULL qualification infrastructure."""

import datetime as dt
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget
import smoke_segments
import smoke_state


class SmokeSegmentsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-h08-20261002T000000Z-12345678"
        self.started = dt.datetime(2026, 10, 2, 0, 0, tzinfo=dt.timezone.utc)

    def _config_copy(self):
        source = Path(__file__).resolve().parents[1]
        target = self.root / "config"
        shutil.copytree(source / "smoke", target / "smoke")
        return target

    def _init_full(self, *, config=None, started=None):
        started = started or self.started
        smoke_state.init(
            self.repo,
            self.run_id,
            "FULL",
            "full-minimal-api",
            "source123",
            "base123",
        )
        smoke_budget.start(self.repo, self.run_id, started)
        smoke_segments.pin_qualification(
            self.repo,
            self.run_id,
            config,
            started.isoformat(),
            source_fingerprint="a" * 64,
        )
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "context_index": {
                    "budget_started_at_utc": started.isoformat(),
                    "contract_parity": {"contract_equal": True},
                }
            },
        )

    def _budget_file(self):
        return self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"

    def _complete_s1(self):
        pinned = smoke_segments.assert_config_intact(self.repo, self.run_id)
        s1 = pinned["segments"][0]
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "completed_scenarios": list(s1["scenarios"]),
                "pending_scenarios": [],
            },
        )
        evidence = self.repo / "docs/verification/S1-EVIDENCE.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text('{"result":"PASS"}\n', encoding="utf-8")
        evidence_rel = "docs/verification/S1-EVIDENCE.json"
        spec = smoke_segments._load_full_invocation_spec()
        for scenario_id in s1["scenarios"]:
            scenario = smoke_segments._scenario_definition(spec, scenario_id)
            for subprobe in scenario["subprobes"]:
                if subprobe["required"]:
                    smoke_segments.register_scenario_evidence(
                        self.repo,
                        self.run_id,
                        scenario_id,
                        subprobe["id"],
                        ["scored PASS for focused H08 test"],
                        [evidence_rel],
                        self.started + dt.timedelta(minutes=1),
                    )
        return s1, evidence_rel

    def test_snapshot_pins_six_segments_and_derived_allowance(self):
        self._init_full()
        state = smoke_state.load(self.repo, self.run_id)
        snapshot = state["context_index"]["qualification_config"]
        self.assertEqual(["S1", "S2", "S3", "S4", "S5", "S6"],
                         [item["id"] for item in snapshot["segments"]])
        self.assertEqual([80, 48, 38, 53, 36, 40],
                         [item["limit_minutes"] for item in snapshot["segments"]])
        self.assertEqual(295, sum(item["limit_minutes"] for item in snapshot["segments"]))
        runtime = state["context_index"]["segment_runtime"]
        self.assertEqual("S1", runtime["active_segment"])
        self.assertEqual("ACTIVE", runtime["active_status"])

    def test_live_profile_drift_is_rejected_without_repinning(self):
        config = self._config_copy()
        self._init_full(config=config)
        profile_path = config / "smoke/profiles.json"
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
        payload["profiles"]["FULL"]["segments"][0]["limit_minutes"] = 81
        profile_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(smoke_segments.SegmentError):
            smoke_segments.assert_config_intact(self.repo, self.run_id, config)

        state = smoke_state.load(self.repo, self.run_id)
        self.assertEqual(
            80,
            state["context_index"]["qualification_config"]["segments"][0]["limit_minutes"],
        )

    def test_invocation_spec_wrong_segment_or_owner_arithmetic_fails_closed(self):
        config = self._config_copy()
        spec_path = config / "smoke/FULL-INVOCATION-SPEC.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        first = next(item for item in spec["scenarios"] if item["id"] == "verification-mutation")
        first["calls"][0]["owner"] = "GPT-5.6 Sol"
        spec_path.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(smoke_segments.SegmentError):
            smoke_segments.build_snapshot(config, "FULL")

    def test_segment_timeout_is_terminal_for_qualification(self):
        old = self.started - dt.timedelta(minutes=81)
        self._init_full(started=old)

        result = smoke_segments.mark_budget_exceeded(self.repo, self.run_id, self.started)

        self.assertEqual("PERFORMANCE_BUDGET_EXCEEDED", result["result"])
        state = smoke_state.load(self.repo, self.run_id)
        self.assertFalse(state["context_index"]["qualification_eligible"])
        self.assertEqual(
            "BUDGET_EXCEEDED",
            state["context_index"]["segment_runtime"]["active_status"],
        )
        self.assertEqual("BLOCKED", state["state"])
        with self.assertRaises(smoke_segments.SegmentError):
            smoke_segments.open_next_segment(self.repo, self.run_id, self.root)

    def test_close_then_open_next_is_checkpoint_bound_and_idempotent(self):
        self._init_full()
        _s1, evidence = self._complete_s1()
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {
            "checkpoint": "CP-REVIEWED",
            "result": "MATCH",
            "expected_fingerprint": "f" * 64,
            "current_fingerprint": "f" * 64,
        }
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            closed = smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )
            replay = smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=21),
            )
            opened = smoke_segments.open_next_segment(
                self.repo,
                self.run_id,
                self.root,
                self.started + dt.timedelta(days=2),
            )
            opened_again = smoke_segments.open_next_segment(
                self.repo,
                self.run_id,
                self.root,
                self.started + dt.timedelta(days=3),
            )

        self.assertEqual("S1", closed["segment_id"])
        self.assertEqual(closed, replay)
        self.assertEqual("S2", opened["segment_id"])
        self.assertEqual(opened["started_at_utc"], opened_again["started_at_utc"])
        state = smoke_state.load(self.repo, self.run_id)
        self.assertIsNone(state["context_index"]["segment_runtime"]["gap"])

    def test_close_rejects_unscored_required_subprobe(self):
        self._init_full()
        pinned = smoke_segments.assert_config_intact(self.repo, self.run_id)
        s1 = pinned["segments"][0]
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "completed_scenarios": list(s1["scenarios"]),
                "pending_scenarios": [],
            },
        )
        evidence = self.repo / "docs/verification/S1-EVIDENCE.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text('{"result":"PASS"}\n', encoding="utf-8")
        spec = smoke_segments._load_full_invocation_spec()
        skipped = False
        for scenario_id in s1["scenarios"]:
            scenario = smoke_segments._scenario_definition(spec, scenario_id)
            for subprobe in scenario["subprobes"]:
                if subprobe["required"]:
                    if not skipped:
                        skipped = True
                        continue
                    smoke_segments.register_scenario_evidence(
                        self.repo,
                        self.run_id,
                        scenario_id,
                        subprobe["id"],
                        ["scored PASS except one intentionally missing subprobe"],
                        ["docs/verification/S1-EVIDENCE.json"],
                        self.started + dt.timedelta(minutes=1),
                    )
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {"checkpoint": "CP-REVIEWED", "result": "MATCH"}
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            with self.assertRaises(smoke_segments.SegmentError):
                smoke_segments.close_segment(
                    self.repo,
                    self.run_id,
                    self.root,
                    None,
                    self.started + dt.timedelta(minutes=20),
                )

    def test_stage_start_is_blocked_between_segments(self):
        self._init_full()
        _s1, evidence = self._complete_s1()
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {"checkpoint": "CP-REVIEWED", "result": "MATCH"}
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )

        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.stage_start(
                self.repo,
                self.run_id,
                "verify",
                "deepseek/deepseek-flash",
                self.started + dt.timedelta(minutes=21),
                source_fingerprint="a" * 64,
                rooted_guard=lambda repo, run_id: None,
            )

    def test_multi_day_gap_is_persisted_and_reported(self):
        self._init_full()
        _s1, _evidence = self._complete_s1()
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {
            "checkpoint": "CP-REVIEWED",
            "result": "MATCH",
            "expected_fingerprint": "f" * 64,
            "current_fingerprint": "f" * 64,
        }
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )
            smoke_segments.record_gap_activity(
                self.repo,
                self.run_id,
                "READ_ONLY_STATUS",
                "Operator checked status only.",
                self.started + dt.timedelta(days=1),
            )
            smoke_segments.open_next_segment(
                self.repo,
                self.run_id,
                self.root,
                self.started + dt.timedelta(days=2),
            )

        report = smoke_segments.qualification_report(
            self.repo,
            self.run_id,
            self.started + dt.timedelta(days=2, minutes=5),
        )
        self.assertEqual(1, len(report["gaps"]))
        self.assertEqual(
            2 * 24 * 60 * 60 - 20 * 60,
            report["inter_segment_gap_seconds"],
        )
        self.assertEqual(
            "READ_ONLY_STATUS",
            report["gaps"][0]["activities"][0]["type"],
        )

    def test_gap_source_drift_disqualifies_qualification(self):
        self._init_full()
        _s1, _evidence = self._complete_s1()
        checkpoint = {
            "checkpoint": "CP-REVIEWED",
            "result": "MATCH",
            "expected_fingerprint": "f" * 64,
            "current_fingerprint": "f" * 64,
        }
        with mock.patch.object(
            smoke_segments.smoke_workspace,
            "source_guard",
            return_value={"source_checkout_path": str(self.root), "fingerprint": "a" * 64},
        ), mock.patch.object(
            smoke_segments.smoke_mechanics,
            "check_checkpoint",
            return_value=checkpoint,
        ):
            smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )

        with mock.patch.object(
            smoke_segments.smoke_workspace,
            "source_guard",
            return_value={"source_checkout_path": str(self.root), "fingerprint": "b" * 64},
        ):
            with self.assertRaises(smoke_segments.SegmentError):
                smoke_segments.open_next_segment(
                    self.repo,
                    self.run_id,
                    self.root,
                    self.started + dt.timedelta(hours=1),
                )

        state = smoke_state.load(self.repo, self.run_id)
        self.assertFalse(state["context_index"]["qualification_eligible"])
        self.assertEqual(
            "SOURCE_DRIFT",
            state["context_index"]["segment_runtime"]["gap"]["disqualification_reason"],
        )

    def test_gap_activity_rejects_substantive_work(self):
        self._init_full()
        _s1, _evidence = self._complete_s1()
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {"checkpoint": "CP-REVIEWED", "result": "MATCH"}
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )

        with self.assertRaises(smoke_segments.SegmentError):
            smoke_segments.record_gap_activity(
                self.repo,
                self.run_id,
                "MODEL_CALL",
                "This must never be accepted.",
            )

    def test_closed_evidence_tamper_is_detected_cumulatively(self):
        self._init_full()
        _s1, evidence = self._complete_s1()
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {"checkpoint": "CP-REVIEWED", "result": "MATCH"}
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )

        (self.repo / evidence).write_text('{"result":"CHANGED"}\n', encoding="utf-8")
        with self.assertRaises(smoke_segments.SegmentError):
            smoke_segments.validate_closed_chain(self.repo, self.run_id)

    def test_closed_ledger_projection_tamper_is_detected(self):
        self._init_full()
        _s1, evidence = self._complete_s1()
        source_guard = {"source_checkout_path": str(self.root), "fingerprint": "a" * 64}
        checkpoint = {"checkpoint": "CP-REVIEWED", "result": "MATCH"}
        with mock.patch.object(smoke_segments.smoke_workspace, "source_guard",
                               return_value=source_guard), \
             mock.patch.object(smoke_segments.smoke_mechanics, "check_checkpoint",
                               return_value=checkpoint):
            smoke_segments.close_segment(
                self.repo,
                self.run_id,
                self.root,
                None,
                self.started + dt.timedelta(minutes=20),
            )

        data = json.loads(self._budget_file().read_text(encoding="utf-8"))
        data["stage_invocations"].append({
            "invocation_id": "verify-999",
            "stage": "verify",
            "model": "deepseek/deepseek-flash",
            "segment_id": "S1",
            "scenario_id": "first-uncommitted-verify",
            "source_fingerprint": "a" * 64,
            "status": "COMPLETED",
            "started_at_utc": self.started.isoformat(),
            "ended_at_utc": (self.started + dt.timedelta(seconds=1)).isoformat(),
            "recovered_at_utc": None,
            "elapsed_seconds": 1.0,
            "termination_reason": None,
        })
        self._budget_file().write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(smoke_segments.SegmentError):
            smoke_segments.validate_closed_chain(self.repo, self.run_id)

    def test_fast_snapshot_preserves_30_minute_budget(self):
        snapshot = smoke_segments.build_snapshot(None, "FAST")
        self.assertEqual(30, snapshot["limit_minutes"])
        self.assertEqual("PROVISIONAL", snapshot["limit_status"])
        self.assertNotIn("segments", snapshot)


if __name__ == "__main__":
    unittest.main()
