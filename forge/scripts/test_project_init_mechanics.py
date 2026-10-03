"""Tests for deterministic project-init mechanics."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_init_mechanics as pim


class ProjectInitMechanicsTests(unittest.TestCase):
    def test_prepare_creates_dirs_and_synchronizes_contract_idempotently(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "project"
            repo.mkdir()
            contract = root / "contract.md"
            contract.write_text("contract-v1\n", encoding="utf-8")

            first = pim.prepare(repo, contract)
            self.assertTrue((repo / pim.CONTRACT_DEST).is_file())
            self.assertTrue(first["contract_copied"])
            self.assertIn("docs/specs", first["created_directories"])
            self.assertTrue(
                (repo / "docs/verification/waiver-refusals").is_dir()
            )

            second = pim.prepare(repo, contract)
            self.assertFalse(second["contract_copied"])
            self.assertEqual([], second["created_directories"])
            self.assertEqual(first["contract_sha256"], second["contract_sha256"])

    def test_prepare_writes_exact_waiver_policy_trace_idempotently(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "project"
            repo.mkdir()
            contract = root / "contract.md"
            contract.write_text("contract-v1\n", encoding="utf-8")
            agents = repo / "AGENTS.md"
            agents.write_text("# Project Rules\n", encoding="utf-8")
            policy = repo / "docs/workflow/H08B-FIXTURE-WAIVER-POLICY.json"
            policy.parent.mkdir(parents=True)
            policy.write_text(
                '{"non_waivable_failure_types":["BEHAVIORAL_TEST"],'
                '"waivable_failure_types":["DOCUMENTATION_QUALITY","LINT_QUALITY"]}\n',
                encoding="utf-8",
            )

            first = pim.prepare(
                repo,
                contract,
                Path("docs/workflow/H08B-FIXTURE-WAIVER-POLICY.json"),
            )
            text = agents.read_text(encoding="utf-8")
            self.assertIn(
                "Waiver Policy Source: docs/workflow/H08B-FIXTURE-WAIVER-POLICY.json",
                text,
            )
            self.assertIn(
                "Waiver Policy SHA-256: {}".format(pim.sha256(policy)),
                text,
            )
            self.assertIn(
                "Non-waivable Failure Types: BEHAVIORAL_TEST",
                text,
            )
            self.assertIn(
                "Waivable Failure Types: DOCUMENTATION_QUALITY, LINT_QUALITY",
                text,
            )
            self.assertTrue(first["waiver_policy_trace_updated"])

            second = pim.prepare(
                repo,
                contract,
                Path("docs/workflow/H08B-FIXTURE-WAIVER-POLICY.json"),
            )
            self.assertFalse(second["waiver_policy_trace_updated"])
            self.assertEqual(text, agents.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
