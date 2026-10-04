#!/usr/bin/env python3
"""Deterministic Kilo workspace handoff for SubhForge smoke runs.

The handoff launches a top-level Kilo continuation rooted in the disposable
``smoke-run`` repository and marks that process tree with a per-handoff secret.
Only a process carrying the marker, whose working tree is the disposable
repository, is treated as rooted. Kilo strips ``KILO_CONFIG_CONTENT`` from
model-visible shell environments, so the config overlay injected here cannot be
removed by the rooted agents themselves.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
import shutil
import subprocess
import sys
from collections.abc import Callable, Mapping
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_state
import smoke_workspace

ENV_RUN_ID = "SUBHFORGE_SMOKE_RUN_ID"
ENV_RUN_DIRECTORY = "SUBHFORGE_SMOKE_RUN_DIRECTORY"
ENV_HANDOFF_TOKEN = "SUBHFORGE_SMOKE_HANDOFF_TOKEN"
MARKER_ENV = (ENV_RUN_ID, ENV_RUN_DIRECTORY, ENV_HANDOFF_TOKEN)
PAID_ADVERSARIES = ("adversary-opus", "adversary-sonnet")
INSTALL_MANIFEST = ".subhforge-install.json"


class SmokeHandoffError(RuntimeError):
    pass


def _validate_run_id(run_id: str) -> None:
    if not run_id.startswith("SMOKE-") or not all(
        char.isalnum() or char == "-" for char in run_id
    ):
        raise SmokeHandoffError("Invalid run ID")


def _run_git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    if not git:
        raise SmokeHandoffError("Git is not available on PATH")
    proc = subprocess.run(
        [git, *args],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise SmokeHandoffError("git {} failed: {}".format(" ".join(args), detail))
    return proc.stdout.strip()


def validate_workspace(repo: Path, run_id: str) -> dict[str, str]:
    """Validate that repo is the initialized disposable workspace for run_id."""
    _validate_run_id(run_id)
    repo = repo.resolve()
    if not repo.is_dir():
        raise SmokeHandoffError("Smoke run directory does not exist: {}".format(repo))
    if repo.name != run_id:
        raise SmokeHandoffError("Smoke run directory name does not match run ID")

    try:
        identity = smoke_workspace.validate_repository_identity(repo, run_id)
    except smoke_workspace.SmokeWorkspaceError as exc:
        raise SmokeHandoffError("Invalid disposable smoke repository: {}".format(exc)) from exc
    branch = identity["run_branch"]

    try:
        state = smoke_state.load(repo, run_id)
    except smoke_state.SmokeStateError as exc:
        raise SmokeHandoffError("Canonical smoke state is unavailable: {}".format(exc)) from exc

    completed = state.get("completed_scenarios")
    if not isinstance(completed, list) or "static-release-gate" not in completed:
        raise SmokeHandoffError(
            "Smoke workspace handoff requires completed static-release-gate bootstrap"
        )

    return {
        "run_directory": str(repo),
        "run_id": run_id,
        "profile": str(state.get("profile") or ""),
        "fixture": str(state.get("fixture") or ""),
        "branch": branch,
    }


def current_project_root(cwd: Path | None = None) -> Path | None:
    """Return the Git work-tree root containing cwd, or None outside Git."""
    base = (cwd or Path.cwd()).resolve()
    git = shutil.which("git")
    if not git:
        raise SmokeHandoffError("Git is not available on PATH")
    proc = subprocess.run(
        [git, "rev-parse", "--show-toplevel"],
        cwd=str(base),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    return Path(value).resolve() if value else None


def handoff_record_path(repo: Path, run_id: str) -> Path:
    _validate_run_id(run_id)
    return repo.resolve() / "docs" / "verification" / "smoke" / (run_id + ".handoff.json")


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _write_json(path: Path, data: dict[str, object]) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def _is_within(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def installed_config_dir(script: Path | None = None) -> Path | None:
    """Return the installed SubhForge config root that owns this helper, if any."""
    root = (script or Path(__file__)).resolve().parent.parent
    return root if (root / INSTALL_MANIFEST).is_file() else None


def protected_source_paths(
    target: Path,
    active_root: Path | None,
    config_dir: Path | None,
) -> list[Path]:
    """Return the SubhForge source checkout path(s) the rooted run must not touch."""
    candidates: list[Path] = []
    if config_dir is not None:
        try:
            manifest = json.loads((config_dir / INSTALL_MANIFEST).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise SmokeHandoffError("Install provenance is unreadable: {}".format(exc)) from exc
        recorded = manifest.get("source_checkout_path")
        if isinstance(recorded, str) and recorded:
            candidates.append(Path(recorded).resolve())
    if active_root is not None and active_root.resolve() != target:
        candidates.append(active_root.resolve())

    protected: list[Path] = []
    for path in candidates:
        if path in protected:
            continue
        if _is_within(target, path):
            raise SmokeHandoffError(
                "Smoke run directory must not be inside the protected source checkout: {}".format(path)
            )
        protected.append(path)
    if not protected:
        raise SmokeHandoffError(
            "Cannot determine the SubhForge source checkout to protect during the rooted run"
        )
    return protected


def build_config_overlay(protected: list[Path]) -> dict[str, object]:
    """Kilo config overlay applied only to the rooted autonomous continuation.

    ``--auto`` approves every permission that is not explicitly denied, so every
    human-controlled capability that must stay unavailable is denied or
    disabled here rather than left at ``ask``.
    """
    external: dict[str, str] = {}
    for path in protected:
        posix = path.as_posix()
        external[posix] = "deny"
        external[posix + "/*"] = "deny"
    return {
        "agent": {name: {"disable": True} for name in PAID_ADVERSARIES},
        "permission": {"external_directory": external},
    }


def build_child_env(
    base: Mapping[str, str],
    target: Path,
    run_id: str,
    token: str,
    overlay: dict[str, object],
    config_dir: Path | None,
) -> dict[str, str]:
    env = {key: value for key, value in base.items() if key not in MARKER_ENV}
    env[ENV_RUN_ID] = run_id
    env[ENV_RUN_DIRECTORY] = str(target)
    env[ENV_HANDOFF_TOKEN] = token
    env["KILO_CONFIG_CONTENT"] = json.dumps(overlay, sort_keys=True)
    if config_dir is not None:
        # Kilo removes KILO_CONFIG_DIR from model shells; restore the exact
        # installed release so the rooted run loads the same configuration.
        env["KILO_CONFIG_DIR"] = str(config_dir)
    return env


def build_kilo_command(kilo: str, repo: Path, run_id: str) -> list[str]:
    """Build the only supported top-level Kilo smoke continuation command."""
    return [
        kilo,
        "run",
        "--dir",
        str(repo.resolve()),
        "--agent",
        "smoke-orchestrator",
        "--model",
        "openai/gpt-5.6-luna",
        "--command",
        "smoke",
        "--auto",
        "RESUME {}".format(run_id),
    ]


def assert_rooted(
    repo: Path,
    run_id: str,
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> dict[str, str]:
    """Fail unless this process belongs to the current rooted handoff for run_id."""
    validated = validate_workspace(repo, run_id)
    target = Path(validated["run_directory"])
    env = os.environ if env is None else env

    missing = [name for name in MARKER_ENV if not env.get(name)]
    if missing:
        raise SmokeHandoffError(
            "Not a rooted smoke session; missing handoff marker(s): {}".format(", ".join(missing))
        )
    if env[ENV_RUN_ID] != run_id:
        raise SmokeHandoffError("Rooted session belongs to a different smoke run")
    if Path(env[ENV_RUN_DIRECTORY]).resolve() != target:
        raise SmokeHandoffError("Rooted session marker names a different run directory")

    record_path = handoff_record_path(target, run_id)
    try:
        record = json.loads(record_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise SmokeHandoffError("Handoff record is missing or unreadable") from exc
    expected = record.get("token_sha256")
    if not isinstance(expected, str) or not hmac.compare_digest(
        expected, _token_digest(env[ENV_HANDOFF_TOKEN])
    ):
        raise SmokeHandoffError("Handoff token does not match the current handoff record")

    active_root = current_project_root(cwd)
    if active_root != target:
        raise SmokeHandoffError(
            "Current working tree is not the disposable smoke repository: {}".format(
                active_root or "NOT_A_GIT_WORK_TREE"
            )
        )

    return {**validated, "result": "ROOTED"}


def ensure_rooted(
    repo: Path,
    run_id: str,
    *,
    dry_run: bool = False,
    current_root: Path | None = None,
    runner: Callable[..., object] | None = None,
    env: Mapping[str, str] | None = None,
    config_dir: Path | None = None,
) -> dict[str, object]:
    """Continue only inside a proven rooted handoff; otherwise launch one."""
    validated = validate_workspace(repo, run_id)
    target = Path(validated["run_directory"])
    env = os.environ if env is None else env
    active_root = current_root.resolve() if current_root is not None else current_project_root()

    if any(env.get(name) for name in MARKER_ENV):
        # Inside a handoff child. Never launch a nested continuation: either this
        # is the proven rooted session, or rooting failed and the run must stop.
        rooted = assert_rooted(target, run_id, env=env, cwd=active_root)
        return {
            **rooted,
            "result": "ALREADY_ROOTED",
            "current_project_root": str(target),
            "command": None,
        }

    kilo = shutil.which("kilo")
    if not kilo:
        raise SmokeHandoffError("Kilo CLI is not available on PATH")

    config_dir = config_dir if config_dir is not None else installed_config_dir()
    protected = protected_source_paths(target, active_root, config_dir)
    overlay = build_config_overlay(protected)
    command = build_kilo_command(kilo, target, run_id)
    summary = {
        **validated,
        "current_project_root": str(active_root) if active_root else None,
        "command": command,
        "protected_source_paths": [str(path) for path in protected],
        "config_overlay": overlay,
    }
    if dry_run:
        return {**summary, "result": "NEEDS_HANDOFF"}

    token = secrets.token_hex(32)
    _write_json(handoff_record_path(target, run_id), {
        "schema_version": 1,
        "run_id": run_id,
        "run_directory": str(target),
        "token_sha256": _token_digest(token),
        "created_at_utc": _utc_now(),
        "protected_source_paths": [str(path) for path in protected],
        "command": command,
    })
    child_env = build_child_env(env, target, run_id, token, overlay, config_dir)

    # Headless Kilo cannot stop for permission prompts. --auto is allowed only
    # after the target has been proven to be the initialized disposable
    # smoke-run repository, and only together with the deny overlay above.
    invoke = runner or subprocess.run
    completed = invoke(command, cwd=str(target), env=child_env)
    returncode = getattr(completed, "returncode", None)
    if returncode != 0:
        raise SmokeHandoffError(
            "Rooted Kilo smoke continuation failed with exit code {}".format(returncode)
        )

    return {**summary, "result": "HANDOFF_COMPLETE", "child_exit_code": returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("ensure")
    actions.add_parser("dry-run")
    actions.add_parser("assert-rooted")
    args = parser.parse_args()

    try:
        if args.action == "assert-rooted":
            result: dict[str, object] = dict(assert_rooted(args.repo, args.run_id))
        else:
            result = ensure_rooted(
                args.repo,
                args.run_id,
                dry_run=args.action == "dry-run",
            )
        print(json.dumps({"ok": True, **result}))
        return 0
    except (
        SmokeHandoffError,
        OSError,
        ValueError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
