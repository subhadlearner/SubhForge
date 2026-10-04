"""Focused regressions for H06 upstream-rerouting probe mechanics."""

import copy
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import smoke_mechanics
import smoke_reroute
import smoke_resume
import smoke_workspace


class SmokeRerouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Building the Git fixture is expensive on Windows because Contract-v1
        # reconstruction launches multiple git.exe processes. Build the exact
        # clean checkpoint once, then copy the tiny repository per test. Each
        # test still gets an isolated .git directory and mechanics ledger.
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

        write("AGENTS.md", "# Project\nTechnology pending.\n")
        write("README.md", "# Project\n")
        write(".kilo/rules/.gitkeep", "")
        write(".kilo/skills/.gitkeep", "")
        write(
            "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md",
            "implementation-state-evidence-v1\n",
        )
        write("docs/verification/smoke/.gitkeep", "")
        git("add", "-A")
        git("commit", "-qm", "baseline")
        git("switch", "-qc", "smoke-run")

        write(
            "AGENTS.md",
            "# Project\nRuntime: Python 3.8+\nPackage manager: standard library\n",
        )
        write(
            "docs/prd/PRD-001.md",
            "# PRD\nStatus: PRD_READY\nEmpty input returns HTTP 400.\n",
        )
        write(
            "docs/architecture/ARCH-001.md",
            "# Architecture\nStatus: ARCHITECTURE_READY\nRuntime: Python 3.8+\nPersistence: in-memory only.\n",
        )
        write(
            "docs/adr/ADR-001.md",
            "# ADR\nStatus: Accepted\nPersistence remains in memory.\n",
        )
        write(
            "docs/specs/SPEC-001.md",
            "# Spec\nStatus: SPEC_READY\nEmpty input returns HTTP 400.\nUse approved in-memory persistence.\n",
        )
        write("app.py", "def handle(value):\n    return 400 if not value else 200\n")
        write("test_app.py", "from app import handle\n")
        write(
            "docs/verification/VERIFY-SPEC-001-001.md",
            "# Verification\nVerification Result: DONE\nDelivery Gate: CLEAR\n",
        )
        write("docs/reviews/REVIEW-001.md", "# Review\nAPPROVE\n")
        write("docs/diagnostics/OLD.md", "# Old diagnosis\n")

        cls._run_id = "SMOKE-FULL-test-20260930T000000Z-12345678"
        smoke_workspace._stamp_repository_identity(
            seed,
            cls._run_id,
            git("rev-parse", "HEAD").strip(),
        )
        smoke_mechanics.checkpoint(seed, cls._run_id, "clean")
        cls._clean_snapshot = smoke_resume.capture_probe_snapshot(seed)

    @classmethod
    def tearDownClass(cls):
        cls._seed_temp.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "repo"
        shutil.copytree(self._seed_repo, self.repo, symlinks=True)

        self.prd = "docs/prd/PRD-001.md"
        self.arch = "docs/architecture/ARCH-001.md"
        self.adr = "docs/adr/ADR-001.md"
        self.spec = "docs/specs/SPEC-001.md"
        self.verification = "docs/verification/VERIFY-SPEC-001-001.md"
        self.impl = ["app.py", "test_app.py"]
        self.run_id = self._run_id
        self.clean_snapshot = copy.deepcopy(self._clean_snapshot)

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True)

    def write(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def prepare(self, probe_id):
        return smoke_reroute.prepare(
            self.repo,
            self.run_id,
            probe_id,
            "clean",
            self.prd,
            self.arch,
            self.adr,
            self.spec,
            "AGENTS.md",
            self.impl,
            self.verification,
        )

    def score_expected(self, probe_id):
        plan = smoke_reroute.PROBE_PLAN[probe_id]
        result = smoke_reroute.score(
            self.repo,
            self.run_id,
            probe_id,
            plan["status"],
            plan["owner"],
            plan["next_command"],
            "Persisted evidence identifies the authority boundary.",
        )
        if result["handoff_required"]:
            smoke_reroute.record_handoff(
                self.repo,
                self.run_id,
                probe_id,
                True,
                "The selected architecture workflow accepted the exact persisted context.",
            )
        restored = smoke_reroute.restore(self.repo, self.run_id, probe_id)
        self.assertEqual("MATCH", restored["checkpoint_result"])
        # restore() already proves byte-identical snapshot restoration and
        # Contract-v1 checkpoint MATCH. Re-capturing the same snapshot here
        # would only add two more git.exe launches per probe on Windows.
        return result, restored

    def test_u01_architecture_product_ambiguity(self):
        result = self.prepare("u01")
        self.assertEqual("planning", result["classifier"])
        self.assertEqual("/architect", result["workflow"])
        self.assertIn("same absent required value", (self.repo / self.prd).read_text())
        self.score_expected("u01")

    def test_u02_spec_architecture_ambiguity_requires_representative_handoff(self):
        self.prepare("u02")
        self.assertIn("Node.js 20+", (self.repo / self.arch).read_text())
        plan = smoke_reroute.PROBE_PLAN["u02"]
        scored = smoke_reroute.score(
            self.repo,
            self.run_id,
            "u02",
            plan["status"],
            plan["owner"],
            plan["next_command"],
            "Architecture and ADR evidence conflict.",
        )
        self.assertTrue(scored["handoff_required"])
        self.assertEqual(
            "/architect -> /project-init -> /spec -> /implement -> /verify",
            scored["regeneration_path"],
        )
        smoke_reroute.record_handoff(
            self.repo,
            self.run_id,
            "u02",
            True,
            "Architecture owner accepted the exact persisted context.",
        )
        restored = smoke_reroute.restore(self.repo, self.run_id, "u02")
        self.assertEqual("PASS", restored["probe_result"])

    def test_u03_implementation_requires_unapproved_architecture_change(self):
        self.prepare("u03")
        self.assertIn("PostgreSQL", (self.repo / self.spec).read_text())
        self.score_expected("u03")

    def test_u04_fix_routes_product_contradiction(self):
        self.prepare("u04")
        text = (self.repo / self.verification).read_text()
        self.assertIn("two incompatible outcomes", text)
        self.assertNotIn("### Owner", text)
        self.score_expected("u04")

    def test_u05_fix_routes_architecture_change(self):
        self.prepare("u05")
        self.assertIn("replacing the approved in-memory", (self.repo / self.verification).read_text())
        self.score_expected("u05")

    def test_u06_fix_routes_project_init_drift_without_answer_leak(self):
        self.prepare("u06")
        self.assertIn("Node.js 20 and npm", (self.repo / "AGENTS.md").read_text())
        ledger = (
            self.repo
            / "docs/verification/smoke"
            / f"{self.run_id}.reroute.json"
        ).read_text(encoding="utf-8")
        self.assertNotIn("expected", ledger)
        self.assertNotIn("PROJECT_INIT", ledger)
        self.assertNotIn("/project-init", ledger)
        self.score_expected("u06")

    def test_u07_fix_routes_specification_contradiction(self):
        self.prepare("u07")
        self.assertIn("same empty required value", (self.repo / self.spec).read_text())
        self.score_expected("u07")

    def test_u08_fix_routes_repository_state(self):
        self.prepare("u08")
        self.assertTrue((self.repo / "local-work.txt").is_file())
        self.score_expected("u08")
        self.assertFalse((self.repo / "local-work.txt").exists())

    def test_wrong_route_scores_fail_and_restores(self):
        self.prepare("u07")
        result = smoke_reroute.score(
            self.repo,
            self.run_id,
            "u07",
            "FIX_BLOCKED",
            "ARCHITECTURE",
            "/architect",
            "Incorrect route.",
        )
        self.assertEqual("FAIL", result["routing_result"])
        restored = smoke_reroute.restore(self.repo, self.run_id, "u07")
        self.assertEqual("FAIL", restored["probe_result"])

    def test_active_probe_must_restore_before_next_prepare(self):
        self.prepare("u01")
        with self.assertRaises(smoke_reroute.RerouteProbeError):
            self.prepare("u02")
        smoke_reroute.restore(self.repo, self.run_id, "u01")

    def test_restored_not_scored_probe_can_retry_same_id(self):
        self.prepare("u05")
        first = smoke_reroute.restore(self.repo, self.run_id, "u05")
        self.assertEqual("NOT_SCORED", first["probe_result"])

        self.prepare("u05")
        ledger = json.loads(
            (
                self.repo
                / "docs/verification/smoke"
                / f"{self.run_id}.reroute.json"
            ).read_text(encoding="utf-8")
        )
        matching = [item for item in ledger["probes"] if item["probe_id"] == "u05"]
        self.assertEqual(1, len(matching))
        self.assertEqual(2, matching[0]["attempt_count"])
        self.assertEqual("PREPARED", matching[0]["state"])
        smoke_reroute.restore(self.repo, self.run_id, "u05")

    def test_scored_reroute_probe_cannot_retry_after_pass_or_fail(self):
        self.prepare("u01")
        self.score_expected("u01")
        with self.assertRaises(smoke_reroute.RerouteProbeError):
            self.prepare("u01")

        self.prepare("u07")
        smoke_reroute.score(
            self.repo,
            self.run_id,
            "u07",
            "FIX_BLOCKED",
            "ARCHITECTURE",
            "/architect",
            "Incorrect route.",
        )
        smoke_reroute.restore(self.repo, self.run_id, "u07")
        with self.assertRaises(smoke_reroute.RerouteProbeError):
            self.prepare("u07")

    def test_classifier_mutation_is_detected_before_scoring(self):
        self.prepare("u05")
        self.write("unexpected.py", "changed by classifier\n")
        plan = smoke_reroute.PROBE_PLAN["u05"]
        with self.assertRaises(smoke_reroute.RerouteProbeError):
            smoke_reroute.score(
                self.repo,
                self.run_id,
                "u05",
                plan["status"],
                plan["owner"],
                plan["next_command"],
                "Claimed route after mutation.",
            )
        restored = smoke_reroute.restore(self.repo, self.run_id, "u05")
        self.assertEqual("MATCH", restored["checkpoint_result"])
        self.assertFalse((self.repo / "unexpected.py").exists())

    def test_handoff_probe_rejects_repository_mutation(self):
        self.prepare("u02")
        plan = smoke_reroute.PROBE_PLAN["u02"]
        smoke_reroute.score(
            self.repo,
            self.run_id,
            "u02",
            plan["status"],
            plan["owner"],
            plan["next_command"],
            "Architecture conflict.",
        )
        self.write(self.arch, (self.repo / self.arch).read_text() + "changed\n")
        with self.assertRaises(smoke_reroute.RerouteProbeError):
            smoke_reroute.record_handoff(
                self.repo,
                self.run_id,
                "u02",
                True,
                "Claimed acceptance after mutation.",
            )
        smoke_reroute.restore(self.repo, self.run_id, "u02")

    def test_context_paths_must_be_normal_repository_paths(self):
        with self.assertRaises(smoke_reroute.RerouteProbeError):
            smoke_reroute.prepare(
                self.repo,
                self.run_id,
                "u01",
                "clean",
                "../PRD.md",
                self.arch,
                self.adr,
                self.spec,
                "AGENTS.md",
                self.impl,
                self.verification,
            )

    def test_status_pass_requires_all_eight_scored_restored_and_handoff(self):
        ledger_path = (
            self.repo
            / "docs/verification/smoke"
            / f"{self.run_id}.reroute.json"
        )
        probes = []
        for probe_id in sorted(smoke_reroute.PROBE_PLAN):
            probes.append(
                {
                    "probe_id": probe_id,
                    "state": "RESTORED",
                    "routing_pass": True,
                    "handoff_pass": True if probe_id == smoke_reroute.HANDOFF_PROBE else None,
                    "probe_result": "PASS",
                    "restored": True,
                }
            )
        ledger_path.write_text(
            json.dumps(
                {"schema_version": smoke_reroute.SCHEMA_VERSION, "probes": probes},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        result = smoke_reroute.status(self.repo, self.run_id)
        self.assertEqual("PASS", result["result"])
        self.assertEqual(8, len(result["completed_probes"]))

        probes[-1]["probe_result"] = "FAIL"
        ledger_path.write_text(
            json.dumps(
                {"schema_version": smoke_reroute.SCHEMA_VERSION, "probes": probes},
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        self.assertEqual(
            "INCOMPLETE",
            smoke_reroute.status(self.repo, self.run_id)["result"],
        )

        serialized = json.dumps(probes)
        self.assertNotIn("expected_owner", serialized)
        self.assertNotIn("expected_next_command", serialized)


if __name__ == "__main__":
    unittest.main()
