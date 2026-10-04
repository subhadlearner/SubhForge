"""Real repository-identity regressions for H10 mutating helper boundaries."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import smoke_budget
import smoke_mechanics
import smoke_reroute
import smoke_resume
import smoke_segments
import smoke_state
import smoke_workspace


class SmokeRepositoryIdentityGuardTests(unittest.TestCase):
    def git(self, *args):
        return subprocess.check_output(
            ["git", *args], cwd=str(self.repo), text=True
        ).strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name) / "unowned"
        self.repo.mkdir()
        self.git("init")
        self.git("config", "user.name", "Smoke")
        self.git("config", "user.email", "smoke@example.test")
        (self.repo / "README.md").write_text("unowned smoke repository\n", encoding="utf-8")
        self.git("add", "-A")
        self.git("commit", "-qm", "baseline")
        self.git("branch", "-M", "smoke-run")
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.baseline = self.git("rev-parse", "HEAD")
        self.run_id = "SMOKE-FULL-guard-20261004T000000Z-12345678"

    def test_budget_start_requires_owned_repository(self):
        with self.assertRaisesRegex(smoke_budget.BudgetError, "ownership metadata is missing"):
            smoke_budget.start(self.repo, self.run_id)

    def test_state_mutators_require_owned_repository(self):
        with self.subTest("init"):
            with self.assertRaisesRegex(smoke_state.SmokeStateError, "ownership metadata is missing"):
                smoke_state.init(
                    self.repo,
                    self.run_id,
                    "FULL",
                    "full-minimal-api",
                    self.baseline,
                    self.baseline,
                )
        with self.subTest("set_values"):
            with self.assertRaisesRegex(smoke_state.SmokeStateError, "ownership metadata is missing"):
                smoke_state.set_values(self.repo, self.run_id, {})

    def test_mechanics_mutators_require_owned_repository(self):
        calls = {
            "checkpoint": lambda: smoke_mechanics.checkpoint(self.repo, self.run_id, "clean"),
            "mutate": lambda: smoke_mechanics.mutate(
                self.repo,
                self.run_id,
                "m1",
                "clean",
                "obvious-deterministic-defect",
                "README.md",
                "unowned",
                "owned",
            ),
            "restore": lambda: smoke_mechanics.restore(self.repo, self.run_id, "m1"),
        }
        for name, call in calls.items():
            with self.subTest(name=name):
                with self.assertRaisesRegex(smoke_mechanics.MechanicsError, "ownership metadata is missing"):
                    call()

    def test_resume_mutator_requires_owned_repository(self):
        with self.assertRaisesRegex(smoke_resume.ResumeProbeError, "ownership metadata is missing"):
            smoke_resume.prepare(
                self.repo,
                self.run_id,
                "r01",
                "clean",
                self.baseline,
                "docs/specs/SPEC.md",
                ["src/app.py"],
                "docs/verification/VERIFY.md",
            )

    def test_reroute_mutator_requires_owned_repository(self):
        with self.assertRaisesRegex(smoke_reroute.RerouteProbeError, "ownership metadata is missing"):
            smoke_reroute.prepare(
                self.repo,
                self.run_id,
                "u01",
                "clean",
                "docs/prd/PRD.md",
                "docs/architecture/ARCH.md",
                "docs/architecture/ADR.md",
                "docs/specs/SPEC.md",
                "AGENTS.md",
                ["src/app.py"],
                "docs/verification/VERIFY.md",
            )

    def test_segment_mutation_guards_require_owned_repository(self):
        with self.subTest("persist_context"):
            with self.assertRaisesRegex(smoke_segments.SegmentError, "ownership metadata is missing"):
                smoke_segments._persist_context(self.repo, self.run_id, {}, {})
        with self.subTest("register_scenario_evidence"):
            with self.assertRaisesRegex(smoke_segments.SegmentError, "ownership metadata is missing"):
                smoke_segments.register_scenario_evidence(
                    self.repo,
                    self.run_id,
                    "static-release-gate",
                    "guard-test",
                    ["guard must run first"],
                )

    def test_snapshot_restores_bind_to_exact_run(self):
        owner_run = "SMOKE-FULL-owner-20261004T000000Z-87654321"
        smoke_workspace._stamp_repository_identity(
            self.repo, owner_run, self.baseline
        )
        with self.assertRaisesRegex(smoke_resume.ResumeProbeError, "different run"):
            smoke_resume.restore_probe_snapshot(self.repo, self.run_id, {})
        with self.assertRaisesRegex(smoke_resume.ResumeProbeError, "different run"):
            smoke_resume.restore_probe_snapshot_at_root(self.repo, self.run_id, {})


if __name__ == "__main__":
    unittest.main()
