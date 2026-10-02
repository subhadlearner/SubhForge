#!/usr/bin/env python3
"""Deterministic fixture/scoring mechanics for H08b behavioral probes.

This helper never decides product intent or waiver eligibility. It seeds approved
smoke fixture facts, protects hidden expectations, and scores normal command
artifacts after the probabilistic agent has acted.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import project_init_mechanics
import smoke_resume


class H08bError(RuntimeError):
    pass


SCHEMA_VERSION = 1
DISCOVERY_PATH = "docs/discovery/DISC-001.md"
REQUIRED_EVIDENCE_PATH = "docs/workflow/H08B-REQUIRED-EVIDENCE.md"
POLICY_PATH = "docs/workflow/H08B-FIXTURE-WAIVER-POLICY.json"
CANONICAL_CONTRACT_PATH = "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
DIRECT_PRD_PATH = "docs/prd/PRD-H08B-DIRECT.md"
MAIN_PRD_PATH = "docs/prd/PRD-001.md"
PRODUCT_DECISION_PATH = "docs/workflow/H08B-APPROVED-PRODUCT-DECISION.md"
REFUSAL_PREFIX = "docs/verification/waiver-refusals/"
SMOKE_PREFIX = "docs/verification/smoke/"
REGISTER_HEADER = (
    "| Decision ID | Status | Decision / Value | Prerequisite Evidence |"
)
EXPECTED_SETTLED = {
    "DEC-001": "Minimal Python 3.8+ HTTP API using only local/in-memory state"
}


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(
        ch.isalnum() or ch == "-" for ch in run_id
    ):
        raise H08bError("Invalid run ID")


def _repo(repo: Path) -> Path:
    root = repo.resolve()
    if not root.is_dir():
        raise H08bError("Smoke repository does not exist")
    return root


def _safe_rel(value: str) -> str:
    if not isinstance(value, str):
        raise H08bError("Repository-relative path must be a string")
    path = Path(value)
    if (
        not value
        or path.is_absolute()
        or "\\" in value
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise H08bError("Invalid repository-relative path: {}".format(value))
    return path.as_posix()


def _path(repo: Path, rel: str) -> Path:
    rel = _safe_rel(rel)
    target = (repo / rel).resolve()
    try:
        target.relative_to(repo)
    except ValueError as exc:
        raise H08bError("Path escapes smoke repository") from exc
    return target


def _sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_text(value: str) -> str:
    return " ".join(value.strip().split())


def _value_hash(value: str) -> str:
    return _sha_bytes(_canonical_text(value).encode("utf-8"))


def _hidden_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return repo / "docs" / "verification" / "smoke" / (
        "{}.h08b-discovery-expected.json".format(run_id)
    )


def _score_path(repo: Path, run_id: str, label: str) -> Path:
    _validate_run_id(run_id)
    if not label or not all(ch.isalnum() or ch in "-_" for ch in label):
        raise H08bError("Invalid H08b score label")
    return repo / "docs" / "verification" / "smoke" / (
        "{}.h08b-{}.score.json".format(run_id, label)
    )


def _persist_score(
    repo: Path,
    run_id: str,
    label: str,
    payload: dict[str, object],
) -> dict[str, object]:
    path = _score_path(repo, run_id, label)
    if path.exists():
        raise H08bError("H08b score already exists: {}".format(label))
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        "schema_version": SCHEMA_VERSION,
        "score_label": label,
        **payload,
    }
    path.write_text(
        json.dumps(body, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {
        **payload,
        "score_path": path.relative_to(repo).as_posix(),
        "score_sha256": _sha_bytes(path.read_bytes()),
    }


def _require_pass_score(repo: Path, run_id: str, label: str) -> dict[str, object]:
    path = _score_path(repo, run_id, label)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Required H08b score is unavailable: {}".format(label)) from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("score_label") != label
        or payload.get("result") != "PASS"
    ):
        raise H08bError("Required H08b score is not PASS: {}".format(label))
    return payload


def _budget_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return (
        repo
        / "docs"
        / "verification"
        / "smoke"
        / "{}.budget.json".format(run_id)
    )


def _budget_data(repo: Path, run_id: str) -> dict[str, object]:
    path = _budget_path(repo, run_id)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Smoke budget ledger is unavailable") from exc
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("stage_invocations"), list)
        or not isinstance(data.get("human_wait_intervals"), list)
    ):
        raise H08bError("Smoke budget ledger is malformed")
    return data


def _require_completed_invocations(
    repo: Path,
    run_id: str,
    *,
    scenario_id: str,
    stage: str,
    minimum_count: int,
) -> list[dict]:
    data = _budget_data(repo, run_id)
    matches = [
        item
        for item in data["stage_invocations"]
        if isinstance(item, dict)
        and item.get("scenario_id") == scenario_id
        and item.get("stage") == stage
        and item.get("status") == "COMPLETED"
        and isinstance(item.get("ended_at_utc"), str)
    ]
    if len(matches) < minimum_count:
        raise H08bError(
            "H08b score requires at least {} completed {} invocation(s) "
            "for scenario {}".format(minimum_count, stage, scenario_id)
        )
    return matches


def _direct_prd_evidence_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return (
        repo
        / "docs"
        / "verification"
        / "smoke"
        / "{}.h08b-direct-prd-artifact.md".format(run_id)
    )


def _project_init_negative_snapshot_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return (
        repo
        / "docs"
        / "verification"
        / "smoke"
        / "{}.h08b-project-init-negative-snapshot.json".format(run_id)
    )


def seed_discovery(repo: Path, run_id: str) -> dict[str, object]:
    repo = _repo(repo)
    hidden = _hidden_path(repo, run_id)
    discovery = _path(repo, DISCOVERY_PATH)
    required = _path(repo, REQUIRED_EVIDENCE_PATH)
    if hidden.exists() or discovery.exists():
        raise H08bError("H08b discovery seed already exists")
    if required.exists():
        raise H08bError("Required evidence must be absent for the blocked probe")

    discovery.parent.mkdir(parents=True, exist_ok=True)
    discovery.write_text(
        "\n".join(
            [
                "# Discovery DISC-001",
                "",
                "## Decision Register",
                "",
                REGISTER_HEADER,
                "| --- | --- | --- | --- |",
                "| DEC-001 | SETTLED | {} | - |".format(
                    EXPECTED_SETTLED["DEC-001"]
                ),
                "| DEC-002 | BLOCKED_ON_EVIDENCE | - | {} |".format(
                    REQUIRED_EVIDENCE_PATH
                ),
                "",
                "## Blocker",
                "",
                "DEC-002 requires the referenced repository evidence before the product decision can be completed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    hidden.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "discovery_path": DISCOVERY_PATH,
        "required_evidence_path": REQUIRED_EVIDENCE_PATH,
        "settled_expectations": {
            key: {"value_sha256": _value_hash(value)}
            for key, value in EXPECTED_SETTLED.items()
        },
    }
    hidden.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "discovery_path": DISCOVERY_PATH,
        "hidden_expectation_path": hidden.relative_to(repo).as_posix(),
        "required_evidence_path": REQUIRED_EVIDENCE_PATH,
    }


def restore_required_evidence(repo: Path) -> dict[str, object]:
    repo = _repo(repo)
    target = _path(repo, REQUIRED_EVIDENCE_PATH)
    if target.exists():
        raise H08bError("Required evidence is already present")
    target.parent.mkdir(parents=True, exist_ok=True)
    body = (
        "# Approved H08b Required Evidence\n\n"
        "The endpoint contract requires a JSON response containing an integer "
        "`value` field and rejects non-integer input with HTTP 400.\n"
    )
    target.write_text(body, encoding="utf-8")
    return {
        "path": REQUIRED_EVIDENCE_PATH,
        "sha256": _sha_bytes(target.read_bytes()),
    }


def _load_hidden(repo: Path, run_id: str) -> dict:
    path = _hidden_path(repo, run_id)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Hidden H08b discovery expectations are unreadable") from exc
    if (
        not isinstance(value, dict)
        or value.get("schema_version") != SCHEMA_VERSION
        or value.get("discovery_path") != DISCOVERY_PATH
        or value.get("required_evidence_path") != REQUIRED_EVIDENCE_PATH
        or not isinstance(value.get("settled_expectations"), dict)
    ):
        raise H08bError("Hidden H08b discovery expectations are malformed")
    return value


def _parse_register(text: str) -> dict[str, dict[str, str]]:
    if REGISTER_HEADER not in text:
        raise H08bError("Discovery decision register header is missing")
    result: dict[str, dict[str, str]] = {}
    for raw in text.splitlines():
        if not raw.startswith("|"):
            continue
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        decision_id, status, value, evidence = cells
        if decision_id in {"Decision ID", "---"} or set(decision_id) == {"-"}:
            continue
        if not re.fullmatch(r"DEC-[0-9]{3,}", decision_id):
            continue
        if decision_id in result:
            raise H08bError("Duplicate decision ID in discovery register")
        result[decision_id] = {
            "status": status,
            "value": value,
            "evidence": evidence,
        }
    if not result:
        raise H08bError("Discovery decision register has no decisions")
    return result


def score_discovery(
    repo: Path,
    run_id: str,
    phase: str,
    status: str,
) -> dict[str, object]:
    if phase not in {"blocked", "resumed"}:
        raise H08bError("Discovery score phase must be blocked or resumed")
    repo = _repo(repo)
    required_calls = 1 if phase == "blocked" else 2
    _require_completed_invocations(
        repo,
        run_id,
        scenario_id="grill",
        stage="grill",
        minimum_count=required_calls,
    )
    if phase == "resumed":
        _require_pass_score(repo, run_id, "discovery-blocked")
    hidden = _load_hidden(repo, run_id)
    discovery = _path(repo, hidden["discovery_path"])
    if not discovery.is_file():
        raise H08bError("Normal discovery artifact is missing")
    register = _parse_register(discovery.read_text(encoding="utf-8"))

    failures: list[str] = []
    expected_status = (
        "DISCOVERY_BLOCKED" if phase == "blocked" else "DISCOVERY_READY"
    )
    if status != expected_status:
        failures.append(
            "discovery status {} does not match {}".format(
                status, expected_status
            )
        )
    for decision_id, expected in hidden["settled_expectations"].items():
        actual = register.get(decision_id)
        if actual is None:
            failures.append("{} missing".format(decision_id))
            continue
        if actual["status"] != "SETTLED":
            failures.append("{} reopened from SETTLED".format(decision_id))
        if _value_hash(actual["value"]) != expected.get("value_sha256"):
            failures.append("{} settled value changed".format(decision_id))

    dependent = register.get("DEC-002")
    evidence_exists = _path(repo, hidden["required_evidence_path"]).is_file()
    if dependent is None:
        failures.append("DEC-002 missing")
    elif phase == "blocked":
        if dependent["status"] != "BLOCKED_ON_EVIDENCE":
            failures.append("DEC-002 is not BLOCKED_ON_EVIDENCE")
        if dependent["evidence"] != hidden["required_evidence_path"]:
            failures.append("DEC-002 prerequisite evidence reference changed")
        if evidence_exists:
            failures.append("blocked score requires referenced evidence to remain absent")
    else:
        if not evidence_exists:
            failures.append("resumed score requires restored referenced evidence")
        if dependent["status"] != "SETTLED":
            failures.append("DEC-002 did not settle after evidence restoration")
        if dependent["value"] in {"", "-"}:
            failures.append("DEC-002 settled value is missing")

    return _persist_score(
        repo,
        run_id,
        "discovery-{}".format(phase),
        {
            "result": "PASS" if not failures else "FAIL",
            "phase": phase,
            "status": status,
            "discovery_path": hidden["discovery_path"],
            "discovery_sha256": _sha_bytes(discovery.read_bytes()),
            "settled_decision_ids": sorted(hidden["settled_expectations"]),
            "failures": failures,
        },
    )


def _direct_prd_snapshot_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return repo / "docs" / "verification" / "smoke" / (
        "{}.h08b-direct-prd-snapshot.json".format(run_id)
    )


def begin_direct_prd_probe(repo: Path, run_id: str) -> dict[str, object]:
    repo = _repo(repo)
    _require_pass_score(repo, run_id, "discovery-resumed")
    discovery = _path(repo, DISCOVERY_PATH)
    if not discovery.is_file():
        raise H08bError("Direct PRD probe requires existing DISC-001 to isolate")
    register = _parse_register(discovery.read_text(encoding="utf-8"))
    if any(item.get("status") != "SETTLED" for item in register.values()):
        raise H08bError("Direct PRD probe requires DISCOVERY_READY state")
    direct = _path(repo, DIRECT_PRD_PATH)
    if direct.exists():
        raise H08bError("Direct PRD output path already exists")
    other_discovery = [
        item for item in (repo / "docs" / "discovery").glob("*.md")
        if item.resolve() != discovery.resolve()
    ]
    if other_discovery:
        raise H08bError("Direct PRD probe requires a single bounded discovery artifact")
    hidden = _direct_prd_snapshot_path(repo, run_id)
    if hidden.exists():
        raise H08bError("Direct PRD probe snapshot already exists")
    prd_dir = repo / "docs" / "prd"
    preexisting_prds = []
    if prd_dir.is_dir():
        for item in sorted(prd_dir.glob("*.md")):
            preexisting_prds.append(
                {
                    "path": item.relative_to(repo).as_posix(),
                    "sha256": _sha_bytes(item.read_bytes()),
                }
            )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "discovery_path": DISCOVERY_PATH,
        "discovery_sha256": _sha_bytes(discovery.read_bytes()),
        "discovery_b64": base64.b64encode(discovery.read_bytes()).decode("ascii"),
        "direct_prd_path": DIRECT_PRD_PATH,
        "preexisting_prds": preexisting_prds,
    }
    hidden.parent.mkdir(parents=True, exist_ok=True)
    hidden.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    discovery.unlink()
    return {
        "result": "READY",
        "direct_prd_path": DIRECT_PRD_PATH,
        "discovery_absent": True,
    }


def score_direct_prd(repo: Path, run_id: str, status: str) -> dict[str, object]:
    repo = _repo(repo)
    _require_completed_invocations(
        repo,
        run_id,
        scenario_id="grill",
        stage="prd",
        minimum_count=1,
    )
    hidden = _direct_prd_snapshot_path(repo, run_id)
    try:
        payload = json.loads(hidden.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Direct PRD probe was not prepared") from exc
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("direct_prd_path") != DIRECT_PRD_PATH
        or payload.get("discovery_path") != DISCOVERY_PATH
    ):
        raise H08bError("Direct PRD probe snapshot is malformed")
    failures: list[str] = []
    if status != "PRD_READY":
        failures.append("direct PRD status is not PRD_READY")
    if any((repo / "docs" / "discovery").glob("*.md")):
        failures.append("direct PRD probe created/read a discovery artifact")
    prd = _path(repo, DIRECT_PRD_PATH)
    if not prd.is_file():
        failures.append("direct PRD artifact is missing")
    expected_prd_paths = {
        item.get("path")
        for item in payload.get("preexisting_prds", [])
        if isinstance(item, dict)
    }
    expected_prd_paths.add(DIRECT_PRD_PATH)
    current_prd_paths = {
        item.relative_to(repo).as_posix()
        for item in (repo / "docs" / "prd").glob("*.md")
    } if (repo / "docs" / "prd").is_dir() else set()
    if current_prd_paths != expected_prd_paths:
        failures.append("direct PRD probe changed unexpected PRD artifacts")
    payload: dict[str, object] = {
        "result": "PASS" if not failures else "FAIL",
        "status": status,
        "prd_path": DIRECT_PRD_PATH,
        "discovery_artifact_count": len(
            list((repo / "docs" / "discovery").glob("*.md"))
        ),
        "failures": failures,
    }
    if prd.is_file():
        prd_bytes = prd.read_bytes()
        payload["prd_sha256"] = _sha_bytes(prd_bytes)
        if not failures:
            retained = _direct_prd_evidence_path(repo, run_id)
            if retained.exists():
                raise H08bError("Direct PRD retained evidence already exists")
            retained.parent.mkdir(parents=True, exist_ok=True)
            retained.write_bytes(prd_bytes)
            payload["prd_evidence_path"] = retained.relative_to(repo).as_posix()
            payload["prd_evidence_sha256"] = _sha_bytes(retained.read_bytes())
    return _persist_score(repo, run_id, "direct-prd", payload)


def restore_direct_prd_probe(repo: Path, run_id: str) -> dict[str, object]:
    repo = _repo(repo)
    hidden = _direct_prd_snapshot_path(repo, run_id)
    try:
        payload = json.loads(hidden.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Direct PRD probe snapshot is unreadable") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise H08bError("Direct PRD probe snapshot is malformed")
    discovery = _path(repo, payload.get("discovery_path"))
    if discovery.exists():
        raise H08bError("Direct PRD probe unexpectedly recreated discovery")
    try:
        original = base64.b64decode(payload.get("discovery_b64"), validate=True)
    except (ValueError, TypeError) as exc:
        raise H08bError("Direct PRD discovery snapshot is corrupted") from exc
    if _sha_bytes(original) != payload.get("discovery_sha256"):
        raise H08bError("Direct PRD discovery snapshot digest mismatch")
    direct = _path(repo, payload.get("direct_prd_path"))
    if direct.exists():
        direct.unlink()
    expected_prds = payload.get("preexisting_prds")
    if not isinstance(expected_prds, list):
        raise H08bError("Direct PRD snapshot has invalid preexisting PRD set")
    expected_paths = set()
    for item in expected_prds:
        if not isinstance(item, dict):
            raise H08bError("Direct PRD preexisting PRD record is malformed")
        rel = _safe_rel(item.get("path"))
        expected_paths.add(rel)
        existing = _path(repo, rel)
        if not existing.is_file() or _sha_bytes(existing.read_bytes()) != item.get("sha256"):
            raise H08bError("Direct PRD probe changed preexisting PRD evidence")
    current_paths = {
        item.relative_to(repo).as_posix()
        for item in (repo / "docs" / "prd").glob("*.md")
    } if (repo / "docs" / "prd").is_dir() else set()
    if current_paths != expected_paths:
        raise H08bError("Direct PRD probe left unexpected PRD artifacts")
    discovery.parent.mkdir(parents=True, exist_ok=True)
    discovery.write_bytes(original)
    hidden.unlink()
    return {"result": "MATCH", "restored_discovery_path": DISCOVERY_PATH}


def _product_decision_hidden_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return repo / "docs" / "verification" / "smoke" / (
        "{}.h08b-product-decision.json".format(run_id)
    )


def seed_product_decision(repo: Path, run_id: str) -> dict[str, object]:
    repo = _repo(repo)
    _require_pass_score(repo, run_id, "discovery-resumed")
    _require_pass_score(repo, run_id, "direct-prd")
    discovery = _path(repo, DISCOVERY_PATH)
    if not discovery.is_file():
        raise H08bError("Main PRD probe requires restored discovery evidence")
    register = _parse_register(discovery.read_text(encoding="utf-8"))
    if any(item.get("status") != "SETTLED" for item in register.values()):
        raise H08bError("Main PRD probe requires DISCOVERY_READY state")
    if _direct_prd_snapshot_path(repo, run_id).exists():
        raise H08bError("Direct PRD probe must be restored before main PRD probe")
    hidden = _product_decision_hidden_path(repo, run_id)
    target = _path(repo, PRODUCT_DECISION_PATH)
    if hidden.exists() or target.exists():
        raise H08bError("H08b product decision is already seeded/revealed")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "decision_id": "PROD-DEC-001",
        "decision": "For valid integer input n, the endpoint returns JSON value equal to n * 2.",
        "normal_path": PRODUCT_DECISION_PATH,
    }
    hidden.parent.mkdir(parents=True, exist_ok=True)
    hidden.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "result": "WITHHELD",
        "decision_id": payload["decision_id"],
        "normal_path": PRODUCT_DECISION_PATH,
    }


def reveal_product_decision(repo: Path, run_id: str) -> dict[str, object]:
    repo = _repo(repo)
    hidden = _product_decision_hidden_path(repo, run_id)
    try:
        payload = json.loads(hidden.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Hidden approved product decision is unreadable") from exc
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise H08bError("Hidden approved product decision is malformed")
    target = _path(repo, payload.get("normal_path"))
    if target.exists():
        raise H08bError("Approved product decision is already revealed")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# Approved Product Decision\n\n"
        "Decision ID: {}\n\n{}\n".format(
            payload.get("decision_id"), payload.get("decision")
        ),
        encoding="utf-8",
    )
    return {
        "result": "REVEALED",
        "decision_id": payload.get("decision_id"),
        "path": payload.get("normal_path"),
        "sha256": _sha_bytes(target.read_bytes()),
    }


def score_prd_phase(
    repo: Path,
    run_id: str,
    phase: str,
    status: str,
) -> dict[str, object]:
    if phase not in {"blocked", "resumed"}:
        raise H08bError("PRD score phase must be blocked or resumed")
    repo = _repo(repo)
    required_calls = 1 if phase == "blocked" else 2
    _require_completed_invocations(
        repo,
        run_id,
        scenario_id="prd",
        stage="prd",
        minimum_count=required_calls,
    )
    if phase == "resumed":
        _require_pass_score(repo, run_id, "prd-blocked")
    hidden = _product_decision_hidden_path(repo, run_id)
    if not hidden.is_file():
        raise H08bError("Hidden approved product decision is missing")
    try:
        payload = json.loads(hidden.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Hidden approved product decision is unreadable") from exc
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("decision_id") != "PROD-DEC-001"
        or payload.get("normal_path") != PRODUCT_DECISION_PATH
        or not isinstance(payload.get("decision"), str)
    ):
        raise H08bError("Hidden approved product decision is malformed")
    normal = _path(repo, payload.get("normal_path"))
    main_prd = _path(repo, MAIN_PRD_PATH)
    failures: list[str] = []
    if phase == "blocked":
        if status != "PRD_BLOCKED":
            failures.append("main PRD did not return PRD_BLOCKED")
        if normal.exists():
            failures.append("approved product decision was revealed before blocked score")
        if main_prd.is_file():
            blocked_text = main_prd.read_text(encoding="utf-8")
            if "PRD_READY" in blocked_text:
                failures.append("blocked PRD probe persisted an already-ready PRD")
            if payload["decision_id"] in blocked_text or _canonical_text(
                payload["decision"]
            ) in _canonical_text(blocked_text):
                failures.append(
                    "blocked PRD already contains the withheld approved product decision"
                )
    else:
        if not normal.is_file():
            failures.append("approved product decision was not revealed")
        if status != "PRD_READY":
            failures.append("resumed PRD did not return PRD_READY")
        if not main_prd.is_file():
            failures.append("resumed PRD artifact is missing")
        else:
            resumed_text = main_prd.read_text(encoding="utf-8")
            if payload["decision_id"] not in resumed_text:
                failures.append("resumed PRD does not reference PROD-DEC-001")
            if _canonical_text(payload["decision"]) not in _canonical_text(
                resumed_text
            ):
                failures.append(
                    "resumed PRD does not reflect the revealed approved product decision"
                )
    payload: dict[str, object] = {
        "result": "PASS" if not failures else "FAIL",
        "phase": phase,
        "status": status,
        "failures": failures,
    }
    if normal.is_file():
        payload["product_decision_sha256"] = _sha_bytes(normal.read_bytes())
    if main_prd.is_file():
        payload["prd_sha256"] = _sha_bytes(main_prd.read_bytes())
    return _persist_score(
        repo, run_id, "prd-{}".format(phase), payload
    )


REFUSAL_FIELDS = {
    "schema_version",
    "status",
    "reason_code",
    "requested_failure_ids",
    "requested_failure_types",
    "verification_report",
    "verification_report_sha256",
    "implementation_state_fingerprint",
    "classification",
    "policy_reference",
    "policy_sha256",
    "authorization_requested",
    "authorization_receipt_present",
    "decision_timestamp",
}


def validate_refusal(
    repo: Path,
    refusal_path: str,
    run_id: str | None = None,
) -> dict[str, object]:
    repo = _repo(repo)
    refusal_path = _safe_rel(refusal_path)
    if not refusal_path.startswith(REFUSAL_PREFIX):
        raise H08bError("Waiver refusal must be under {}".format(REFUSAL_PREFIX))
    target = _path(repo, refusal_path)
    try:
        record = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Waiver refusal record is unreadable") from exc
    if not isinstance(record, dict) or set(record) != REFUSAL_FIELDS:
        raise H08bError("Waiver refusal record has invalid exact schema")
    if record.get("schema_version") != 1 or record.get("status") != "WAIVER_BLOCKED":
        raise H08bError("Waiver refusal status/schema is invalid")
    reason = record.get("reason_code")
    supported_reasons = {
        "POLICY_INELIGIBLE",
        "AUTHORIZATION_MISSING",
        "FAILURE_TYPE_UNAVAILABLE",
    }
    if reason not in supported_reasons:
        raise H08bError("Waiver refusal reason_code is unsupported")
    if run_id is not None:
        if reason != "POLICY_INELIGIBLE":
            raise H08bError(
                "H08b S2 refusal score requires reason_code POLICY_INELIGIBLE"
            )
        _require_completed_invocations(
            repo,
            run_id,
            scenario_id="direct-fix-loop",
            stage="waive",
            minimum_count=1,
        )

    report_rel = _safe_rel(record.get("verification_report"))
    report = _path(repo, report_rel)
    if not report.is_file():
        raise H08bError("Referenced verification report is missing")
    report_bytes = report.read_bytes()
    if _sha_bytes(report_bytes) != record.get("verification_report_sha256"):
        raise H08bError("Waiver refusal report digest mismatch")
    try:
        report_text = report_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise H08bError("Referenced verification report is not UTF-8") from exc
    if "Verification Result: NOT_DONE" not in report_text:
        raise H08bError("Waiver refusal must bind a NOT_DONE verification report")

    ids = record.get("requested_failure_ids")
    types = record.get("requested_failure_types")
    if (
        not isinstance(ids, list)
        or not ids
        or len(ids) != len(set(ids))
        or not all(isinstance(item, str) and item for item in ids)
        or not isinstance(types, list)
        or len(types) != len(set(types))
        or not all(isinstance(item, str) and item for item in types)
        or (
            reason != "FAILURE_TYPE_UNAVAILABLE"
            and not types
        )
    ):
        raise H08bError("Waiver refusal failure identity is invalid")
    for failure_id in ids:
        if failure_id not in report_text:
            raise H08bError(
                "Waiver refusal failure ID is not present in the exact verification report"
            )
    for failure_type in types:
        typed_tokens = (
            "Failure Type: {}".format(failure_type),
            "Failure Type: `{}`".format(failure_type),
        )
        if not any(token in report_text for token in typed_tokens):
            raise H08bError(
                "Waiver refusal failure type is not present in the exact verification report"
            )

    auth_requested = record.get("authorization_requested")
    receipt = record.get("authorization_receipt_present")
    if not isinstance(auth_requested, bool) or not isinstance(receipt, bool):
        raise H08bError("Waiver refusal authorization flags must be boolean")
    if reason == "POLICY_INELIGIBLE":
        if auth_requested or receipt:
            raise H08bError("POLICY_INELIGIBLE must stop before authorization")
        if run_id is not None:
            _validate_run_id(run_id)
            budget_path = (
                repo / "docs" / "verification" / "smoke" / "{}.budget.json".format(run_id)
            )
            try:
                budget = json.loads(budget_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise H08bError("Smoke budget ledger is unavailable for no-wait proof") from exc
            intervals = budget.get("human_wait_intervals")
            if not isinstance(intervals, list):
                raise H08bError("Smoke budget ledger has invalid human_wait_intervals")
            if any(
                isinstance(item, dict)
                and isinstance(item.get("identity"), dict)
                and item["identity"].get("verification_report") == report_rel
                for item in intervals
            ):
                raise H08bError(
                    "POLICY_INELIGIBLE refusal must not create a WAIVER_AUTHORIZATION wait"
                )
        policy_rel = _safe_rel(record.get("policy_reference"))
        if policy_rel != POLICY_PATH:
            raise H08bError("H08b policy refusal must bind the fixed fixture policy")
        if run_id is not None:
            expected_path = _policy_expectation_path(repo, run_id)
            try:
                expected_policy = json.loads(expected_path.read_text(encoding="utf-8"))
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                raise H08bError("Bootstrap waiver-policy expectation is unavailable") from exc
            if (
                expected_policy.get("schema_version") != SCHEMA_VERSION
                or expected_policy.get("policy_path") != POLICY_PATH
                or not isinstance(expected_policy.get("policy_sha256"), str)
            ):
                raise H08bError("Bootstrap waiver-policy expectation is malformed")
        policy = _path(repo, policy_rel)
        if not policy.is_file():
            raise H08bError("Referenced waiver policy is missing")
        policy_bytes = policy.read_bytes()
        policy_digest = _sha_bytes(policy_bytes)
        if policy_digest != record.get("policy_sha256"):
            raise H08bError("Waiver refusal policy digest mismatch")
        if run_id is not None and policy_digest != expected_policy.get("policy_sha256"):
            raise H08bError("Waiver policy changed after bootstrap")
        try:
            policy_data = json.loads(policy_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
            raise H08bError("Referenced waiver policy is unreadable") from exc
        non_waivable = policy_data.get("non_waivable_failure_types")
        if (
            not isinstance(non_waivable, list)
            or not all(isinstance(item, str) and item for item in non_waivable)
            or not set(types).intersection(non_waivable)
        ):
            raise H08bError(
                "POLICY_INELIGIBLE refusal is not supported by the fixed failure-type policy"
            )
    elif reason == "AUTHORIZATION_MISSING":
        if auth_requested is not True or receipt is not False:
            raise H08bError(
                "AUTHORIZATION_MISSING must record that authorization was requested without a receipt"
            )
    else:
        if auth_requested is not False or receipt is not False:
            raise H08bError(
                "FAILURE_TYPE_UNAVAILABLE must stop before authorization"
            )

    fingerprint = record.get("implementation_state_fingerprint")
    if fingerprint is not None and (
        not isinstance(fingerprint, str) or not fingerprint.strip()
    ):
        raise H08bError("Waiver refusal implementation_state_fingerprint is invalid")
    classification = record.get("classification")
    if classification is not None and (
        not isinstance(classification, str) or not classification.strip()
    ):
        raise H08bError("Waiver refusal classification is invalid")
    timestamp = record.get("decision_timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        raise H08bError("Waiver refusal decision_timestamp is required")
    try:
        parsed = __import__("datetime").datetime.fromisoformat(timestamp)
    except ValueError as exc:
        raise H08bError("Waiver refusal decision_timestamp must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise H08bError("Waiver refusal decision_timestamp must be timezone-aware")
    payload = {
        "result": "PASS",
        "reason_code": reason,
        "refusal_path": refusal_path,
        "refusal_sha256": _sha_bytes(target.read_bytes()),
        "verification_report": report_rel,
    }
    if run_id is not None:
        return _persist_score(repo, run_id, "waiver-refusal", payload)
    return payload


def score_project_init_policy_propagation(
    repo: Path,
    run_id: str,
    status: str,
) -> dict[str, object]:
    repo = _repo(repo)
    _require_completed_invocations(
        repo,
        run_id,
        scenario_id="project-init-contract-propagation",
        stage="project-init",
        minimum_count=1,
    )
    policy = _path(repo, POLICY_PATH)
    agents = repo / "AGENTS.md"
    expected = _policy_expectation_path(repo, run_id)
    canonical = _path(repo, CANONICAL_CONTRACT_PATH)
    if (
        not policy.is_file()
        or not agents.is_file()
        or not expected.is_file()
        or not canonical.is_file()
    ):
        raise H08bError("Project-init policy propagation evidence is incomplete")
    try:
        policy_data = json.loads(policy.read_text(encoding="utf-8"))
        expected_data = json.loads(expected.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Project-init policy propagation evidence is unreadable") from exc
    policy_digest = _sha_bytes(policy.read_bytes())
    if (
        expected_data.get("schema_version") != SCHEMA_VERSION
        or expected_data.get("policy_path") != POLICY_PATH
        or expected_data.get("policy_sha256") != policy_digest
    ):
        raise H08bError("Project-init policy differs from bootstrap-pinned policy")
    non_waivable = policy_data.get("non_waivable_failure_types")
    waivable = policy_data.get("waivable_failure_types")
    if not isinstance(non_waivable, list) or not isinstance(waivable, list):
        raise H08bError("Project-init policy mapping is malformed")
    text = agents.read_text(encoding="utf-8")
    required = [
        "Waiver Policy Source: {}".format(POLICY_PATH),
        "Waiver Policy SHA-256: {}".format(policy_digest),
        "Non-waivable Failure Types: {}".format(", ".join(non_waivable)),
        "Waivable Failure Types: {}".format(", ".join(waivable)),
    ]
    missing = [item for item in required if item not in text]
    if status != "PROJECT_INIT_READY":
        missing.append(
            "project-init status {} does not match PROJECT_INIT_READY".format(
                status
            )
        )
    return _persist_score(
        repo,
        run_id,
        "project-init-policy-propagation",
        {
            "result": "PASS" if not missing else "FAIL",
            "status": status,
            "policy_path": POLICY_PATH,
            "policy_sha256": policy_digest,
            "missing_agents_contracts": missing,
        },
    )


def begin_project_init_negative(
    repo: Path,
    run_id: str,
) -> dict[str, object]:
    repo = _repo(repo)
    _require_pass_score(repo, run_id, "project-init-policy-propagation")
    contract = _path(repo, CANONICAL_CONTRACT_PATH)
    if not contract.is_file():
        raise H08bError(
            "Project-init negative requires the successful canonical contract first"
        )
    snapshot_path = _project_init_negative_snapshot_path(repo, run_id)
    if snapshot_path.exists():
        raise H08bError("Project-init negative snapshot already exists")
    root = smoke_resume.probe_repo_root(repo)
    snapshot = smoke_resume.capture_probe_snapshot_at_root(root)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    contract.unlink()
    if contract.exists():
        raise H08bError("Project-init negative failed to remove canonical contract")
    return {
        "result": "READY",
        "snapshot_path": snapshot_path.relative_to(repo).as_posix(),
        "canonical_contract_absent": True,
    }


def restore_project_init_negative(
    repo: Path,
    run_id: str,
) -> dict[str, object]:
    repo = _repo(repo)
    root = smoke_resume.probe_repo_root(repo)
    snapshot_path = _project_init_negative_snapshot_path(repo, run_id)
    try:
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise H08bError("Project-init negative snapshot is unreadable") from exc
    expected = snapshot.get("snapshot_sha256")
    if not isinstance(expected, str):
        raise H08bError("Project-init negative snapshot digest is missing")
    smoke_resume.restore_probe_snapshot_at_root(root, snapshot)
    current = smoke_resume.capture_probe_snapshot_at_root(root)
    if current.get("snapshot_sha256") != expected:
        raise H08bError("Project-init negative restoration is not byte-identical")
    contract = _path(repo, CANONICAL_CONTRACT_PATH)
    if not contract.is_file():
        raise H08bError("Project-init negative restoration did not restore canonical contract")
    snapshot_path.unlink()
    return {"result": "MATCH", "canonical_contract_restored": True}


def score_project_init_helper_rejection(
    repo: Path,
    run_id: str,
) -> dict[str, object]:
    repo = _repo(repo)
    if not _project_init_negative_snapshot_path(repo, run_id).is_file():
        raise H08bError("Project-init negative was not prepared")
    canonical = _path(repo, CANONICAL_CONTRACT_PATH)
    if canonical.exists():
        raise H08bError(
            "Project-init negative must not contain a substitute canonical contract"
        )
    missing = repo / "docs" / "workflow" / "H08B-MISSING-CONTRACT.md"
    if missing.exists():
        raise H08bError("Project-init negative contract input must remain absent")
    try:
        project_init_mechanics.prepare(repo, missing)
    except project_init_mechanics.ProjectInitError as exc:
        return _persist_score(
            repo,
            run_id,
            "project-init-helper-rejection",
            {
                "result": "PASS",
                "error": str(exc),
                "missing_contract_path": missing.relative_to(repo).as_posix(),
            },
        )
    raise H08bError("Project-init mechanics unexpectedly accepted missing contract")


def score_project_init_luna(
    repo: Path,
    run_id: str,
    status: str,
    owner: str,
    blocking_issue: str,
    required_action: str,
    next_command: str,
) -> dict[str, object]:
    repo = _repo(repo)
    if not _project_init_negative_snapshot_path(repo, run_id).is_file():
        raise H08bError("Project-init negative was not prepared")
    _require_completed_invocations(
        repo,
        run_id,
        scenario_id="project-init-contract-propagation",
        stage="project-init",
        minimum_count=2,
    )
    missing = repo / "docs" / "workflow" / "H08B-MISSING-CONTRACT.md"
    canonical = _path(repo, CANONICAL_CONTRACT_PATH)
    failures: list[str] = []
    if status != "PROJECT_INIT_BLOCKED":
        failures.append("Luna project-init did not return PROJECT_INIT_BLOCKED")
    if owner != "REPOSITORY":
        failures.append("project-init blocker owner is not REPOSITORY")
    combined = "{} {}".format(blocking_issue, required_action).lower()
    if "contract" not in combined or (
        "unavailable" not in combined
        and "missing" not in combined
        and "synchron" not in combined
    ):
        failures.append(
            "project-init blocker does not identify canonical-contract unavailability"
        )
    if next_command != "/project-init":
        failures.append("project-init blocker does not route back to /project-init")
    if missing.exists():
        failures.append("negative project-init contract input unexpectedly exists")
    if canonical.exists():
        failures.append("Luna project-init invented a substitute canonical contract")
    return _persist_score(
        repo,
        run_id,
        "project-init-luna-rejection",
        {
            "result": "PASS" if not failures else "FAIL",
            "status": status,
            "owner": owner,
            "blocking_issue": blocking_issue,
            "required_action": required_action,
            "next_command": next_command,
            "failures": failures,
        },
    )


def _policy_expectation_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return repo / "docs" / "verification" / "smoke" / (
        "{}.h08b-policy-expected.json".format(run_id)
    )


def write_fixture_policy(
    repo: Path,
    policy: dict,
    run_id: str | None = None,
) -> dict[str, object]:
    repo = _repo(repo)
    if not isinstance(policy, dict):
        raise H08bError("Fixture waiver policy is invalid")
    if policy.get("policy_id") != "SMOKE-FULL-WAIVER-POLICY-V1":
        raise H08bError("Fixture waiver policy ID is invalid")
    non_waivable = policy.get("non_waivable_failure_types")
    waivable = policy.get("waivable_failure_types")
    if (
        not isinstance(non_waivable, list)
        or not non_waivable
        or len(non_waivable) != len(set(non_waivable))
        or not all(isinstance(item, str) and item for item in non_waivable)
        or not isinstance(waivable, list)
        or not waivable
        or len(waivable) != len(set(waivable))
        or not all(isinstance(item, str) and item for item in waivable)
        or set(non_waivable).intersection(waivable)
        or "BEHAVIORAL_TEST" not in non_waivable
        or not isinstance(policy.get("purpose"), str)
        or not policy["purpose"].strip()
    ):
        raise H08bError("Fixture waiver policy failure-type mapping is invalid")
    target = _path(repo, POLICY_PATH)
    hidden = _policy_expectation_path(repo, run_id) if run_id is not None else None
    if target.exists():
        raise H08bError("Fixture waiver policy already exists")
    if hidden is not None and hidden.exists():
        raise H08bError("Fixture waiver-policy expectation already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(policy, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    digest = _sha_bytes(target.read_bytes())
    result = {"path": POLICY_PATH, "sha256": digest}
    if hidden is not None:
        hidden.parent.mkdir(parents=True, exist_ok=True)
        hidden.write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "policy_path": POLICY_PATH,
                    "policy_sha256": digest,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        result["hidden_expectation_path"] = hidden.relative_to(repo).as_posix()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id")
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("seed-discovery")
    actions.add_parser("restore-evidence")
    actions.add_parser("begin-direct-prd")
    direct_score = actions.add_parser("score-direct-prd")
    direct_score.add_argument("--status", required=True)
    actions.add_parser("restore-direct-prd")
    actions.add_parser("seed-product-decision")
    actions.add_parser("reveal-product-decision")
    prd_score = actions.add_parser("score-prd")
    prd_score.add_argument("--phase", choices=["blocked", "resumed"], required=True)
    prd_score.add_argument("--status", required=True)
    pi_policy = actions.add_parser("score-project-init-policy")
    pi_policy.add_argument("--status", required=True)
    actions.add_parser("begin-project-init-negative")
    actions.add_parser("score-project-init-helper")
    pi_luna = actions.add_parser("score-project-init-luna")
    pi_luna.add_argument("--status", required=True)
    pi_luna.add_argument("--owner", required=True)
    pi_luna.add_argument("--blocking-issue", required=True)
    pi_luna.add_argument("--required-action", required=True)
    pi_luna.add_argument("--next-command", required=True)
    actions.add_parser("restore-project-init-negative")
    score = actions.add_parser("score-discovery")
    score.add_argument("--phase", choices=["blocked", "resumed"], required=True)
    score.add_argument("--status", required=True)
    refusal = actions.add_parser("validate-refusal")
    refusal.add_argument("--path", required=True)
    args = parser.parse_args()
    try:
        if args.action == "seed-discovery":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = seed_discovery(args.repo, args.run_id)
        elif args.action == "restore-evidence":
            result = restore_required_evidence(args.repo)
        elif args.action == "score-discovery":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = score_discovery(
                args.repo, args.run_id, args.phase, args.status
            )
        elif args.action == "begin-direct-prd":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = begin_direct_prd_probe(args.repo, args.run_id)
        elif args.action == "score-direct-prd":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = score_direct_prd(args.repo, args.run_id, args.status)
        elif args.action == "restore-direct-prd":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = restore_direct_prd_probe(args.repo, args.run_id)
        elif args.action == "seed-product-decision":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = seed_product_decision(args.repo, args.run_id)
        elif args.action == "reveal-product-decision":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = reveal_product_decision(args.repo, args.run_id)
        elif args.action == "score-prd":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = score_prd_phase(
                args.repo, args.run_id, args.phase, args.status
            )
        elif args.action == "score-project-init-policy":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = score_project_init_policy_propagation(
                args.repo, args.run_id, args.status
            )
        elif args.action == "begin-project-init-negative":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = begin_project_init_negative(args.repo, args.run_id)
        elif args.action == "score-project-init-helper":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = score_project_init_helper_rejection(
                args.repo, args.run_id
            )
        elif args.action == "score-project-init-luna":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = score_project_init_luna(
                args.repo,
                args.run_id,
                args.status,
                args.owner,
                args.blocking_issue,
                args.required_action,
                args.next_command,
            )
        elif args.action == "restore-project-init-negative":
            if not args.run_id:
                raise H08bError("--run-id is required")
            result = restore_project_init_negative(args.repo, args.run_id)
        else:
            result = validate_refusal(args.repo, args.path, args.run_id)
        print(json.dumps({"ok": True, **result}))
        return 0
    except (H08bError, OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
