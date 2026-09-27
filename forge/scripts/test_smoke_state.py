"""Tests for structured smoke orchestration state."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_state


class SmokeStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"

    def test_init_and_targeted_update(self):
        created = smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        self.assertEqual("static-release-gate", created["current_stage"])
        updated = smoke_state.set_values(
            self.repo,
            self.run_id,
            {
                "current_stage": "architect",
                "completed_scenarios": ["static-release-gate", "grill", "prd"],
                "context_index": {
                    "prd": "docs/prd/PRD-001.md",
                    "architecture": "docs/architecture/ARCH-001.md",
                },
            },
        )
        self.assertEqual("architect", updated["current_stage"])
        self.assertEqual("docs/prd/PRD-001.md", updated["context_index"]["prd"])
        self.assertEqual(updated, smoke_state.load(self.repo, self.run_id))

    def test_immutable_identity_fields_fail_closed(self):
        smoke_state.init(
            self.repo, self.run_id, "FULL", "full-minimal-api", "abc123", "base123"
        )
        with self.assertRaises(smoke_state.SmokeStateError):
            smoke_state.set_values(self.repo, self.run_id, {"source_commit": "other"})


if __name__ == "__main__":
    unittest.main()
