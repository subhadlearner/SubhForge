"""Tests for deterministic review freshness preflight."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import review_preflight
import implementation_state


class ReviewPreflightTests(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        implementation_state.git(repo, "init")
        implementation_state.git(repo, "config", "user.email", "subhforge@test.local")
        implementation_state.git(repo, "config", "user.name", "SubhForge Test")
        (repo / "app.py").write_text("print('ok')\n", encoding="utf-8")
        implementation_state.git(repo, "add", "app.py")
        implementation_state.git(repo, "commit", "-m", "baseline")
        return repo

    def test_match_when_manifest_is_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self._repo(Path(temp))
            base = implementation_state.git(repo, "rev-parse", "HEAD").strip().decode("ascii")
            (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
            manifest = implementation_state.canonical_manifest(repo, base)
            evidence_dir = repo / "docs" / "verification"
            evidence_dir.mkdir(parents=True)
            path = evidence_dir / "VERIFY-SPEC-001-001.manifest"
            path.write_bytes(manifest)

            result = review_preflight.review_preflight(repo, base, path)

            self.assertEqual("MATCH", result["freshness"])
            self.assertTrue(result["canonical_manifest_equal"])
            self.assertNotIn("docs/verification/", implementation_state.canonical_manifest(repo, base).decode())

    def test_mismatch_after_identity_change(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = self._repo(Path(temp))
            base = implementation_state.git(repo, "rev-parse", "HEAD").strip().decode("ascii")
            (repo / "app.py").write_text("print('changed')\n", encoding="utf-8")
            evidence_dir = repo / "docs" / "verification"
            evidence_dir.mkdir(parents=True)
            path = evidence_dir / "VERIFY-SPEC-001-001.manifest"
            path.write_bytes(implementation_state.canonical_manifest(repo, base))
            (repo / "app.py").write_text("print('changed again')\n", encoding="utf-8")

            result = review_preflight.review_preflight(repo, base, path)

            self.assertEqual("MISMATCH", result["freshness"])
            self.assertFalse(result["canonical_manifest_equal"])


if __name__ == "__main__":
    unittest.main()
