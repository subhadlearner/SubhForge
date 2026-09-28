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
import smoke_workspace


class BudgetError(RuntimeError):
    pass


RootedGuard = Callable[[Path, str], object]
SourceGuard = Callable[[Path, str], dict[str, object]]

INVOCATION_ACTIVE = "ACTIVE"
INVOCATION_COMPLETED = "COMPLETED"
INVOCATION_ABORTED = "ABORTED"
INVOCATION_INTERRUPTED = "INTERRUPTED"
INVOCATION_STATUSES = {
    INVOCATION_ACTIVE,
    INVOCATION_COMPLETED,
    INVOCATION_ABORTED,
    INVOCATION_INTERRUPTED,
}
CONTINUATION_BLOCKING_ABORT_REASONS = {"SOURCE_CHECKOUT_MUTATED"}


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
    data.setdefault("continuation_blocker", None)
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


def _is_source_fingerprint(source_fingerprint: object) -> bool:
    return (
        isinstance(source_fingerprint, str)
        and len(source_fingerprint) == 64
        and all(char in "0123456789abcdefABCDEF" for char in source_fingerprint)
    )


def _validate_source_fingerprint(source_fingerprint: str) -> None:
    if not _is_source_fingerprint(source_fingerprint):
        raise BudgetError("Source fingerprint must be a 64-character SHA-256 hex digest")


def _validate_reason(reason: str) -> str:
    if not isinstance(reason, str) or not reason.strip():
        raise BudgetError("Invocation termination reason is required")
    return reason.strip()


def _invocation_status(item: dict) -> str:
    status = item.get("status")
    if status is None:
        # Backward compatibility with ledgers written before explicit lifecycle
        # states existed.
        return (
            INVOCATION_ACTIVE
            if item.get("ended_at_utc") is None
            else INVOCATION_COMPLETED
        )
    if status not in INVOCATION_STATUSES:
        raise BudgetError("Invalid smoke stage invocation status: {}".format(status))
    return status


def _active_invocations(data: dict) -> list[dict]:
    return [
        item
        for item in data["stage_invocations"]
        if _invocation_status(item) == INVOCATION_ACTIVE
    ]


def _current_time(now: Optional[dt.datetime], field: str) -> dt.datetime:
    current = now or _now()
    if current.tzinfo is None:
        raise BudgetError("{} must be timezone-aware".format(field))
    return current


def start(repo: Path, run_id: str, now: Optional[dt.datetime] = None) -> dict:
    path = _state_path(repo, run_id)
    if path.exists():
        raise BudgetError("Budget state already exists")
    current = now or _now()
    if current.tzinfo is None:
        raise BudgetError("Budget start timestamp must be timezone-aware")
    data = {
        "started_at_utc": current.isoformat(),
        "stage_invocations": [],
        "continuation_blocker": None,
    }
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
                source_fingerprint: str,
                rooted_guard: Optional[RootedGuard] = None) -> dict:
    _validate_stage(stage)
    if not model or not isinstance(model, str):
        raise BudgetError("Model is required")
    _validate_source_fingerprint(source_fingerprint)
    _require_rooted(repo, run_id, rooted_guard)
    path, data = _load(repo, run_id)
    invocations = data["stage_invocations"]
    if data.get("continuation_blocker") is not None:
        raise BudgetError("Smoke invocation recovery is blocked; no new stage may start")
    if _active_invocations(data):
        raise BudgetError("A smoke stage invocation is already active")
    sequence = 1 + sum(1 for item in invocations if item.get("stage") == stage)
    invocation_id = f"{stage}-{sequence:03d}"
    current = _current_time(now, "Stage start timestamp")
    item = {
        "invocation_id": invocation_id,
        "stage": stage,
        "model": model,
        "source_fingerprint": source_fingerprint.lower(),
        "status": INVOCATION_ACTIVE,
        "started_at_utc": current.isoformat(),
        "ended_at_utc": None,
        "recovered_at_utc": None,
        "elapsed_seconds": None,
        "termination_reason": None,
    }
    invocations.append(item)
    _save(path, data)
    return dict(item)


def _find_invocation(data: dict, invocation_id: str) -> dict:
    matches = [
        item
        for item in data["stage_invocations"]
        if item.get("invocation_id") == invocation_id
    ]
    if len(matches) != 1:
        raise BudgetError("Unknown or ambiguous stage invocation ID")
    return matches[0]


def _require_active(item: dict) -> None:
    status = _invocation_status(item)
    if status != INVOCATION_ACTIVE:
        raise BudgetError(
            "Stage invocation is not active: {} ({})".format(
                item.get("invocation_id", "UNKNOWN"), status
            )
        )


def stage_end(repo: Path, run_id: str, invocation_id: str,
              now: Optional[dt.datetime] = None, *,
              rooted_guard: Optional[RootedGuard] = None) -> dict:
    _require_rooted(repo, run_id, rooted_guard)
    path, data = _load(repo, run_id)
    item = _find_invocation(data, invocation_id)
    _require_active(item)
    started = _aware_timestamp(item["started_at_utc"], "Stage start timestamp")
    current = _current_time(now, "Stage end timestamp")
    elapsed = max(0.0, (current - started).total_seconds())
    item["status"] = INVOCATION_COMPLETED
    item["ended_at_utc"] = current.isoformat()
    item["elapsed_seconds"] = round(elapsed, 3)
    item["termination_reason"] = None
    item["recovered_at_utc"] = None
    _save(path, data)
    return dict(item)


def stage_abort(repo: Path, run_id: str, invocation_id: str, reason: str,
                now: Optional[dt.datetime] = None, *,
                rooted_guard: Optional[RootedGuard] = None) -> dict:
    """Close an invocation whose child returned but cannot be accepted."""
    _require_rooted(repo, run_id, rooted_guard)
    reason = _validate_reason(reason)
    path, data = _load(repo, run_id)
    item = _find_invocation(data, invocation_id)
    _require_active(item)
    started = _aware_timestamp(item["started_at_utc"], "Stage start timestamp")
    current = _current_time(now, "Stage abort timestamp")
    elapsed = max(0.0, (current - started).total_seconds())
    item["status"] = INVOCATION_ABORTED
    item["ended_at_utc"] = current.isoformat()
    item["elapsed_seconds"] = round(elapsed, 3)
    item["termination_reason"] = reason
    item["recovered_at_utc"] = None
    if reason in CONTINUATION_BLOCKING_ABORT_REASONS:
        data["continuation_blocker"] = {
            "code": reason,
            "invocation_id": item.get("invocation_id"),
            "expected_fingerprint": item.get("source_fingerprint"),
        }
    _save(path, data)
    return dict(item)


def recover_active(repo: Path, run_id: str, source: Path,
                   now: Optional[dt.datetime] = None, *,
                   reason: str = "RESUME_RECOVERY",
                   rooted_guard: Optional[RootedGuard] = None,
                   source_guard: Optional[SourceGuard] = None) -> dict:
    """Recover a stale ACTIVE invocation and verify its pre-child source guard.

    Source revalidation is performed inside this deterministic transition so a
    second crash cannot persist INTERRUPTED while losing the evidence needed to
    decide whether continuation is safe. The true child termination time is
    unknowable, so ended_at_utc and elapsed_seconds remain unset.
    """
    _require_rooted(repo, run_id, rooted_guard)
    reason = _validate_reason(reason)
    path, data = _load(repo, run_id)

    blocker = data.get("continuation_blocker")
    if blocker is not None:
        return {
            "result": "RECOVERY_BLOCKED",
            "recovered": False,
            "invocation": None,
            "source_guard_result": None,
            "continuation_blocker": blocker,
        }

    active = _active_invocations(data)
    if len(active) > 1:
        raise BudgetError("Multiple active smoke stage invocations require manual diagnosis")
    if not active:
        return {
            "result": "NO_ACTIVE_INVOCATION",
            "recovered": False,
            "invocation": None,
            "source_guard_result": None,
            "continuation_blocker": None,
        }

    item = active[0]
    expected = item.get("source_fingerprint")
    source_result: dict[str, object]
    continuation_blocker: dict[str, object] | None = None

    if not _is_source_fingerprint(expected):
        source_result = {
            "result": "UNRECONSTRUCTABLE",
            "expected_fingerprint": expected,
        }
        continuation_blocker = {
            "code": "INTERRUPTED_SOURCE_GUARD_UNAVAILABLE",
            "invocation_id": item.get("invocation_id"),
        }
    else:
        guard = source_guard or smoke_workspace.verify_source_guard
        try:
            source_result = dict(guard(source.resolve(), str(expected)))
        except smoke_workspace.SmokeWorkspaceError as exc:
            # Do not close ACTIVE when the deterministic guard itself could not
            # run; a later RESUME can retry the same recovery safely.
            raise BudgetError("Interrupted source guard check failed: {}".format(exc)) from exc
        result = source_result.get("result")
        if result not in {"MATCH", "MISMATCH"}:
            raise BudgetError("Interrupted source guard returned an invalid result")
        if result == "MISMATCH":
            continuation_blocker = {
                "code": "SOURCE_CHECKOUT_MUTATED",
                "invocation_id": item.get("invocation_id"),
                "expected_fingerprint": expected,
                "actual_fingerprint": source_result.get("fingerprint"),
            }

    current = _current_time(now, "Invocation recovery timestamp")
    item["status"] = INVOCATION_INTERRUPTED
    item["ended_at_utc"] = None
    item["elapsed_seconds"] = None
    item["recovered_at_utc"] = current.isoformat()
    item["termination_reason"] = reason
    item["recovery_source_guard"] = source_result
    data["continuation_blocker"] = continuation_blocker
    _save(path, data)
    return {
        "result": "INTERRUPTED_INVOCATION_RECOVERED",
        "recovered": True,
        "invocation": dict(item),
        "source_guard_result": source_result,
        "continuation_blocker": continuation_blocker,
    }


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
    stage_start_parser.add_argument("--source-fingerprint", required=True)
    stage_end_parser = actions.add_parser("stage-end")
    stage_end_parser.add_argument("--invocation-id", required=True)
    stage_abort_parser = actions.add_parser("stage-abort")
    stage_abort_parser.add_argument("--invocation-id", required=True)
    stage_abort_parser.add_argument("--reason", required=True)
    recover_parser = actions.add_parser("recover-active")
    recover_parser.add_argument("--source", type=Path, required=True)
    recover_parser.add_argument("--reason", default="RESUME_RECOVERY")
    args = parser.parse_args()
    try:
        if args.action == "start":
            result = start(args.repo, args.run_id)
        elif args.action == "check":
            result = check(args.repo, args.run_id, args.limit_minutes)
        elif args.action == "stage-start":
            result = stage_start(
                args.repo,
                args.run_id,
                args.stage,
                args.model,
                source_fingerprint=args.source_fingerprint,
            )
        elif args.action == "stage-end":
            result = stage_end(args.repo, args.run_id, args.invocation_id)
        elif args.action == "stage-abort":
            result = stage_abort(
                args.repo,
                args.run_id,
                args.invocation_id,
                args.reason,
            )
        else:
            result = recover_active(
                args.repo,
                args.run_id,
                args.source,
                reason=args.reason,
            )
        print(json.dumps({"ok": True, **result}))
        return 3 if result.get("result") == "PERFORMANCE_BUDGET_EXCEEDED" else 0
    except (BudgetError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
