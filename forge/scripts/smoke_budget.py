#!/usr/bin/env python3
"""Deterministic elapsed-time budget and stage timing for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_handoff
import smoke_state
import smoke_segments
import smoke_workspace


class BudgetError(RuntimeError):
    pass


RootedGuard = Callable[[Path, str], object]
SourceGuard = Callable[[Path, str], dict[str, object]]
WorkspaceGuard = Callable[[Path, str], object]
StateGuard = Callable[[Path, str], dict[str, object]]

HUMAN_WAIT_WAIVER_AUTHORIZATION = "WAIVER_AUTHORIZATION"
ALLOWED_HUMAN_WAIT_GATE_TYPES = {HUMAN_WAIT_WAIVER_AUTHORIZATION}
WAIVER_CLASSIFICATIONS = {
    "TEST_FLAKINESS",
    "ENVIRONMENT_FAILURE",
    "NON_CRITICAL_QUALITY_GATE",
    "KNOWN_PRODUCT_DEFECT",
    "SECURITY_EXCEPTION",
    "DATA_INTEGRITY_EXCEPTION",
    "COMPLIANCE_EXCEPTION",
}

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
    waits = data.setdefault("human_wait_intervals", [])
    if not isinstance(waits, list):
        raise BudgetError("human_wait_intervals must be a list")
    data.setdefault("continuation_blocker", None)
    _validate_human_wait_intervals(data, run_id)
    return path, data


def _save(path: Path, data: dict) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _aware_timestamp(value: object, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise BudgetError(f"{field} must be a non-empty ISO timestamp")
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise BudgetError(f"{field} is not a valid ISO timestamp") from exc
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


def _validate_gate_type(gate_type: str) -> str:
    if gate_type not in ALLOWED_HUMAN_WAIT_GATE_TYPES:
        raise BudgetError("Human authorization gate type is not allow-listed: {}".format(gate_type))
    return gate_type


def _normalize_verification_report(value: str) -> str:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise BudgetError("Verification report must be a repository-relative POSIX path")
    normalized = value.strip()
    parts = normalized.split("/")
    if (
        len(parts) < 3
        or parts[0] != "docs"
        or parts[1] != "verification"
        or any(part in {"", ".", ".."} for part in parts)
    ):
        raise BudgetError("Verification report must be under docs/verification/")
    return "/".join(parts)


def _validate_contract_fingerprint(value: str) -> str:
    prefix = "GIT_BLOB_OID:"
    if not isinstance(value, str) or not value.startswith(prefix):
        raise BudgetError("Implementation-state fingerprint must use GIT_BLOB_OID:<object-id>")
    object_id = value[len(prefix):]
    if (
        len(object_id) not in {40, 64}
        or not all(char in "0123456789abcdefABCDEF" for char in object_id)
    ):
        raise BudgetError("Implementation-state fingerprint has an invalid Git object ID")
    return prefix + object_id.lower()


def _normalize_failure_set(failures: list[str]) -> list[str]:
    if not isinstance(failures, list) or not failures:
        raise BudgetError("Human authorization gate requires a non-empty failure set")
    normalized = []
    for failure in failures:
        if not isinstance(failure, str) or not failure.strip():
            raise BudgetError("Failure identifiers must be non-empty strings")
        normalized.append(failure.strip())
    if len(normalized) != len(set(normalized)):
        raise BudgetError("Failure set must not contain duplicates")
    return sorted(normalized, key=lambda item: item.encode("utf-8"))


def _validate_classification(classification: str) -> str:
    if classification not in WAIVER_CLASSIFICATIONS:
        raise BudgetError("Invalid waiver classification: {}".format(classification))
    return classification


def _waiver_gate_identity(
    repo: Path,
    run_id: str,
    verification_report: str,
    implementation_state_fingerprint: str,
    failures: list[str],
    classification: str,
) -> dict[str, object]:
    report = _normalize_verification_report(verification_report)
    report_path = (repo.resolve() / Path(*report.split("/"))).resolve()
    try:
        report_path.relative_to(repo.resolve())
    except ValueError as exc:
        raise BudgetError("Verification report escapes the smoke repository") from exc
    if not report_path.is_file():
        raise BudgetError("Verification report does not exist: {}".format(report))
    return {
        "run_id": run_id,
        "gate_type": HUMAN_WAIT_WAIVER_AUTHORIZATION,
        "verification_report": report,
        "verification_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "implementation_state_fingerprint": _validate_contract_fingerprint(
            implementation_state_fingerprint
        ),
        "failure_set": _normalize_failure_set(failures),
        "classification": _validate_classification(classification),
    }


def _gate_id_from_identity(identity: dict[str, object]) -> str:
    canonical = json.dumps(
        identity,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _require_report_binding(repo: Path, identity: dict[str, object]) -> None:
    report = _normalize_verification_report(identity.get("verification_report"))
    expected = identity.get("verification_report_sha256")
    if not isinstance(expected, str):
        raise BudgetError("Human authorization gate is missing verification-report digest")
    report_path = (repo.resolve() / Path(*report.split("/"))).resolve()
    try:
        report_path.relative_to(repo.resolve())
    except ValueError as exc:
        raise BudgetError("Verification report escapes the smoke repository") from exc
    if not report_path.is_file():
        raise BudgetError("Verification report no longer exists: {}".format(report))
    actual = hashlib.sha256(report_path.read_bytes()).hexdigest()
    if actual != expected:
        raise BudgetError("Verification report changed after human authorization was requested")


def _required_human_text(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BudgetError("{} is required for human authorization".format(field))
    return value


def _waiver_authorization_payload(
    identity: dict[str, object],
    *,
    decision: str,
    verification_report: str,
    failures: list[str],
    classification: str,
    justification: str,
    residual_risk: str,
    compensating_control: str,
    remediation: str,
    expiry: str,
) -> dict[str, object]:
    if decision != "ACCEPTED_TEMPORARILY":
        raise BudgetError("Human waiver decision must be ACCEPTED_TEMPORARILY")
    report = _normalize_verification_report(verification_report)
    normalized_failures = _normalize_failure_set(failures)
    normalized_classification = _validate_classification(classification)
    if report != identity.get("verification_report"):
        raise BudgetError("Human authorization names a different verification report")
    if normalized_failures != identity.get("failure_set"):
        raise BudgetError("Human authorization names a different failure set")
    if normalized_classification != identity.get("classification"):
        raise BudgetError("Human authorization names a different waiver classification")
    return {
        "decision": decision,
        "verification_report": report,
        "failure_set": normalized_failures,
        "classification": normalized_classification,
        "justification": _required_human_text(justification, "Justification"),
        "residual_risk": _required_human_text(residual_risk, "Residual risk"),
        "compensating_control": _required_human_text(
            compensating_control, "Compensating control"
        ),
        "remediation": _required_human_text(remediation, "Remediation"),
        "expiry": _required_human_text(expiry, "Expiry"),
    }


def _validate_human_wait_intervals(data: dict, run_id: str) -> None:
    intervals = data["human_wait_intervals"]
    budget_started = _aware_timestamp(data["started_at_utc"], "Budget start timestamp")
    previous_end = budget_started
    seen_gate_ids: set[str] = set()
    saw_open = False
    required_interval_fields = {
        "gate_type",
        "gate_id",
        "segment_id",
        "identity",
        "started_at_utc",
        "ended_at_utc",
        "authorization",
    }
    required_identity_fields = {
        "run_id",
        "gate_type",
        "verification_report",
        "verification_report_sha256",
        "implementation_state_fingerprint",
        "failure_set",
        "classification",
    }

    for index, item in enumerate(intervals):
        if not isinstance(item, dict) or set(item) != required_interval_fields:
            raise BudgetError("Human wait interval {} has an invalid schema".format(index))
        gate_type = _validate_gate_type(item.get("gate_type"))
        segment_id = item.get("segment_id")
        if segment_id not in {"S1", "S2", "S3", "S4", "S5", "S6"}:
            raise BudgetError("Human wait segment_id must identify a FULL segment")
        gate_id = item.get("gate_id")
        if (
            not isinstance(gate_id, str)
            or len(gate_id) != 64
            or not all(char in "0123456789abcdef" for char in gate_id)
        ):
            raise BudgetError("Human wait gate_id must be a lowercase SHA-256 digest")
        if gate_id in seen_gate_ids:
            raise BudgetError("Human wait gate_id must not be reused")
        seen_gate_ids.add(gate_id)

        identity = item.get("identity")
        if not isinstance(identity, dict) or set(identity) != required_identity_fields:
            raise BudgetError("Human wait identity has an invalid schema")
        if identity.get("run_id") != run_id or identity.get("gate_type") != gate_type:
            raise BudgetError("Human wait identity does not belong to this run/gate")
        _normalize_verification_report(identity.get("verification_report"))
        report_sha256 = identity.get("verification_report_sha256")
        if (
            not isinstance(report_sha256, str)
            or len(report_sha256) != 64
            or not all(char in "0123456789abcdef" for char in report_sha256)
        ):
            raise BudgetError("Human wait verification-report SHA-256 is invalid")
        _validate_contract_fingerprint(identity.get("implementation_state_fingerprint"))
        normalized_failures = _normalize_failure_set(identity.get("failure_set"))
        if normalized_failures != identity.get("failure_set"):
            raise BudgetError("Human wait failure set is not canonically ordered")
        _validate_classification(identity.get("classification"))
        if _gate_id_from_identity(identity) != gate_id:
            raise BudgetError("Human wait gate_id does not match its canonical identity")

        started = _aware_timestamp(item.get("started_at_utc"), "Human wait start timestamp")
        if started < previous_end:
            raise BudgetError("Human wait intervals overlap or are out of order")
        ended_value = item.get("ended_at_utc")
        authorization = item.get("authorization")
        if ended_value is None:
            if authorization is not None:
                raise BudgetError("Open human wait cannot contain authorization")
            if saw_open:
                raise BudgetError("Multiple open human wait intervals are not allowed")
            saw_open = True
            if index != len(intervals) - 1:
                raise BudgetError("Open human wait interval must be the last interval")
            continue

        ended = _aware_timestamp(ended_value, "Human wait end timestamp")
        if ended < started:
            raise BudgetError("Human wait end precedes its start")
        if not isinstance(authorization, dict):
            raise BudgetError("Closed human wait requires persisted authorization")
        validated = _waiver_authorization_payload(
            identity,
            decision=authorization.get("decision"),
            verification_report=authorization.get("verification_report"),
            failures=authorization.get("failure_set"),
            classification=authorization.get("classification"),
            justification=authorization.get("justification"),
            residual_risk=authorization.get("residual_risk"),
            compensating_control=authorization.get("compensating_control"),
            remediation=authorization.get("remediation"),
            expiry=authorization.get("expiry"),
        )
        if validated != authorization:
            raise BudgetError("Persisted human authorization is not canonical")
        previous_end = ended


def _open_human_wait(data: dict) -> dict | None:
    intervals = data["human_wait_intervals"]
    if intervals and intervals[-1].get("ended_at_utc") is None:
        return intervals[-1]
    return None


def _require_workspace(
    repo: Path,
    run_id: str,
    guard: Optional[WorkspaceGuard],
) -> None:
    try:
        (guard or smoke_handoff.validate_workspace)(repo, run_id)
    except smoke_handoff.SmokeHandoffError as exc:
        raise BudgetError(
            "Human authorization capture requires the validated disposable smoke workspace: {}".format(
                exc
            )
        ) from exc


def _human_gate_state(
    repo: Path,
    run_id: str,
    guard: Optional[StateGuard],
) -> dict[str, object]:
    try:
        state = dict((guard or smoke_state.load)(repo, run_id))
    except smoke_state.SmokeStateError as exc:
        raise BudgetError(
            "Human authorization gate requires valid canonical smoke state: {}".format(exc)
        ) from exc

    if state.get("profile") != "FULL":
        raise BudgetError("Human authorization wait is only enabled for FULL smoke")
    if state.get("current_scenario") != "waive-review-loop":
        raise BudgetError(
            "Human authorization wait requires current_scenario waive-review-loop"
        )
    if state.get("current_stage") not in {"verify", "waive", "waive-review-loop"}:
        raise BudgetError(
            "Human authorization wait requires the waiver verification/waive stage"
        )

    latest = state.get("latest_verification")
    if not isinstance(latest, dict):
        raise BudgetError("Human authorization wait requires canonical verification evidence")
    expected = {
        "result": "NOT_DONE",
        "delivery_gate": "BLOCKED",
        "freshness": "MATCH",
    }
    for field, value in expected.items():
        if latest.get(field) != value:
            raise BudgetError(
                "Human authorization wait requires latest_verification.{}={}".format(
                    field, value
                )
            )
    return state


def _require_waiting_blocker(
    state: dict[str, object],
    gate_type: str,
    gate_id: str,
) -> None:
    if state.get("state") != "WAITING_FOR_USER":
        raise BudgetError("Human authorization capture requires WAITING_FOR_USER state")
    blocker = state.get("blocker")
    if not isinstance(blocker, dict):
        raise BudgetError("Human authorization capture requires persisted blocker identity")
    if blocker.get("gate_type") != gate_type or blocker.get("gate_id") != gate_id:
        raise BudgetError("Canonical blocker does not match the active human authorization gate")


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
    try:
        identity = smoke_workspace.validate_repository_identity(repo, run_id)
    except smoke_workspace.SmokeWorkspaceError as exc:
        raise BudgetError(
            "Smoke budget initialization requires the owned disposable repository: {}".format(exc)
        ) from exc
    repo = Path(identity["run_directory"])
    path = _state_path(repo, run_id)
    if path.exists():
        raise BudgetError("Budget state already exists")
    current = now or _now()
    if current.tzinfo is None:
        raise BudgetError("Budget start timestamp must be timezone-aware")
    data = {
        "started_at_utc": current.isoformat(),
        "stage_invocations": [],
        "human_wait_intervals": [],
        "continuation_blocker": None,
    }
    _save(path, data)
    return data


def check(repo: Path, run_id: str,
          now: Optional[dt.datetime] = None) -> dict:
    """Check the pinned qualification budget; callers cannot supply a limit."""
    if isinstance(now, (int, float)) and not isinstance(now, bool):
        raise BudgetError(
            "Numeric performance-budget overrides are not supported; use the pinned profile limit"
        )
    _, data = _load(repo, run_id)
    state = smoke_state.load(repo, run_id)
    current = _current_time(now, "Budget check timestamp")
    try:
        pinned = smoke_segments.assert_config_intact(repo, run_id)
    except smoke_segments.SegmentError as exc:
        raise BudgetError(str(exc)) from exc

    if state.get("profile") == "FULL":
        try:
            result = smoke_segments.segment_timing(repo, run_id, current)
        except smoke_segments.SegmentError as exc:
            raise BudgetError(str(exc)) from exc
        active_wait = None
        for interval in data["human_wait_intervals"]:
            if interval.get("ended_at_utc") is None:
                active_wait = {
                    "gate_type": interval["gate_type"],
                    "gate_id": interval["gate_id"],
                    "segment_id": interval["segment_id"],
                    "identity": dict(interval["identity"]),
                    "started_at_utc": interval["started_at_utc"],
                }
        result = {
            **result,
            "active_human_wait": active_wait,
            "completed_human_wait_count": sum(
                1 for interval in data["human_wait_intervals"]
                if interval.get("ended_at_utc") is not None
            ),
        }
        if result["result"] == "PERFORMANCE_BUDGET_EXCEEDED":
            try:
                smoke_segments.mark_budget_exceeded(repo, run_id, current)
            except smoke_segments.SegmentError as exc:
                raise BudgetError(str(exc)) from exc
        return result

    started = _aware_timestamp(data["started_at_utc"], "Budget start timestamp")
    wall_elapsed = max(0.0, (current - started).total_seconds())
    excluded = 0.0
    for interval in data["human_wait_intervals"]:
        wait_started = _aware_timestamp(interval["started_at_utc"], "Human wait start timestamp")
        wait_ended = (
            _aware_timestamp(interval["ended_at_utc"], "Human wait end timestamp")
            if interval.get("ended_at_utc") is not None else current
        )
        if wait_ended > wait_started:
            excluded += (min(wait_ended, current) - wait_started).total_seconds()
    elapsed = max(0.0, wall_elapsed - min(wall_elapsed, excluded))
    limit_seconds = int(pinned["limit_minutes"] * 60)
    return {
        "started_at_utc": started.isoformat(),
        "wall_elapsed_seconds": round(wall_elapsed, 3),
        "excluded_human_wait_seconds": round(excluded, 3),
        "elapsed_seconds": round(elapsed, 3),
        "limit_seconds": limit_seconds,
        "remaining_seconds": round(max(0.0, limit_seconds - elapsed), 3),
        "active_human_wait": None,
        "completed_human_wait_count": 0,
        "result": "PERFORMANCE_BUDGET_EXCEEDED"
        if elapsed >= limit_seconds else "WITHIN_BUDGET",
    }


def human_wait_start(
    repo: Path,
    run_id: str,
    gate_type: str,
    verification_report: str,
    implementation_state_fingerprint: str,
    failures: list[str],
    classification: str,
    now: Optional[dt.datetime] = None,
    *,
    rooted_guard: Optional[RootedGuard] = None,
    state_guard: Optional[StateGuard] = None,
) -> dict:
    """Open the single allow-listed human-authorization pause for this request."""
    _validate_gate_type(gate_type)
    _require_rooted(repo, run_id, rooted_guard)
    state = _human_gate_state(repo, run_id, state_guard)
    try:
        segment = smoke_segments.active_segment(repo, run_id)
        timing = smoke_segments.segment_timing(repo, run_id, now)
    except smoke_segments.SegmentError as exc:
        raise BudgetError(str(exc)) from exc
    if segment["segment"]["id"] != "S4":
        raise BudgetError("Human authorization wait is only valid inside FULL segment S4")
    if timing["result"] != "WITHIN_BUDGET":
        smoke_segments.mark_budget_exceeded(repo, run_id, now)
        raise BudgetError("FULL segment budget is exhausted; human wait cannot start")
    path, data = _load(repo, run_id)
    if data.get("continuation_blocker") is not None:
        raise BudgetError("Smoke invocation recovery is blocked; human wait cannot start")
    if _active_invocations(data):
        raise BudgetError("A smoke stage invocation is active; human wait cannot start")

    if gate_type != HUMAN_WAIT_WAIVER_AUTHORIZATION:
        raise BudgetError("No identity contract is implemented for gate type {}".format(gate_type))
    identity = _waiver_gate_identity(
        repo,
        run_id,
        verification_report,
        implementation_state_fingerprint,
        failures,
        classification,
    )
    gate_id = _gate_id_from_identity(identity)

    open_wait = _open_human_wait(data)
    if open_wait is not None:
        if open_wait["gate_id"] == gate_id:
            run_state = state.get("state")
            if run_state == "WAITING_FOR_USER":
                _require_waiting_blocker(state, gate_type, gate_id)
            elif run_state != "IN_PROGRESS":
                raise BudgetError(
                    "Open human authorization wait has incompatible canonical run state"
                )
            return {
                "result": "HUMAN_AUTHORIZATION_WAIT_ACTIVE",
                "gate": dict(open_wait),
            }
        raise BudgetError("A different human authorization wait is already active")
    if state.get("state") != "IN_PROGRESS":
        raise BudgetError("A new human authorization wait requires IN_PROGRESS state")
    if any(item.get("gate_id") == gate_id for item in data["human_wait_intervals"]):
        raise BudgetError("A completed human authorization gate cannot be reopened")

    current = _current_time(now, "Human wait start timestamp")
    budget_started = _aware_timestamp(data["started_at_utc"], "Budget start timestamp")
    if current < budget_started:
        raise BudgetError("Human wait cannot start before the smoke budget")
    item = {
        "gate_type": gate_type,
        "gate_id": gate_id,
        "segment_id": segment["segment"]["id"],
        "identity": identity,
        "started_at_utc": current.isoformat(),
        "ended_at_utc": None,
        "authorization": None,
    }
    data["human_wait_intervals"].append(item)
    _save(path, data)
    return {
        "result": "HUMAN_AUTHORIZATION_WAIT_STARTED",
        "gate": dict(item),
    }


def human_wait_authorize(
    repo: Path,
    run_id: str,
    gate_type: str,
    gate_id: str,
    *,
    decision: str,
    verification_report: str,
    failures: list[str],
    classification: str,
    justification: str,
    residual_risk: str,
    compensating_control: str,
    remediation: str,
    expiry: str,
    now: Optional[dt.datetime] = None,
    workspace_guard: Optional[WorkspaceGuard] = None,
    state_guard: Optional[StateGuard] = None,
) -> dict:
    """Persist a structurally complete explicit human decision and close its wait.

    This action intentionally does not require a rooted Kilo marker: it is the
    deterministic bridge that captures the current human RESUME input in the
    validated disposable workspace before the source-root invocation hands off
    to the rooted autonomous continuation.
    """
    _validate_gate_type(gate_type)
    _require_workspace(repo, run_id, workspace_guard)
    state = _human_gate_state(repo, run_id, state_guard)
    path, data = _load(repo, run_id)
    if data.get("continuation_blocker") is not None:
        raise BudgetError("Smoke invocation recovery is blocked; authorization cannot be captured")
    if _active_invocations(data):
        raise BudgetError("A smoke stage invocation is active; authorization cannot be captured")

    open_wait = _open_human_wait(data)
    if open_wait is None:
        raise BudgetError("No human authorization wait is active")
    if open_wait.get("gate_type") != gate_type or open_wait.get("gate_id") != gate_id:
        raise BudgetError("Human authorization does not match the active gate")
    _require_waiting_blocker(state, gate_type, gate_id)
    _require_report_binding(repo, open_wait["identity"])

    authorization = _waiver_authorization_payload(
        open_wait["identity"],
        decision=decision,
        verification_report=verification_report,
        failures=failures,
        classification=classification,
        justification=justification,
        residual_risk=residual_risk,
        compensating_control=compensating_control,
        remediation=remediation,
        expiry=expiry,
    )
    current = _current_time(now, "Human authorization timestamp")
    started = _aware_timestamp(
        open_wait["started_at_utc"], "Human wait start timestamp"
    )
    if current < started:
        raise BudgetError("Human authorization precedes the wait request")

    # Mutate only after every target, gate-binding, and required-field check has
    # passed. Any rejected/invalid RESUME attempt is therefore a pure no-op on
    # the existing open interval.
    open_wait["ended_at_utc"] = current.isoformat()
    open_wait["authorization"] = authorization
    _save(path, data)
    return {
        "result": "HUMAN_AUTHORIZATION_ACCEPTED",
        "gate": dict(open_wait),
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
    current = _current_time(now, "Stage start timestamp")
    budget = check(repo, run_id, current)
    if budget["result"] != "WITHIN_BUDGET":
        raise BudgetError("Pinned smoke performance budget is exhausted")
    try:
        segment_id, scenario_id = smoke_segments.stage_ownership(repo, run_id)
        state = smoke_state.load(repo, run_id)
        if state.get("profile") == "FULL":
            active = smoke_segments.active_segment(repo, run_id)
            expected_source = active.get("source_fingerprint")
            if not isinstance(expected_source, str):
                raise BudgetError("ACTIVE FULL segment is missing its protected source fingerprint")
            if source_fingerprint.lower() != expected_source:
                raise BudgetError("Stage source fingerprint does not match ACTIVE segment source identity")
    except smoke_segments.SegmentError as exc:
        raise BudgetError(str(exc)) from exc
    path, data = _load(repo, run_id)
    invocations = data["stage_invocations"]
    if data.get("continuation_blocker") is not None:
        raise BudgetError("Smoke invocation recovery is blocked; no new stage may start")
    if _open_human_wait(data) is not None:
        raise BudgetError("Human authorization wait is active; no new stage may start")
    if _active_invocations(data):
        raise BudgetError("A smoke stage invocation is already active")
    sequence = 1 + sum(1 for item in invocations if item.get("stage") == stage)
    invocation_id = f"{stage}-{sequence:03d}"
    item = {
        "invocation_id": invocation_id,
        "stage": stage,
        "model": model,
        "segment_id": segment_id,
        "scenario_id": scenario_id,
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
    actions.add_parser("check")
    wait_start_parser = actions.add_parser("human-wait-start")
    wait_start_parser.add_argument("--gate-type", required=True)
    wait_start_parser.add_argument("--verification-report", required=True)
    wait_start_parser.add_argument("--implementation-state-fingerprint", required=True)
    wait_start_parser.add_argument("--failure", action="append", required=True)
    wait_start_parser.add_argument("--classification", required=True)
    authorize_parser = actions.add_parser("human-wait-authorize")
    authorize_parser.add_argument("--gate-type", required=True)
    authorize_parser.add_argument("--gate-id", required=True)
    authorize_parser.add_argument("--decision", required=True)
    authorize_parser.add_argument("--verification-report", required=True)
    authorize_parser.add_argument("--failure", action="append", required=True)
    authorize_parser.add_argument("--classification", required=True)
    authorize_parser.add_argument("--justification", required=True)
    authorize_parser.add_argument("--residual-risk", required=True)
    authorize_parser.add_argument("--compensating-control", required=True)
    authorize_parser.add_argument("--remediation", required=True)
    authorize_parser.add_argument("--expiry", required=True)
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
            result = check(args.repo, args.run_id)
        elif args.action == "human-wait-start":
            result = human_wait_start(
                args.repo,
                args.run_id,
                args.gate_type,
                args.verification_report,
                args.implementation_state_fingerprint,
                args.failure,
                args.classification,
            )
        elif args.action == "human-wait-authorize":
            result = human_wait_authorize(
                args.repo,
                args.run_id,
                args.gate_type,
                args.gate_id,
                decision=args.decision,
                verification_report=args.verification_report,
                failures=args.failure,
                classification=args.classification,
                justification=args.justification,
                residual_risk=args.residual_risk,
                compensating_control=args.compensating_control,
                remediation=args.remediation,
                expiry=args.expiry,
            )
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
    except (
        BudgetError,
        smoke_segments.SegmentError,
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
