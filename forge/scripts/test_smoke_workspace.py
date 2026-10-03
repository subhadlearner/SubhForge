"""Regression tests for internal SubhForge smoke workspace provisioning."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_workspace


class SmokeWorkspaceTests(unittest.TestCase):
    def git(self, repo, *args):
        return subprocess.check_output(["git", *args], cwd=str(repo), text=True).strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "SubhForge"
        self.source.mkdir()
        self.git(self.source, "init")
        self.git(self.source, "config", "user.name", "Test")
        self.git(self.source, "config", "user.email", "test@example.invalid")
        template = self.source / "template"
        template.mkdir()
        (template / "README.md").write_text("committed template\n", encoding="utf-8")
        (template / "docs").mkdir()
        (template / "docs" / "placeholder.md").write_text("placeholder\n", encoding="utf-8")
        self.git(self.source, "add", "-A")
        self.git(self.source, "commit", "-m", "baseline")
        self.commit = self.git(self.source, "rev-parse", "HEAD")

    def test_create_uses_exact_recorded_commit_and_does_not_require_clean_source(self):
        # Dirty the source after the recorded release commit. The smoke fixture
        # must still come from the recorded commit and leave the source alone.
        (self.source / "template" / "README.md").write_text(
            "dirty working tree\n", encoding="utf-8"
        )
        before_status = self.git(self.source, "status", "--porcelain")

        result = smoke_workspace.create_workspace(
            self.source, self.commit, "FULL", "full-minimal-api"
        )
        run_dir = Path(result["run_directory"])
        self.addCleanup(
            lambda: run_dir.exists()
            and smoke_workspace.destroy_workspace(self.source, result["run_id"])
        )

        self.assertEqual("smoke-run", self.git(run_dir, "branch", "--show-current"))
        self.assertEqual("committed template\n",
                         (run_dir / "README.md").read_text(encoding="utf-8"))
        self.assertEqual(self.commit, result["source_commit"])
        self.assertEqual(before_status, self.git(self.source, "status", "--porcelain"))

        run_root = self.source.parent / "SubhForge-smoke-runs"
        leftovers = [
            p.name for p in run_root.iterdir()
            if p.name.startswith(".release-") or p.name.startswith(".baseline-")
        ]
        self.assertEqual([], leftovers)


    def test_source_guard_allows_preexisting_dirty_source_when_unchanged(self):
        dirty = self.source / "template" / "README.md"
        dirty.write_text("dirty working tree\n", encoding="utf-8")

        before = smoke_workspace.source_guard(self.source)
        verified = smoke_workspace.verify_source_guard(
            self.source, before["fingerprint"]
        )

        self.assertEqual("MATCH", verified["result"])

    def test_source_guard_detects_new_untracked_smoke_artifact(self):
        before = smoke_workspace.source_guard(self.source)
        leaked = self.source / "docs" / "discovery"
        leaked.mkdir(parents=True)
        (leaked / "full-minimal-api-discovery.md").write_text(
            "smoke leak\n", encoding="utf-8"
        )

        verified = smoke_workspace.verify_source_guard(
            self.source, before["fingerprint"]
        )

        self.assertEqual("MISMATCH", verified["result"])
        self.assertNotEqual(before["fingerprint"], verified["fingerprint"])

    def test_locate_and_destroy_use_internal_run_root(self):
        result = smoke_workspace.create_workspace(
            self.source, self.commit, "FAST", "fast-micro-library"
        )
        located = smoke_workspace.locate_workspace(self.source, result["run_id"])
        self.assertEqual(result["run_directory"], located["run_directory"])
        destroyed = smoke_workspace.destroy_workspace(self.source, result["run_id"])
        self.assertEqual("true", destroyed["destroyed"])
        self.assertFalse(Path(result["run_directory"]).exists())


if __name__ == "__main__":
    unittest.main()
