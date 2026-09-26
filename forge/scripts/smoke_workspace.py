#!/usr/bin/env python3
"""Deterministic disposable workspace management for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import stat
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Dict, Optional


class SmokeWorkspaceError(RuntimeError):
    pass


def _run_git(repo: Path, *args: str) -> str:
    git = shutil.which("git")
    if not git:
        raise SmokeWorkspaceError("Git is not available on PATH.")
    proc = subprocess.run(
        [git, *args],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout).strip()
        raise SmokeWorkspaceError("git {} failed: {}".format(" ".join(args), detail))
    return proc.stdout.strip()


def _repo_name(source: Path) -> str:
    return source.name or "project"


def _run_root(source: Path) -> Path:
    return source.parent / ("{}-smoke-runs".format(_repo_name(source)))


def _new_run_id(profile: str, fixture: str) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return "SMOKE-{}-{}-{}-{}".format(profile.upper(), fixture, stamp, suffix)


def create_workspace(source: Path, profile: str, fixture: str) -> Dict[str, str]:
    source = source.resolve()
    if not source.is_dir():
        raise SmokeWorkspaceError("Source repository does not exist: {}".format(source))

    inside = _run_git(source, "rev-parse", "--is-inside-work-tree")
    if inside.lower() != "true":
        raise SmokeWorkspaceError("Source path is not a Git work tree: {}".format(source))

    dirty = _run_git(source, "status", "--porcelain")
    if dirty:
        raise SmokeWorkspaceError(
            "Source repository must be clean before a smoke run. "
            "Commit, stash, or remove unrelated changes first."
        )

    baseline_head = _run_git(source, "rev-parse", "HEAD")
    baseline_branch = _run_git(source, "branch", "--show-current") or "DETACHED"

    root = _run_root(source)
    root.mkdir(parents=True, exist_ok=True)

    for _ in range(10):
        run_id = _new_run_id(profile, fixture)
        target = root / run_id
        if not target.exists():
            break
    else:
        raise SmokeWorkspaceError("Unable to allocate a unique smoke run directory.")

    git = shutil.which("git")
    assert git is not None
    clone = subprocess.run(
        [git, "clone", "--no-hardlinks", "--local", str(source), str(target)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if clone.returncode != 0:
        detail = (clone.stderr or clone.stdout).strip()
        raise SmokeWorkspaceError("git clone failed: {}".format(detail))

    try:
        _run_git(target, "switch", "-c", "smoke-run")
    except Exception:
        shutil.rmtree(str(target), ignore_errors=True)
        raise

    cloned_head = _run_git(target, "rev-parse", "HEAD")
    if cloned_head != baseline_head:
        shutil.rmtree(str(target), ignore_errors=True)
        raise SmokeWorkspaceError(
            "Disposable clone HEAD {} does not match baseline HEAD {}.".format(
                cloned_head, baseline_head
            )
        )

    return {
        "run_id": run_id,
        "profile": profile.upper(),
        "fixture": fixture,
        "source_repository": str(source),
        "baseline_branch": baseline_branch,
        "baseline_head": baseline_head,
        "run_directory": str(target),
        "run_branch": "smoke-run",
    }


def locate_workspace(source: Path, run_id: str) -> Dict[str, str]:
    source = source.resolve()
    target = _run_root(source) / run_id
    if not target.is_dir():
        raise SmokeWorkspaceError("Smoke run directory not found: {}".format(target))
    head = _run_git(target, "rev-parse", "HEAD")
    branch = _run_git(target, "branch", "--show-current") or "DETACHED"
    return {
        "run_id": run_id,
        "source_repository": str(source),
        "run_directory": str(target),
        "current_head": head,
        "run_branch": branch,
    }


def _remove_readonly(func, path, exc):
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def destroy_workspace(source: Path, run_id: str) -> Dict[str, str]:
    source = source.resolve()
    root = _run_root(source).resolve()
    target = (root / run_id).resolve()

    if target.parent != root:
        raise SmokeWorkspaceError("Refusing to delete path outside smoke run root.")
    if not target.exists():
        return {
            "run_id": run_id,
            "source_repository": str(source),
            "run_directory": str(target),
            "destroyed": "false",
            "reason": "NOT_FOUND",
        }

    # Safety check: only delete a workspace created by this helper.
    branch = _run_git(target, "branch", "--show-current") or "DETACHED"
    if branch != "smoke-run":
        raise SmokeWorkspaceError(
            "Refusing to delete workspace whose current branch is not smoke-run: {}".format(branch)
        )

    shutil.rmtree(str(target), onexc=_remove_readonly)
    return {
        "run_id": run_id,
        "source_repository": str(source),
        "run_directory": str(target),
        "destroyed": "true",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage isolated SubhForge smoke workspaces.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--source", required=True)
    create.add_argument("--profile", required=True, choices=["FAST", "FULL"])
    create.add_argument("--fixture", required=True)

    locate = sub.add_parser("locate")
    locate.add_argument("--source", required=True)
    locate.add_argument("--run-id", required=True)

    destroy = sub.add_parser("destroy")
    destroy.add_argument("--source", required=True)
    destroy.add_argument("--run-id", required=True)

    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "create":
            result = create_workspace(Path(args.source), args.profile, args.fixture)
        elif args.command == "locate":
            result = locate_workspace(Path(args.source), args.run_id)
        else:
            result = destroy_workspace(Path(args.source), args.run_id)
    except SmokeWorkspaceError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2

    print(json.dumps({"ok": True, **result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
