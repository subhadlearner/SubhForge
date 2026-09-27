"""Tests for path-aware static smoke gates."""

import sys
import tempfile
import unittest
import shutil
import json
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_static
import smoke_budget
import smoke_state


class SmokeStaticTests(unittest.TestCase):
    def _gate_fixture(self, root):
        source = Path(__file__).resolve().parents[1]
        config = root / "config"
        for folder in ("commands", "agents", "contracts", "smoke"):
            shutil.copytree(source / folder, config / folder)
        shutil.copy2(source / "AGENTS.md", config / "AGENTS.md")
        repo = root / "repo"
        evidence = repo / "docs/verification/smoke"
        evidence.mkdir(parents=True)
        project_contract = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
        project_contract.parent.mkdir(parents=True)
        shutil.copy2(config / "contracts/implementation-state-evidence-v1.md", project_contract)
        run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"
        smoke_state.init(repo, run_id, "FULL", "full-minimal-api", "sha", "base")
        smoke_budget.start(repo, run_id, now=dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=42))
        return config, repo, run_id

    def test_release_gate_persists_real_timing_and_scenarios(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertTrue(result["ok"], result["failures"])
            self.assertGreaterEqual(result["stage_metric"]["elapsed_seconds"], 42)
            state = smoke_state.load(repo, run_id)
            self.assertEqual(["static-release-gate"], state["completed_scenarios"])
            self.assertNotIn("static-release-gate", state["pending_scenarios"])
            self.assertEqual("grill", state["current_stage"])

    def test_release_gate_blocks_missing_mode_without_false_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            worker = config / "agents/planning-worker.md"
            worker.write_text(worker.read_text(encoding="utf-8").replace("`RECONCILE_ONLY`", "reconcile-only"), encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("planning:modes", result["failures"])
            state = smoke_state.load(repo, run_id)
            self.assertEqual("BLOCKED", state["state"])
            self.assertEqual([], state["completed_scenarios"])

    def test_release_gate_blocks_contract_drift_and_expired_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            project = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
            project.write_text("drift", encoding="utf-8")
            budget_path = repo / f"docs/verification/smoke/{run_id}.budget.json"
            budget_path.write_text(json.dumps({"started_at_utc": (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=31)).isoformat()}), encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertIn("contract:parity", result["failures"])
            self.assertIn("budget:30-minutes", result["failures"])

    def test_release_gate_detects_broken_agent_model_route(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            executor = config / "agents/smoke-executor.md"
            executor.write_text(executor.read_text(encoding="utf-8").replace(
                "model: deepseek/deepseek-flash", "model: anthropic/claude-sonnet"), encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertIn("routing:default", result["failures"])

    def test_required_equal_optional_missing_does_not_fail_parity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.md"
            b = root / "b.md"
            missing = root / "optional.md"
            a.write_text("same\n", encoding="utf-8")
            b.write_text("same\n", encoding="utf-8")

            result = smoke_static.contract_parity([a, b], [missing])

            self.assertTrue(result["contract_equal"])
            self.assertEqual([str(missing.resolve())], result["missing_optional"])

    def test_required_mismatch_fails_parity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.md"
            b = root / "b.md"
            a.write_text("one\n", encoding="utf-8")
            b.write_text("two\n", encoding="utf-8")

            result = smoke_static.contract_parity([a, b], [])

            self.assertFalse(result["contract_equal"])

    def test_missing_required_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.md"
            a.write_text("same\n", encoding="utf-8")

            with self.assertRaises(smoke_static.StaticGateError):
                smoke_static.contract_parity([a, root / "missing.md"], [])


if __name__ == "__main__":
    unittest.main()
