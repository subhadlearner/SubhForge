"""Direct regressions for shared Contract-v1 implementation-state reconstruction."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import implementation_state


class ImplementationStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        implementation_state.git(self.repo, "init", "-q")
        implementation_state.git(self.repo, "config", "user.name", "SubhForge Test")
        implementation_state.git(self.repo, "config", "user.email", "subhforge@test.local")
        (self.repo / "app.py").write_text("print('base')\n", encoding="utf-8")
        implementation_state.git(self.repo, "add", "app.py")
        implementation_state.git(self.repo, "commit", "-qm", "baseline")
        self.base = implementation_state.git(self.repo, "rev-parse", "HEAD").strip().decode("ascii")

    def test_manifest_tracks_changed_and_untracked_files_but_excludes_evidence(self):
        (self.repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
        (self.repo / "new.py").write_text("new\n", encoding="utf-8")
        evidence = self.repo / "docs" / "verification"
        evidence.mkdir(parents=True)
        (evidence / "VERIFY-001.md").write_text("evidence\n", encoding="utf-8")

        manifest = implementation_state.canonical_manifest(self.repo, self.base).decode("utf-8")

        self.assertIn("app.py\t100644\t", manifest)
        self.assertIn("new.py\t100644\t", manifest)
        self.assertNotIn("docs/verification/", manifest)

    def test_identity_is_stable_for_evidence_only_changes(self):
        (self.repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
        before = implementation_state.identity(self.repo, self.base)

        evidence = self.repo / "docs" / "reviews"
        evidence.mkdir(parents=True)
        (evidence / "REVIEW-001.md").write_text("review\n", encoding="utf-8")

        after = implementation_state.identity(self.repo, self.base)

        self.assertEqual(before["manifest"], after["manifest"])
        self.assertEqual(before["fingerprint"], after["fingerprint"])

    def test_missing_base_fails_closed(self):
        with self.assertRaises(implementation_state.ImplementationStateError):
            implementation_state.canonical_manifest(self.repo, "does-not-exist")

    def test_repo_root_is_required(self):
        child = self.repo / "child"
        child.mkdir()
        with self.assertRaises(implementation_state.ImplementationStateError):
            implementation_state.canonical_manifest(child, self.base)

    @unittest.skipIf(os.name == "nt", "Windows does not expose executable-bit changes")
    def test_mode_only_change_changes_manifest(self):
        before = implementation_state.canonical_manifest(self.repo, self.base)
        (self.repo / "app.py").chmod(0o755)
        after = implementation_state.canonical_manifest(self.repo, self.base)

        self.assertNotEqual(before, after)
        self.assertIn("app.py\t100755\t", after.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
