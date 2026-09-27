"""Tests for deterministic Kilo smoke workspace handoff."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_handoff
import smoke_state


class SmokeHandoffTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=str(repo), text=True
        ).strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_id = "SMOKE-FULL-full-minimal-api-20260927T000000Z-12345678"
        self.repo = self.root / self.run_id
        self.repo.mkdir()

        self.git(self.repo, "init")
        self.git(self.repo, "config", "user.name", "Test")
        self.git(self.repo, "config", "user.email", "test@example.invalid")
        self.git(self.repo, "switch", "-c", "smoke-run")
        (self.repo / "README.md").write_text("fixture\n", encoding="utf-8")
        self.git(self.repo, "add", "-A")
        self.git(self.repo, "commit", "-m", "baseline")

        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        smoke_state.init(
            self.repo,
            self.run_id,
            "FULL",
            "full-minimal-api",
            "source123",
            self.git(self.repo, "rev-parse", "HEAD"),
        )

    def test_already_rooted_does_not_launch_nested_kilo(self):
        result = smoke_handoff.ensure_rooted(
            self.repo,
            self.run_id,
            current_root=self.repo,
        )

        self.assertEqual("ALREADY_ROOTED", result["result"])
        self.assertIsNone(result["command"])

    def test_dry_run_builds_rooted_smoke_continuation_without_launching(self):
        original_which = shutil.which

        def fake_which(name):
            if name == "kilo":
                return "kilo-test"
            return original_which(name)

        source_root = self.root / "SubhForge"
        source_root.mkdir()
        with mock.patch("smoke_handoff.shutil.which", side_effect=fake_which):
            result = smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                dry_run=True,
                current_root=source_root,
            )

        self.assertEqual("NEEDS_HANDOFF", result["result"])
        command = result["command"]
        self.assertEqual("kilo-test", command[0])
        self.assertEqual(str(self.repo.resolve()), command[command.index("--dir") + 1])
        self.assertEqual(
            "smoke-orchestrator", command[command.index("--agent") + 1]
        )
        self.assertEqual(
            "openai/gpt-5.6-luna", command[command.index("--model") + 1]
        )
        self.assertEqual("smoke", command[command.index("--command") + 1])
        self.assertIn("--auto", command)
        self.assertEqual("RESUME {}".format(self.run_id), command[-1])

    def test_live_handoff_uses_disposable_repo_as_process_cwd(self):
        original_which = shutil.which
        calls = []

        def fake_which(name):
            if name == "kilo":
                return "kilo-test"
            return original_which(name)

        def runner(command, cwd):
            calls.append((command, cwd))
            return SimpleNamespace(returncode=0)

        source_root = self.root / "SubhForge"
        source_root.mkdir()
        with mock.patch("smoke_handoff.shutil.which", side_effect=fake_which):
            result = smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                current_root=source_root,
                runner=runner,
            )

        self.assertEqual("HANDOFF_COMPLETE", result["result"])
        self.assertEqual(1, len(calls))
        command, cwd = calls[0]
        self.assertEqual(str(self.repo.resolve()), cwd)
        self.assertEqual(str(self.repo.resolve()), command[command.index("--dir") + 1])

    def test_wrong_branch_is_rejected_before_kilo_launch(self):
        self.git(self.repo, "switch", "-c", "not-smoke-run")

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                dry_run=True,
                current_root=self.root,
            )

    def test_run_directory_name_must_match_run_id(self):
        wrong = self.root / "different-name"
        self.repo.rename(wrong)

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.validate_workspace(wrong, self.run_id)

    def test_missing_canonical_state_is_rejected(self):
        state_path = (
            self.repo
            / "docs/verification/smoke"
            / "{}.state.json".format(self.run_id)
        )
        state_path.unlink()

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                dry_run=True,
                current_root=self.root,
            )

    def test_failed_nested_kilo_run_fails_closed(self):
        original_which = shutil.which

        def fake_which(name):
            if name == "kilo":
                return "kilo-test"
            return original_which(name)

        with mock.patch("smoke_handoff.shutil.which", side_effect=fake_which):
            with self.assertRaises(smoke_handoff.SmokeHandoffError):
                smoke_handoff.ensure_rooted(
                    self.repo,
                    self.run_id,
                    current_root=self.root,
                    runner=lambda command, cwd: SimpleNamespace(returncode=1),
                )


if __name__ == "__main__":
    unittest.main()
