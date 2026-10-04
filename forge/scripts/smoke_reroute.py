#!/usr/bin/env python3
"""Deterministic preparation, scoring, and restoration for H06 reroute probes.

This helper owns smoke mechanics only. It never chooses the upstream authority
or continuation command on behalf of the model under test.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import implementation_state
import smoke_mechanics
import smoke_resume


class RerouteProbeError(RuntimeError):
    pass


SCHEMA_VERSION = 1
HANDOFF_PROBE = "u02"

# Hidden harness expectations. These values are never written into the prepared
# repository or reroute ledger before the model returns its own classification.
PROBE_PLAN = {
    "u01": {
        "classifier": "planning",
        "workflow": "/architect",
        "status": "ARCHITECTURE_BLOCKED",
        "owner": "PRODUCT",
        "next_command": "/prd",
        "regeneration_path": "/prd -> /architect -> /project-init -> /spec -> /implement -> /verify",
    },
    "u02": {
        "classifier": "planning",
        "workflow": "/spec",
        "status": "SPEC_BLOCKED",
        "owner": "ARCHITECTURE",
        "next_command": "/architect",
        "regeneration_path": "/architect -> /project-init -> /spec -> /implement -> /verify",
    },
    "u03": {
        "classifier": "planning",
        "workflow": "/implement",
        "status": "IMPLEMENTATION_BLOCKED",
        "owner": "ARCHITECTURE",
        "next_command": "/architect",
        "regeneration_path": "/architect -> /project-init -> /spec -> /implement -> /verify",
    },
    "u04": {
        "classifier": "fix",
        "workflow": "/fix",
        "status": "FIX_BLOCKED",
        "owner": "PRODUCT",
        "next_command": "/prd",
        "regeneration_path": "/prd -> /architect -> /project-init -> /spec -> /implement -> /verify",
    },
    "u05": {
        "classifier": "fix",
        "workflow": "/fix",
        "status": "FIX_BLOCKED",
        "owner": "ARCHITECTURE",
        "next_command": "/architect",
        "regeneration_path": "/architect -> /project-init -> /spec -> /implement -> /verify",
    },
    "u06": {
        "classifier": "fix",
        "workflow": "/fix",
        "status": "FIX_BLOCKED",
        "owner": "PROJECT_INIT",
        "next_command": "/project-init",
        "regeneration_path": "/project-init -> /spec -> /implement -> /verify",
    },
    "u07": {
        "classifier": "fix",
        "workflow": "/fix",
        "status": "FIX_BLOCKED",
        "owner": "SPECIFICATION",
        "next_command": "/spec",
        "regeneration_path": "/spec -> /implement -> /verify",
    },
    "u08": {
        "classifier": "fix",
        "workflow": "/fix",
        "status": "FIX_BLOCKED",
        "owner": "REPOSITORY",
        "next_command": "/fix",
        "regeneration_path": "/fix -> /verify",
    },
}

ALLOWED_OWNERS = {
    "PRODUCT",
    "ARCHITECTURE",
    "PROJECT_INIT",
    "SPECIFICATION",
    "REPOSITORY",
}
ALLOWED_NEXT = {"/prd", "/architect", "/project-init", "/spec", "/implement", "/fix"}
ALLOWED_STATUS = {
    "ARCHITECTURE_BLOCKED",
    "PROJECT_INIT_BLOCKED",
    "SPEC_BLOCKED",
    "IMPLEMENTATION_BLOCKED",
    "FIX_BLOCKED",
}
SMOKE_PREFIX = "docs/verification/smoke/"
NORMAL_EVIDENCE_PREFIXES = ("docs/verification/", "docs/reviews/", "docs/diagnostics/")


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(
        char.isalnum() or char == "-" for char in run_id
    ):
        raise RerouteProbeError("Invalid run ID")


def _repo(repo: Path, run_id: str | None = None) -> Path:
    try:
        return smoke_resume.probe_repo_root(repo, run_id)
    except (smoke_resume.ResumeProbeError, implementation_state.ImplementationStateError) as exc:
        raise RerouteProbeError(str(exc)) from exc


def _ledger_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    folder = repo / "docs" / "verification" / "smoke"
    if not folder.is_dir():
        raise RerouteProbeError("Smoke evidence directory is missing")
    return folder / f"{run_id}.reroute.json"


def _snapshot_path(repo: Path, run_id: str, probe_id: str) -> Path:
    return repo / "docs" / "verification" / "smoke" / (
        f"{run_id}.reroute-snapshot-{probe_id}.json"
    )


def _read_ledger(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "probes": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RerouteProbeError("Reroute probe ledger is unreadable") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != SCHEMA_VERSION
        or set(data) != {"schema_version", "probes"}
        or not isinstance(data.get("probes"), list)
    ):
        raise RerouteProbeError("Malformed reroute probe ledger")
    return data


def _save_json(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def _snapshot_digest(snapshot: dict[str, object]) -> str:
    body = {
        "schema_version": snapshot.get("schema_version"),
        "entries": snapshot.get("entries"),
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return __import__("hashlib").sha256(encoded).hexdigest()


def _load_snapshot(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise RerouteProbeError("Reroute snapshot is unreadable") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != smoke_resume.SCHEMA_VERSION
        or not isinstance(data.get("entries"), list)
        or not isinstance(data.get("snapshot_sha256"), str)
        or _snapshot_digest(data) != data["snapshot_sha256"]
    ):
        raise RerouteProbeError("Malformed or corrupted reroute snapshot")
    return data


def _path(repo: Path, name: str) -> Path:
    try:
        return smoke_resume.probe_path(repo, name)
    except smoke_resume.ResumeProbeError as exc:
        raise RerouteProbeError(str(exc)) from exc


def _names(repo: Path) -> list[str]:
    try:
        return smoke_resume.probe_workspace_names_at_root(repo)
    except smoke_resume.ResumeProbeError as exc:
        raise RerouteProbeError(str(exc)) from exc


def _capture(repo: Path) -> dict[str, object]:
    try:
        return smoke_resume.capture_probe_snapshot_at_root(repo)
    except smoke_resume.ResumeProbeError as exc:
        raise RerouteProbeError(str(exc)) from exc


def _restore(repo: Path, run_id: str, snapshot: dict[str, object]) -> None:
    try:
        smoke_resume.restore_probe_snapshot_at_root(repo, run_id, snapshot)
    except smoke_resume.ResumeProbeError as exc:
        raise RerouteProbeError(str(exc)) from exc


def _snapshot_entry(snapshot: dict[str, object], name: str) -> dict[str, object]:
    entries = snapshot.get("entries")
    if not isinstance(entries, list):
        raise RerouteProbeError("Malformed clean snapshot")
    for raw in entries:
        if isinstance(raw, dict) and raw.get("path") == name:
            return raw
    raise RerouteProbeError(f"Required path is absent from clean snapshot: {name}")


def _require_file(snapshot: dict[str, object], name: str, prefix: str | None = None) -> str:
    if prefix is not None and not name.startswith(prefix):
        raise RerouteProbeError(f"Path must be under {prefix}: {name}")
    entry = _snapshot_entry(snapshot, name)
    if entry.get("kind") != "file":
        raise RerouteProbeError(f"Probe path must be a regular file: {name}")
    return name


def _remove(repo: Path, name: str) -> None:
    target = _path(repo, name)
    try:
        info = target.lstat()
    except FileNotFoundError:
        return
    if target.is_dir() and not target.is_symlink():
        raise RerouteProbeError(f"Refusing to remove directory target: {name}")
    target.unlink()


def _clear_normal_evidence(repo: Path) -> None:
    for name in _names(repo):
        if name.startswith(SMOKE_PREFIX):
            continue
        if any(name.startswith(prefix) for prefix in NORMAL_EVIDENCE_PREFIXES):
            _remove(repo, name)


def _append(repo: Path, name: str, text: str) -> None:
    target = _path(repo, name)
    if not target.is_file() or target.is_symlink():
        raise RerouteProbeError(f"Cannot append reroute fixture text to {name}")
    before = target.read_text(encoding="utf-8")
    target.write_text(before.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def _write_verification(
    repo: Path,
    path: str,
    spec_path: str,
    symptom: str,
    checkpoint_info: dict[str, object],
) -> None:
    target = _path(repo, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    head = checkpoint_info.get("base_head")
    fingerprint = checkpoint_info.get("current_fingerprint")
    if not isinstance(head, str) or not isinstance(fingerprint, str):
        raise RerouteProbeError("Checkpoint identity metadata is unavailable")
    target.write_text(
        "\n".join(
            [
                "# Verification",
                "",
                f"- Specification/change: {spec_path}",
                "- Branch: smoke-run",
                f"- Verification base HEAD SHA: {head}",
                "- Evidence contract version: implementation-state-evidence-v1",
                f"- Verified implementation-state fingerprint: {fingerprint}",
                "- Verification Result: NOT_DONE",
                "- Delivery Gate: BLOCKED",
                "",
                "## Blocking check",
                "",
                symptom,
                "",
            ]
        ),
        encoding="utf-8",
    )


def _validate_context(
    snapshot: dict[str, object],
    prd_path: str,
    architecture_path: str,
    adr_path: str,
    spec_path: str,
    project_instructions: str,
    implementation_paths: list[str],
    verification_path: str,
) -> tuple[str, str, str, str, str, list[str], str]:
    prd_path = _require_file(snapshot, prd_path, "docs/prd/")
    architecture_path = _require_file(snapshot, architecture_path, "docs/architecture/")
    adr_path = _require_file(snapshot, adr_path, "docs/adr/")
    spec_path = _require_file(snapshot, spec_path, "docs/specs/")
    project_instructions = _require_file(snapshot, project_instructions)
    if project_instructions != "AGENTS.md":
        raise RerouteProbeError("Project instructions path must be AGENTS.md")
    verification_path = _require_file(snapshot, verification_path, "docs/verification/")
    if verification_path.startswith(SMOKE_PREFIX):
        raise RerouteProbeError("Verification path must be normal verification evidence")
    implementation_paths = [
        _require_file(snapshot, name) for name in implementation_paths
    ]
    if not implementation_paths:
        raise RerouteProbeError("At least one implementation path is required")
    return (
        prd_path,
        architecture_path,
        adr_path,
        spec_path,
        project_instructions,
        implementation_paths,
        verification_path,
    )


PRODUCT_CONTRADICTION = """## Required empty-input behavior

- When the required value is absent, the endpoint must return HTTP 200 and apply a default.
- For that same absent required value, the endpoint must return HTTP 400 and reject the request.
"""

ARCHITECTURE_CONTRADICTION = """## Runtime decision

- Application runtime: Python 3.8+.
- Application runtime: Node.js 20+.
"""

ADR_CONTRADICTION = """## Persistence decision

The application must persist request state in SQLite across process restarts.
"""

SPEC_ARCHITECTURE_CHANGE = """## Persistence implementation requirement

This specification requires replacing the approved in-memory persistence
strategy with PostgreSQL as part of implementation.
"""

PROJECT_INIT_DRIFT = """## Local runtime configuration

The initialized repository is configured for Node.js 20 and npm.
"""

SPEC_CONTRADICTION = """## Required boundary behavior

- An empty required value is accepted and returns HTTP 200.
- The same empty required value is rejected and returns HTTP 400.
"""


def _apply_probe(
    repo: Path,
    probe_id: str,
    prd_path: str,
    architecture_path: str,
    adr_path: str,
    spec_path: str,
    project_instructions: str,
    implementation_paths: list[str],
    verification_path: str,
    checkpoint_info: dict[str, object],
) -> None:
    _clear_normal_evidence(repo)

    if probe_id == "u01":
        _append(repo, prd_path, PRODUCT_CONTRADICTION)
    elif probe_id == "u02":
        _append(repo, architecture_path, ARCHITECTURE_CONTRADICTION)
        _append(repo, adr_path, ADR_CONTRADICTION)
    elif probe_id == "u03":
        _append(repo, spec_path, SPEC_ARCHITECTURE_CHANGE)
    elif probe_id == "u04":
        _append(repo, prd_path, PRODUCT_CONTRADICTION)
        _write_verification(
            repo,
            verification_path,
            spec_path,
            "The approved requirements demand two incompatible outcomes for the same empty input, so a local code repair cannot establish the intended behavior.",
            checkpoint_info,
        )
    elif probe_id == "u05":
        _write_verification(
            repo,
            verification_path,
            spec_path,
            "Repairing the failing persistence behavior would require replacing the approved in-memory persistence strategy with SQLite.",
            checkpoint_info,
        )
    elif probe_id == "u06":
        _append(repo, project_instructions, PROJECT_INIT_DRIFT)
        _write_verification(
            repo,
            verification_path,
            spec_path,
            "The repository initialization/runtime instructions no longer match the approved architecture, so implementation repair cannot safely proceed against the current initialized project.",
            checkpoint_info,
        )
    elif probe_id == "u07":
        _append(repo, spec_path, SPEC_CONTRADICTION)
        _write_verification(
            repo,
            verification_path,
            spec_path,
            "The active specification contains contradictory acceptance criteria for the same input and must be corrected before implementation can be repaired.",
            checkpoint_info,
        )
    elif probe_id == "u08":
        local = _path(repo, "local-work.txt")
        if local.exists() or local.is_symlink():
            raise RerouteProbeError("Repository-state probe target already exists")
        local.write_text("unrelated local work that must be preserved\n", encoding="utf-8")
        _write_verification(
            repo,
            verification_path,
            spec_path,
            "The implementation defect is understood, but unrelated local repository work is present and must be preserved before the same repair can safely continue.",
            checkpoint_info,
        )
    else:
        raise RerouteProbeError("Unknown reroute probe ID")


def _normal_evidence_has_answer_leak(repo: Path, verification_path: str) -> bool:
    target = _path(repo, verification_path)
    if not target.exists():
        return False
    text = target.read_text(encoding="utf-8")
    return "### Owner" in text or "NEXT_COMMAND:" in text or "Next command:" in text


def _probe_checks(
    repo: Path,
    probe_id: str,
    clean_snapshot: dict[str, object],
    prepared_snapshot: dict[str, object],
    prd_path: str,
    architecture_path: str,
    adr_path: str,
    spec_path: str,
    project_instructions: str,
    verification_path: str,
) -> dict[str, bool]:
    entries = prepared_snapshot.get("entries")
    if not isinstance(entries, list):
        raise RerouteProbeError("Malformed prepared reroute snapshot")
    names = {
        str(item.get("path"))
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("path"), str)
    }
    plan = PROBE_PLAN[probe_id]
    is_fix = plan["classifier"] == "fix"

    checks = {
        "prepared_state_differs": (
            prepared_snapshot["snapshot_sha256"] != clean_snapshot["snapshot_sha256"]
        ),
        "normal_verification_shape": (
            verification_path in names if is_fix else verification_path not in names
        ),
        "review_evidence_absent": not any(name.startswith("docs/reviews/") for name in names),
        "diagnostic_evidence_absent": not any(
            name.startswith("docs/diagnostics/") for name in names
        ),
        "expected_answer_not_written_to_verification": not _normal_evidence_has_answer_leak(
            repo, verification_path
        ),
    }

    if probe_id in {"u01", "u04"}:
        checks["product_contradiction_present"] = (
            "same absent required value" in _path(repo, prd_path).read_text(encoding="utf-8")
        )
    elif probe_id == "u02":
        checks["architecture_conflict_present"] = (
            "Node.js 20+" in _path(repo, architecture_path).read_text(encoding="utf-8")
            and "SQLite across process restarts"
            in _path(repo, adr_path).read_text(encoding="utf-8")
        )
    elif probe_id == "u03":
        checks["unapproved_architecture_change_present"] = (
            "PostgreSQL" in _path(repo, spec_path).read_text(encoding="utf-8")
        )
    elif probe_id == "u06":
        checks["project_init_drift_present"] = (
            "Node.js 20 and npm"
            in _path(repo, project_instructions).read_text(encoding="utf-8")
        )
    elif probe_id == "u07":
        checks["specification_contradiction_present"] = (
            "same empty required value"
            in _path(repo, spec_path).read_text(encoding="utf-8")
        )
    elif probe_id == "u08":
        checks["repository_state_present"] = "local-work.txt" in names

    return checks


def prepare(
    repo: Path,
    run_id: str,
    probe_id: str,
    checkpoint_label: str,
    prd_path: str,
    architecture_path: str,
    adr_path: str,
    spec_path: str,
    project_instructions: str,
    implementation_paths: list[str],
    verification_path: str,
) -> dict[str, object]:
    repo = _repo(repo, run_id)
    if probe_id not in PROBE_PLAN:
        raise RerouteProbeError("Unknown reroute probe ID")
    ledger_path = _ledger_path(repo, run_id)
    ledger = _read_ledger(ledger_path)
    probes = ledger["probes"]
    assert isinstance(probes, list)

    matches = [
        item
        for item in probes
        if isinstance(item, dict) and item.get("probe_id") == probe_id
    ]
    if len(matches) > 1:
        raise RerouteProbeError("Duplicate reroute probe ledger entries are invalid")
    retry_record: dict[str, object] | None = None
    if matches:
        existing = matches[0]
        if existing.get("restored") is not True:
            raise RerouteProbeError("Reroute probe is still active")
        if existing.get("probe_result") != "NOT_SCORED":
            raise RerouteProbeError("Scored reroute probe is immutable and cannot be retried")
        retry_record = existing
    if any(isinstance(item, dict) and not item.get("restored", False) for item in probes):
        raise RerouteProbeError("Restore the active reroute probe before preparing another")

    checkpoint_info = smoke_mechanics.check_checkpoint(repo, run_id, checkpoint_label)
    if checkpoint_info["result"] != "MATCH":
        raise RerouteProbeError("Clean checkpoint drifted before reroute probe")

    snapshot = _capture(repo)
    (
        prd_path,
        architecture_path,
        adr_path,
        spec_path,
        project_instructions,
        implementation_paths,
        verification_path,
    ) = _validate_context(
        snapshot,
        prd_path,
        architecture_path,
        adr_path,
        spec_path,
        project_instructions,
        implementation_paths,
        verification_path,
    )

    snap_path = _snapshot_path(repo, run_id, probe_id)
    if snap_path.exists():
        raise RerouteProbeError("Reroute snapshot already exists")
    _save_json(snap_path, snapshot)

    try:
        _apply_probe(
            repo,
            probe_id,
            prd_path,
            architecture_path,
            adr_path,
            spec_path,
            project_instructions,
            implementation_paths,
            verification_path,
            checkpoint_info,
        )
        prepared = _capture(repo)
        checks = _probe_checks(
            repo,
            probe_id,
            snapshot,
            prepared,
            prd_path,
            architecture_path,
            adr_path,
            spec_path,
            project_instructions,
            verification_path,
        )
        if not all(checks.values()):
            raise RerouteProbeError(
                "Prepared reroute probe failed validation: {}".format(
                    ", ".join(key for key, ok in checks.items() if not ok)
                )
            )
    except Exception:
        _restore(repo, run_id, snapshot)
        snap_path.unlink(missing_ok=True)
        raise

    plan = PROBE_PLAN[probe_id]
    attempt_count = 1
    if retry_record is not None:
        prior_attempts = retry_record.get("attempt_count", 1)
        if not isinstance(prior_attempts, int) or prior_attempts < 1:
            raise RerouteProbeError("Malformed reroute probe attempt count")
        attempt_count = prior_attempts + 1

    record = {
        "probe_id": probe_id,
        "snapshot_file": snap_path.name,
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "prepared_snapshot_sha256": prepared["snapshot_sha256"],
        "checkpoint": checkpoint_label,
        "classifier": plan["classifier"],
        "workflow": plan["workflow"],
        "state": "PREPARED",
        "routing_pass": None,
        "handoff_pass": None,
        "probe_result": None,
        "restored": False,
        "attempt_count": attempt_count,
    }
    if retry_record is None:
        probes.append(record)
    else:
        retry_record.clear()
        retry_record.update(record)
    _save_json(ledger_path, ledger)

    return {
        "probe_id": probe_id,
        "state": "PREPARED",
        "classifier": plan["classifier"],
        "workflow": plan["workflow"],
        "checks": checks,
    }


def _active_probe(ledger: dict[str, object], probe_id: str) -> dict[str, object]:
    probes = ledger.get("probes")
    if not isinstance(probes, list):
        raise RerouteProbeError("Malformed reroute probe ledger")
    matches = [
        item
        for item in probes
        if isinstance(item, dict)
        and item.get("probe_id") == probe_id
        and item.get("restored") is not True
    ]
    if len(matches) != 1:
        raise RerouteProbeError("Expected exactly one active reroute probe")
    return matches[0]


def _require_prepared_unchanged(repo: Path, record: dict[str, object]) -> None:
    expected = record.get("prepared_snapshot_sha256")
    if not isinstance(expected, str):
        raise RerouteProbeError("Prepared reroute probe digest is missing")
    current = _capture(repo)["snapshot_sha256"]
    if current != expected:
        raise RerouteProbeError("Prepared reroute probe changed before deterministic scoring")


def score(
    repo: Path,
    run_id: str,
    probe_id: str,
    actual_status: str,
    actual_owner: str,
    actual_next_command: str,
    reason: str,
) -> dict[str, object]:
    repo = _repo(repo, run_id)
    if probe_id not in PROBE_PLAN:
        raise RerouteProbeError("Unknown reroute probe ID")
    if actual_status not in ALLOWED_STATUS:
        raise RerouteProbeError("Invalid blocked status")
    if actual_owner not in ALLOWED_OWNERS:
        raise RerouteProbeError("Invalid authority owner")
    if actual_next_command not in ALLOWED_NEXT:
        raise RerouteProbeError("Invalid next command")
    if not reason.strip():
        raise RerouteProbeError("Routing reason is required")

    path = _ledger_path(repo, run_id)
    ledger = _read_ledger(path)
    record = _active_probe(ledger, probe_id)
    if record.get("state") != "PREPARED":
        raise RerouteProbeError("Reroute probe has already been scored")
    _require_prepared_unchanged(repo, record)

    expected = PROBE_PLAN[probe_id]
    routing_pass = (
        actual_status == expected["status"]
        and actual_owner == expected["owner"]
        and actual_next_command == expected["next_command"]
    )
    record["actual_status"] = actual_status
    record["actual_owner"] = actual_owner
    record["actual_next_command"] = actual_next_command
    record["reason"] = reason.strip()
    record["routing_pass"] = routing_pass

    if not routing_pass:
        record["state"] = "SCORED"
        record["probe_result"] = "FAIL"
        handoff_required = False
    elif probe_id == HANDOFF_PROBE:
        record["state"] = "ROUTING_PASS_HANDOFF_REQUIRED"
        handoff_required = True
    else:
        record["state"] = "SCORED"
        record["probe_result"] = "PASS"
        handoff_required = False

    _save_json(path, ledger)
    return {
        "probe_id": probe_id,
        "routing_result": "PASS" if routing_pass else "FAIL",
        "handoff_required": handoff_required,
        "regeneration_path": expected["regeneration_path"] if routing_pass else None,
    }


def record_handoff(
    repo: Path,
    run_id: str,
    probe_id: str,
    accepted: bool,
    evidence: str,
) -> dict[str, object]:
    repo = _repo(repo, run_id)
    if probe_id != HANDOFF_PROBE:
        raise RerouteProbeError("Only the representative reroute probe accepts handoff evidence")
    if not evidence.strip():
        raise RerouteProbeError("Handoff evidence is required")

    path = _ledger_path(repo, run_id)
    ledger = _read_ledger(path)
    record = _active_probe(ledger, probe_id)
    if record.get("state") != "ROUTING_PASS_HANDOFF_REQUIRED":
        raise RerouteProbeError("Reroute probe is not awaiting handoff evidence")
    _require_prepared_unchanged(repo, record)

    record["handoff_pass"] = accepted
    record["handoff_evidence"] = evidence.strip()
    record["probe_result"] = "PASS" if accepted else "FAIL"
    record["state"] = "SCORED"
    _save_json(path, ledger)
    return {
        "probe_id": probe_id,
        "handoff_result": "PASS" if accepted else "FAIL",
    }


def restore(repo: Path, run_id: str, probe_id: str) -> dict[str, object]:
    repo = _repo(repo, run_id)
    path = _ledger_path(repo, run_id)
    ledger = _read_ledger(path)
    record = _active_probe(ledger, probe_id)

    snap_name = record.get("snapshot_file")
    expected_digest = record.get("snapshot_sha256")
    checkpoint_label = record.get("checkpoint")
    if not all(isinstance(item, str) for item in (snap_name, expected_digest, checkpoint_label)):
        raise RerouteProbeError("Malformed active reroute probe record")

    snap_path = repo / "docs" / "verification" / "smoke" / str(snap_name)
    snapshot = _load_snapshot(snap_path)
    if snapshot["snapshot_sha256"] != expected_digest:
        raise RerouteProbeError("Reroute snapshot digest does not match ledger")

    _restore(repo, run_id, snapshot)
    checkpoint_result = smoke_mechanics.check_checkpoint(
        repo, run_id, str(checkpoint_label)
    )["result"]
    if checkpoint_result != "MATCH":
        raise RerouteProbeError("Reroute probe restoration did not reproduce checkpoint")

    record["restored"] = True
    record["state"] = "RESTORED"
    if record.get("probe_result") is None:
        record["probe_result"] = "NOT_SCORED"
    _save_json(path, ledger)
    snap_path.unlink()

    return {
        "probe_id": probe_id,
        "state": "RESTORED",
        "checkpoint_result": "MATCH",
        "probe_result": record["probe_result"],
    }


def status(repo: Path, run_id: str) -> dict[str, object]:
    repo = _repo(repo, run_id)
    ledger = _read_ledger(_ledger_path(repo, run_id))
    probes = ledger["probes"]
    assert isinstance(probes, list)
    by_id = {
        item.get("probe_id"): item
        for item in probes
        if isinstance(item, dict) and isinstance(item.get("probe_id"), str)
    }
    complete = (
        set(by_id) == set(PROBE_PLAN)
        and all(
            item.get("restored") is True and item.get("probe_result") == "PASS"
            for item in by_id.values()
        )
        and by_id[HANDOFF_PROBE].get("handoff_pass") is True
    )
    return {
        "result": "PASS" if complete else "INCOMPLETE",
        "completed_probes": sorted(
            probe_id
            for probe_id, item in by_id.items()
            if item.get("restored") is True and item.get("probe_result") == "PASS"
        ),
        "required_probe_count": len(PROBE_PLAN),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)

    prepare_p = actions.add_parser("prepare")
    prepare_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_PLAN))
    prepare_p.add_argument("--checkpoint", required=True)
    prepare_p.add_argument("--prd", required=True)
    prepare_p.add_argument("--architecture", required=True)
    prepare_p.add_argument("--adr", required=True)
    prepare_p.add_argument("--spec", required=True)
    prepare_p.add_argument("--project-instructions", default="AGENTS.md")
    prepare_p.add_argument("--implementation", action="append", default=[])
    prepare_p.add_argument("--verification", required=True)

    score_p = actions.add_parser("score")
    score_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_PLAN))
    score_p.add_argument("--status", required=True)
    score_p.add_argument("--owner", required=True)
    score_p.add_argument("--next-command", required=True)
    score_p.add_argument("--reason", required=True)

    handoff_p = actions.add_parser("record-handoff")
    handoff_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_PLAN))
    handoff_p.add_argument("--result", required=True, choices=["ACCEPTED", "REJECTED"])
    handoff_p.add_argument("--evidence", required=True)

    restore_p = actions.add_parser("restore")
    restore_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_PLAN))

    actions.add_parser("status")

    args = parser.parse_args()
    try:
        if args.action == "prepare":
            result = prepare(
                args.repo,
                args.run_id,
                args.probe_id,
                args.checkpoint,
                args.prd,
                args.architecture,
                args.adr,
                args.spec,
                args.project_instructions,
                args.implementation,
                args.verification,
            )
        elif args.action == "score":
            result = score(
                args.repo,
                args.run_id,
                args.probe_id,
                args.status,
                args.owner,
                args.next_command,
                args.reason,
            )
        elif args.action == "record-handoff":
            result = record_handoff(
                args.repo,
                args.run_id,
                args.probe_id,
                args.result == "ACCEPTED",
                args.evidence,
            )
        elif args.action == "restore":
            result = restore(args.repo, args.run_id, args.probe_id)
        else:
            result = status(args.repo, args.run_id)
        print(json.dumps({"ok": True, **result}))
        return 0
    except (
        RerouteProbeError,
        smoke_resume.ResumeProbeError,
        implementation_state.ImplementationStateError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
