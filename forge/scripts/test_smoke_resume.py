"""Focused regressions for H05 arbitrary-stage resume probe mechanics."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import smoke_mechanics
import smoke_resume


class SmokeResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Smoke")
        self.git("config", "user.email", "smoke@example.test")

        self.write("AGENTS.md", "Project instructions: technology pending.\n")
        self.write("README.md", "# Project\nTechnology pending.\n")
        self.write(".kilo/rules/.gitkeep", "")
        self.write(".kilo/skills/.gitkeep", "")
        self.write(
            "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md",
            "implementation-state-evidence-v1\n",
        )
        self.write("docs/verification/smoke/.gitkeep", "")
        self.git("add", "-A")
        self.git("commit", "-qm", "baseline")
        self.baseline = self.git("rev-parse", "HEAD").strip()
        self.git("switch", "-qc", "smoke-run")

        self.write("AGENTS.md", "Project instructions: Python 3.8+ initialized.\n")
        self.write("README.md", "# Project\nPython minimal API.\n")
        self.write(".kilo/rules/python.md", "Use Python 3.8+.\n")
        self.write("docs/prd/PRD-001.md", "# PRD\nStatus: PRD_READY\n")
        self.write(
            "docs/architecture/ARCH-001.md",
            "# Architecture\nStatus: ARCHITECTURE_READY\n",
        )
        self.write("docs/adr/ADR-001.md", "# ADR\nStatus: Accepted\n")
        self.spec = "docs/specs/SPEC-001.md"
        self.write(self.spec, "# Spec\nStatus: SPEC_READY\n")
        self.impl = ["app.py", "test_app.py"]
        self.write("app.py", "def ping():\n    return 'pong'\n")
        self.write("test_app.py", "from app import ping\n")
        self.verification = "docs/verification/VERIFY-SPEC-001-001.md"
        self.write(
            self.verification,
            "\n".join(
                [
                    "# Verification",
                    "Verification Result: DONE",
                    "Delivery Gate: CLEAR",
                    "Freshness: MATCH",
                    "Evidence Contract: implementation-state-evidence-v1",
                    "",
                ]
            ),
        )
        self.write(
            "docs/reviews/REVIEW-SPEC-001-001.md",
            "# Review\nFinal AI Review Decision: APPROVE\n",
        )
        self.write("docs/diagnostics/OLD.md", "# Historical diagnostic\n")

        self.run_id = "SMOKE-FULL-test-20260929T000000Z-12345678"
        smoke_mechanics.checkpoint(self.repo, self.run_id, "opaque-base")
        self.clean_snapshot = smoke_resume._capture_snapshot(self.repo)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True)

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def prepare(self, probe_id):
        return smoke_resume.prepare(
            self.repo,
            self.run_id,
            probe_id,
            "opaque-base",
            self.baseline,
            self.spec,
            self.impl,
            self.verification,
        )

    def score_and_restore(self, probe_id):
        routed = smoke_resume.PROBE_EXPECTED[probe_id]
        score = smoke_resume.score(
            self.repo,
            self.run_id,
            probe_id,
            routed,
            "Persisted repository evidence identifies the earliest continuation.",
        )
        if score["handoff_required"]:
            smoke_resume.record_handoff(
                self.repo,
                self.run_id,
                probe_id,
                True,
                "DeepSeek accepted the persisted Spec/context handoff.",
            )
        restored = smoke_resume.restore(self.repo, self.run_id, probe_id)
        self.assertEqual("MATCH", restored["checkpoint_result"])
        self.assertEqual(
            self.clean_snapshot["snapshot_sha256"],
            smoke_resume._capture_snapshot(self.repo)["snapshot_sha256"],
        )

    def test_r01_architecture_ready_project_init_incomplete(self):
        result = self.prepare("r01")
        self.assertTrue(result["checks"]["project_init_state_correct"])
        self.assertIn("PRD_READY", (self.repo / "docs/prd/PRD-001.md").read_text())
        self.assertTrue((self.repo / "docs/architecture/ARCH-001.md").is_file())
        self.assertEqual(
            "Project instructions: technology pending.\n",
            (self.repo / "AGENTS.md").read_text(),
        )
        self.assertFalse((self.repo / self.spec).exists())
        self.assertFalse((self.repo / "app.py").exists())
        self.assertFalse((self.repo / self.verification).exists())
        self.score_and_restore("r01")

    def test_r02_project_init_ready_without_spec(self):
        result = self.prepare("r02")
        self.assertTrue(result["checks"]["project_init_state_correct"])
        self.assertIn("Python 3.8+ initialized", (self.repo / "AGENTS.md").read_text())
        self.assertFalse((self.repo / self.spec).exists())
        self.assertFalse((self.repo / "app.py").exists())
        self.score_and_restore("r02")

    def test_r03_spec_ready_without_implementation_requires_handoff(self):
        self.prepare("r03")
        self.assertTrue((self.repo / self.spec).is_file())
        self.assertFalse((self.repo / "app.py").exists())
        score = smoke_resume.score(
            self.repo,
            self.run_id,
            "r03",
            "/implement",
            "Approved persisted Spec exists and implementation has not started.",
        )
        self.assertTrue(score["handoff_required"])
        smoke_resume.record_handoff(
            self.repo,
            self.run_id,
            "r03",
            True,
            "Implementation owner accepted the exact persisted Spec.",
        )
        restored = smoke_resume.restore(self.repo, self.run_id, "r03")
        self.assertEqual("PASS", restored["probe_result"])

    def test_r04_implementation_without_verification(self):
        self.prepare("r04")
        self.assertTrue((self.repo / "app.py").is_file())
        self.assertFalse((self.repo / self.verification).exists())
        self.score_and_restore("r04")

    def test_r05_fresh_verification_without_review(self):
        self.prepare("r05")
        self.assertTrue((self.repo / self.verification).is_file())
        self.assertFalse(any((self.repo / "docs/reviews").glob("*.md")))
        self.assertEqual(
            "MATCH",
            smoke_mechanics.check_checkpoint(
                self.repo, self.run_id, "opaque-base"
            )["result"],
        )
        self.score_and_restore("r05")

    def test_r06_stale_verification_is_real_identity_mismatch(self):
        before = (self.repo / "app.py").read_bytes()
        self.prepare("r06")
        self.assertTrue((self.repo / self.verification).is_file())
        self.assertNotEqual(before, (self.repo / "app.py").read_bytes())
        self.assertEqual(
            "MISMATCH",
            smoke_mechanics.check_checkpoint(
                self.repo, self.run_id, "opaque-base"
            )["result"],
        )
        self.score_and_restore("r06")

    def test_r07_blocking_review_is_persisted_normal_evidence(self):
        self.prepare("r07")
        reviews = list((self.repo / "docs/reviews").glob("*.md"))
        self.assertEqual(1, len(reviews))
        content = reviews[0].read_text(encoding="utf-8")
        self.assertIn("CHANGES_REQUIRED", content)
        self.assertIn("/fix → /verify → /review", content)
        self.assertIn("Reviewed implementation-state fingerprint:", content)
        self.assertIn("Canonical-manifest equality result: MATCH", content)
        self.assertEqual(
            "MATCH",
            smoke_mechanics.check_checkpoint(
                self.repo, self.run_id, "opaque-base"
            )["result"],
        )
        self.score_and_restore("r07")

    def test_wrong_route_fails_without_exposing_expected_in_ledger(self):
        self.prepare("r02")
        ledger_path = (
            self.repo
            / "docs/verification/smoke"
            / f"{self.run_id}.resume.json"
        )
        prepared = ledger_path.read_text(encoding="utf-8")
        self.assertNotIn("expected", prepared)
        self.assertNotIn("/spec", prepared)

        result = smoke_resume.score(
            self.repo,
            self.run_id,
            "r02",
            "/verify",
            "Incorrect test route.",
        )
        self.assertEqual("FAIL", result["routing_result"])
        restored = smoke_resume.restore(self.repo, self.run_id, "r02")
        self.assertEqual("FAIL", restored["probe_result"])

    def test_active_probe_must_be_restored_before_next_prepare(self):
        self.prepare("r04")
        with self.assertRaises(smoke_resume.ResumeProbeError):
            self.prepare("r05")
        smoke_resume.restore(self.repo, self.run_id, "r04")

    def test_router_mutation_is_detected_before_scoring(self):
        self.prepare("r04")
        self.write("unexpected.py", "changed during routing\n")
        with self.assertRaises(smoke_resume.ResumeProbeError):
            smoke_resume.score(
                self.repo,
                self.run_id,
                "r04",
                "/verify",
                "Implementation exists without verification.",
            )
        restored = smoke_resume.restore(self.repo, self.run_id, "r04")
        self.assertEqual("MATCH", restored["checkpoint_result"])
        self.assertFalse((self.repo / "unexpected.py").exists())

    def test_handoff_probe_rejects_repository_mutation(self):
        self.prepare("r03")
        smoke_resume.score(
            self.repo,
            self.run_id,
            "r03",
            "/implement",
            "Approved Spec exists.",
        )
        self.write(self.spec, "# Spec\nStatus: SPEC_READY\nchanged\n")
        with self.assertRaises(smoke_resume.ResumeProbeError):
            smoke_resume.record_handoff(
                self.repo,
                self.run_id,
                "r03",
                True,
                "Claimed acceptance after changing the repository.",
            )
        restored = smoke_resume.restore(self.repo, self.run_id, "r03")
        self.assertEqual("MATCH", restored["checkpoint_result"])

    def test_context_paths_must_be_repository_relative_and_present(self):
        with self.assertRaises(smoke_resume.ResumeProbeError):
            smoke_resume.prepare(
                self.repo,
                self.run_id,
                "r03",
                "opaque-base",
                self.baseline,
                "../SPEC.md",
                self.impl,
                self.verification,
            )

    def test_all_seven_pass_only_after_routing_handoff_and_restoration(self):
        for probe_id in sorted(smoke_resume.PROBE_EXPECTED):
            self.prepare(probe_id)
            self.score_and_restore(probe_id)

        result = smoke_resume.status(self.repo, self.run_id)
        self.assertEqual("PASS", result["result"])
        self.assertEqual(7, len(result["completed_probes"]))

        ledger = json.loads(
            (
                self.repo
                / "docs/verification/smoke"
                / f"{self.run_id}.resume.json"
            ).read_text(encoding="utf-8")
        )
        self.assertNotIn("expected_stage", json.dumps(ledger))


if __name__ == "__main__":
    unittest.main()
