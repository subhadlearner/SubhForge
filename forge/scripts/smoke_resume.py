#!/usr/bin/env python3
"""Deterministic preparation, scoring, and restoration for H05 resume probes.

This helper owns smoke mechanics only. It never chooses the continuation stage
for the routing model.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import implementation_state
import smoke_mechanics


class ResumeProbeError(RuntimeError):
    pass


SCHEMA_VERSION = 1
PROBE_EXPECTED = {
    "r01": "/project-init",
    "r02": "/spec",
    "r03": "/implement",
    "r04": "/verify",
    "r05": "/review",
    "r06": "/verify",
    "r07": "/fix",
}
HANDOFF_PROBE = "r03"
ALLOWED_STAGES = {
    "/grill",
    "/prd",
    "/architect",
    "/project-init",
    "/spec",
    "/implement",
    "/verify",
    "/review",
    "/fix",
    "/diagnose",
    "/waive",
    "/adversarial-check",
}
SMOKE_PREFIX = "docs/verification/smoke/"
PROJECT_INIT_PREFIXES = (
    "AGENTS.md",
    "README.md",
    ".kilo/rules/",
    ".kilo/skills/",
    "docs/workflow/",
)
COMMON_EVIDENCE_PREFIXES = (
    "docs/verification/",
    "docs/reviews/",
    "docs/diagnostics/",
)
HISTORICAL_EVIDENCE_PREFIXES = (
    "docs/verification/waiver-refusals/",
)


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return implementation_state.git(repo, *args, input_bytes=input_bytes)


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(
        char.isalnum() or char == "-" for char in run_id
    ):
        raise ResumeProbeError("Invalid run ID")


def _repo_root(repo: Path) -> Path:
    try:
        root = implementation_state.repo_root(repo)
    except implementation_state.ImplementationStateError as exc:
        raise ResumeProbeError(str(exc)) from exc
    branch = _git(root, "branch", "--show-current").strip().decode("utf-8", "replace")
    if branch != "smoke-run":
        raise ResumeProbeError("Resume probes are restricted to the smoke-run branch")
    return root


def _ledger_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    folder = repo / "docs" / "verification" / "smoke"
    if not folder.is_dir():
        raise ResumeProbeError("Smoke evidence directory is missing")
    return folder / f"{run_id}.resume.json"


def _snapshot_path(repo: Path, run_id: str, probe_id: str) -> Path:
    return repo / "docs" / "verification" / "smoke" / (
        f"{run_id}.resume-snapshot-{probe_id}.json"
    )


def _read_ledger(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "probes": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ResumeProbeError("Resume probe ledger is unreadable") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != SCHEMA_VERSION
        or set(data) != {"schema_version", "probes"}
        or not isinstance(data.get("probes"), list)
    ):
        raise ResumeProbeError("Malformed resume probe ledger")
    return data


def _save_json(path: Path, data: object) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temp.replace(path)


def _safe_name(name: str) -> str:
    if (
        not name
        or name.startswith("/")
        or "\\" in name
        or any(part in ("", ".", "..") for part in name.split("/"))
        or name == ".git"
        or name.startswith(".git/")
    ):
        raise ResumeProbeError("Invalid repository-relative path: {!r}".format(name))
    return name


def _path(repo: Path, name: str) -> Path:
    name = _safe_name(name)
    target = repo / name
    try:
        parent = target.parent.resolve()
    except OSError as exc:
        raise ResumeProbeError("Unable to resolve repository path") from exc
    try:
        parent.relative_to(repo.resolve())
    except ValueError as exc:
        raise ResumeProbeError("Path escapes repository: {}".format(name)) from exc
    return target


def _decode_name(raw: bytes) -> str:
    try:
        name = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ResumeProbeError("Non-UTF-8 repository path") from exc
    if not name or any(char in name for char in "\t\r\n"):
        raise ResumeProbeError("Unrepresentable repository path")
    return _safe_name(name)


def _index_modes(repo: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in _git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if not raw:
            continue
        meta, raw_name = raw.split(b"\t", 1)
        mode, _, stage = meta.decode("ascii").split()
        if stage != "0":
            raise ResumeProbeError("Unmerged index is not valid probe input")
        result[_decode_name(raw_name)] = mode
    return result


def _workspace_names(repo: Path) -> list[str]:
    raw = _git(
        repo,
        "ls-files",
        "-z",
        "--cached",
        "--others",
        "--exclude-standard",
    )
    names = sorted({_decode_name(item) for item in raw.split(b"\0") if item})
    return [name for name in names if not name.startswith(SMOKE_PREFIX)]


def _capture_snapshot(repo: Path) -> dict[str, object]:
    index = _index_modes(repo)
    entries: list[dict[str, object]] = []
    for name in _workspace_names(repo):
        target = _path(repo, name)
        try:
            info = target.lstat()
        except FileNotFoundError:
            entries.append({"path": name, "kind": "missing"})
            continue

        if stat.S_ISLNK(info.st_mode):
            entries.append(
                {
                    "path": name,
                    "kind": "symlink",
                    "mode": "120000",
                    "target": os.readlink(target),
                }
            )
            continue
        if not stat.S_ISREG(info.st_mode):
            raise ResumeProbeError(
                "Unsupported probe snapshot file type: {}".format(name)
            )

        mode = index.get(name)
        if mode not in ("100644", "100755"):
            mode = "100755" if info.st_mode & 0o111 else "100644"
        payload = target.read_bytes()
        entries.append(
            {
                "path": name,
                "kind": "file",
                "mode": mode,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "data": base64.b64encode(payload).decode("ascii"),
            }
        )

    body = {"schema_version": SCHEMA_VERSION, "entries": entries}
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return {
        **body,
        "snapshot_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _snapshot_digest(snapshot: dict[str, object]) -> str:
    body = {
        "schema_version": snapshot.get("schema_version"),
        "entries": snapshot.get("entries"),
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _load_snapshot(path: Path) -> dict[str, object]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ResumeProbeError("Resume snapshot is unreadable") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != SCHEMA_VERSION
        or not isinstance(data.get("entries"), list)
        or not isinstance(data.get("snapshot_sha256"), str)
        or _snapshot_digest(data) != data["snapshot_sha256"]
    ):
        raise ResumeProbeError("Malformed or corrupted resume snapshot")
    return data


def _remove_target(target: Path) -> None:
    try:
        info = target.lstat()
    except FileNotFoundError:
        return
    if stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode):
        raise ResumeProbeError(
            "Probe helper refuses to remove a directory as a file target: {}".format(
                target
            )
        )
    target.unlink()


def _write_entry(repo: Path, entry: dict[str, object]) -> None:
    name = entry.get("path")
    kind = entry.get("kind")
    if not isinstance(name, str) or kind not in {"file", "symlink", "missing"}:
        raise ResumeProbeError("Malformed resume snapshot entry")
    target = _path(repo, name)
    if kind == "missing":
        _remove_target(target)
        return

    target.parent.mkdir(parents=True, exist_ok=True)
    _remove_target(target)
    if kind == "symlink":
        link_target = entry.get("target")
        if not isinstance(link_target, str):
            raise ResumeProbeError("Malformed symlink snapshot entry")
        os.symlink(link_target, target)
        return

    encoded = entry.get("data")
    digest = entry.get("sha256")
    mode = entry.get("mode")
    if (
        not isinstance(encoded, str)
        or not isinstance(digest, str)
        or mode not in ("100644", "100755")
    ):
        raise ResumeProbeError("Malformed file snapshot entry")
    payload = base64.b64decode(encoded.encode("ascii"), validate=True)
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ResumeProbeError("Resume snapshot file hash mismatch")
    target.write_bytes(payload)
    try:
        target.chmod(0o755 if mode == "100755" else 0o644)
    except OSError as exc:
        raise ResumeProbeError("Unable to restore file mode: {}".format(name)) from exc


def _restore_snapshot(repo: Path, snapshot: dict[str, object]) -> None:
    for name in _workspace_names(repo):
        _remove_target(_path(repo, name))
    for raw in snapshot["entries"]:
        if not isinstance(raw, dict):
            raise ResumeProbeError("Malformed resume snapshot entry")
        _write_entry(repo, raw)

    current = _capture_snapshot(repo)
    if current["snapshot_sha256"] != snapshot["snapshot_sha256"]:
        raise ResumeProbeError("Resume snapshot restoration is not byte-identical")


# Public probe-state substrate reused by later smoke hardening helpers. These
# wrappers intentionally expose mechanics only; they do not expose H05 routing
# expectations or choose any workflow stage.
def probe_repo_root(repo: Path) -> Path:
    return _repo_root(repo)


def capture_probe_snapshot(repo: Path) -> dict[str, object]:
    return _capture_snapshot(_repo_root(repo))


def restore_probe_snapshot(repo: Path, snapshot: dict[str, object]) -> None:
    _restore_snapshot(_repo_root(repo), snapshot)


def probe_workspace_names(repo: Path) -> list[str]:
    return _workspace_names(_repo_root(repo))


def probe_path(repo: Path, name: str) -> Path:
    return _path(_repo_root(repo), name)


# Fast-path variants for helpers that have already called probe_repo_root() in
# the same top-level action. They preserve the exact snapshot semantics while
# avoiding redundant rev-parse/branch subprocesses on Windows.
def capture_probe_snapshot_at_root(repo: Path) -> dict[str, object]:
    return _capture_snapshot(repo)


def restore_probe_snapshot_at_root(repo: Path, snapshot: dict[str, object]) -> None:
    _restore_snapshot(repo, snapshot)


def probe_workspace_names_at_root(repo: Path) -> list[str]:
    return _workspace_names(repo)


def _snapshot_entry(snapshot: dict[str, object], name: str) -> dict[str, object]:
    for raw in snapshot["entries"]:
        if isinstance(raw, dict) and raw.get("path") == name:
            return raw
    raise ResumeProbeError("Required path is absent from clean probe snapshot: {}".format(name))


def _restore_one_from_snapshot(
    repo: Path, snapshot: dict[str, object], name: str
) -> None:
    _write_entry(repo, _snapshot_entry(snapshot, name))


def _matches_prefix(name: str, prefix: str) -> bool:
    return name == prefix.rstrip("/") or name.startswith(prefix)


def _clear_prefixes(
    repo: Path,
    prefixes: tuple[str, ...],
    preserve_prefixes: tuple[str, ...] = (),
) -> None:
    for name in _workspace_names(repo):
        if any(_matches_prefix(name, prefix) for prefix in preserve_prefixes):
            continue
        if any(_matches_prefix(name, prefix) for prefix in prefixes):
            _remove_target(_path(repo, name))


def _clear_paths(repo: Path, names: list[str]) -> None:
    for name in names:
        _remove_target(_path(repo, name))


def _project_init_owned(name: str) -> bool:
    return any(_matches_prefix(name, prefix) for prefix in PROJECT_INIT_PREFIXES)


def _baseline_entries(repo: Path, baseline_head: str) -> list[dict[str, object]]:
    try:
        _git(repo, "cat-file", "-e", "{}^{{commit}}".format(baseline_head))
    except implementation_state.ImplementationStateError as exc:
        raise ResumeProbeError("Baseline HEAD is unavailable") from exc

    raw = _git(
        repo,
        "ls-tree",
        "-r",
        "-z",
        baseline_head,
        "--",
        "AGENTS.md",
        "README.md",
        ".kilo/rules",
        ".kilo/skills",
        "docs/workflow",
    )
    entries: list[dict[str, object]] = []
    for item in raw.split(b"\0"):
        if not item:
            continue
        meta, raw_name = item.split(b"\t", 1)
        mode, kind, _ = meta.decode("ascii").split()
        name = _decode_name(raw_name)
        if kind != "blob":
            raise ResumeProbeError("Unsupported baseline tree entry: {}".format(name))
        payload = _git(repo, "show", "{}:{}".format(baseline_head, name))
        if mode == "120000":
            entries.append(
                {
                    "path": name,
                    "kind": "symlink",
                    "mode": mode,
                    "target": payload.decode("utf-8", "strict"),
                }
            )
        elif mode in ("100644", "100755"):
            entries.append(
                {
                    "path": name,
                    "kind": "file",
                    "mode": mode,
                    "sha256": hashlib.sha256(payload).hexdigest(),
                    "data": base64.b64encode(payload).decode("ascii"),
                }
            )
        else:
            raise ResumeProbeError("Unsupported baseline mode: {}".format(mode))
    return entries


def _reset_project_init_to_baseline(repo: Path, baseline_head: str) -> None:
    for name in _workspace_names(repo):
        if _project_init_owned(name):
            _remove_target(_path(repo, name))
    for entry in _baseline_entries(repo, baseline_head):
        _write_entry(repo, entry)


def _subset_digest(entries: list[dict[str, object]]) -> str:
    encoded = json.dumps(
        sorted(entries, key=lambda item: str(item.get("path"))),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _project_init_snapshot_entries(
    snapshot: dict[str, object],
) -> list[dict[str, object]]:
    return [
        raw
        for raw in snapshot["entries"]
        if isinstance(raw, dict)
        and isinstance(raw.get("path"), str)
        and _project_init_owned(raw["path"])
    ]


def _current_project_init_digest(repo: Path) -> str:
    return _subset_digest(_project_init_snapshot_entries(_capture_snapshot(repo)))


def _baseline_project_init_digest(repo: Path, baseline_head: str) -> str:
    return _subset_digest(_baseline_entries(repo, baseline_head))


def _snapshot_project_init_digest(snapshot: dict[str, object]) -> str:
    return _subset_digest(_project_init_snapshot_entries(snapshot))


def _has_normal_file(repo: Path, prefix: str) -> bool:
    return any(_matches_prefix(name, prefix) for name in _workspace_names(repo))


def _validate_context(
    repo: Path,
    snapshot: dict[str, object],
    spec_path: str,
    implementation_paths: list[str],
    verification_path: str,
) -> tuple[str, list[str], str]:
    spec_path = _safe_name(spec_path)
    verification_path = _safe_name(verification_path)
    implementation_paths = [_safe_name(name) for name in implementation_paths]
    if not implementation_paths:
        raise ResumeProbeError("At least one implementation path is required")
    if not spec_path.startswith("docs/specs/"):
        raise ResumeProbeError("Spec path must be under docs/specs/")
    if (
        not verification_path.startswith("docs/verification/")
        or verification_path.startswith(SMOKE_PREFIX)
    ):
        raise ResumeProbeError("Verification path must be normal verification evidence")

    _snapshot_entry(snapshot, spec_path)
    _snapshot_entry(snapshot, verification_path)
    for name in implementation_paths:
        entry = _snapshot_entry(snapshot, name)
        if entry.get("kind") != "file":
            raise ResumeProbeError(
                "Implementation probe path must be a regular file: {}".format(name)
            )

    if not _has_normal_file(repo, "docs/prd/"):
        raise ResumeProbeError("Clean probe checkpoint has no persisted PRD")
    if not (
        _has_normal_file(repo, "docs/architecture/")
        or _has_normal_file(repo, "docs/adr/")
    ):
        raise ResumeProbeError("Clean probe checkpoint has no persisted architecture")
    return spec_path, implementation_paths, verification_path


def _blocking_review_path(spec_path: str) -> str:
    stem = Path(spec_path).stem
    safe = "".join(ch for ch in stem if ch.isalnum() or ch in "-_") or "SPEC"
    return "docs/reviews/REVIEW-{}-900.md".format(safe)


def _write_blocking_review(
    repo: Path,
    run_id: str,
    checkpoint_label: str,
    spec_path: str,
    verification_path: str,
    implementation_path: str,
) -> str:
    name = _blocking_review_path(spec_path)
    target = _path(repo, name)
    target.parent.mkdir(parents=True, exist_ok=True)
    checkpoint = smoke_mechanics.check_checkpoint(repo, run_id, checkpoint_label)
    fingerprint = checkpoint["current_fingerprint"]
    head = _git(repo, "rev-parse", "HEAD").strip().decode("ascii")
    target.write_text(
        "\n".join(
            [
                "# Code Review",
                "",
                "## Identity",
                "",
                "- Review ID: REVIEW-900",
                "- Specification/change: {}".format(spec_path),
                "- Branch: smoke-run",
                "- Current HEAD SHA: {}".format(head),
                "- Reviewed implementation-state fingerprint: {}".format(fingerprint),
                "",
                "## Verification Input",
                "",
                "- Persisted verification report: {}".format(verification_path),
                "- Verification base HEAD SHA: {}".format(head),
                "- Verified implementation-state fingerprint: {}".format(fingerprint),
                "- Factual verification result: DONE",
                "- Effective delivery gate: CLEAR",
                "- Evidence contract version: implementation-state-evidence-v1",
                "- Freshness result: MATCH",
                "- Canonical-manifest equality result: MATCH",
                "- Active waiver: none",
                "",
                "## Pre-Review",
                "",
                "- Result: CHANGES_REQUIRED",
                "- Blocking issue: persisted implementation review blocker remains unresolved.",
                "- Affected path: {}".format(implementation_path),
                "",
                "## Senior Review",
                "",
                "- Result: NOT_RUN",
                "- Reason: blocking issues remain in pre-review.",
                "",
                "## Final AI Review Decision",
                "",
                "CHANGES_REQUIRED",
                "",
                "## Next Action",
                "",
                "/fix → /verify → /review",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return name


def _probe_checks(
    repo: Path,
    run_id: str,
    probe_id: str,
    checkpoint_label: str,
    baseline_head: str,
    clean_snapshot: dict[str, object],
    spec_path: str,
    implementation_paths: list[str],
    verification_path: str,
    review_path: str | None,
) -> dict[str, bool]:
    names = set(_workspace_names(repo))
    has_spec = spec_path in names
    has_impl = all(name in names and _path(repo, name).is_file() for name in implementation_paths)
    has_verification = verification_path in names
    has_reviews = any(name.startswith("docs/reviews/") for name in names)
    has_diagnostics = any(name.startswith("docs/diagnostics/") for name in names)

    try:
        checkpoint_result = smoke_mechanics.check_checkpoint(
            repo, run_id, checkpoint_label
        )["result"]
    except implementation_state.ImplementationStateError as exc:
        raise ResumeProbeError(str(exc)) from exc

    checks = {
        "prd_present": _has_normal_file(repo, "docs/prd/"),
        "architecture_present": (
            _has_normal_file(repo, "docs/architecture/")
            or _has_normal_file(repo, "docs/adr/")
        ),
        "diagnostics_absent": not has_diagnostics,
        "project_init_state_correct": (
            _current_project_init_digest(repo)
            == (
                _baseline_project_init_digest(repo, baseline_head)
                if probe_id == "r01"
                else _snapshot_project_init_digest(clean_snapshot)
            )
        ),
    }

    if probe_id in {"r01", "r02"}:
        checks.update(
            {
                "spec_absent": not has_spec,
                "implementation_absent": not has_impl,
                "verification_absent": not has_verification,
                "review_absent": not has_reviews,
            }
        )
    elif probe_id == "r03":
        checks.update(
            {
                "spec_present": has_spec,
                "implementation_absent": not has_impl,
                "verification_absent": not has_verification,
                "review_absent": not has_reviews,
            }
        )
    elif probe_id == "r04":
        checks.update(
            {
                "spec_present": has_spec,
                "implementation_present": has_impl,
                "verification_absent": not has_verification,
                "review_absent": not has_reviews,
            }
        )
    elif probe_id == "r05":
        checks.update(
            {
                "spec_present": has_spec,
                "implementation_present": has_impl,
                "verification_present": has_verification,
                "review_absent": not has_reviews,
                "checkpoint_match": checkpoint_result == "MATCH",
            }
        )
    elif probe_id == "r06":
        checks.update(
            {
                "spec_present": has_spec,
                "implementation_present": has_impl,
                "verification_present": has_verification,
                "review_absent": not has_reviews,
                "checkpoint_stale": checkpoint_result == "MISMATCH",
            }
        )
    elif probe_id == "r07":
        checks.update(
            {
                "spec_present": has_spec,
                "implementation_present": has_impl,
                "verification_present": has_verification,
                "blocking_review_present": (
                    review_path is not None and review_path in names
                ),
                "checkpoint_match": checkpoint_result == "MATCH",
            }
        )
    else:
        raise ResumeProbeError("Unknown resume probe ID")

    return checks


def prepare(
    repo: Path,
    run_id: str,
    probe_id: str,
    checkpoint_label: str,
    baseline_head: str,
    spec_path: str,
    implementation_paths: list[str],
    verification_path: str,
) -> dict[str, object]:
    repo = _repo_root(repo)
    if probe_id not in PROBE_EXPECTED:
        raise ResumeProbeError("Unknown resume probe ID")

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
        raise ResumeProbeError("Duplicate resume probe ledger entries are invalid")
    retry_record: dict[str, object] | None = None
    if matches:
        existing = matches[0]
        if existing.get("restored") is not True:
            raise ResumeProbeError("Resume probe is still active")
        if existing.get("probe_result") != "NOT_SCORED":
            raise ResumeProbeError("Scored resume probe is immutable and cannot be retried")
        retry_record = existing
    if any(
        isinstance(item, dict) and not item.get("restored", False)
        for item in probes
    ):
        raise ResumeProbeError("Restore the active resume probe before preparing another")

    try:
        if smoke_mechanics.check_checkpoint(
            repo, run_id, checkpoint_label
        )["result"] != "MATCH":
            raise ResumeProbeError("Clean checkpoint drifted before resume probe")
    except implementation_state.ImplementationStateError as exc:
        raise ResumeProbeError(str(exc)) from exc

    snapshot = _capture_snapshot(repo)
    spec_path, implementation_paths, verification_path = _validate_context(
        repo, snapshot, spec_path, implementation_paths, verification_path
    )

    snap_path = _snapshot_path(repo, run_id, probe_id)
    if snap_path.exists():
        raise ResumeProbeError("Resume snapshot already exists")
    _save_json(snap_path, snapshot)

    review_path: str | None = None
    try:
        _clear_prefixes(
            repo,
            COMMON_EVIDENCE_PREFIXES,
            preserve_prefixes=HISTORICAL_EVIDENCE_PREFIXES,
        )

        if probe_id == "r01":
            _reset_project_init_to_baseline(repo, baseline_head)
            _clear_prefixes(repo, ("docs/specs/",))
            _clear_paths(repo, implementation_paths)
        elif probe_id == "r02":
            _clear_prefixes(repo, ("docs/specs/",))
            _clear_paths(repo, implementation_paths)
        elif probe_id == "r03":
            _clear_paths(repo, implementation_paths)
        elif probe_id == "r04":
            pass
        elif probe_id == "r05":
            _restore_one_from_snapshot(repo, snapshot, verification_path)
        elif probe_id == "r06":
            _restore_one_from_snapshot(repo, snapshot, verification_path)
            target = _path(repo, implementation_paths[0])
            target.write_bytes(target.read_bytes() + b"\n")
        elif probe_id == "r07":
            _restore_one_from_snapshot(repo, snapshot, verification_path)
            review_path = _write_blocking_review(
                repo,
                run_id,
                checkpoint_label,
                spec_path,
                verification_path,
                implementation_paths[0],
            )

        checks = _probe_checks(
            repo,
            run_id,
            probe_id,
            checkpoint_label,
            baseline_head,
            snapshot,
            spec_path,
            implementation_paths,
            verification_path,
            review_path,
        )
        if not all(checks.values()):
            raise ResumeProbeError(
                "Prepared resume probe failed validation: {}".format(
                    ", ".join(key for key, ok in checks.items() if not ok)
                )
            )
    except Exception:
        _restore_snapshot(repo, snapshot)
        snap_path.unlink(missing_ok=True)
        raise

    prepared_snapshot = _capture_snapshot(repo)
    attempt_count = 1
    if retry_record is not None:
        prior_attempts = retry_record.get("attempt_count", 1)
        if not isinstance(prior_attempts, int) or prior_attempts < 1:
            raise ResumeProbeError("Malformed resume probe attempt count")
        attempt_count = prior_attempts + 1

    record = {
        "probe_id": probe_id,
        "checkpoint": checkpoint_label,
        "snapshot_file": snap_path.name,
        "snapshot_sha256": snapshot["snapshot_sha256"],
        "prepared_snapshot_sha256": prepared_snapshot["snapshot_sha256"],
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
        "checks": checks,
    }


def _active_probe(
    ledger: dict[str, object], probe_id: str
) -> dict[str, object]:
    probes = ledger.get("probes")
    if not isinstance(probes, list):
        raise ResumeProbeError("Malformed resume probe ledger")
    for raw in probes:
        if (
            isinstance(raw, dict)
            and raw.get("probe_id") == probe_id
            and not raw.get("restored", False)
        ):
            return raw
    raise ResumeProbeError("Resume probe is not active")


def _require_prepared_unchanged(
    repo: Path, record: dict[str, object]
) -> None:
    expected = record.get("prepared_snapshot_sha256")
    if not isinstance(expected, str):
        raise ResumeProbeError("Prepared resume probe digest is missing")
    current = _capture_snapshot(repo)["snapshot_sha256"]
    if current != expected:
        raise ResumeProbeError(
            "Prepared resume probe changed before deterministic scoring"
        )


def score(
    repo: Path,
    run_id: str,
    probe_id: str,
    actual_stage: str,
    reason: str,
) -> dict[str, object]:
    repo = _repo_root(repo)
    if probe_id not in PROBE_EXPECTED:
        raise ResumeProbeError("Unknown resume probe ID")
    if actual_stage not in ALLOWED_STAGES:
        raise ResumeProbeError("Invalid routed stage")
    if not reason.strip():
        raise ResumeProbeError("Routing reason is required")

    path = _ledger_path(repo, run_id)
    ledger = _read_ledger(path)
    record = _active_probe(ledger, probe_id)
    if record.get("state") != "PREPARED":
        raise ResumeProbeError("Resume probe has already been scored")
    _require_prepared_unchanged(repo, record)

    routing_pass = actual_stage == PROBE_EXPECTED[probe_id]
    record["actual_stage"] = actual_stage
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
    }


def record_handoff(
    repo: Path,
    run_id: str,
    probe_id: str,
    accepted: bool,
    evidence: str,
) -> dict[str, object]:
    repo = _repo_root(repo)
    if probe_id != HANDOFF_PROBE:
        raise ResumeProbeError("Only one resume probe accepts a handoff result")
    if not evidence.strip():
        raise ResumeProbeError("Handoff evidence is required")

    path = _ledger_path(repo, run_id)
    ledger = _read_ledger(path)
    record = _active_probe(ledger, probe_id)
    if record.get("state") != "ROUTING_PASS_HANDOFF_REQUIRED":
        raise ResumeProbeError("Resume probe is not awaiting handoff evidence")
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
    repo = _repo_root(repo)
    path = _ledger_path(repo, run_id)
    ledger = _read_ledger(path)
    record = _active_probe(ledger, probe_id)

    snap_name = record.get("snapshot_file")
    checkpoint_label = record.get("checkpoint")
    expected_digest = record.get("snapshot_sha256")
    if (
        not isinstance(snap_name, str)
        or not isinstance(checkpoint_label, str)
        or not isinstance(expected_digest, str)
    ):
        raise ResumeProbeError("Malformed active resume probe record")

    snap_path = repo / "docs" / "verification" / "smoke" / snap_name
    snapshot = _load_snapshot(snap_path)
    if snapshot["snapshot_sha256"] != expected_digest:
        raise ResumeProbeError("Resume snapshot digest does not match ledger")

    _restore_snapshot(repo, snapshot)
    try:
        checkpoint_result = smoke_mechanics.check_checkpoint(
            repo, run_id, checkpoint_label
        )["result"]
    except implementation_state.ImplementationStateError as exc:
        raise ResumeProbeError(str(exc)) from exc
    if checkpoint_result != "MATCH":
        raise ResumeProbeError("Resume probe restoration did not reproduce checkpoint")

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
    repo = _repo_root(repo)
    ledger = _read_ledger(_ledger_path(repo, run_id))
    probes = ledger["probes"]
    assert isinstance(probes, list)

    by_id = {
        item.get("probe_id"): item
        for item in probes
        if isinstance(item, dict) and isinstance(item.get("probe_id"), str)
    }
    complete = (
        set(by_id) == set(PROBE_EXPECTED)
        and all(
            item.get("restored") is True and item.get("probe_result") == "PASS"
            for item in by_id.values()
        )
    )
    return {
        "result": "PASS" if complete else "INCOMPLETE",
        "completed_probes": sorted(
            probe_id
            for probe_id, item in by_id.items()
            if item.get("restored") is True and item.get("probe_result") == "PASS"
        ),
        "required_probe_count": len(PROBE_EXPECTED),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)

    prepare_p = actions.add_parser("prepare")
    prepare_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_EXPECTED))
    prepare_p.add_argument("--checkpoint", required=True)
    prepare_p.add_argument("--baseline-head", required=True)
    prepare_p.add_argument("--spec", required=True)
    prepare_p.add_argument("--implementation", action="append", default=[])
    prepare_p.add_argument("--verification", required=True)

    score_p = actions.add_parser("score")
    score_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_EXPECTED))
    score_p.add_argument("--actual-stage", required=True)
    score_p.add_argument("--reason", required=True)

    handoff_p = actions.add_parser("record-handoff")
    handoff_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_EXPECTED))
    handoff_p.add_argument("--result", required=True, choices=["ACCEPTED", "REJECTED"])
    handoff_p.add_argument("--evidence", required=True)

    restore_p = actions.add_parser("restore")
    restore_p.add_argument("--probe-id", required=True, choices=sorted(PROBE_EXPECTED))

    actions.add_parser("status")

    args = parser.parse_args()
    try:
        if args.action == "prepare":
            result = prepare(
                args.repo,
                args.run_id,
                args.probe_id,
                args.checkpoint,
                args.baseline_head,
                args.spec,
                args.implementation,
                args.verification,
            )
        elif args.action == "score":
            result = score(
                args.repo,
                args.run_id,
                args.probe_id,
                args.actual_stage,
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
        ResumeProbeError,
        implementation_state.ImplementationStateError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
