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
    "qualification_config",
    "segment_runtime",
    "qualification_eligible",
}


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(c.isalnum() or c == "-" for c in run_id):
        raise SmokeStateError("Invalid run ID")


def _validate_timestamp(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SmokeStateError("{} must be a non-empty ISO timestamp".format(field))
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise SmokeStateError("{} must be an ISO timestamp".format(field)) from exc
    if parsed.tzinfo is None:
        raise SmokeStateError("{} must be timezone-aware".format(field))


def _validate_sha256(value: object, field: str) -> None:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or not all(ch in "0123456789abcdefABCDEF" for ch in value)
    ):
        raise SmokeStateError("{} must be a 64-character SHA-256 digest".format(field))


def _validate_segment_runtime(runtime: dict[str, object]) -> None:
    expected_fields = {
        "runtime_schema_version",
        "active_segment",
        "active_status",
        "active_started_at_utc",
        "active_source_fingerprint",
        "closed_segments",
        "gaps",
        "gap",
        "disqualification_reason",
    }
    if set(runtime) != expected_fields:
        raise SmokeStateError("segment_runtime has an invalid exact schema")
    if runtime.get("runtime_schema_version") != 1:
        raise SmokeStateError("segment_runtime.runtime_schema_version must be 1")

    segment_ids = ["S1", "S2", "S3", "S4", "S5", "S6"]
    active_segment = runtime.get("active_segment")
    active_status = runtime.get("active_status")
    active_started = runtime.get("active_started_at_utc")
    active_source = runtime.get("active_source_fingerprint")
    if active_segment is None:
        if any(value is not None for value in (active_status, active_started, active_source)):
            raise SmokeStateError(
                "segment_runtime inactive segment fields must all be null"
            )
    else:
        if active_segment not in segment_ids:
            raise SmokeStateError("segment_runtime.active_segment is invalid")
        if active_status not in {"ACTIVE", "BUDGET_EXCEEDED"}:
            raise SmokeStateError("segment_runtime.active_status is invalid")
        _validate_timestamp(active_started, "segment_runtime.active_started_at_utc")
        _validate_sha256(
            active_source, "segment_runtime.active_source_fingerprint"
        )

    reason = runtime.get("disqualification_reason")
    if reason is not None and (
        not isinstance(reason, str) or not reason.strip()
    ):
        raise SmokeStateError(
            "segment_runtime.disqualification_reason must be null or non-empty"
        )

    closed = runtime.get("closed_segments")
    if not isinstance(closed, list):
        raise SmokeStateError("segment_runtime.closed_segments must be a list")
    closed_ids: list[str] = []
    close_fields = {
        "segment_id",
        "status",
        "started_at_utc",
        "closed_at_utc",
        "charged_elapsed_seconds",
        "excluded_human_wait_seconds",
        "configured_limit_minutes",
        "assigned_scenarios",
        "completed_scenarios",
        "checkpoint",
        "verified_checkpoint",
        "checkpoint_fingerprint",
        "source_fingerprint",
        "evidence_manifest",
        "ledger_projection_sha256",
    }
    for index, close in enumerate(closed):
        if not isinstance(close, dict) or set(close) != close_fields:
            raise SmokeStateError("segment_runtime closed segment has invalid exact schema")
        segment_id = close.get("segment_id")
        if segment_id != segment_ids[index]:
            raise SmokeStateError("closed segments must be an ordered S1..S6 prefix")
        closed_ids.append(segment_id)
        if close.get("status") != "COMPLETED":
            raise SmokeStateError("closed segment status must be COMPLETED")
        _validate_timestamp(close.get("started_at_utc"), "closed segment started_at_utc")
        _validate_timestamp(close.get("closed_at_utc"), "closed segment closed_at_utc")
        for field in ("charged_elapsed_seconds", "excluded_human_wait_seconds"):
            value = close.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or value < 0
            ):
                raise SmokeStateError("{} must be non-negative".format(field))
        limit = close.get("configured_limit_minutes")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise SmokeStateError("configured_limit_minutes must be positive")
        assigned = _string_list(close.get("assigned_scenarios"), "assigned_scenarios")
        completed = _string_list(close.get("completed_scenarios"), "completed_scenarios")
        if assigned != completed:
            raise SmokeStateError("closed segment must complete every assigned scenario")
        for field in ("checkpoint", "verified_checkpoint"):
            value = close.get(field)
            if not isinstance(value, str) or not value:
                raise SmokeStateError("{} must be non-empty".format(field))
        _validate_sha256(
            close.get("checkpoint_fingerprint"), "checkpoint_fingerprint"
        )
        _validate_sha256(close.get("source_fingerprint"), "source_fingerprint")
        _validate_sha256(
            close.get("ledger_projection_sha256"), "ledger_projection_sha256"
        )
        manifest = close.get("evidence_manifest")
        if not isinstance(manifest, dict) or set(manifest) != {"entries", "sha256"}:
            raise SmokeStateError("evidence_manifest has an invalid exact schema")
        entries = manifest.get("entries")
        if not isinstance(entries, list) or not entries:
            raise SmokeStateError("evidence_manifest.entries must be non-empty")
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
                raise SmokeStateError("evidence manifest entry has invalid exact schema")
            if not isinstance(entry.get("path"), str) or not entry.get("path"):
                raise SmokeStateError("evidence manifest path must be non-empty")
            _validate_sha256(entry.get("sha256"), "evidence manifest sha256")
        _validate_sha256(manifest.get("sha256"), "evidence_manifest.sha256")

    activities_fields = {"type", "detail", "recorded_at_utc"}
    allowed_activity = {
        "OPERATOR_INACTIVITY",
        "READ_ONLY_STATUS",
        "READ_ONLY_PREFLIGHT",
    }

    def validate_activities(value: object) -> None:
        if not isinstance(value, list):
            raise SmokeStateError("gap activities must be a list")
        for activity in value:
            if not isinstance(activity, dict) or set(activity) != activities_fields:
                raise SmokeStateError("gap activity has invalid exact schema")
            if activity.get("type") not in allowed_activity:
                raise SmokeStateError("gap activity type is invalid")
            if not isinstance(activity.get("detail"), str) or not activity.get("detail").strip():
                raise SmokeStateError("gap activity detail must be non-empty")
            _validate_timestamp(activity.get("recorded_at_utc"), "gap activity recorded_at_utc")

    gap_common = {
        "state",
        "after_segment",
        "started_at_utc",
        "activities",
        "drift_detected",
        "disqualification_reason",
    }
    gaps = runtime.get("gaps")
    if not isinstance(gaps, list):
        raise SmokeStateError("segment_runtime.gaps must be a list")
    for gap in gaps:
        expected = gap_common | {"before_segment", "ended_at_utc"}
        if not isinstance(gap, dict) or set(gap) != expected:
            raise SmokeStateError("completed gap has invalid exact schema")
        if gap.get("state") != "BETWEEN_SEGMENTS":
            raise SmokeStateError("completed gap state is invalid")
        if gap.get("after_segment") not in segment_ids or gap.get("before_segment") not in segment_ids:
            raise SmokeStateError("completed gap segment IDs are invalid")
        _validate_timestamp(gap.get("started_at_utc"), "gap started_at_utc")
        _validate_timestamp(gap.get("ended_at_utc"), "gap ended_at_utc")
        if not isinstance(gap.get("drift_detected"), bool):
            raise SmokeStateError("gap drift_detected must be boolean")
        gap_reason = gap.get("disqualification_reason")
        if gap_reason is not None and (
            not isinstance(gap_reason, str) or not gap_reason.strip()
        ):
            raise SmokeStateError("gap disqualification_reason is invalid")
        validate_activities(gap.get("activities"))

    active_gap = runtime.get("gap")
    if active_gap is not None:
        if not isinstance(active_gap, dict) or set(active_gap) != gap_common:
            raise SmokeStateError("active gap has invalid exact schema")
        if active_gap.get("state") != "BETWEEN_SEGMENTS":
            raise SmokeStateError("active gap state is invalid")
        if active_gap.get("after_segment") not in segment_ids:
            raise SmokeStateError("active gap after_segment is invalid")
        _validate_timestamp(active_gap.get("started_at_utc"), "gap started_at_utc")
        if not isinstance(active_gap.get("drift_detected"), bool):
            raise SmokeStateError("gap drift_detected must be boolean")
        gap_reason = active_gap.get("disqualification_reason")
        if gap_reason is not None and (
            not isinstance(gap_reason, str) or not gap_reason.strip()
        ):
            raise SmokeStateError("gap disqualification_reason is invalid")
        validate_activities(active_gap.get("activities"))

    if active_segment is not None and active_segment in closed_ids:
        raise SmokeStateError("active segment cannot already be closed")
    if active_gap is not None and active_segment is not None:
        raise SmokeStateError("segment_runtime cannot be ACTIVE and BETWEEN_SEGMENTS")


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

    qualification_config = context.get("qualification_config")
    if qualification_config is not None and not isinstance(qualification_config, dict):
        raise SmokeStateError("context_index.qualification_config must be an object")
    segment_runtime = context.get("segment_runtime")
    if segment_runtime is not None:
        if not isinstance(segment_runtime, dict):
            raise SmokeStateError("context_index.segment_runtime must be null or an object")
        _validate_segment_runtime(segment_runtime)
    qualification_eligible = context.get("qualification_eligible")
    if qualification_eligible is not None and not isinstance(qualification_eligible, bool):
        raise SmokeStateError("context_index.qualification_eligible must be boolean")


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
        if profile == "FULL":
            assert isinstance(context_index, dict)
            if context_index.get("qualification_eligible") is not True:
                raise SmokeStateError("FULL PASS requires an eligible pinned qualification")
            runtime = context_index.get("segment_runtime")
            if not isinstance(runtime, dict):
                raise SmokeStateError("FULL PASS requires segmented runtime state")
            closed = runtime.get("closed_segments")
            closed_ids = [
                item.get("segment_id")
                for item in closed
                if isinstance(item, dict) and item.get("status") == "COMPLETED"
            ] if isinstance(closed, list) else []
            if closed_ids != ["S1", "S2", "S3", "S4", "S5", "S6"]:
                raise SmokeStateError("FULL PASS requires immutable completion of S1 through S6")
            if runtime.get("active_segment") is not None:
                raise SmokeStateError("FULL PASS cannot have an active segment")
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
        if profile == "FULL":
            assert isinstance(context_index, dict)
            if context_index.get("qualification_eligible") is not True:
                raise SmokeStateError(
                    "FULL PASS_WITH_ENVIRONMENT_LIMITATION requires an eligible pinned qualification"
                )
            runtime = context_index.get("segment_runtime")
            closed = runtime.get("closed_segments") if isinstance(runtime, dict) else None
            closed_ids = [
                item.get("segment_id")
                for item in closed
                if isinstance(item, dict) and item.get("status") == "COMPLETED"
            ] if isinstance(closed, list) else []
            if closed_ids != ["S1", "S2", "S3", "S4", "S5", "S6"]:
                raise SmokeStateError(
                    "FULL PASS_WITH_ENVIRONMENT_LIMITATION requires completion of S1 through S6"
                )
            if runtime.get("active_segment") is not None:
                raise SmokeStateError(
                    "FULL PASS_WITH_ENVIRONMENT_LIMITATION cannot have an active segment"
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

    if (
        candidate.get("profile") == "FULL"
        and candidate.get("state") in {"PASS", "PASS_WITH_ENVIRONMENT_LIMITATION"}
    ):
        try:
            import smoke_segments
            smoke_segments.validate_terminal_integrity(repo, run_id)
        except Exception as exc:
            if exc.__class__.__name__ == "SegmentError":
                raise SmokeStateError(
                    "FULL terminal integrity validation failed: {}".format(exc)
                ) from exc
            raise

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
