"""Tests for deterministic smoke bootstrap."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_bootstrap
import smoke_state


class SmokeBootstrapTests(unittest.TestCase):
    def test_bootstrap_initializes_state_budget_and_parity(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "docs/verification/smoke").mkdir(parents=True)
            a = repo / "a.md"
            b = repo / "b.md"
            optional = repo / "missing.md"
            a.write_text("same\n", encoding="utf-8")
            b.write_text("same\n", encoding="utf-8")
            run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"

            result = smoke_bootstrap.bootstrap(
                repo,
                run_id,
                "FULL",
                "full-minimal-api",
                "abc123",
                "base123",
                [a, b],
                [optional],
            )

            self.assertTrue(Path(result["state_path"]).is_file())
            state = smoke_state.load(repo, run_id)
            parity = state["context_index"]["contract_parity"]
            self.assertTrue(parity["contract_equal"])
            self.assertEqual([str(optional.resolve())], parity["missing_optional"])
            self.assertTrue((repo / f"docs/verification/smoke/{run_id}.budget.json").is_file())

    def test_bootstrap_refuses_required_contract_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            (repo / "docs/verification/smoke").mkdir(parents=True)
            a = repo / "a.md"
            b = repo / "b.md"
            a.write_text("one\n", encoding="utf-8")
            b.write_text("two\n", encoding="utf-8")

            with self.assertRaises(smoke_bootstrap.SmokeBootstrapError):
                smoke_bootstrap.bootstrap(
                    repo,
                    "SMOKE-FULL-test-20260927T000000Z-87654321",
                    "FULL",
                    "full-minimal-api",
                    "abc123",
                    "base123",
                    [a, b],
                    [],
                )


if __name__ == "__main__":
    unittest.main()
