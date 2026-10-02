"""Focused H08b regressions for early lifecycle and waiver-refusal mechanics."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_h08b


class SmokeH08bTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-h08b-20261002T000000Z-12345678"

    def test_seeded_blocked_discovery_preserves_settled_decision(self):
        seeded = smoke_h08b.seed_discovery(self.repo, self.run_id)
        self.assertFalse((self.repo / seeded["required_evidence_path"]).exists())

        blocked = smoke_h08b.score_discovery(self.repo, self.run_id, "blocked")

        self.assertEqual("PASS", blocked["result"])
        self.assertEqual(["DEC-001"], blocked["settled_decision_ids"])
        self.assertTrue((self.repo / blocked["score_path"]).is_file())

    def test_discovery_tamper_reopens_or_changes_settled_decision_fails(self):
        smoke_h08b.seed_discovery(self.repo, self.run_id)
        discovery = self.repo / smoke_h08b.DISCOVERY_PATH
        text = discovery.read_text(encoding="utf-8").replace(
            "| DEC-001 | SETTLED | Minimal Python 3.8+ HTTP API using only local/in-memory state | - |",
            "| DEC-001 | OPEN | Changed value | - |",
        )
        discovery.write_text(text, encoding="utf-8")

        result = smoke_h08b.score_discovery(self.repo, self.run_id, "blocked")

        self.assertEqual("FAIL", result["result"])
        self.assertTrue(any("DEC-001" in item for item in result["failures"]))

    def test_resumed_discovery_requires_exact_restored_evidence_and_settlement(self):
        smoke_h08b.seed_discovery(self.repo, self.run_id)
        smoke_h08b.restore_required_evidence(self.repo)
        discovery = self.repo / smoke_h08b.DISCOVERY_PATH
        text = discovery.read_text(encoding="utf-8").replace(
            "| DEC-002 | BLOCKED_ON_EVIDENCE | - | docs/workflow/H08B-REQUIRED-EVIDENCE.md |",
            "| DEC-002 | SETTLED | Return JSON integer value; reject non-integer input with HTTP 400 | docs/workflow/H08B-REQUIRED-EVIDENCE.md |",
        )
        discovery.write_text(text, encoding="utf-8")

        result = smoke_h08b.score_discovery(self.repo, self.run_id, "resumed")

        self.assertEqual("PASS", result["result"])

    def test_direct_prd_probe_proves_no_discovery_artifact_and_restores(self):
        smoke_h08b.seed_discovery(self.repo, self.run_id)
        prepared = smoke_h08b.begin_direct_prd_probe(self.repo, self.run_id)
        self.assertTrue(prepared["discovery_absent"])
        self.assertFalse((self.repo / smoke_h08b.DISCOVERY_PATH).exists())

        prd = self.repo / smoke_h08b.DIRECT_PRD_PATH
        prd.parent.mkdir(parents=True, exist_ok=True)
        prd.write_text("# Direct PRD\nStatus: PRD_READY\n", encoding="utf-8")

        scored = smoke_h08b.score_direct_prd(
            self.repo, self.run_id, "PRD_READY"
        )
        self.assertEqual("PASS", scored["result"])
        score_path = self.repo / scored["score_path"]
        self.assertTrue(score_path.is_file())
        restored = smoke_h08b.restore_direct_prd_probe(
            self.repo, self.run_id
        )
        self.assertEqual("MATCH", restored["result"])
        self.assertTrue((self.repo / smoke_h08b.DISCOVERY_PATH).is_file())
        self.assertFalse(prd.exists())
        self.assertTrue(score_path.is_file())

    def test_main_prd_blocks_until_approved_product_decision_is_revealed(self):
        seeded = smoke_h08b.seed_product_decision(self.repo, self.run_id)
        self.assertEqual("WITHHELD", seeded["result"])
        self.assertFalse((self.repo / smoke_h08b.PRODUCT_DECISION_PATH).exists())

        blocked = smoke_h08b.score_prd_phase(
            self.repo, self.run_id, "blocked", "PRD_BLOCKED"
        )
        self.assertEqual("PASS", blocked["result"])
        self.assertTrue((self.repo / blocked["score_path"]).is_file())

        revealed = smoke_h08b.reveal_product_decision(
            self.repo, self.run_id
        )
        self.assertEqual("REVEALED", revealed["result"])
        prd = self.repo / smoke_h08b.MAIN_PRD_PATH
        prd.parent.mkdir(parents=True, exist_ok=True)
        prd.write_text("# Main PRD\nStatus: PRD_READY\n", encoding="utf-8")

        resumed = smoke_h08b.score_prd_phase(
            self.repo, self.run_id, "resumed", "PRD_READY"
        )
        self.assertEqual("PASS", resumed["result"])
        self.assertTrue((self.repo / resumed["score_path"]).is_file())

    def test_project_init_negative_scores_helper_and_luna_separately(self):
        helper = smoke_h08b.score_project_init_helper_rejection(
            self.repo, self.run_id
        )
        self.assertEqual("PASS", helper["result"])
        self.assertTrue((self.repo / helper["score_path"]).is_file())

        luna = smoke_h08b.score_project_init_luna(
            self.repo, self.run_id, "PROJECT_INIT_BLOCKED"
        )
        self.assertEqual("PASS", luna["result"])
        self.assertTrue((self.repo / luna["score_path"]).is_file())

    def test_prd_scoring_requires_harness_preparation(self):
        prd = self.repo / smoke_h08b.DIRECT_PRD_PATH
        prd.parent.mkdir(parents=True, exist_ok=True)
        prd.write_text("# Direct PRD\nStatus: PRD_READY\n", encoding="utf-8")
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.score_direct_prd(
                self.repo, self.run_id, "PRD_READY"
            )

    def _write_refusal(self, reason):
        report = self.repo / "docs/verification/VERIFY-SPEC-001-001.md"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            "Verification Result: NOT_DONE\n"
            "Failed Check: behavioral-test\n"
            "Failure Type: BEHAVIORAL_TEST\n",
            encoding="utf-8",
        )

        policy_data = {
            "policy_id": "SMOKE-FULL-WAIVER-POLICY-V1",
            "non_waivable_failure_types": ["BEHAVIORAL_TEST"],
            "waivable_failure_types": ["DOCUMENTATION_QUALITY", "LINT_QUALITY"],
            "purpose": "H08b fixed failure-type waiver policy.",
        }
        smoke_h08b.write_fixture_policy(self.repo, policy_data, self.run_id)
        policy = self.repo / smoke_h08b.POLICY_PATH

        refusal = self.repo / "docs/verification/waiver-refusals/WAIVER-REFUSAL-SPEC-001-001.json"
        refusal.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "schema_version": 1,
            "status": "WAIVER_BLOCKED",
            "reason_code": reason,
            "requested_failure_ids": ["behavioral-test"],
            "requested_failure_types": ["BEHAVIORAL_TEST"],
            "verification_report": "docs/verification/VERIFY-SPEC-001-001.md",
            "verification_report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
            "implementation_state_fingerprint": "GIT_BLOB_OID:" + ("a" * 40),
            "classification": "NON_CRITICAL_QUALITY_GATE",
            "policy_reference": smoke_h08b.POLICY_PATH if reason == "POLICY_INELIGIBLE" else None,
            "policy_sha256": hashlib.sha256(policy.read_bytes()).hexdigest() if reason == "POLICY_INELIGIBLE" else None,
            "authorization_requested": reason == "AUTHORIZATION_MISSING",
            "authorization_receipt_present": False,
            "decision_timestamp": "2026-10-02T00:00:00+00:00",
        }
        refusal.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return refusal

    def test_policy_ineligible_refusal_binds_report_policy_and_has_no_auth_or_wait(self):
        refusal = self._write_refusal("POLICY_INELIGIBLE")
        budget = self.repo / "docs/verification/smoke" / f"{self.run_id}.budget.json"
        budget.write_text(
            json.dumps(
                {
                    "started_at_utc": "2026-10-02T00:00:00+00:00",
                    "stage_invocations": [],
                    "human_wait_intervals": [],
                    "continuation_blocker": None,
                }
            )
            + "\n",
            encoding="utf-8",
        )

        result = smoke_h08b.validate_refusal(
            self.repo, refusal.relative_to(self.repo).as_posix(), self.run_id
        )

        self.assertEqual("PASS", result["result"])
        self.assertEqual("POLICY_INELIGIBLE", result["reason_code"])

        data = json.loads(budget.read_text(encoding="utf-8"))
        data["human_wait_intervals"].append(
            {
                "gate_type": "WAIVER_AUTHORIZATION",
                "identity": {
                    "verification_report": "docs/verification/VERIFY-SPEC-001-001.md"
                },
            }
        )
        budget.write_text(json.dumps(data) + "\n", encoding="utf-8")
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo, refusal.relative_to(self.repo).as_posix(), self.run_id
            )

    def test_authorization_missing_refusal_is_distinct(self):
        refusal = self._write_refusal("AUTHORIZATION_MISSING")

        result = smoke_h08b.validate_refusal(
            self.repo, refusal.relative_to(self.repo).as_posix()
        )

        self.assertEqual("PASS", result["result"])
        self.assertEqual("AUTHORIZATION_MISSING", result["reason_code"])

    def test_policy_mutation_after_bootstrap_fails_closed(self):
        refusal = self._write_refusal("POLICY_INELIGIBLE")
        policy = self.repo / smoke_h08b.POLICY_PATH
        payload = json.loads(policy.read_text(encoding="utf-8"))
        payload["non_waivable_failure_types"] = ["DOCUMENTATION_QUALITY"]
        policy.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        record = json.loads(refusal.read_text(encoding="utf-8"))
        record["policy_sha256"] = hashlib.sha256(policy.read_bytes()).hexdigest()
        refusal.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo, refusal.relative_to(self.repo).as_posix(), self.run_id
            )

    def test_refusal_digest_tamper_fails_closed(self):
        refusal = self._write_refusal("POLICY_INELIGIBLE")
        report = self.repo / "docs/verification/VERIFY-SPEC-001-001.md"
        report.write_text("changed\n", encoding="utf-8")

        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo, refusal.relative_to(self.repo).as_posix()
            )

    def test_fixture_policy_write_is_immutable(self):
        result = smoke_h08b.write_fixture_policy(
            self.repo,
            {
                "policy_id": "SMOKE-FULL-WAIVER-POLICY-V1",
                "non_waivable_failure_types": ["BEHAVIORAL_TEST"],
                "waivable_failure_types": ["DOCUMENTATION_QUALITY", "LINT_QUALITY"],
                "purpose": "H08b fixed failure-type waiver policy.",
            },
        )
        self.assertEqual(smoke_h08b.POLICY_PATH, result["path"])
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.write_fixture_policy(
                self.repo,
                {
                    "policy_id": "SMOKE-FULL-WAIVER-POLICY-V1",
                    "non_waivable_failure_types": ["BEHAVIORAL_TEST"],
                },
            )


if __name__ == "__main__":
    unittest.main()
