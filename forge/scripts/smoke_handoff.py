#!/usr/bin/env python3
"""Deterministic Kilo workspace handoff for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_state


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

    root = Path(_run_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if root != repo:
        raise SmokeHandoffError("Smoke handoff target must be the repository root")
    branch = _run_git(repo, "branch", "--show-current")
    if branch != "smoke-run":
        raise SmokeHandoffError(
            "Smoke handoff target must be on smoke-run, found: {}".format(
                branch or "DETACHED"
            )
        )

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
    """Return the current Git project root, or None outside a Git work tree."""
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


def ensure_rooted(
    repo: Path,
    run_id: str,
    *,
    dry_run: bool = False,
    current_root: Path | None = None,
    runner: Callable[..., object] | None = None,
) -> dict[str, object]:
    """Continue locally when rooted, otherwise run smoke in the disposable repo."""
    validated = validate_workspace(repo, run_id)
    target = Path(validated["run_directory"])
    active_root = current_root.resolve() if current_root is not None else current_project_root()

    if active_root == target:
        return {
            **validated,
            "result": "ALREADY_ROOTED",
            "current_project_root": str(active_root),
            "command": None,
        }

    kilo = shutil.which("kilo")
    if not kilo:
        raise SmokeHandoffError("Kilo CLI is not available on PATH")

    command = build_kilo_command(kilo, target, run_id)
    if dry_run:
        return {
            **validated,
            "result": "NEEDS_HANDOFF",
            "current_project_root": str(active_root) if active_root else None,
            "command": command,
        }

    # Headless Kilo cannot stop for permission prompts. --auto is allowed only
    # after the target has been proven to be the initialized disposable
    # smoke-run repository. Explicit deny rules in the installed agents remain
    # authoritative inside that isolated repository.
    invoke = runner or subprocess.run
    completed = invoke(command, cwd=str(target))
    returncode = getattr(completed, "returncode", None)
    if returncode != 0:
        raise SmokeHandoffError(
            "Rooted Kilo smoke continuation failed with exit code {}".format(returncode)
        )

    return {
        **validated,
        "result": "HANDOFF_COMPLETE",
        "current_project_root": str(active_root) if active_root else None,
        "child_exit_code": returncode,
        "command": command,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    actions.add_parser("ensure")
    actions.add_parser("dry-run")
    args = parser.parse_args()

    try:
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
