"""Tests for path-aware static smoke gates."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_static


class SmokeStaticTests(unittest.TestCase):
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
