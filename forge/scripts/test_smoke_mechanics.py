"""Focused regressions for disposable smoke checkpoint and identity mechanics."""

import subprocess
import tempfile
import unittest
import os
from pathlib import Path

from smoke_mechanics import (MechanicsError, canonical_manifest, check_checkpoint,
                             checkpoint, identity, mutate, restore)


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
