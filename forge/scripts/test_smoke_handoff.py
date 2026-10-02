"""Tests for deterministic Kilo smoke workspace handoff and rooted-session proof."""

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget
import smoke_handoff
import smoke_segments
import smoke_state


class SmokeHandoffTests(unittest.TestCase):
    def git(self, repo: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", *args], cwd=str(repo), text=True
        ).strip()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.run_id = "SMOKE-FULL-full-minimal-api-20260927T000000Z-12345678"
        self.repo = self.root / self.run_id
        self.repo.mkdir()
        self.source_root = self.root / "SubhForge"
        self.source_root.mkdir()

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
        started = "2026-09-27T00:00:00+00:00"
        smoke_budget.start(
            self.repo,
            self.run_id,
            dt.datetime.fromisoformat(started),
        )
        smoke_segments.pin_qualification(
            self.repo,
            self.run_id,
            None,
            started,
            source_fingerprint="a" * 64,
        )
        smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "context_index": {
                    "budget_started_at_utc": started,
                    "contract_parity": {"contract_equal": True},
                },
                "completed_scenarios": ["static-release-gate"],
                "current_stage": "grill",
            },
        )

        original_which = shutil.which

        def fake_which(name):
            if name == "kilo":
                return "kilo-test"
            return original_which(name)

        patcher = mock.patch("smoke_handoff.shutil.which", side_effect=fake_which)
        patcher.start()
        self.addCleanup(patcher.stop)

    def handoff(self, env=None, **kwargs):
        """Run a live handoff with a recording runner; return (result, calls)."""
        calls = []

        def runner(command, cwd, env):
            calls.append({"command": command, "cwd": cwd, "env": env})
            return SimpleNamespace(returncode=0)

        kwargs.setdefault("current_root", self.source_root)
        result = smoke_handoff.ensure_rooted(
            self.repo, self.run_id, runner=runner, env=env or {}, **kwargs
        )
        return result, calls

    def rooted_env(self):
        _, calls = self.handoff()
        return calls[0]["env"]

    # --- handoff launch -------------------------------------------------

    def test_dry_run_builds_rooted_smoke_continuation_without_launching(self):
        result = smoke_handoff.ensure_rooted(
            self.repo,
            self.run_id,
            dry_run=True,
            current_root=self.source_root,
            env={},
        )

        self.assertEqual("NEEDS_HANDOFF", result["result"])
        command = result["command"]
        self.assertEqual("kilo-test", command[0])
        self.assertEqual(str(self.repo), command[command.index("--dir") + 1])
        self.assertEqual("smoke-orchestrator", command[command.index("--agent") + 1])
        self.assertEqual("openai/gpt-5.6-luna", command[command.index("--model") + 1])
        self.assertEqual("smoke", command[command.index("--command") + 1])
        self.assertIn("--auto", command)
        self.assertEqual("RESUME {}".format(self.run_id), command[-1])
        self.assertFalse(
            smoke_handoff.handoff_record_path(self.repo, self.run_id).exists(),
            "dry-run must not mint a handoff token",
        )

    def test_live_handoff_roots_child_process_in_disposable_repo(self):
        result, calls = self.handoff()

        self.assertEqual("HANDOFF_COMPLETE", result["result"])
        self.assertEqual(1, len(calls))
        call = calls[0]
        self.assertEqual(str(self.repo), call["cwd"])
        self.assertEqual(str(self.repo), call["command"][call["command"].index("--dir") + 1])
        env = call["env"]
        self.assertEqual(self.run_id, env[smoke_handoff.ENV_RUN_ID])
        self.assertEqual(str(self.repo), env[smoke_handoff.ENV_RUN_DIRECTORY])
        self.assertGreaterEqual(len(env[smoke_handoff.ENV_HANDOFF_TOKEN]), 64)

    def test_handoff_record_stores_only_token_digest(self):
        env = self.rooted_env()
        record = json.loads(
            smoke_handoff.handoff_record_path(self.repo, self.run_id).read_text(encoding="utf-8")
        )
        token = env[smoke_handoff.ENV_HANDOFF_TOKEN]

        self.assertNotIn(token, json.dumps(record))
        self.assertEqual(smoke_handoff._token_digest(token), record["token_sha256"])
        self.assertEqual(str(self.repo), record["run_directory"])

    def test_autonomous_overlay_disables_paid_claude_and_denies_source_checkout(self):
        env = self.rooted_env()
        overlay = json.loads(env["KILO_CONFIG_CONTENT"])

        for name in ("adversary-opus", "adversary-sonnet"):
            self.assertIs(True, overlay["agent"][name]["disable"])
        external = overlay["permission"]["external_directory"]
        source = self.source_root.as_posix()
        self.assertEqual("deny", external[source])
        self.assertEqual("deny", external[source + "/*"])
        self.assertNotIn(self.repo.as_posix(), external)
        self.assertNotIn("allow", external.values())
        self.assertNotIn("ask", external.values())

    def test_install_provenance_source_checkout_is_protected(self):
        config = self.root / "config"
        config.mkdir()
        recorded_source = self.root / "RecordedSource"
        recorded_source.mkdir()
        (config / smoke_handoff.INSTALL_MANIFEST).write_text(
            json.dumps({"source_checkout_path": str(recorded_source)}), encoding="utf-8"
        )

        result, calls = self.handoff(config_dir=config)

        protected = result["protected_source_paths"]
        self.assertIn(str(recorded_source), protected)
        self.assertIn(str(self.source_root), protected)
        self.assertEqual(str(config), calls[0]["env"]["KILO_CONFIG_DIR"])

    def test_run_directory_inside_source_checkout_is_rejected(self):
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            self.handoff(current_root=self.root)

    def test_unknown_source_checkout_fails_closed(self):
        with mock.patch("smoke_handoff.installed_config_dir", return_value=None):
            with self.assertRaises(smoke_handoff.SmokeHandoffError):
                self.handoff(current_root=self.repo)

    def test_partial_inherited_marker_fails_closed_instead_of_relaunching(self):
        partial = {smoke_handoff.ENV_HANDOFF_TOKEN: "stale", "KEEP": "1"}
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            self.handoff(env=partial)
        self.assertFalse(smoke_handoff.handoff_record_path(self.repo, self.run_id).exists())

    def test_failed_nested_kilo_run_fails_closed(self):
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                current_root=self.source_root,
                env={},
                runner=lambda command, cwd, env: SimpleNamespace(returncode=1),
            )

    # --- rooted-session proof ------------------------------------------

    def test_marked_session_in_disposable_repo_is_already_rooted_without_relaunch(self):
        env = self.rooted_env()
        launched = []

        result = smoke_handoff.ensure_rooted(
            self.repo,
            self.run_id,
            current_root=self.repo,
            env=env,
            runner=lambda *args, **kwargs: launched.append(args),
        )

        self.assertEqual("ALREADY_ROOTED", result["result"])
        self.assertIsNone(result["command"])
        self.assertEqual([], launched)

    def test_cwd_in_disposable_repo_without_marker_is_not_rooted(self):
        # Regression: shell cwd alone does not prove the Kilo project root.
        config = self.root / "config"
        config.mkdir()
        (config / smoke_handoff.INSTALL_MANIFEST).write_text(
            json.dumps({"source_checkout_path": str(self.source_root)}), encoding="utf-8"
        )
        result = smoke_handoff.ensure_rooted(
            self.repo,
            self.run_id,
            dry_run=True,
            current_root=self.repo,
            env={},
            config_dir=config,
        )
        self.assertEqual("NEEDS_HANDOFF", result["result"])
        self.assertEqual([str(self.source_root)], result["protected_source_paths"])

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(self.repo, self.run_id, env={}, cwd=self.repo)

    def test_marked_session_outside_disposable_repo_refuses_nested_handoff(self):
        env = self.rooted_env()
        launched = []

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                current_root=self.source_root,
                env=env,
                runner=lambda *args, **kwargs: launched.append(args),
            )
        self.assertEqual([], launched)

    def test_assert_rooted_accepts_current_handoff(self):
        env = self.rooted_env()
        result = smoke_handoff.assert_rooted(self.repo, self.run_id, env=env, cwd=self.repo)
        self.assertEqual("ROOTED", result["result"])

    def test_assert_rooted_accepts_nested_cwd_inside_disposable_repo(self):
        env = self.rooted_env()
        nested = self.repo / "docs"
        result = smoke_handoff.assert_rooted(self.repo, self.run_id, env=env, cwd=nested)
        self.assertEqual("ROOTED", result["result"])

    def test_assert_rooted_rejects_source_root_cwd_even_with_valid_token(self):
        env = self.rooted_env()
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(
                self.repo, self.run_id, env=env, cwd=self.source_root
            )

    def test_assert_rooted_rejects_marker_for_other_run(self):
        env = dict(self.rooted_env())
        env[smoke_handoff.ENV_RUN_ID] = "SMOKE-FULL-other-20260927T000000Z-87654321"
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(self.repo, self.run_id, env=env, cwd=self.repo)

    def test_assert_rooted_rejects_marker_for_other_directory(self):
        env = dict(self.rooted_env())
        env[smoke_handoff.ENV_RUN_DIRECTORY] = str(self.source_root)
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(self.repo, self.run_id, env=env, cwd=self.repo)

    def test_assert_rooted_rejects_forged_token(self):
        env = dict(self.rooted_env())
        env[smoke_handoff.ENV_HANDOFF_TOKEN] = "0" * 64
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(self.repo, self.run_id, env=env, cwd=self.repo)

    def test_new_handoff_invalidates_previous_rooted_session(self):
        first = self.rooted_env()
        second = self.rooted_env()

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(self.repo, self.run_id, env=first, cwd=self.repo)
        smoke_handoff.assert_rooted(self.repo, self.run_id, env=second, cwd=self.repo)

    def test_assert_rooted_rejects_missing_handoff_record(self):
        env = self.rooted_env()
        smoke_handoff.handoff_record_path(self.repo, self.run_id).unlink()
        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.assert_rooted(self.repo, self.run_id, env=env, cwd=self.repo)

    def test_assert_rooted_cli_fails_closed_without_marker(self):
        script = Path(smoke_handoff.__file__).resolve()
        env = {key: value for key, value in os.environ.items()
               if key not in smoke_handoff.MARKER_ENV}
        proc = subprocess.run(
            [sys.executable, str(script), "--repo", str(self.repo),
             "--run-id", self.run_id, "assert-rooted"],
            cwd=str(self.repo), env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True,
        )
        self.assertEqual(2, proc.returncode, proc.stderr)
        self.assertFalse(json.loads(proc.stdout)["ok"])

    # --- workspace validation ------------------------------------------

    def test_wrong_branch_is_rejected_before_kilo_launch(self):
        self.git(self.repo, "switch", "-c", "not-smoke-run")

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                dry_run=True,
                current_root=self.source_root,
                env={},
            )

    def test_run_directory_name_must_match_run_id(self):
        wrong = self.root / "different-name"
        wrong.mkdir()

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.validate_workspace(wrong, self.run_id)

    def test_incomplete_static_gate_is_rejected_before_kilo_launch(self):
        state_path = (
            self.repo
            / "docs/verification/smoke"
            / "{}.state.json".format(self.run_id)
        )
        state = smoke_state.load(self.repo, self.run_id)
        state["completed_scenarios"] = []
        smoke_state._save(state_path, state)

        with self.assertRaises(smoke_handoff.SmokeHandoffError):
            smoke_handoff.ensure_rooted(
                self.repo,
                self.run_id,
                dry_run=True,
                current_root=self.source_root,
                env={},
            )

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
                current_root=self.source_root,
                env={},
            )


if __name__ == "__main__":
    unittest.main()
