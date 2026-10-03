"""Tests for the repository-confined file digest helper."""

import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import file_digest


class FileDigestTests(unittest.TestCase):
    def test_digest_returns_exact_repo_relative_sha256(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            target = repo / "docs" / "verification" / "report.md"
            target.parent.mkdir(parents=True)
            target.write_bytes(b"exact-report-bytes\n")

            result = file_digest.digest(
                repo, Path("docs/verification/report.md")
            )

            self.assertEqual(
                "docs/verification/report.md", result["path"]
            )
            self.assertEqual(
                hashlib.sha256(b"exact-report-bytes\n").hexdigest(),
                result["sha256"],
            )

    def test_digest_rejects_hidden_smoke_and_unrelated_repo_files(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp) / "repo"
            repo.mkdir()
            hidden = repo / "docs/verification/smoke/key.json"
            hidden.parent.mkdir(parents=True)
            hidden.write_text('{"secret":"value"}\n', encoding="utf-8")
            source = repo / "src/app.py"
            source.parent.mkdir(parents=True)
            source.write_text("print('x')\n", encoding="utf-8")

            with self.assertRaises(file_digest.FileDigestError):
                file_digest.digest(repo, Path("docs/verification/smoke/key.json"))
            with self.assertRaises(file_digest.FileDigestError):
                file_digest.digest(repo, Path("src/app.py"))

    def test_digest_rejects_path_escape_and_missing_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            repo.mkdir()
            outside = root / "outside.txt"
            outside.write_text("outside\n", encoding="utf-8")

            with self.assertRaises(file_digest.FileDigestError):
                file_digest.digest(repo, outside)
            with self.assertRaises(file_digest.FileDigestError):
                file_digest.digest(repo, Path("missing.txt"))


if __name__ == "__main__":
    unittest.main()
