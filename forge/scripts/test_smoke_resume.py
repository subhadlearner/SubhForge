"""Focused regressions for H05 arbitrary-stage resume probe mechanics."""

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import smoke_mechanics
import smoke_resume


class SmokeResumeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build the Git/checkpoint fixture once. Recreating it for every H05
        # test launches many git.exe processes on Windows and does not add
        # isolation beyond copying the tiny repository per test.
        cls._seed_temp = tempfile.TemporaryDirectory()
        seed = Path(cls._seed_temp.name) / "seed"
        seed.mkdir()
        cls._seed_repo = seed

        def git(*args):
            return subprocess.check_output(["git", *args], cwd=seed, text=True)

        def write(name, content):
            path = seed / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        git("init", "-q")
        git("config", "user.name", "Smoke")
        git("config", "user.email", "smoke@example.test")

        write("AGENTS.md", "Project instructions: technology pending.\n")
        write("README.md", "# Project\nTechnology pending.\n")
        write(".kilo/rules/.gitkeep", "")
        write(".kilo/skills/.gitkeep", "")
        write(
            "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md",
            "implementation-state-evidence-v1\n",
        )
        write("docs/verification/smoke/.gitkeep", "")
        git("add", "-A")
        git("commit", "-qm", "baseline")
        cls._baseline = git("rev-parse", "HEAD").strip()
        git("switch", "-qc", "smoke-run")

        write("AGENTS.md", "Project instructions: Python 3.8+ initialized.\n")
        write("README.md", "# Project\nPython minimal API.\n")
        write(".kilo/rules/python.md", "Use Python 3.8+.\n")
        write("docs/prd/PRD-001.md", "# PRD\nStatus: PRD_READY\n")
        write(
            "docs/architecture/ARCH-001.md",
            "# Architecture\nStatus: ARCHITECTURE_READY\n",
        )
        write("docs/adr/ADR-001.md", "# ADR\nStatus: Accepted\n")
        write("docs/specs/SPEC-001.md", "# Spec\nStatus: SPEC_READY\n")
        write("app.py", "def ping():\n    return 'pong'\n")
        write("test_app.py", "from app import ping\n")
        write(
            "docs/verification/VERIFY-SPEC-001-001.md",
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
        write(
            "docs/reviews/REVIEW-SPEC-001-001.md",
            "# Review\nFinal AI Review Decision: APPROVE\n",
        )
        write("docs/diagnostics/OLD.md", "# Historical diagnostic\n")

        cls._run_id = "SMOKE-FULL-test-20260929T000000Z-12345678"
        smoke_mechanics.checkpoint(seed, cls._run_id, "opaque-base")
        cls._clean_snapshot = smoke_resume.capture_probe_snapshot(seed)

    @classmethod
    def tearDownClass(cls):
        cls._seed_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        shutil.copytree(self._seed_repo, self.repo, symlinks=True)

        self.baseline = self._baseline
        self.spec = "docs/specs/SPEC-001.md"
        self.impl = ["app.py", "test_app.py"]
        self.verification = "docs/verification/VERIFY-SPEC-001-001.md"
        self.run_id = self._run_id
        self.clean_snapshot = copy.deepcopy(self._clean_snapshot)

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
        # restore() already proves byte-identical snapshot restoration plus
        # Contract-v1 checkpoint MATCH. Avoid recapturing the same repository.

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

    def test_h05_resume_preserves_historical_waiver_refusal_as_non_active_evidence(self):
        refusal = (
            self.repo
            / "docs/verification/waiver-refusals"
            / "WAIVER-REFUSAL-SPEC-001-001.json"
        )
        refusal.parent.mkdir(parents=True, exist_ok=True)
        refusal.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "WAIVER_BLOCKED",
                    "reason_code": "POLICY_INELIGIBLE",
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        self.prepare("r05")
        self.assertTrue(refusal.is_file())
        self.score_and_restore("r05")

        self.assertTrue(refusal.is_file())
        self.assertIn(
            '"status": "WAIVER_BLOCKED"',
            refusal.read_text(encoding="utf-8"),
        )
        self.assertFalse(
            any(
                path.name.startswith("WAIVER-")
                for path in (self.repo / "docs/verification/waivers").glob("*")
            )
            if (self.repo / "docs/verification/waivers").exists()
            else False
        )

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

    def test_restored_not_scored_probe_can_retry_same_id(self):
        self.prepare("r04")
        first = smoke_resume.restore(self.repo, self.run_id, "r04")
        self.assertEqual("NOT_SCORED", first["probe_result"])

        self.prepare("r04")
        ledger = json.loads(
            (
                self.repo
                / "docs/verification/smoke"
                / f"{self.run_id}.resume.json"
            ).read_text(encoding="utf-8")
        )
        matching = [item for item in ledger["probes"] if item["probe_id"] == "r04"]
        self.assertEqual(1, len(matching))
        self.assertEqual(2, matching[0]["attempt_count"])
        self.assertEqual("PREPARED", matching[0]["state"])
        smoke_resume.restore(self.repo, self.run_id, "r04")

    def test_scored_resume_probe_cannot_retry_after_pass_or_fail(self):
        self.prepare("r01")
        smoke_resume.score(
            self.repo,
            self.run_id,
            "r01",
            smoke_resume.PROBE_EXPECTED["r01"],
            "Correct route.",
        )
        smoke_resume.restore(self.repo, self.run_id, "r01")
        with self.assertRaises(smoke_resume.ResumeProbeError):
            self.prepare("r01")

        self.prepare("r02")
        smoke_resume.score(
            self.repo,
            self.run_id,
            "r02",
            "/verify",
            "Incorrect route.",
        )
        smoke_resume.restore(self.repo, self.run_id, "r02")
        with self.assertRaises(smoke_resume.ResumeProbeError):
            self.prepare("r02")

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

    def test_status_pass_requires_all_seven_scored_and_restored(self):
        ledger_path = (
            self.repo
            / "docs/verification/smoke"
            / f"{self.run_id}.resume.json"
        )
        probes = []
        for probe_id in sorted(smoke_resume.PROBE_EXPECTED):
            probes.append(
                {
                    "probe_id": probe_id,
                    "state": "RESTORED",
                    "routing_pass": True,
                    "handoff_pass": True if probe_id == smoke_resume.HANDOFF_PROBE else None,
                    "probe_result": "PASS",
                    "restored": True,
                    "attempt_count": 1,
                }
            )
        ledger_path.write_text(
            json.dumps(
                {"schema_version": smoke_resume.SCHEMA_VERSION, "probes": probes},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        result = smoke_resume.status(self.repo, self.run_id)
        self.assertEqual("PASS", result["result"])
        self.assertEqual(7, len(result["completed_probes"]))

        probes[-1]["probe_result"] = "FAIL"
        ledger_path.write_text(
            json.dumps(
                {"schema_version": smoke_resume.SCHEMA_VERSION, "probes": probes},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        self.assertEqual(
            "INCOMPLETE",
            smoke_resume.status(self.repo, self.run_id)["result"],
        )
        self.assertNotIn("expected_stage", json.dumps(probes))


if __name__ == "__main__":
    unittest.main()
