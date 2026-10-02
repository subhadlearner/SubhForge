#!/usr/bin/env python3
"""Deterministic H08 segmented FULL qualification mechanics.

Canonical segment state lives inside the existing smoke state JSON. This helper
owns all segment lifecycle mutations so generic smoke_state.set_values cannot
forge or rewrite pinned qualification contracts or committed segment closes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_mechanics
import smoke_state
import smoke_workspace


class SegmentError(RuntimeError):
    pass


PIN_SCHEMA_VERSION = 1
RUNTIME_SCHEMA_VERSION = 1
SEGMENT_NOT_STARTED = "NOT_STARTED"
SEGMENT_ACTIVE = "ACTIVE"
SEGMENT_COMPLETED = "COMPLETED"
SEGMENT_BUDGET_EXCEEDED = "BUDGET_EXCEEDED"
BETWEEN_SEGMENTS = "BETWEEN_SEGMENTS"


def _now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _aware(value: object, field: str) -> dt.datetime:
    if not isinstance(value, str) or not value.strip():
        raise SegmentError("{} must be a non-empty ISO timestamp".format(field))
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as exc:
        raise SegmentError("{} must be an ISO timestamp".format(field)) from exc
    if parsed.tzinfo is None:
        raise SegmentError("{} must be timezone-aware".format(field))
    return parsed


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")


def _sha256_object(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _config_root(config_root: Optional[Path] = None) -> Path:
    return (config_root or Path(__file__).resolve().parent.parent).resolve()


def _load_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise SegmentError("{} is missing: {}".format(label, path))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SegmentError("{} is unreadable".format(label)) from exc
    if not isinstance(value, dict):
        raise SegmentError("{} must be a JSON object".format(label))
    return value


def _validate_profile_definition(profile: str, definition: dict) -> None:
    required = definition.get("required_scenarios")
    optional = definition.get("optional_scenarios")
    if (
        not isinstance(required, list)
        or not required
        or not all(isinstance(item, str) and item for item in required)
        or len(required) != len(set(required))
    ):
        raise SegmentError("{} required_scenarios must be a unique non-empty list".format(profile))
    if (
        not isinstance(optional, list)
        or not all(isinstance(item, str) and item for item in optional)
        or len(optional) != len(set(optional))
    ):
        raise SegmentError("{} optional_scenarios must be a unique list".format(profile))
    if set(required).intersection(optional):
        raise SegmentError("{} required/optional scenarios must be disjoint".format(profile))

    if profile == "FAST":
        limit = definition.get("limit_minutes")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise SegmentError("FAST limit_minutes must be a positive integer")
        if definition.get("limit_status") != "PROVISIONAL":
            raise SegmentError("FAST limit_status must be PROVISIONAL")
        return

    segments = definition.get("segments")
    if not isinstance(segments, list) or len(segments) != 6:
        raise SegmentError("FULL must define exactly six ordered segments")
    expected_ids = ["S1", "S2", "S3", "S4", "S5", "S6"]
    actual_ids = [item.get("id") if isinstance(item, dict) else None for item in segments]
    if actual_ids != expected_ids:
        raise SegmentError("FULL segment order must be S1..S6")

    flattened = []
    previous_close = None
    for index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            raise SegmentError("FULL segment entries must be objects")
        scenarios = segment.get("scenarios")
        if (
            not isinstance(scenarios, list)
            or not scenarios
            or not all(isinstance(item, str) and item for item in scenarios)
            or len(scenarios) != len(set(scenarios))
        ):
            raise SegmentError("Segment {} scenarios must be unique".format(segment.get("id")))
        limit = segment.get("limit_minutes")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise SegmentError("Segment {} limit_minutes must be positive".format(segment.get("id")))
        if segment.get("limit_status") != "PROVISIONAL":
            raise SegmentError("Segment {} limit_status must be PROVISIONAL".format(segment.get("id")))
        start_checkpoint = segment.get("start_checkpoint")
        close_checkpoint = segment.get("close_checkpoint")
        if not isinstance(start_checkpoint, str) or not start_checkpoint:
            raise SegmentError("Segment {} start_checkpoint is required".format(segment.get("id")))
        if not isinstance(close_checkpoint, str) or not close_checkpoint:
            raise SegmentError("Segment {} close_checkpoint is required".format(segment.get("id")))
        if index == 0:
            if start_checkpoint != "BOOTSTRAP":
                raise SegmentError("S1 must start at BOOTSTRAP")
        elif start_checkpoint != previous_close:
            raise SegmentError("Segment checkpoint adjacency is invalid at {}".format(segment.get("id")))
        previous_close = close_checkpoint
        flattened.extend(scenarios)

    if flattened != required:
        raise SegmentError("FULL segments must cover required_scenarios exactly once and in order")


def _validate_invocation_spec(spec: dict, required_scenarios: list[str]) -> None:
    if spec.get("schema_version") != 1 or spec.get("qualification_profile") != "FULL":
        raise SegmentError("FULL invocation spec schema/profile is unsupported")
    if spec.get("segment_order") != ["S1", "S2", "S3", "S4", "S5", "S6"]:
        raise SegmentError("FULL invocation spec has invalid segment order")
    scenarios = spec.get("scenarios")
    if not isinstance(scenarios, list):
        raise SegmentError("FULL invocation spec scenarios must be a list")
    ids = [item.get("id") if isinstance(item, dict) else None for item in scenarios]
    if ids != required_scenarios or len(ids) != len(set(ids)):
        raise SegmentError("FULL invocation spec must contain all 24 required scenarios exactly once")
    by_id = {item["id"]: item for item in scenarios}
    stale = by_id.get("stale-waiver", {})
    if stale.get("depends_on") != ["waive-review-loop"]:
        raise SegmentError("stale-waiver must depend on waive-review-loop")
    direct = by_id.get("direct-fix-loop", {})
    calls = direct.get("calls")
    owners = [item.get("owner") for item in calls] if isinstance(calls, list) else []
    if owners != ["DeepSeek", "GPT-5.6 Luna", "DeepSeek", "DeepSeek", "DeepSeek", "GPT-5.6 Sol"]:
        raise SegmentError("direct-fix-loop must declare the six-call H08 sequence")
    purposes = [item.get("purpose", "") for item in calls]
    if not any("POLICY_INELIGIBLE" in purpose for purpose in purposes):
        raise SegmentError("direct-fix-loop must declare Luna POLICY_INELIGIBLE")
    budget = spec.get("call_budget")
    if not isinstance(budget, dict) or budget.get("baseline_total") != 50 or budget.get("maximum_total") != 51:
        raise SegmentError("FULL invocation spec must pin 50/51 call arithmetic")

    expected_zero = {
        "static-release-gate",
        "identical-commit-freshness",
        "content-mutation-stale-evidence",
        "mode-type-identity",
        "stale-waiver",
        "malformed-evidence",
        "evidence-exclusion",
        "static-claude-routing",
    }
    declared_zero = spec.get("zero_substantive_call_scenarios")
    if (
        not isinstance(declared_zero, list)
        or set(declared_zero) != expected_zero
        or len(declared_zero) != len(expected_zero)
    ):
        raise SegmentError("FULL invocation spec must declare exactly the eight zero-call scenarios")

    optional = []
    baseline_by_segment = {segment_id: 0 for segment_id in spec["segment_order"]}
    baseline_by_owner = {"GPT-5.6 Sol": 0, "GPT-5.6 Luna": 0, "DeepSeek": 0}
    for scenario in scenarios:
        calls = scenario.get("calls", [])
        if not isinstance(calls, list):
            raise SegmentError("Scenario calls must be a list")
        if scenario["id"] in expected_zero and calls:
            raise SegmentError("Zero-call scenario unexpectedly declares substantive calls")
        for call in calls:
            if not isinstance(call, dict):
                raise SegmentError("Invocation call entries must be objects")
            owner = call.get("owner")
            if owner not in baseline_by_owner:
                raise SegmentError("Invocation call has unsupported owner: {}".format(owner))
            if call.get("required") is False:
                optional.append(call.get("optional_call_id"))
                continue
            baseline_by_owner[owner] += 1
            baseline_by_segment[scenario["segment"]] += 1

    if optional != ["S4.adversarial-reconcile-only.optional-adversary-recheck"]:
        raise SegmentError("Only the S4 adversarial recheck may be optional")
    if sum(baseline_by_owner.values()) != 50:
        raise SegmentError("FULL invocation baseline must contain exactly 50 required calls")
    if baseline_by_owner != {"GPT-5.6 Sol": 16, "GPT-5.6 Luna": 11, "DeepSeek": 23}:
        raise SegmentError("FULL invocation owner totals must be 16 Sol / 11 Luna / 23 DeepSeek")
    if baseline_by_segment != {"S1": 13, "S2": 7, "S3": 6, "S4": 7, "S5": 8, "S6": 9}:
        raise SegmentError("FULL invocation segment totals must be 13/7/6/7/8/9")


def build_snapshot(config_root: Optional[Path], profile: str) -> dict:
    root = _config_root(config_root)
    profiles = _load_json(root / "smoke" / "profiles.json", "Smoke profile registry")
    definitions = profiles.get("profiles")
    if not isinstance(definitions, dict) or not isinstance(definitions.get(profile), dict):
        raise SegmentError("Unknown smoke profile: {}".format(profile))
    definition = definitions[profile]
    _validate_profile_definition(profile, definition)

    snapshot = {
        "pin_schema_version": PIN_SCHEMA_VERSION,
        "registry_version": profiles.get("registry_version"),
        "profile": profile,
        "required_scenarios": list(definition["required_scenarios"]),
        "optional_scenarios": list(definition["optional_scenarios"]),
    }
    if profile == "FULL":
        spec_path = root / "smoke" / "FULL-INVOCATION-SPEC.json"
        spec = _load_json(spec_path, "FULL invocation spec")
        _validate_invocation_spec(spec, definition["required_scenarios"])
        snapshot["segments"] = json.loads(json.dumps(definition["segments"]))
        snapshot["invocation_spec_sha256"] = _sha256_file(spec_path)
        snapshot["invocation_schema_version"] = spec["schema_version"]
    else:
        snapshot["limit_minutes"] = definition["limit_minutes"]
        snapshot["limit_status"] = definition["limit_status"]
        snapshot["invocation_spec_sha256"] = None
        snapshot["invocation_schema_version"] = None

    snapshot["canonical_sha256"] = _sha256_object(snapshot)
    return snapshot


def _validate_snapshot(snapshot: object) -> dict:
    if not isinstance(snapshot, dict):
        raise SegmentError("Pinned qualification_config is missing or invalid")
    digest = snapshot.get("canonical_sha256")
    if (
        not isinstance(digest, str)
        or len(digest) != 64
        or not all(ch in "0123456789abcdef" for ch in digest)
    ):
        raise SegmentError("Pinned qualification_config hash is invalid")
    unhashed = dict(snapshot)
    unhashed.pop("canonical_sha256", None)
    if _sha256_object(unhashed) != digest:
        raise SegmentError("Pinned qualification_config hash does not match its content")
    profile = snapshot.get("profile")
    if profile not in {"FAST", "FULL"}:
        raise SegmentError("Pinned qualification_config has unsupported profile")
    return snapshot


def _state_context(repo: Path, run_id: str) -> tuple[dict, dict]:
    state = smoke_state.load(repo, run_id)
    context = state.get("context_index")
    if not isinstance(context, dict):
        raise SegmentError("Canonical context_index is invalid")
    return state, context


def _persist_context(repo: Path, run_id: str, state: dict, context: dict) -> dict:
    candidate = dict(state)
    candidate["context_index"] = context
    smoke_state._validate_full_state(candidate, expected_run_id=run_id)
    smoke_state._save(smoke_state.state_path(repo, run_id), candidate)
    return candidate


def pin_qualification(
    repo: Path,
    run_id: str,
    config_root: Optional[Path],
    started_at_utc: str,
) -> dict:
    state, context = _state_context(repo, run_id)
    if any(key in context for key in ("qualification_config", "segment_runtime", "qualification_eligible")):
        raise SegmentError("Qualification configuration is already pinned")
    snapshot = build_snapshot(config_root, str(state["profile"]))
    if snapshot["profile"] != state["profile"]:
        raise SegmentError("Pinned profile does not match canonical smoke state")
    started = _aware(started_at_utc, "Qualification start timestamp")

    context = dict(context)
    context["qualification_config"] = snapshot
    context["qualification_eligible"] = True
    if state["profile"] == "FULL":
        first = snapshot["segments"][0]
        context["segment_runtime"] = {
            "runtime_schema_version": RUNTIME_SCHEMA_VERSION,
            "active_segment": first["id"],
            "active_status": SEGMENT_ACTIVE,
            "active_started_at_utc": started.isoformat(),
            "closed_segments": [],
            "gap": None,
        }
    else:
        context["segment_runtime"] = None
    _persist_context(repo, run_id, state, context)
    return snapshot


def assert_config_intact(
    repo: Path, run_id: str, config_root: Optional[Path] = None
) -> dict:
    state, context = _state_context(repo, run_id)
    pinned = _validate_snapshot(context.get("qualification_config"))
    if pinned.get("profile") != state.get("profile"):
        raise SegmentError("Pinned qualification profile does not match canonical state")
    live = build_snapshot(config_root, str(state["profile"]))
    if live.get("canonical_sha256") != pinned.get("canonical_sha256"):
        raise SegmentError("Live smoke profile/invocation configuration changed after bootstrap")
    return pinned


def _runtime(context: dict) -> dict:
    runtime = context.get("segment_runtime")
    if not isinstance(runtime, dict):
        raise SegmentError("FULL segmented runtime is missing")
    if runtime.get("runtime_schema_version") != RUNTIME_SCHEMA_VERSION:
        raise SegmentError("Unsupported segment runtime schema")
    closed = runtime.get("closed_segments")
    if not isinstance(closed, list):
        raise SegmentError("closed_segments must be a list")
    return runtime


def active_segment(repo: Path, run_id: str, config_root: Optional[Path] = None) -> dict:
    pinned = assert_config_intact(repo, run_id, config_root)
    state, context = _state_context(repo, run_id)
    if state.get("profile") != "FULL":
        raise SegmentError("Active segments exist only for FULL qualification")
    runtime = _runtime(context)
    segment_id = runtime.get("active_segment")
    if segment_id is None or runtime.get("active_status") not in {SEGMENT_ACTIVE, SEGMENT_BUDGET_EXCEEDED}:
        raise SegmentError("No FULL segment is active or budget-exceeded")
    matches = [item for item in pinned["segments"] if item["id"] == segment_id]
    if len(matches) != 1:
        raise SegmentError("ACTIVE segment is not in pinned configuration")
    return {
        "segment": matches[0],
        "started_at_utc": runtime.get("active_started_at_utc"),
        "qualification_eligible": context.get("qualification_eligible") is True,
    }


def _normalize_evidence_path(repo: Path, value: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise SegmentError("Evidence paths must be repository-relative POSIX paths")
    normalized = value.strip()
    parts = normalized.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise SegmentError("Evidence path contains invalid traversal")
    target = repo.resolve().joinpath(*parts)
    if target.is_symlink():
        raise SegmentError("Evidence path must not be a symlink: {}".format(normalized))
    resolved = target.resolve()
    try:
        resolved.relative_to(repo.resolve())
    except ValueError as exc:
        raise SegmentError("Evidence path escapes repository: {}".format(normalized)) from exc
    if not resolved.is_file():
        raise SegmentError("Evidence file does not exist: {}".format(normalized))
    return normalized, resolved


def evidence_manifest(repo: Path, evidence_paths: list[str]) -> dict:
    if (
        not isinstance(evidence_paths, list)
        or not evidence_paths
        or not all(isinstance(item, str) and item for item in evidence_paths)
    ):
        raise SegmentError("Segment close requires a non-empty evidence path list")
    entries = []
    seen = set()
    for raw in evidence_paths:
        normalized, path = _normalize_evidence_path(repo, raw)
        if normalized in seen:
            raise SegmentError("Evidence manifest contains duplicate paths")
        seen.add(normalized)
        entries.append({"path": normalized, "sha256": _sha256_file(path)})
    entries.sort(key=lambda item: item["path"].encode("utf-8"))
    return {"entries": entries, "sha256": _sha256_object(entries)}


def _budget_path(repo: Path, run_id: str) -> Path:
    return repo.resolve() / "docs" / "verification" / "smoke" / (run_id + ".budget.json")


def _budget_data(repo: Path, run_id: str) -> dict:
    path = _budget_path(repo, run_id)
    if not path.is_file():
        raise SegmentError("Budget ledger is missing")
    data = _load_json(path, "Budget ledger")
    if not isinstance(data.get("stage_invocations"), list) or not isinstance(data.get("human_wait_intervals"), list):
        raise SegmentError("Budget ledger invocation/wait collections are invalid")
    return data


def _segment_ledger_projection(data: dict, segment_id: str) -> dict:
    invocations = [
        item for item in data["stage_invocations"] if item.get("segment_id") == segment_id
    ]
    waits = [
        item for item in data["human_wait_intervals"] if item.get("segment_id") == segment_id
    ]
    return {
        "segment_id": segment_id,
        "stage_invocations": invocations,
        "human_wait_intervals": waits,
    }


def _excluded_wait_seconds(data: dict, segment_id: str, start: dt.datetime, end: dt.datetime) -> float:
    excluded = 0.0
    for interval in data["human_wait_intervals"]:
        if interval.get("segment_id") != segment_id:
            continue
        wait_start = _aware(interval.get("started_at_utc"), "Human wait start timestamp")
        ended = interval.get("ended_at_utc")
        if ended is None:
            wait_end = end
        else:
            wait_end = _aware(ended, "Human wait end timestamp")
        effective_start = max(start, wait_start)
        effective_end = min(end, wait_end)
        if effective_end > effective_start:
            excluded += (effective_end - effective_start).total_seconds()
    return max(0.0, excluded)


def segment_timing(
    repo: Path,
    run_id: str,
    now: Optional[dt.datetime] = None,
    config_root: Optional[Path] = None,
) -> dict:
    current = now or _now()
    if current.tzinfo is None:
        raise SegmentError("Segment timing timestamp must be timezone-aware")
    current_info = active_segment(repo, run_id, config_root)
    segment = current_info["segment"]
    start = _aware(current_info["started_at_utc"], "Segment start timestamp")
    if current < start:
        raise SegmentError("Segment timing timestamp precedes committed segment start")
    data = _budget_data(repo, run_id)
    excluded = _excluded_wait_seconds(data, segment["id"], start, current)
    wall = (current - start).total_seconds()
    charged = max(0.0, wall - excluded)
    limit_seconds = segment["limit_minutes"] * 60
    return {
        "segment_id": segment["id"],
        "started_at_utc": start.isoformat(),
        "wall_elapsed_seconds": round(wall, 3),
        "excluded_human_wait_seconds": round(excluded, 3),
        "elapsed_seconds": round(charged, 3),
        "limit_seconds": limit_seconds,
        "remaining_seconds": round(max(0.0, limit_seconds - charged), 3),
        "result": "PERFORMANCE_BUDGET_EXCEEDED" if charged >= limit_seconds else "WITHIN_BUDGET",
    }


def mark_budget_exceeded(
    repo: Path, run_id: str, now: Optional[dt.datetime] = None
) -> dict:
    timing = segment_timing(repo, run_id, now)
    state, context = _state_context(repo, run_id)
    runtime = _runtime(context)
    if timing["result"] != "PERFORMANCE_BUDGET_EXCEEDED":
        return timing
    if runtime.get("active_status") == SEGMENT_BUDGET_EXCEEDED:
        return timing
    if runtime.get("active_status") != SEGMENT_ACTIVE:
        raise SegmentError("Only ACTIVE segment can become BUDGET_EXCEEDED")
    runtime = json.loads(json.dumps(runtime))
    runtime["active_status"] = SEGMENT_BUDGET_EXCEEDED
    context = dict(context)
    context["segment_runtime"] = runtime
    context["qualification_eligible"] = False
    candidate = dict(state)
    candidate["blocker"] = {
        "code": "PERFORMANCE_BUDGET_EXCEEDED",
        "segment_id": timing["segment_id"],
    }
    candidate["state"] = "BLOCKED"
    candidate["context_index"] = context
    smoke_state._validate_full_state(candidate, expected_run_id=run_id)
    smoke_state._save(smoke_state.state_path(repo, run_id), candidate)
    return timing


def _verify_manifest(repo: Path, manifest: dict) -> None:
    entries = manifest.get("entries")
    if not isinstance(entries, list) or not entries:
        raise SegmentError("Committed evidence manifest is invalid")
    current = []
    for entry in entries:
        if not isinstance(entry, dict):
            raise SegmentError("Committed evidence manifest entry is invalid")
        normalized, path = _normalize_evidence_path(repo, entry.get("path"))
        digest = _sha256_file(path)
        if digest != entry.get("sha256"):
            raise SegmentError("Committed evidence changed: {}".format(normalized))
        current.append({"path": normalized, "sha256": digest})
    current.sort(key=lambda item: item["path"].encode("utf-8"))
    if _sha256_object(current) != manifest.get("sha256"):
        raise SegmentError("Committed evidence manifest digest mismatch")


def _verify_closed_chain(repo: Path, runtime: dict) -> None:
    data = _budget_data(repo, "")
    # This helper is replaced below because run_id is required; kept unreachable
    # to make accidental call sites fail closed during development.
    raise SegmentError("Internal closed-chain validation requires run_id")


def validate_closed_chain(repo: Path, run_id: str, runtime: Optional[dict] = None) -> None:
    if runtime is None:
        _state, context = _state_context(repo, run_id)
        runtime = _runtime(context)
    data = _budget_data(repo, run_id)
    for close in runtime["closed_segments"]:
        _verify_manifest(repo, close["evidence_manifest"])
        projection = _segment_ledger_projection(data, close["segment_id"])
        if _sha256_object(projection) != close.get("ledger_projection_sha256"):
            raise SegmentError("Closed segment ledger projection changed: {}".format(close["segment_id"]))


def _source_fingerprint(source: Path) -> str:
    try:
        return smoke_workspace.source_guard(source.resolve())["fingerprint"]
    except smoke_workspace.SmokeWorkspaceError as exc:
        raise SegmentError("Source guard failed: {}".format(exc)) from exc


def close_segment(
    repo: Path,
    run_id: str,
    source: Path,
    evidence_paths: list[str],
    now: Optional[dt.datetime] = None,
) -> dict:
    state, context = _state_context(repo, run_id)
    pinned = assert_config_intact(repo, run_id)
    if state.get("profile") != "FULL":
        raise SegmentError("Segment close is only valid for FULL")
    runtime = _runtime(context)

    if runtime.get("active_segment") is None and runtime["closed_segments"]:
        # Lost acknowledgement after a committed close is idempotent.
        return dict(runtime["closed_segments"][-1])
    if runtime.get("active_status") != SEGMENT_ACTIVE:
        raise SegmentError("Only ACTIVE segment can close")

    segment_id = runtime["active_segment"]
    segment = next(item for item in pinned["segments"] if item["id"] == segment_id)
    missing = [item for item in segment["scenarios"] if item not in state["completed_scenarios"]]
    if missing:
        raise SegmentError("Segment {} has incomplete scenarios: {}".format(segment_id, ", ".join(missing)))

    data = _budget_data(repo, run_id)
    if any(item.get("status", "ACTIVE") == "ACTIVE" for item in data["stage_invocations"]):
        raise SegmentError("Segment cannot close while a stage invocation is ACTIVE")
    if any(item.get("ended_at_utc") is None for item in data["human_wait_intervals"]):
        raise SegmentError("Segment cannot close while a human authorization wait is open")

    timing = segment_timing(repo, run_id, now)
    if timing["result"] != "WITHIN_BUDGET":
        mark_budget_exceeded(repo, run_id, now)
        raise SegmentError("Segment exceeded its pinned performance budget")

    checkpoint = segment["close_checkpoint"]
    if checkpoint != "QUALIFICATION_EVIDENCE_READY":
        try:
            checkpoint_result = smoke_mechanics.check_checkpoint(repo, run_id, checkpoint)
        except smoke_mechanics.MechanicsError as exc:
            raise SegmentError("Required close checkpoint is unavailable: {}".format(exc)) from exc
        if checkpoint_result.get("result") != "MATCH":
            raise SegmentError("Required close checkpoint drifted: {}".format(checkpoint))
    else:
        checkpoint_result = {"checkpoint": checkpoint, "result": "MATCH"}

    manifest = evidence_manifest(repo, evidence_paths)
    projection = _segment_ledger_projection(data, segment_id)
    current = now or _now()
    if current.tzinfo is None:
        raise SegmentError("Segment close timestamp must be timezone-aware")
    close = {
        "segment_id": segment_id,
        "status": SEGMENT_COMPLETED,
        "started_at_utc": runtime["active_started_at_utc"],
        "closed_at_utc": current.isoformat(),
        "charged_elapsed_seconds": timing["elapsed_seconds"],
        "excluded_human_wait_seconds": timing["excluded_human_wait_seconds"],
        "configured_limit_minutes": segment["limit_minutes"],
        "assigned_scenarios": list(segment["scenarios"]),
        "completed_scenarios": [item for item in segment["scenarios"] if item in state["completed_scenarios"]],
        "checkpoint": checkpoint,
        "checkpoint_fingerprint": checkpoint_result.get("current_fingerprint") or checkpoint_result.get("expected_fingerprint"),
        "source_fingerprint": _source_fingerprint(source),
        "evidence_manifest": manifest,
        "ledger_projection_sha256": _sha256_object(projection),
    }
    runtime = json.loads(json.dumps(runtime))
    runtime["closed_segments"].append(close)
    runtime["active_segment"] = None
    runtime["active_status"] = None
    runtime["active_started_at_utc"] = None
    runtime["gap"] = {
        "state": BETWEEN_SEGMENTS,
        "after_segment": segment_id,
        "started_at_utc": current.isoformat(),
    }
    context = dict(context)
    context["segment_runtime"] = runtime
    _persist_context(repo, run_id, state, context)
    return close


def open_next_segment(
    repo: Path,
    run_id: str,
    source: Path,
    now: Optional[dt.datetime] = None,
) -> dict:
    state, context = _state_context(repo, run_id)
    pinned = assert_config_intact(repo, run_id)
    if state.get("profile") != "FULL":
        raise SegmentError("Segment open is only valid for FULL")
    runtime = _runtime(context)

    if runtime.get("active_segment") is not None:
        # Lost acknowledgement after a committed open returns the original start.
        return {
            "segment_id": runtime["active_segment"],
            "started_at_utc": runtime["active_started_at_utc"],
            "status": runtime["active_status"],
        }
    if context.get("qualification_eligible") is not True:
        raise SegmentError("Qualification is permanently ineligible for PASS")
    if not runtime["closed_segments"]:
        raise SegmentError("S1 is opened only by bootstrap")

    validate_closed_chain(repo, run_id, runtime)
    data = _budget_data(repo, run_id)
    if any(item.get("status", "ACTIVE") == "ACTIVE" for item in data["stage_invocations"]):
        raise SegmentError("Next segment cannot open while a stage invocation is ACTIVE")
    if any(item.get("ended_at_utc") is None for item in data["human_wait_intervals"]):
        raise SegmentError("Next segment cannot open while a human authorization wait is open")

    last_close = runtime["closed_segments"][-1]
    if _source_fingerprint(source) != last_close.get("source_fingerprint"):
        context = dict(context)
        context["qualification_eligible"] = False
        runtime = json.loads(json.dumps(runtime))
        runtime["gap"] = {**(runtime.get("gap") or {}), "drift_detected": True}
        context["segment_runtime"] = runtime
        _persist_context(repo, run_id, state, context)
        raise SegmentError("Source drift detected during BETWEEN_SEGMENTS gap")

    order = [item["id"] for item in pinned["segments"]]
    index = order.index(last_close["segment_id"])
    if index + 1 >= len(order):
        raise SegmentError("All FULL segments are already closed")
    segment = pinned["segments"][index + 1]
    if segment["start_checkpoint"] != last_close["checkpoint"]:
        raise SegmentError("Pinned segment checkpoint adjacency is inconsistent")
    try:
        checkpoint_result = smoke_mechanics.check_checkpoint(
            repo, run_id, segment["start_checkpoint"]
        )
    except smoke_mechanics.MechanicsError as exc:
        raise SegmentError("Required start checkpoint is unavailable: {}".format(exc)) from exc
    if checkpoint_result.get("result") != "MATCH":
        raise SegmentError("Required start checkpoint drifted: {}".format(segment["start_checkpoint"]))

    current = now or _now()
    if current.tzinfo is None:
        raise SegmentError("Segment start timestamp must be timezone-aware")
    runtime = json.loads(json.dumps(runtime))
    runtime["active_segment"] = segment["id"]
    runtime["active_status"] = SEGMENT_ACTIVE
    runtime["active_started_at_utc"] = current.isoformat()
    runtime["gap"] = None
    context = dict(context)
    context["segment_runtime"] = runtime
    _persist_context(repo, run_id, state, context)
    return {
        "segment_id": segment["id"],
        "started_at_utc": current.isoformat(),
        "status": SEGMENT_ACTIVE,
    }


def stage_ownership(repo: Path, run_id: str) -> tuple[str, str]:
    state = smoke_state.load(repo, run_id)
    if state.get("profile") != "FULL":
        return ("FAST", str(state.get("current_scenario") or state.get("current_stage")))
    info = active_segment(repo, run_id)
    scenario = state.get("current_scenario") or state.get("current_stage")
    if scenario not in info["segment"]["scenarios"]:
        raise SegmentError(
            "Current scenario/stage {} is not owned by ACTIVE segment {}".format(
                scenario, info["segment"]["id"]
            )
        )
    return info["segment"]["id"], str(scenario)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)

    pin = actions.add_parser("pin")
    pin.add_argument("--config-root", type=Path)
    pin.add_argument("--started-at-utc", required=True)

    actions.add_parser("status")

    close = actions.add_parser("close")
    close.add_argument("--source", type=Path, required=True)
    close.add_argument("--evidence", action="append", required=True)

    open_p = actions.add_parser("open-next")
    open_p.add_argument("--source", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.action == "pin":
            result = pin_qualification(args.repo, args.run_id, args.config_root, args.started_at_utc)
        elif args.action == "status":
            state, context = _state_context(args.repo, args.run_id)
            result = {
                "qualification_config": _validate_snapshot(context.get("qualification_config")),
                "qualification_eligible": context.get("qualification_eligible"),
                "segment_runtime": context.get("segment_runtime"),
            }
        elif args.action == "close":
            result = close_segment(args.repo, args.run_id, args.source, args.evidence)
        else:
            result = open_next_segment(args.repo, args.run_id, args.source)
        print(json.dumps({"ok": True, "result": result}))
        return 0
    except (
        SegmentError,
        smoke_state.SmokeStateError,
        smoke_mechanics.MechanicsError,
        smoke_workspace.SmokeWorkspaceError,
        OSError,
        ValueError,
        KeyError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
