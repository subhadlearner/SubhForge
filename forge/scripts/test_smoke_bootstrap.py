"""Tests for deterministic smoke bootstrap."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_bootstrap
import smoke_state


class SmokeBootstrapTests(unittest.TestCase):
    def _config_fixture(self, root: Path) -> Path:
        source = Path(__file__).resolve().parents[1]
        config = root / "config"
        for folder in ("commands", "agents", "contracts", "smoke"):
            shutil.copytree(source / folder, config / folder)
        (config / "scripts").mkdir()
        shutil.copy2(source / "scripts/smoke_handoff.py", config / "scripts/smoke_handoff.py")
        shutil.copy2(source / "scripts/smoke_mechanics.py", config / "scripts/smoke_mechanics.py")
        shutil.copy2(source / "scripts/smoke_resume.py", config / "scripts/smoke_resume.py")
        shutil.copy2(source / "scripts/smoke_reroute.py", config / "scripts/smoke_reroute.py")
        shutil.copy2(source / "AGENTS.md", config / "AGENTS.md")
        return config

    def _repo_fixture(self, root: Path, config: Path) -> tuple[Path, Path, Path]:
        repo = root / "repo"
        (repo / "docs/verification/smoke").mkdir(parents=True)
        project_contract = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
        project_contract.parent.mkdir(parents=True)
        shutil.copy2(config / "contracts/implementation-state-evidence-v1.md", project_contract)
        installed_contract = config / "contracts/implementation-state-evidence-v1.md"
        optional = repo / "missing.md"
        return repo, installed_contract, optional

    def test_bootstrap_initializes_state_budget_parity_and_release_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self._config_fixture(root)
            repo, installed_contract, optional = self._repo_fixture(root, config)
            project_contract = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
            run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"

            result = smoke_bootstrap.bootstrap(
                repo, run_id, "FULL", "full-minimal-api", "abc123", "base123",
                [installed_contract, project_contract], [optional], config_root=config,
                source=Path(__file__).resolve().parents[2],
            )

            self.assertTrue(Path(result["state_path"]).is_file())
            self.assertTrue(result["release_gate"]["ok"])
            state = smoke_state.load(repo, run_id)
            parity = state["context_index"]["contract_parity"]
            self.assertTrue(parity["contract_equal"])
            self.assertEqual([str(optional.resolve())], parity["missing_optional"])
            self.assertEqual(["static-release-gate"], state["completed_scenarios"])
            self.assertEqual("grill", state["current_stage"])
            self.assertNotIn("static-release-gate", state["pending_scenarios"])
            self.assertTrue((repo / f"docs/verification/smoke/{run_id}.budget.json").is_file())

    def test_bootstrap_refuses_required_contract_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self._config_fixture(root)
            repo = root / "repo"
            (repo / "docs/verification/smoke").mkdir(parents=True)
            a = repo / "a.md"
            b = repo / "b.md"
            a.write_text("one\n", encoding="utf-8")
            b.write_text("two\n", encoding="utf-8")

            with self.assertRaises(smoke_bootstrap.SmokeBootstrapError):
                smoke_bootstrap.bootstrap(
                    repo, "SMOKE-FULL-test-20260927T000000Z-87654321",
                    "FULL", "full-minimal-api", "abc123", "base123",
                    [a, b], [], config_root=config,
                source=Path(__file__).resolve().parents[2],
            )

    def test_bootstrap_persists_blocked_state_when_static_gate_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = self._config_fixture(root)
            repo, installed_contract, _ = self._repo_fixture(root, config)
            project_contract = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
            worker = config / "agents/planning-worker.md"
            worker.write_text(
                worker.read_text(encoding="utf-8").replace("`RECONCILE_ONLY`", "reconcile-only"),
                encoding="utf-8",
            )
            run_id = "SMOKE-FULL-test-20260927T000000Z-blocked12"

            result = smoke_bootstrap.bootstrap(
                repo, run_id, "FULL", "full-minimal-api", "abc123", "base123",
                [installed_contract, project_contract], [], config_root=config,
                source=Path(__file__).resolve().parents[2],
            )

            self.assertFalse(result["release_gate"]["ok"])
            state = smoke_state.load(repo, run_id)
            self.assertEqual("BLOCKED", state["state"])
            self.assertEqual("STATIC_RELEASE_GATE_FAILED", state["blocker"]["code"])
            self.assertNotIn("static-release-gate", state["completed_scenarios"])


if __name__ == "__main__":
    unittest.main()
