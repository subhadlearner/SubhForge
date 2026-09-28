#!/usr/bin/env python3
"""Structured machine-readable state for SubhForge smoke orchestration."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path


class SmokeStateError(RuntimeError):
    pass


SCHEMA_VERSION = 1

IMMUTABLE_FIELDS = {
    "schema_version",
    "run_id",
    "profile",
    "fixture",
    "source_commit",
    "baseline_head",
}

MUTABLE_FIELDS = {
    "state",
    "current_stage",
    "current_scenario",
    "completed_scenarios",
    "pending_scenarios",
    "context_index",
    "stage_metrics",
    "latest_verification",
    "latest_review",
    "blocker",
    "final_result",
}

TOP_LEVEL_FIELDS = IMMUTABLE_FIELDS | MUTABLE_FIELDS

ALLOWED_RUN_STATES = {
    "IN_PROGRESS",
    "WAITING_FOR_USER",
    "BLOCKED",
    "PASS",
    "PASS_WITH_ENVIRONMENT_LIMITATION",
    "FAIL",
    "ABANDONED",
}

WORKFLOW_STAGES = {
    "static-release-gate",
    "grill",
    "prd",
    "architect",
    "project-init",
    "spec",
    "implement",
    "verify",
    "pre-review",
    "review",
    "fix",
    "diagnose",
    "waive",
    "adversarial-check",
    "complete",
    "COMPLETE",
}

PROTECTED_CONTEXT_KEYS = {
    "budget_started_at_utc",
    "contract_parity",
}


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(c.isalnum() or c == "-" for c in run_id):
        raise SmokeStateError("Invalid run ID")


def _profiles_path() -> Path:
    return Path(__file__).resolve().parent.parent / "smoke" / "profiles.json"


def _profile_scenarios(profile: str) -> tuple[set[str], set[str], set[str]]:
    path = _profiles_path()
    if not path.is_file():
        raise SmokeStateError("Smoke profile registry is missing: {}".format(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SmokeStateError("Smoke profile registry is unreadable") from exc

    profiles = payload.get("profiles")
    if not isinstance(profiles, dict):
        raise SmokeStateError("Smoke profile registry has no profiles object")
    definition = profiles.get(profile)
    if not isinstance(definition, dict):
        raise SmokeStateError("Unknown smoke profile: {}".format(profile))

    def scenario_set(field: str) -> set[str]:
        values = definition.get(field)
        if (
            not isinstance(values, list)
            or not all(isinstance(item, str) and item for item in values)
            or len(values) != len(set(values))
        ):
            raise SmokeStateError(
                "Smoke profile {} {} must be a unique list of scenario IDs".format(
                    profile, field
                )
            )
        return set(values)

    required = scenario_set("required_scenarios")
    optional = scenario_set("optional_scenarios")
    if required.intersection(optional):
        raise SmokeStateError(
            "Smoke profile required/optional scenario registries must be disjoint"
        )
    return required, optional, required | optional


def state_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    folder = repo.resolve() / "docs" / "verification" / "smoke"
    if not folder.is_dir():
        raise SmokeStateError("Smoke evidence directory is missing")
    return folder / (run_id + ".state.json")


def _string_list(value: object, field: str) -> list[str]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise SmokeStateError("{} must be a list of scenario IDs".format(field))
    if len(value) != len(set(value)):
        raise SmokeStateError("{} must not contain duplicate scenario IDs".format(field))
    return value


def _validate_context_index(context: object) -> None:
    if not isinstance(context, dict):
        raise SmokeStateError("context_index must be an object")
    if not all(isinstance(key, str) and key for key in context):
        raise SmokeStateError("context_index keys must be non-empty strings")

    budget_started = context.get("budget_started_at_utc")
    if budget_started is not None:
        if not isinstance(budget_started, str) or not budget_started.strip():
            raise SmokeStateError(
                "context_index.budget_started_at_utc must be a non-empty string"
            )
        try:
            parsed = dt.datetime.fromisoformat(budget_started)
        except ValueError as exc:
            raise SmokeStateError(
                "context_index.budget_started_at_utc must be an ISO timestamp"
            ) from exc
        if parsed.tzinfo is None:
            raise SmokeStateError(
                "context_index.budget_started_at_utc must be timezone-aware"
            )

    parity = context.get("contract_parity")
    if parity is not None:
        if not isinstance(parity, dict):
            raise SmokeStateError("context_index.contract_parity must be an object")
        if not isinstance(parity.get("contract_equal"), bool):
            raise SmokeStateError(
                "context_index.contract_parity.contract_equal must be boolean"
            )


def _validate_stage_metrics(metrics: object) -> None:
    if not isinstance(metrics, dict):
        raise SmokeStateError("stage_metrics must be an object")
    for stage, entry in metrics.items():
        if not isinstance(stage, str) or not stage:
            raise SmokeStateError(
                "stage_metrics keys must be non-empty stage/invocation IDs"
            )
        if not isinstance(entry, dict):
            raise SmokeStateError("stage_metrics entries must map stage IDs to objects")
        elapsed = entry.get("elapsed_seconds")
        if elapsed is not None and (
            isinstance(elapsed, bool)
            or not isinstance(elapsed, (int, float))
            or elapsed < 0
        ):
            raise SmokeStateError("stage_metrics elapsed_seconds must be non-negative")
        context_paths = entry.get("context_paths")
        if context_paths is not None and (
            not isinstance(context_paths, list)
            or not all(isinstance(item, str) and item for item in context_paths)
        ):
            raise SmokeStateError(
                "stage_metrics context_paths must be a list of non-empty paths"
            )


def _validate_blocker(blocker: object) -> None:
    if blocker is None:
        return
    if not isinstance(blocker, dict) or not blocker:
        raise SmokeStateError("blocker must be null or a non-empty object")


def _validate_final_result(final_result: object) -> None:
    if final_result is not None and (
        not isinstance(final_result, str) or not final_result.strip()
    ):
        raise SmokeStateError("final_result must be null or a non-empty string")


def _validate_full_state(data: object, expected_run_id: str | None = None) -> dict[str, object]:
    if not isinstance(data, dict):
        raise SmokeStateError("Smoke state must be a JSON object")

    fields = set(data)
    unknown = fields - TOP_LEVEL_FIELDS
    missing = TOP_LEVEL_FIELDS - fields
    if unknown:
        raise SmokeStateError(
            "Unknown smoke state fields: {}".format(", ".join(sorted(unknown)))
        )
    if missing:
        raise SmokeStateError(
            "Missing smoke state fields: {}".format(", ".join(sorted(missing)))
        )

    if data.get("schema_version") != SCHEMA_VERSION:
        raise SmokeStateError(
            "Unsupported smoke state schema_version: {}".format(
                data.get("schema_version")
            )
        )

    run_id = data.get("run_id")
    if not isinstance(run_id, str):
        raise SmokeStateError("run_id must be a string")
    _validate_run_id(run_id)
    if expected_run_id is not None and run_id != expected_run_id:
        raise SmokeStateError("Smoke state run ID mismatch")

    profile = data.get("profile")
    if not isinstance(profile, str) or not profile:
        raise SmokeStateError("profile must be a non-empty string")
    required, _optional, allowed_scenarios = _profile_scenarios(profile)

    for field in ("fixture", "source_commit", "baseline_head"):
        value = data.get(field)
        if not isinstance(value, str) or not value:
            raise SmokeStateError("{} must be a non-empty string".format(field))

    state = data.get("state")
    if state not in ALLOWED_RUN_STATES:
        raise SmokeStateError("Invalid smoke run state: {}".format(state))

    allowed_stage_ids = WORKFLOW_STAGES | allowed_scenarios
    current_stage = data.get("current_stage")
    if not isinstance(current_stage, str) or current_stage not in allowed_stage_ids:
        raise SmokeStateError(
            "Invalid current_stage for profile {}: {}".format(profile, current_stage)
        )

    completed = _string_list(data.get("completed_scenarios"), "completed_scenarios")
    pending = _string_list(data.get("pending_scenarios"), "pending_scenarios")

    unknown_scenarios = (set(completed) | set(pending)) - allowed_scenarios
    if unknown_scenarios:
        raise SmokeStateError(
            "Unknown scenario IDs for profile {}: {}".format(
                profile, ", ".join(sorted(unknown_scenarios))
            )
        )

    overlap = set(completed).intersection(pending)
    if overlap:
        raise SmokeStateError(
            "completed_scenarios and pending_scenarios must be disjoint: {}".format(
                ", ".join(sorted(overlap))
            )
        )

    static_complete = "static-release-gate" in completed
    if completed and not static_complete:
        raise SmokeStateError(
            "static-release-gate must be the first completed smoke scenario"
        )
    if current_stage != "static-release-gate" and not static_complete:
        raise SmokeStateError(
            "current_stage cannot advance before static-release-gate is completed"
        )

    current_scenario = data.get("current_scenario")
    if current_scenario is not None:
        if not isinstance(current_scenario, str) or current_scenario not in allowed_scenarios:
            raise SmokeStateError(
                "Invalid current_scenario for profile {}: {}".format(
                    profile, current_scenario
                )
            )
        if current_scenario in completed:
            raise SmokeStateError(
                "current_scenario cannot already be completed: {}".format(
                    current_scenario
                )
            )
        if not static_complete:
            raise SmokeStateError(
                "current_scenario cannot start before static-release-gate is completed"
            )

    context_index = data.get("context_index")
    _validate_context_index(context_index)
    if static_complete:
        assert isinstance(context_index, dict)
        missing_bootstrap = PROTECTED_CONTEXT_KEYS - set(context_index)
        if missing_bootstrap:
            raise SmokeStateError(
                "Completed static-release-gate requires bootstrap context: {}".format(
                    ", ".join(sorted(missing_bootstrap))
                )
            )

    _validate_stage_metrics(data.get("stage_metrics"))

    latest_verification = data.get("latest_verification")
    if latest_verification is not None and not isinstance(latest_verification, dict):
        raise SmokeStateError("latest_verification must be null or an object")

    latest_review = data.get("latest_review")
    if latest_review is not None and not isinstance(latest_review, (str, dict)):
        raise SmokeStateError("latest_review must be null, a string, or an object")

    blocker = data.get("blocker")
    _validate_blocker(blocker)
    final_result = data.get("final_result")
    _validate_final_result(final_result)

    if state in {"BLOCKED", "WAITING_FOR_USER"} and blocker is None:
        raise SmokeStateError("{} state requires blocker details".format(state))

    if state in {"IN_PROGRESS", "BLOCKED", "WAITING_FOR_USER"}:
        if final_result is not None:
            raise SmokeStateError(
                "{} state cannot have a final_result".format(state)
            )
    elif state == "PASS":
        missing_required = required - set(completed)
        if missing_required:
            raise SmokeStateError(
                "PASS requires all required scenarios completed: {}".format(
                    ", ".join(sorted(missing_required))
                )
            )
        expected = "{}_SMOKE_PASS".format(profile)
        if final_result != expected:
            raise SmokeStateError(
                "PASS final_result must be {}".format(expected)
            )
    elif state == "PASS_WITH_ENVIRONMENT_LIMITATION":
        missing_required = required - set(completed)
        if missing_required:
            raise SmokeStateError(
                "PASS_WITH_ENVIRONMENT_LIMITATION requires all required scenarios completed: {}".format(
                    ", ".join(sorted(missing_required))
                )
            )
        expected = "{}_SMOKE_PASS_WITH_ENVIRONMENT_LIMITATION".format(profile)
        if final_result != expected:
            raise SmokeStateError(
                "PASS_WITH_ENVIRONMENT_LIMITATION final_result must be {}".format(
                    expected
                )
            )
    elif state == "FAIL" and final_result != "SMOKE_FAIL":
        raise SmokeStateError("FAIL final_result must be SMOKE_FAIL")

    return data


def load(repo: Path, run_id: str) -> dict[str, object]:
    path = state_path(repo, run_id)
    if not path.is_file():
        raise SmokeStateError("Smoke state is missing")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SmokeStateError("Smoke state is unreadable") from exc
    return _validate_full_state(data, expected_run_id=run_id)


def init(repo: Path, run_id: str, profile: str, fixture: str,
         source_commit: str, baseline_head: str) -> dict[str, object]:
    path = state_path(repo, run_id)
    if path.exists():
        raise SmokeStateError("Smoke state already exists")

    # Validate the selected profile before creating canonical state.
    _profile_scenarios(profile)

    data = {
        "schema_version": SCHEMA_VERSION,
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
        "stage_metrics": {},
        "latest_verification": None,
        "latest_review": None,
        "blocker": None,
        "final_result": None,
    }
    _validate_full_state(data, expected_run_id=run_id)
    _save(path, data)
    return data


def _save(path: Path, data: dict[str, object]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def _merge_context_index(
    data: dict[str, object],
    incoming: object,
) -> dict[str, object]:
    if not isinstance(incoming, dict):
        raise SmokeStateError("context_index must be an object")
    existing = data.get("context_index")
    if not isinstance(existing, dict):
        raise SmokeStateError("Existing context_index must be an object")

    completed = data.get("completed_scenarios")
    if not isinstance(completed, list):
        raise SmokeStateError("Existing completed_scenarios must be a list")
    bootstrap_open = (
        data.get("current_stage") == "static-release-gate"
        and "static-release-gate" not in completed
    )

    for key in PROTECTED_CONTEXT_KEYS:
        if key not in incoming:
            continue
        if key in existing:
            if incoming[key] != existing[key]:
                raise SmokeStateError(
                    "Protected bootstrap context cannot be changed: {}".format(key)
                )
        elif not bootstrap_open:
            raise SmokeStateError(
                "Protected bootstrap context can only be established during bootstrap: {}".format(
                    key
                )
            )
    return {**existing, **incoming}


def set_values(repo: Path, run_id: str, updates: dict[str, object]) -> dict[str, object]:
    if not isinstance(updates, dict):
        raise SmokeStateError("Smoke state updates must be an object")

    unknown = set(updates) - MUTABLE_FIELDS
    if unknown:
        immutable = set(updates).intersection(IMMUTABLE_FIELDS)
        if immutable:
            raise SmokeStateError(
                "Immutable smoke state fields cannot be changed: {}".format(
                    ", ".join(sorted(immutable))
                )
            )
        raise SmokeStateError(
            "Unknown mutable smoke state fields: {}".format(
                ", ".join(sorted(unknown))
            )
        )

    data = load(repo, run_id)
    candidate = dict(data)
    merged_updates = dict(updates)

    if "context_index" in merged_updates:
        merged_updates["context_index"] = _merge_context_index(
            candidate,
            merged_updates["context_index"],
        )

    if "stage_metrics" in merged_updates:
        incoming_metrics = merged_updates["stage_metrics"]
        existing_metrics = candidate.get("stage_metrics")
        if not isinstance(incoming_metrics, dict):
            raise SmokeStateError("stage_metrics must be an object")
        if not isinstance(existing_metrics, dict):
            raise SmokeStateError("Existing stage_metrics must be an object")
        merged_updates["stage_metrics"] = {**existing_metrics, **incoming_metrics}

    candidate.update(merged_updates)
    _validate_full_state(candidate, expected_run_id=run_id)

    # Persist only after the entire resulting state is valid. Invalid updates
    # never partially mutate the canonical JSON.
    _save(state_path(repo, run_id), candidate)
    return candidate


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
