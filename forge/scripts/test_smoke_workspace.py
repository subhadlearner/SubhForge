"""Regression tests for internal SubhForge smoke workspace provisioning."""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
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
        self.assertEqual(
            result["run_id"],
            self.git(run_dir, "config", "--local", "--get", smoke_workspace.SMOKE_RUN_ID_CONFIG),
        )
        self.assertEqual(
            result["baseline_head"],
            self.git(
                run_dir,
                "config",
                "--local",
                "--get",
                smoke_workspace.SMOKE_BASELINE_HEAD_CONFIG,
            ),
        )
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


    def test_source_operations_reject_plain_child_of_enclosing_git_repository(self):
        child = self.source / "plain-child"
        child.mkdir()

        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "must itself be the Git top-level",
        ):
            smoke_workspace.source_guard(child)
        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "must itself be the Git top-level",
        ):
            smoke_workspace.create_workspace(
                child, self.commit, "FAST", "fast-micro-library"
            )

        self.assertTrue(child.is_dir())

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

    def test_workspace_operations_reject_malformed_or_escaping_run_ids(self):
        run_root = self.source.parent / "SubhForge-smoke-runs"
        valid_run = smoke_workspace.create_workspace(
            self.source, self.commit, "FAST", "fast-micro-library"
        )
        self.addCleanup(
            lambda: Path(valid_run["run_directory"]).exists()
            and smoke_workspace.destroy_workspace(self.source, valid_run["run_id"])
        )

        outside = self.root / "outside-smoke-run"
        outside.mkdir()
        absolute = str(outside.resolve())

        for run_id in (
            "../SubhForge",
            "..",
            "SMOKE-../SubhForge",
            "SMOKE-FULL/bad",
            "SMOKE-FULL\\bad",
            absolute,
            "not-a-smoke-run",
            "SMOKE-",
            "SMOKE-FAST-fixture-20261004T102400Z",
            "SMOKE-FAST--20261004T102400Z-12345678",
            "SMOKE-FAST-fixture-not-a-time-12345678",
            "SMOKE-FAST-fixture-20261004T102400Z-nothex12",
            "SMOKE-FAST-fixture-２０２６１００４T１０２４００Z-12345678",
            "",
        ):
            with self.subTest(run_id=run_id):
                with self.assertRaises(smoke_workspace.SmokeWorkspaceError):
                    smoke_workspace.locate_workspace(self.source, run_id)
                with self.assertRaises(smoke_workspace.SmokeWorkspaceError):
                    smoke_workspace.destroy_workspace(self.source, run_id)

        self.assertTrue(self.source.is_dir())
        self.assertTrue(outside.is_dir())
        self.assertTrue(Path(valid_run["run_directory"]).is_dir())
        self.assertTrue(run_root.is_dir())

    def test_workspace_operations_reject_valid_run_id_link_escape(self):
        run_root = self.source.parent / "SubhForge-smoke-runs"
        run_root.mkdir()
        outside = self.root / "outside-link-target"
        outside.mkdir()
        self.git(outside, "init")
        self.git(outside, "config", "user.name", "Test")
        self.git(outside, "config", "user.email", "test@example.invalid")
        (outside / "README.md").write_text("outside repository\n", encoding="utf-8")
        self.git(outside, "add", "-A")
        self.git(outside, "commit", "-m", "outside baseline")
        self.git(outside, "branch", "-M", "smoke-run")

        run_id = "SMOKE-FAST-link-20261004T102400Z-12345678"
        link = run_root / run_id

        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as symlink_error:
            if os.name != "nt":
                self.skipTest("Directory symlinks are unavailable: {}".format(symlink_error))
            junction = subprocess.run(
                ["cmd.exe", "/c", "mklink", "/J", str(link), str(outside)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if junction.returncode != 0:
                self.fail(
                    "Windows containment regression requires a directory junction: {}".format(
                        (junction.stderr or junction.stdout).strip()
                    )
                )

        def remove_link():
            if link.is_symlink():
                link.unlink()
            elif link.exists():
                os.rmdir(str(link))

        self.addCleanup(remove_link)

        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "escapes smoke run root",
        ):
            smoke_workspace.locate_workspace(self.source, run_id)
        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "escapes smoke run root",
        ):
            smoke_workspace.destroy_workspace(self.source, run_id)
        self.assertTrue(outside.is_dir())
        self.assertEqual("smoke-run", self.git(outside, "branch", "--show-current"))

    def test_locate_and_destroy_reject_parent_git_discovery(self):
        run_root = self.source.parent / "SubhForge-smoke-runs"
        run_root.mkdir()
        self.git(run_root, "init")
        self.git(run_root, "config", "user.name", "Test")
        self.git(run_root, "config", "user.email", "test@example.invalid")
        (run_root / "README.md").write_text("enclosing repository\n", encoding="utf-8")
        self.git(run_root, "add", "-A")
        self.git(run_root, "commit", "-m", "enclosing baseline")
        self.git(run_root, "branch", "-M", "smoke-run")

        run_id = "SMOKE-FAST-child-20261004T102400Z-12345678"
        child = run_root / run_id
        child.mkdir()

        for operation in (
            smoke_workspace.locate_workspace,
            smoke_workspace.destroy_workspace,
        ):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(
                    smoke_workspace.SmokeWorkspaceError,
                    "must itself be the Git top-level",
                ):
                    operation(self.source, run_id)
        self.assertTrue(child.is_dir())

    def test_locate_and_destroy_reject_wrong_repository_identity(self):
        run_root = self.source.parent / "SubhForge-smoke-runs"
        run_root.mkdir()
        run_id = "SMOKE-FAST-wrong-20261004T102400Z-12345678"
        target = run_root / run_id
        target.mkdir()
        self.git(target, "init")
        self.git(target, "config", "user.name", "Test")
        self.git(target, "config", "user.email", "test@example.invalid")
        (target / "README.md").write_text("wrong repository\n", encoding="utf-8")
        self.git(target, "add", "-A")
        self.git(target, "commit", "-m", "wrong baseline")
        self.git(target, "branch", "-M", "smoke-run")

        for operation in (
            smoke_workspace.locate_workspace,
            smoke_workspace.destroy_workspace,
        ):
            with self.subTest(operation=operation.__name__):
                with self.assertRaisesRegex(
                    smoke_workspace.SmokeWorkspaceError,
                    "ownership metadata is missing",
                ):
                    operation(self.source, run_id)
        self.assertTrue(target.is_dir())

    def test_repository_identity_rejects_wrong_branch_and_wrong_run_stamp(self):
        run_root = self.source.parent / "SubhForge-smoke-runs"
        run_root.mkdir()
        run_id = "SMOKE-FAST-owner-20261004T102400Z-12345678"
        other_run_id = "SMOKE-FAST-other-20261004T102400Z-87654321"
        target = run_root / run_id
        target.mkdir()
        self.git(target, "init")
        self.git(target, "config", "user.name", "Test")
        self.git(target, "config", "user.email", "test@example.invalid")
        (target / "README.md").write_text("owned repository\n", encoding="utf-8")
        self.git(target, "add", "-A")
        self.git(target, "commit", "-m", "baseline")
        baseline = self.git(target, "rev-parse", "HEAD")

        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "must be on smoke-run",
        ):
            smoke_workspace.validate_repository_identity(target, run_id)

        self.git(target, "branch", "-M", "smoke-run")
        self.git(
            target, "config", "--local",
            smoke_workspace.SMOKE_RUN_ID_CONFIG, other_run_id
        )
        self.git(
            target, "config", "--local",
            smoke_workspace.SMOKE_BASELINE_HEAD_CONFIG, baseline
        )
        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "belongs to a different run",
        ):
            smoke_workspace.validate_repository_identity(target, run_id)

        self.git(
            target, "config", "--local",
            smoke_workspace.SMOKE_RUN_ID_CONFIG, run_id
        )
        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "baseline identity does not match",
        ):
            smoke_workspace.validate_repository_identity(
                target, run_id, "0" * 40
            )

    def test_repository_identity_rejects_history_rewritten_away_from_stamped_baseline(self):
        run_id = "SMOKE-FAST-owner-20261004T102400Z-12345678"
        target = self.root / "owned-rewritten"
        target.mkdir()
        self.git(target, "init")
        self.git(target, "config", "user.name", "Test")
        self.git(target, "config", "user.email", "test@example.invalid")
        (target / "README.md").write_text("baseline\n", encoding="utf-8")
        self.git(target, "add", "-A")
        self.git(target, "commit", "-m", "baseline")
        self.git(target, "branch", "-M", "smoke-run")
        baseline = self.git(target, "rev-parse", "HEAD")
        smoke_workspace._stamp_repository_identity(target, run_id, baseline)

        self.git(target, "checkout", "--orphan", "rewritten")
        self.git(target, "rm", "-rf", ".")
        (target / "README.md").write_text("unrelated history\n", encoding="utf-8")
        self.git(target, "add", "-A")
        self.git(target, "commit", "-m", "unrelated")
        self.git(target, "branch", "-M", "smoke-run")

        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "merge-base --is-ancestor",
        ):
            smoke_workspace.validate_repository_identity(target, run_id)

    def test_repository_identity_rejects_fake_git_directory_inside_parent_repository(self):
        parent = self.root / "enclosing"
        parent.mkdir()
        self.git(parent, "init")
        self.git(parent, "config", "user.name", "Test")
        self.git(parent, "config", "user.email", "test@example.invalid")
        (parent / "README.md").write_text("parent repository\n", encoding="utf-8")
        self.git(parent, "add", "-A")
        self.git(parent, "commit", "-m", "parent baseline")
        baseline = self.git(parent, "rev-parse", "HEAD")

        run_id = "SMOKE-FAST-fakegit-20261004T102400Z-12345678"
        target = parent / "plain-child"
        git_dir = target / ".git"
        git_dir.mkdir(parents=True)
        (git_dir / "HEAD").write_text("ref: refs/heads/smoke-run\n", encoding="utf-8")
        (git_dir / "config").write_text(
            "[subhforge]\n"
            "    smokeRunId = {}\n"
            "    smokeBaselineHead = {}\n".format(run_id, baseline),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(
            smoke_workspace.SmokeWorkspaceError,
            "merge-base --is-ancestor",
        ):
            smoke_workspace.validate_repository_identity(target, run_id)

    def test_repository_identity_tolerates_unrelated_legal_git_config_shapes(self):
        run_id = "SMOKE-FAST-config-20261004T102400Z-12345678"
        target = self.root / "owned-config"
        target.mkdir()
        self.git(target, "init")
        self.git(target, "config", "user.name", "Test")
        self.git(target, "config", "user.email", "test@example.invalid")
        (target / "README.md").write_text("owned repository\n", encoding="utf-8")
        self.git(target, "add", "-A")
        self.git(target, "commit", "-m", "baseline")
        self.git(target, "branch", "-M", "smoke-run")
        baseline = self.git(target, "rev-parse", "HEAD")
        smoke_workspace._stamp_repository_identity(target, run_id, baseline)

        config = target / ".git" / "config"
        with config.open("a", encoding="utf-8") as handle:
            handle.write(
                "\n[remote \"origin\"]\n"
                "    fetch = +refs/heads/*:refs/remotes/origin/*\n"
                "    fetch = +refs/tags/*:refs/tags/*\n"
                "[custom]\n"
                "    valueless\n"
                "[remote \"origin\"]\n"
                "    fetch = +refs/notes/*:refs/notes/*\n"
            )

        identity = smoke_workspace.validate_repository_identity(target, run_id)
        self.assertEqual(run_id, identity["run_id"])
        self.assertEqual(baseline, identity["baseline_head"])

    def test_create_rejects_generated_run_id_that_is_not_a_confined_identifier(self):
        escaped = self.root / "escaped-smoke-run"
        with mock.patch.object(
            smoke_workspace,
            "_new_run_id",
            return_value="../escaped-smoke-run",
        ):
            with self.assertRaises(smoke_workspace.SmokeWorkspaceError):
                smoke_workspace.create_workspace(
                    self.source, self.commit, "FAST", "fast-micro-library"
                )
        self.assertFalse(escaped.exists())

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
