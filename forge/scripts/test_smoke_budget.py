"""Tests for deterministic smoke elapsed-time budget enforcement."""

import datetime as dt
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget


class SmokeBudgetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        (self.repo / "docs/verification/smoke").mkdir(parents=True)
        self.run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"
        self.started = dt.datetime(2026, 9, 27, 0, 0, tzinfo=dt.timezone.utc)

    def test_budget_boundary(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        before = smoke_budget.check(
            self.repo, self.run_id, 30,
            self.started + dt.timedelta(minutes=29, seconds=59),
        )
        self.assertEqual("WITHIN_BUDGET", before["result"])
        at_limit = smoke_budget.check(
            self.repo, self.run_id, 30,
            self.started + dt.timedelta(minutes=30),
        )
        self.assertEqual("PERFORMANCE_BUDGET_EXCEEDED", at_limit["result"])

    def test_duplicate_start_fails_closed(self):
        smoke_budget.start(self.repo, self.run_id, self.started)
        with self.assertRaises(smoke_budget.BudgetError):
            smoke_budget.start(self.repo, self.run_id, self.started)


if __name__ == "__main__":
    unittest.main()
