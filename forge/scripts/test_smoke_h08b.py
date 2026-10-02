"""Focused H08b regressions for early lifecycle and waiver-refusal mechanics."""

import hashlib
import json
import subprocess
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
        smoke_dir = self.repo / "docs/verification/smoke"
        smoke_dir.mkdir(parents=True)
        self.run_id = "SMOKE-FULL-h08b-20261002T000000Z-12345678"
        self.budget = smoke_dir / f"{self.run_id}.budget.json"
        self.budget.write_text(
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

    def _complete_stage(self, scenario_id, stage):
        data = json.loads(self.budget.read_text(encoding="utf-8"))
        sequence = 1 + sum(
            1
            for item in data["stage_invocations"]
            if item.get("stage") == stage
        )
        data["stage_invocations"].append(
            {
                "invocation_id": f"{stage}-{sequence:03d}",
                "stage": stage,
                "model": "test-model",
                "segment_id": "S1" if scenario_id != "direct-fix-loop" else "S2",
                "scenario_id": scenario_id,
                "source_fingerprint": "a" * 64,
                "status": "COMPLETED",
                "started_at_utc": "2026-10-02T00:00:00+00:00",
                "ended_at_utc": "2026-10-02T00:00:01+00:00",
                "recovered_at_utc": None,
                "elapsed_seconds": 1.0,
                "termination_reason": None,
            }
        )
        self.budget.write_text(json.dumps(data) + "\n", encoding="utf-8")

    def _init_git_smoke_run(self):
        subprocess.check_call(["git", "init", "-q"], cwd=self.repo)
        subprocess.check_call(
            ["git", "config", "user.name", "Smoke"], cwd=self.repo
        )
        subprocess.check_call(
            ["git", "config", "user.email", "smoke@example.test"], cwd=self.repo
        )
        subprocess.check_call(["git", "add", "-A"], cwd=self.repo)
        subprocess.check_call(
            ["git", "commit", "-qm", "fixture"], cwd=self.repo
        )
        subprocess.check_call(["git", "switch", "-qc", "smoke-run"], cwd=self.repo)

    def _make_discovery_ready(self):
        smoke_h08b.seed_discovery(self.repo, self.run_id)
        self._complete_stage("grill", "grill")
        blocked = smoke_h08b.score_discovery(
            self.repo, self.run_id, "blocked", "DISCOVERY_BLOCKED"
        )
        self.assertEqual("PASS", blocked["result"])
        smoke_h08b.restore_required_evidence(self.repo)
        discovery = self.repo / smoke_h08b.DISCOVERY_PATH
        discovery.write_text(
            discovery.read_text(encoding="utf-8").replace(
                "| DEC-002 | BLOCKED_ON_EVIDENCE | - | docs/workflow/H08B-REQUIRED-EVIDENCE.md |",
                "| DEC-002 | SETTLED | Return JSON integer value; reject non-integer input with HTTP 400 | docs/workflow/H08B-REQUIRED-EVIDENCE.md |",
            ),
            encoding="utf-8",
        )
        self._complete_stage("grill", "grill")
        resumed = smoke_h08b.score_discovery(
            self.repo, self.run_id, "resumed", "DISCOVERY_READY"
        )
        self.assertEqual("PASS", resumed["result"])
        return resumed

    def _complete_direct_prd_probe(self):
        prepared = smoke_h08b.begin_direct_prd_probe(self.repo, self.run_id)
        self.assertTrue(prepared["discovery_absent"])
        prd = self.repo / smoke_h08b.DIRECT_PRD_PATH
        prd.parent.mkdir(parents=True, exist_ok=True)
        prd.write_text("# Direct PRD\nStatus: PRD_READY\n", encoding="utf-8")
        self._complete_stage("grill", "prd")
        scored = smoke_h08b.score_direct_prd(
            self.repo, self.run_id, "PRD_READY"
        )
        self.assertEqual("PASS", scored["result"])
        restored = smoke_h08b.restore_direct_prd_probe(
            self.repo, self.run_id
        )
        self.assertEqual("MATCH", restored["result"])
        return scored

    def test_seeded_blocked_discovery_preserves_settled_decision(self):
        seeded = smoke_h08b.seed_discovery(self.repo, self.run_id)
        self.assertFalse((self.repo / seeded["required_evidence_path"]).exists())

        self._complete_stage("grill", "grill")
        blocked = smoke_h08b.score_discovery(
            self.repo, self.run_id, "blocked", "DISCOVERY_BLOCKED"
        )

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
        self._complete_stage("grill", "grill")

        result = smoke_h08b.score_discovery(
            self.repo, self.run_id, "blocked", "DISCOVERY_BLOCKED"
        )

        self.assertEqual("FAIL", result["result"])
        self.assertTrue(any("DEC-001" in item for item in result["failures"]))

    def test_resumed_discovery_requires_exact_restored_evidence_and_settlement(self):
        result = self._make_discovery_ready()
        self.assertEqual("PASS", result["result"])

    def test_direct_prd_probe_proves_no_discovery_artifact_and_restores(self):
        self._make_discovery_ready()
        scored = self._complete_direct_prd_probe()
        score_path = self.repo / scored["score_path"]
        self.assertTrue(score_path.is_file())
        self.assertTrue((self.repo / smoke_h08b.DISCOVERY_PATH).is_file())
        self.assertFalse((self.repo / smoke_h08b.DIRECT_PRD_PATH).exists())
        self.assertTrue((self.repo / scored["prd_evidence_path"]).is_file())
        self.assertEqual(
            scored["prd_evidence_sha256"],
            hashlib.sha256(
                (self.repo / scored["prd_evidence_path"]).read_bytes()
            ).hexdigest(),
        )

    def test_main_prd_blocks_until_approved_product_decision_is_revealed(self):
        self._make_discovery_ready()
        self._complete_direct_prd_probe()

        seeded = smoke_h08b.seed_product_decision(self.repo, self.run_id)
        self.assertEqual("WITHHELD", seeded["result"])
        self.assertFalse((self.repo / smoke_h08b.PRODUCT_DECISION_PATH).exists())

        self._complete_stage("prd", "prd")
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
        prd.write_text(
            "# Main PRD\n"
            "Status: PRD_READY\n"
            "Decision ID: PROD-DEC-001\n"
            "For valid integer input n, the endpoint returns JSON value equal to n * 2.\n",
            encoding="utf-8",
        )
        self._complete_stage("prd", "prd")

        resumed = smoke_h08b.score_prd_phase(
            self.repo, self.run_id, "resumed", "PRD_READY"
        )
        self.assertEqual("PASS", resumed["result"])
        self.assertTrue((self.repo / resumed["score_path"]).is_file())

    def test_project_init_success_preserves_bootstrap_pinned_waiver_policy(self):
        policy = {
            "policy_id": "SMOKE-FULL-WAIVER-POLICY-V1",
            "non_waivable_failure_types": ["BEHAVIORAL_TEST"],
            "waivable_failure_types": ["DOCUMENTATION_QUALITY", "LINT_QUALITY"],
            "purpose": "H08b fixed failure-type waiver policy.",
        }
        written = smoke_h08b.write_fixture_policy(
            self.repo, policy, self.run_id
        )
        agents = self.repo / "AGENTS.md"
        agents.write_text(
            "Waiver Policy Source: {}\n"
            "Waiver Policy SHA-256: {}\n"
            "Non-waivable Failure Types: BEHAVIORAL_TEST\n"
            "Waivable Failure Types: DOCUMENTATION_QUALITY, LINT_QUALITY\n".format(
                smoke_h08b.POLICY_PATH,
                written["sha256"],
            ),
            encoding="utf-8",
        )
        canonical = self.repo / smoke_h08b.CANONICAL_CONTRACT_PATH
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text("implementation-state-evidence-v1\n", encoding="utf-8")

        self._complete_stage(
            "project-init-contract-propagation", "project-init"
        )
        scored = smoke_h08b.score_project_init_policy_propagation(
            self.repo, self.run_id, "PROJECT_INIT_READY"
        )

        self.assertEqual("PASS", scored["result"])
        self.assertTrue((self.repo / scored["score_path"]).is_file())

    def test_project_init_negative_scores_helper_and_luna_separately(self):
        policy = {
            "policy_id": "SMOKE-FULL-WAIVER-POLICY-V1",
            "non_waivable_failure_types": ["BEHAVIORAL_TEST"],
            "waivable_failure_types": ["DOCUMENTATION_QUALITY", "LINT_QUALITY"],
            "purpose": "H08b fixed failure-type waiver policy.",
        }
        written = smoke_h08b.write_fixture_policy(
            self.repo, policy, self.run_id
        )
        agents = self.repo / "AGENTS.md"
        agents.write_text(
            "Waiver Policy Source: {}\n"
            "Waiver Policy SHA-256: {}\n"
            "Non-waivable Failure Types: BEHAVIORAL_TEST\n"
            "Waivable Failure Types: DOCUMENTATION_QUALITY, LINT_QUALITY\n".format(
                smoke_h08b.POLICY_PATH,
                written["sha256"],
            ),
            encoding="utf-8",
        )
        canonical = self.repo / smoke_h08b.CANONICAL_CONTRACT_PATH
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text("implementation-state-evidence-v1\n", encoding="utf-8")
        self._complete_stage(
            "project-init-contract-propagation", "project-init"
        )
        positive = smoke_h08b.score_project_init_policy_propagation(
            self.repo, self.run_id, "PROJECT_INIT_READY"
        )
        self.assertEqual("PASS", positive["result"])

        self._init_git_smoke_run()
        prepared = smoke_h08b.begin_project_init_negative(
            self.repo, self.run_id
        )
        self.assertTrue(prepared["canonical_contract_absent"])
        self.assertFalse(canonical.exists())

        helper = smoke_h08b.score_project_init_helper_rejection(
            self.repo, self.run_id
        )
        self.assertEqual("PASS", helper["result"])
        self.assertTrue((self.repo / helper["score_path"]).is_file())

        self._complete_stage(
            "project-init-contract-propagation", "project-init"
        )
        luna = smoke_h08b.score_project_init_luna(
            self.repo,
            self.run_id,
            "PROJECT_INIT_BLOCKED",
            "REPOSITORY",
            "Canonical Contract-v1 input is unavailable.",
            "Restore the canonical contract input and rerun project initialization.",
            "/project-init",
        )
        self.assertEqual("PASS", luna["result"])
        self.assertTrue((self.repo / luna["score_path"]).is_file())

        restored = smoke_h08b.restore_project_init_negative(
            self.repo, self.run_id
        )
        self.assertEqual("MATCH", restored["result"])
        self.assertTrue(canonical.is_file())

    def test_project_init_negative_rejects_wrong_blocker_cause(self):
        policy = {
            "policy_id": "SMOKE-FULL-WAIVER-POLICY-V1",
            "non_waivable_failure_types": ["BEHAVIORAL_TEST"],
            "waivable_failure_types": ["DOCUMENTATION_QUALITY", "LINT_QUALITY"],
            "purpose": "H08b fixed failure-type waiver policy.",
        }
        written = smoke_h08b.write_fixture_policy(
            self.repo, policy, self.run_id
        )
        agents = self.repo / "AGENTS.md"
        agents.write_text(
            "Waiver Policy Source: {}\n"
            "Waiver Policy SHA-256: {}\n"
            "Non-waivable Failure Types: BEHAVIORAL_TEST\n"
            "Waivable Failure Types: DOCUMENTATION_QUALITY, LINT_QUALITY\n".format(
                smoke_h08b.POLICY_PATH,
                written["sha256"],
            ),
            encoding="utf-8",
        )
        canonical = self.repo / smoke_h08b.CANONICAL_CONTRACT_PATH
        canonical.parent.mkdir(parents=True, exist_ok=True)
        canonical.write_text("implementation-state-evidence-v1\n", encoding="utf-8")
        self._complete_stage(
            "project-init-contract-propagation", "project-init"
        )
        smoke_h08b.score_project_init_policy_propagation(
            self.repo, self.run_id, "PROJECT_INIT_READY"
        )
        self._init_git_smoke_run()
        smoke_h08b.begin_project_init_negative(self.repo, self.run_id)
        smoke_h08b.score_project_init_helper_rejection(self.repo, self.run_id)
        self._complete_stage(
            "project-init-contract-propagation", "project-init"
        )

        result = smoke_h08b.score_project_init_luna(
            self.repo,
            self.run_id,
            "PROJECT_INIT_BLOCKED",
            "ARCHITECTURE",
            "A technology decision is missing.",
            "Choose a framework.",
            "/architect",
        )

        self.assertEqual("FAIL", result["result"])
        self.assertTrue(result["failures"])

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
        self._complete_stage("direct-fix-loop", "waive")

        result = smoke_h08b.validate_refusal(
            self.repo,
            refusal.relative_to(self.repo).as_posix(),
            self.run_id,
            "WAIVER_BLOCKED",
        )

        self.assertEqual("PASS", result["result"])
        self.assertEqual("POLICY_INELIGIBLE", result["reason_code"])

        data = json.loads(self.budget.read_text(encoding="utf-8"))
        data["human_wait_intervals"].append(
            {
                "gate_type": "WAIVER_AUTHORIZATION",
                "identity": {
                    "verification_report": "docs/verification/VERIFY-SPEC-001-001.md"
                },
            }
        )
        self.budget.write_text(json.dumps(data) + "\n", encoding="utf-8")
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo,
                refusal.relative_to(self.repo).as_posix(),
                self.run_id,
                "WAIVER_BLOCKED",
            )

    def test_discovery_score_requires_completed_grill_invocation(self):
        smoke_h08b.seed_discovery(self.repo, self.run_id)
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.score_discovery(
                self.repo, self.run_id, "blocked", "DISCOVERY_BLOCKED"
            )

    def test_run_scoped_refusal_rejects_wrong_terminal_status(self):
        refusal = self._write_refusal("POLICY_INELIGIBLE")
        self._complete_stage("direct-fix-loop", "waive")
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo,
                refusal.relative_to(self.repo).as_posix(),
                self.run_id,
                "WAIVER_READY",
            )

    def test_run_scoped_refusal_rejects_authorization_missing_reason(self):
        refusal = self._write_refusal("AUTHORIZATION_MISSING")
        self._complete_stage("direct-fix-loop", "waive")
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo,
                refusal.relative_to(self.repo).as_posix(),
                self.run_id,
                "WAIVER_BLOCKED",
            )

    def test_resumed_prd_requires_prior_blocked_pass_and_revealed_decision(self):
        self._make_discovery_ready()
        self._complete_direct_prd_probe()
        smoke_h08b.seed_product_decision(self.repo, self.run_id)
        smoke_h08b.reveal_product_decision(self.repo, self.run_id)
        prd = self.repo / smoke_h08b.MAIN_PRD_PATH
        prd.parent.mkdir(parents=True, exist_ok=True)
        prd.write_text(
            "# Main PRD\nStatus: PRD_READY\n",
            encoding="utf-8",
        )
        self._complete_stage("prd", "prd")
        self._complete_stage("prd", "prd")
        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.score_prd_phase(
                self.repo, self.run_id, "resumed", "PRD_READY"
            )

    def test_authorization_missing_refusal_is_distinct(self):
        refusal = self._write_refusal("AUTHORIZATION_MISSING")

        result = smoke_h08b.validate_refusal(
            self.repo, refusal.relative_to(self.repo).as_posix()
        )

        self.assertEqual("PASS", result["result"])
        self.assertEqual("AUTHORIZATION_MISSING", result["reason_code"])

    def test_failure_type_unavailable_is_valid_generic_refusal_reason(self):
        refusal = self._write_refusal("AUTHORIZATION_MISSING")
        record = json.loads(refusal.read_text(encoding="utf-8"))
        record["reason_code"] = "FAILURE_TYPE_UNAVAILABLE"
        record["requested_failure_types"] = []
        record["authorization_requested"] = False
        record["classification"] = None
        refusal.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

        result = smoke_h08b.validate_refusal(
            self.repo, refusal.relative_to(self.repo).as_posix()
        )

        self.assertEqual("PASS", result["result"])
        self.assertEqual("FAILURE_TYPE_UNAVAILABLE", result["reason_code"])

    def test_policy_mutation_after_bootstrap_fails_closed(self):
        refusal = self._write_refusal("POLICY_INELIGIBLE")
        policy = self.repo / smoke_h08b.POLICY_PATH
        payload = json.loads(policy.read_text(encoding="utf-8"))
        payload["non_waivable_failure_types"] = ["DOCUMENTATION_QUALITY"]
        policy.write_text(json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8")
        record = json.loads(refusal.read_text(encoding="utf-8"))
        record["policy_sha256"] = hashlib.sha256(policy.read_bytes()).hexdigest()
        refusal.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        self._complete_stage("direct-fix-loop", "waive")

        with self.assertRaises(smoke_h08b.H08bError):
            smoke_h08b.validate_refusal(
                self.repo,
                refusal.relative_to(self.repo).as_posix(),
                self.run_id,
                "WAIVER_BLOCKED",
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
                    "waivable_failure_types": ["DOCUMENTATION_QUALITY", "LINT_QUALITY"],
                    "purpose": "H08b fixed failure-type waiver policy.",
                },
            )


if __name__ == "__main__":
    unittest.main()
