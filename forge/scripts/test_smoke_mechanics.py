"""Focused regressions for disposable smoke checkpoint and identity mechanics."""

import subprocess
import tempfile
import unittest
import os
from pathlib import Path

from smoke_mechanics import (
    VERIFICATION_MUTATION_PATH,
    MechanicsError,
    arm_verification_mutation,
    canonical_manifest,
    check_checkpoint,
    checkpoint,
    fire_verification_mutation,
    identity,
    mutate,
    restore,
)


class SmokeMechanicsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Smoke")
        self.git("config", "user.email", "smoke@example.test")
        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b\n")
        self.git("add", "app.py")
        self.git("commit", "-qm", "baseline")
        self.git("switch", "-qc", "smoke-run")
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.base = self.git("rev-parse", "HEAD").strip()
        self.run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"

    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.repo, text=True)

    def test_manifest_tracks_uncommitted_content_and_ignores_only_evidence(self):
        (self.repo / "app.py").write_text("def add(a, b):\n    return a - b\n")
        (self.repo / "new.py").write_text("new\n")
        (self.repo / "docs/verification/smoke" / "run.md").write_text("evidence")
        manifest = canonical_manifest(self.repo, self.base).decode()
        self.assertIn("app.py\t100644\t", manifest)
        self.assertIn("new.py\t100644\t", manifest)
        self.assertNotIn("docs/verification/", manifest)
        self.assertEqual(manifest, identity(self.repo, self.base)["manifest"])

    def test_mutation_restores_exact_checkpoint_and_refuses_drift(self):
        checkpoint(self.repo, self.run_id, "verified")
        mutate(self.repo, self.run_id, "defect", "verified", "obvious-deterministic-defect",
               "app.py", "return a + b", "return a - b")
        self.assertEqual("MISMATCH", check_checkpoint(self.repo, self.run_id, "verified")["result"])
        (self.repo / "app.py").write_text("unrelated edit\n")
        with self.assertRaises(MechanicsError):
            restore(self.repo, self.run_id, "defect")
        (self.repo / "app.py").write_text("def add(a, b):\n    return a - b\n")
        self.assertEqual("MATCH", restore(self.repo, self.run_id, "defect")["result"])
        self.assertEqual("MATCH", check_checkpoint(self.repo, self.run_id, "verified")["result"])

    def test_ambiguous_anchor_and_evidence_mutation_fail_closed(self):
        checkpoint(self.repo, self.run_id, "verified")
        with self.assertRaises(MechanicsError):
            mutate(self.repo, self.run_id, "bad", "verified", "obvious-deterministic-defect",
                   "app.py", "absent", "broken")
        with self.assertRaises(MechanicsError):
            mutate(self.repo, self.run_id, "bad", "verified", "obvious-deterministic-defect",
                   "docs/verification/smoke/run.md", "x", "y")

    def test_verification_mutation_fires_between_identity_captures_and_restores(self):
        checkpoint(self.repo, self.run_id, "reviewed")
        pre = identity(self.repo, self.base)
        armed = arm_verification_mutation(
            self.repo, self.run_id, "verify-mutation-1", "reviewed"
        )
        self.assertEqual("ARMED", armed["state"])
        self.assertFalse((self.repo / VERIFICATION_MUTATION_PATH).exists())
        self.assertEqual("MATCH", check_checkpoint(self.repo, self.run_id, "reviewed")["result"])
        self.assertIn("return a + b", (self.repo / "app.py").read_text())

        fired = fire_verification_mutation(self.repo, self.run_id, "verify-mutation-1")
        self.assertEqual("APPLIED", fired["state"])
        self.assertEqual("MISMATCH", fired["checkpoint_result"])
        post = identity(self.repo, self.base)
        self.assertNotEqual(pre["manifest"], post["manifest"])
        self.assertIn(VERIFICATION_MUTATION_PATH, post["manifest"])

        restored = restore(self.repo, self.run_id, "verify-mutation-1")
        self.assertEqual("MATCH", restored["result"])
        self.assertFalse((self.repo / VERIFICATION_MUTATION_PATH).exists())
        self.assertEqual(pre["manifest"], identity(self.repo, self.base)["manifest"])

    def test_verification_mutation_recipe_cannot_use_immediate_mutate(self):
        checkpoint(self.repo, self.run_id, "reviewed")
        with self.assertRaises(MechanicsError):
            mutate(self.repo, self.run_id, "wrong-path", "reviewed",
                   "verification-mutation", "app.py",
                   "return a + b", "return a - b")

    def test_verification_mutation_refuses_checkpoint_drift_before_fire(self):
        checkpoint(self.repo, self.run_id, "reviewed")
        arm_verification_mutation(self.repo, self.run_id, "verify-mutation-1", "reviewed")
        (self.repo / "app.py").write_text("def add(a, b):\n    return a - b\n")
        with self.assertRaises(MechanicsError):
            fire_verification_mutation(self.repo, self.run_id, "verify-mutation-1")
        self.assertFalse((self.repo / VERIFICATION_MUTATION_PATH).exists())
        (self.repo / "app.py").write_text("def add(a, b):\n    return a + b\n")
        self.assertEqual("MATCH", restore(self.repo, self.run_id, "verify-mutation-1")["result"])

    def test_unfired_verification_mutation_can_be_disarmed(self):
        checkpoint(self.repo, self.run_id, "reviewed")
        arm_verification_mutation(self.repo, self.run_id, "verify-mutation-1", "reviewed")
        restored = restore(self.repo, self.run_id, "verify-mutation-1")
        self.assertEqual("RESTORED", restored["state"])
        self.assertEqual("MATCH", restored["result"])
        self.assertFalse((self.repo / VERIFICATION_MUTATION_PATH).exists())

    def test_verification_mutation_must_be_identity_bearing(self):
        (self.repo / ".gitignore").write_text(
            VERIFICATION_MUTATION_PATH + "\n", encoding="utf-8"
        )
        checkpoint(self.repo, self.run_id, "reviewed")
        arm_verification_mutation(self.repo, self.run_id, "verify-mutation-1", "reviewed")
        with self.assertRaises(MechanicsError):
            fire_verification_mutation(self.repo, self.run_id, "verify-mutation-1")
        self.assertFalse((self.repo / VERIFICATION_MUTATION_PATH).exists())

    @unittest.skipIf(os.name == "nt", "Windows does not expose executable bit changes")
    def test_identity_changes_for_mode_only_and_deletion(self):
        before = identity(self.repo, self.base)["manifest"]
        (self.repo / "app.py").chmod(0o755)
        self.assertIn("app.py\t100755\t", identity(self.repo, self.base)["manifest"])
        (self.repo / "app.py").unlink()
        self.assertIn("app.py\tDELETED\tDELETED\n", identity(self.repo, self.base)["manifest"])
        self.assertNotEqual(before, identity(self.repo, self.base)["manifest"])

    def test_identical_commit_and_evidence_do_not_invalidate_manifest(self):
        (self.repo / "app.py").write_text("def add(a, b):\n    return a - b\n")
        expected = identity(self.repo, self.base)["manifest"]
        self.git("add", "app.py")
        self.git("commit", "-qm", "same verified content")
        (self.repo / "docs/verification/smoke/run.md").write_text("new evidence")
        self.assertEqual(expected, identity(self.repo, self.base)["manifest"])


if __name__ == "__main__":
    unittest.main()
