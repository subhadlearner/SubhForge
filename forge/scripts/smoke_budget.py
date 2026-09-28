#!/usr/bin/env python3
"""Deterministic elapsed-time budget and stage timing for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_handoff


class BudgetError(RuntimeError):
    pass


RootedGuard = Callable[[Path, str], object]


def _require_rooted(repo: Path, run_id: str, guard: Optional[RootedGuard]) -> None:
    """Stage timing brackets every smoke child; refuse it outside a rooted session."""
    try:
        (guard or smoke_handoff.assert_rooted)(repo, run_id)
    except smoke_handoff.SmokeHandoffError as exc:
        raise BudgetError(
            "Smoke stage timing requires the rooted disposable smoke session: {}".format(exc)
        ) from exc


def _state_path(repo: Path, run_id: str) -> Path:
    if not run_id.startswith("SMOKE-") or not all(c.isalnum() or c == "-" for c in run_id):
        raise BudgetError("Invalid run ID")
    folder = repo.resolve() / "docs" / "verification" / "smoke"
    if not folder.is_dir():
        raise BudgetError("Smoke evidence directory is missing")
    return folder / (run_id + ".budget.json")


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _load(repo: Path, run_id: str) -> tuple[Path, dict]:
    path = _state_path(repo, run_id)
    if not path.exists():
        raise BudgetError("Budget state is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    if "started_at_utc" not in data:
        raise BudgetError("Budget start timestamp is missing")
    invocations = data.setdefault("stage_invocations", [])
    if not isinstance(invocations, list):
        raise BudgetError("stage_invocations must be a list")
    return path, data


def _save(path: Path, data: dict) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _aware_timestamp(value: str, field: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise BudgetError(f"{field} must be timezone-aware")
    return parsed


def _validate_stage(stage: str) -> None:
    if not stage or not all(c.isalnum() or c in "-_" for c in stage):
        raise BudgetError("Invalid stage ID")


def start(repo: Path, run_id: str, now: Optional[dt.datetime] = None) -> dict:
    path = _state_path(repo, run_id)
    if path.exists():
        raise BudgetError("Budget state already exists")
    current = now or _now()
    if current.tzinfo is None:
        raise BudgetError("Budget start timestamp must be timezone-aware")
    data = {"started_at_utc": current.isoformat(), "stage_invocations": []}
    _save(path, data)
    return data


def check(repo: Path, run_id: str, limit_minutes: int = 30,
          now: Optional[dt.datetime] = None) -> dict:
    _, data = _load(repo, run_id)
    started = _aware_timestamp(data["started_at_utc"], "Budget start timestamp")
    current = now or _now()
    elapsed = max(0.0, (current - started).total_seconds())
    limit = float(limit_minutes * 60)
    exceeded = elapsed >= limit
    return {
        "started_at_utc": started.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "limit_seconds": int(limit),
        "remaining_seconds": round(max(0.0, limit - elapsed), 3),
        "result": "PERFORMANCE_BUDGET_EXCEEDED" if exceeded else "WITHIN_BUDGET",
    }


def stage_start(repo: Path, run_id: str, stage: str, model: str,
                now: Optional[dt.datetime] = None, *,
                rooted_guard: Optional[RootedGuard] = None) -> dict:
    _validate_stage(stage)
    if not model or not isinstance(model, str):
        raise BudgetError("Model is required")
    _require_rooted(repo, run_id, rooted_guard)
    path, data = _load(repo, run_id)
    invocations = data["stage_invocations"]
    if any(item.get("ended_at_utc") is None for item in invocations):
        raise BudgetError("A smoke stage invocation is already active")
    sequence = 1 + sum(1 for item in invocations if item.get("stage") == stage)
    invocation_id = f"{stage}-{sequence:03d}"
    current = now or _now()
    if current.tzinfo is None:
        raise BudgetError("Stage start timestamp must be timezone-aware")
    item = {
        "invocation_id": invocation_id,
        "stage": stage,
        "model": model,
        "started_at_utc": current.isoformat(),
        "ended_at_utc": None,
        "elapsed_seconds": None,
    }
    invocations.append(item)
    _save(path, data)
    return dict(item)


def stage_end(repo: Path, run_id: str, invocation_id: str,
              now: Optional[dt.datetime] = None, *,
              rooted_guard: Optional[RootedGuard] = None) -> dict:
    _require_rooted(repo, run_id, rooted_guard)
    path, data = _load(repo, run_id)
    matches = [item for item in data["stage_invocations"]
               if item.get("invocation_id") == invocation_id]
    if len(matches) != 1:
        raise BudgetError("Unknown or ambiguous stage invocation ID")
    item = matches[0]
    if item.get("ended_at_utc") is not None:
        raise BudgetError("Stage invocation is already complete")
    started = _aware_timestamp(item["started_at_utc"], "Stage start timestamp")
    current = now or _now()
    if current.tzinfo is None:
        raise BudgetError("Stage end timestamp must be timezone-aware")
    elapsed = max(0.0, (current - started).total_seconds())
    item["ended_at_utc"] = current.isoformat()
    item["elapsed_seconds"] = round(elapsed, 3)
    _save(path, data)
    return dict(item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("start")
    check_parser = actions.add_parser("check")
    check_parser.add_argument("--limit-minutes", type=int, default=30)
    stage_start_parser = actions.add_parser("stage-start")
    stage_start_parser.add_argument("--stage", required=True)
    stage_start_parser.add_argument("--model", required=True)
    stage_end_parser = actions.add_parser("stage-end")
    stage_end_parser.add_argument("--invocation-id", required=True)
    args = parser.parse_args()
    try:
        if args.action == "start":
            result = start(args.repo, args.run_id)
        elif args.action == "check":
            result = check(args.repo, args.run_id, args.limit_minutes)
        elif args.action == "stage-start":
            result = stage_start(args.repo, args.run_id, args.stage, args.model)
        else:
            result = stage_end(args.repo, args.run_id, args.invocation_id)
        print(json.dumps({"ok": True, **result}))
        return 3 if result.get("result") == "PERFORMANCE_BUDGET_EXCEEDED" else 0
    except (BudgetError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
