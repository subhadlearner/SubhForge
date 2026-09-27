#!/usr/bin/env python3
"""Structured machine-readable state for SubhForge smoke orchestration."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class SmokeStateError(RuntimeError):
    pass


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(c.isalnum() or c == "-" for c in run_id):
        raise SmokeStateError("Invalid run ID")


def state_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    folder = repo.resolve() / "docs" / "verification" / "smoke"
    if not folder.is_dir():
        raise SmokeStateError("Smoke evidence directory is missing")
    return folder / (run_id + ".state.json")


def load(repo: Path, run_id: str) -> dict[str, Any]:
    path = state_path(repo, run_id)
    if not path.is_file():
        raise SmokeStateError("Smoke state is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("run_id") != run_id:
        raise SmokeStateError("Smoke state run ID mismatch")
    return data


def init(repo: Path, run_id: str, profile: str, fixture: str,
         source_commit: str, baseline_head: str) -> dict[str, Any]:
    path = state_path(repo, run_id)
    if path.exists():
        raise SmokeStateError("Smoke state already exists")
    data = {
        "schema_version": 1,
        "run_id": run_id,
        "profile": profile,
        "fixture": fixture,
        "source_commit": source_commit,
        "baseline_head": baseline_head,
        "state": "IN_PROGRESS",
        "current_stage": "static-release-gate",
        "current_scenario": None,
        "completed_scenarios": [],
        "pending_scenarios": [],
        "context_index": {},
        "latest_verification": None,
        "latest_review": None,
        "blocker": None,
        "final_result": None,
    }
    _save(path, data)
    return data


def _save(path: Path, data: dict[str, Any]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def set_values(repo: Path, run_id: str, updates: dict[str, Any]) -> dict[str, Any]:
    data = load(repo, run_id)
    protected = {"schema_version", "run_id", "profile", "fixture", "source_commit", "baseline_head"}
    overlap = protected.intersection(updates)
    if overlap:
        raise SmokeStateError("Immutable smoke state fields cannot be changed: {}".format(
            ", ".join(sorted(overlap))))
    data.update(updates)
    _save(state_path(repo, run_id), data)
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)

    init_p = actions.add_parser("init")
    init_p.add_argument("--profile", required=True)
    init_p.add_argument("--fixture", required=True)
    init_p.add_argument("--source-commit", required=True)
    init_p.add_argument("--baseline-head", required=True)

    set_p = actions.add_parser("set")
    set_p.add_argument("--json", required=True, help="JSON object of mutable fields to replace")

    actions.add_parser("get")

    args = parser.parse_args()
    try:
        if args.action == "init":
            result = init(args.repo, args.run_id, args.profile, args.fixture,
                          args.source_commit, args.baseline_head)
        elif args.action == "set":
            updates = json.loads(args.json)
            if not isinstance(updates, dict):
                raise SmokeStateError("--json must contain a JSON object")
            result = set_values(args.repo, args.run_id, updates)
        else:
            result = load(args.repo, args.run_id)
        print(json.dumps({"ok": True, "state": result}))
        return 0
    except (SmokeStateError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
