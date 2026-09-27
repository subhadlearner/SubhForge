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

            second = pim.prepare(repo, contract)
            self.assertFalse(second["contract_copied"])
            self.assertEqual([], second["created_directories"])
            self.assertEqual(first["contract_sha256"], second["contract_sha256"])


if __name__ == "__main__":
    unittest.main()
