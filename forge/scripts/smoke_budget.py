#!/usr/bin/env python3
"""Deterministic elapsed-time budget guard for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


class BudgetError(RuntimeError):
    pass


def _state_path(repo: Path, run_id: str) -> Path:
    if not run_id.startswith("SMOKE-") or not all(c.isalnum() or c == "-" for c in run_id):
        raise BudgetError("Invalid run ID")
    folder = repo.resolve() / "docs" / "verification" / "smoke"
    if not folder.is_dir():
        raise BudgetError("Smoke evidence directory is missing")
    return folder / (run_id + ".budget.json")


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def start(repo: Path, run_id: str, now: dt.datetime | None = None) -> dict:
    path = _state_path(repo, run_id)
    if path.exists():
        raise BudgetError("Budget state already exists")
    current = now or _now()
    data = {"started_at_utc": current.isoformat()}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return data


def check(repo: Path, run_id: str, limit_minutes: int = 30,
          now: dt.datetime | None = None) -> dict:
    path = _state_path(repo, run_id)
    if not path.exists():
        raise BudgetError("Budget state is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    started = dt.datetime.fromisoformat(data["started_at_utc"])
    if started.tzinfo is None:
        raise BudgetError("Budget start timestamp must be timezone-aware")
    current = now or _now()
    elapsed = max(0.0, (current - started).total_seconds())
    limit = float(limit_minutes * 60)
    exceeded = elapsed >= limit
    return {
        "started_at_utc": started.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "limit_seconds": int(limit),
        "result": "PERFORMANCE_BUDGET_EXCEEDED" if exceeded else "WITHIN_BUDGET",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("start")
    check_parser = actions.add_parser("check")
    check_parser.add_argument("--limit-minutes", type=int, default=30)
    args = parser.parse_args()
    try:
        if args.action == "start":
            result = start(args.repo, args.run_id)
        else:
            result = check(args.repo, args.run_id, args.limit_minutes)
        print(json.dumps({"ok": True, **result}))
        return 3 if result.get("result") == "PERFORMANCE_BUDGET_EXCEEDED" else 0
    except (BudgetError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
