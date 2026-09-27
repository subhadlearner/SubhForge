#!/usr/bin/env python3
"""Deterministic disposable workspace management for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
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


def create_workspace(source: Path, source_commit: str, profile: str, fixture: str) -> Dict[str, str]:
    """Provision a disposable project from SubhForge/template at an exact release commit."""
    source = source.resolve()
    if not source.is_dir():
        raise SmokeWorkspaceError("SubhForge source checkout does not exist: {}".format(source))
    if _run_git(source, "rev-parse", "--is-inside-work-tree").lower() != "true":
        raise SmokeWorkspaceError("SubhForge source path is not a Git work tree: {}".format(source))

    resolved_commit = _run_git(source, "rev-parse", "{}^{{commit}}".format(source_commit))
    if resolved_commit != source_commit:
        source_commit = resolved_commit

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
    token = uuid.uuid4().hex[:8]
    release_clone = root / (".release-" + token)
    baseline = root / (".baseline-" + token)
    try:
        clone_release = subprocess.run(
            [git, "clone", "--no-hardlinks", "--local", "--no-checkout", str(source), str(release_clone)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if clone_release.returncode != 0:
            raise SmokeWorkspaceError("release clone failed: {}".format(
                (clone_release.stderr or clone_release.stdout).strip()))
        _run_git(release_clone, "checkout", "--detach", source_commit)

        template = release_clone / "template"
        if not template.is_dir():
            raise SmokeWorkspaceError("template/ is missing at release commit {}".format(source_commit))
        shutil.copytree(str(template), str(baseline))

        init = subprocess.run([git, "init", "-b", "main"], cwd=str(baseline),
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if init.returncode != 0:
            init = subprocess.run([git, "init"], cwd=str(baseline),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if init.returncode != 0:
            raise SmokeWorkspaceError("baseline git init failed: {}".format(
                (init.stderr or init.stdout).strip()))
        # Normalize the baseline branch name even when older Git required the
        # fallback init path.
        _run_git(baseline, "branch", "-M", "main")
        _run_git(baseline, "add", "-A")
        env = os.environ.copy()
        env["GIT_AUTHOR_DATE"] = "2000-01-01T00:00:00Z"
        env["GIT_COMMITTER_DATE"] = "2000-01-01T00:00:00Z"
        commit = subprocess.run(
            [git, "-c", "user.name=SubhForge", "-c", "user.email=subhforge@local",
             "commit", "-m", "Initialize smoke fixture from SubhForge template"],
            cwd=str(baseline), env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if commit.returncode != 0:
            raise SmokeWorkspaceError("baseline commit failed: {}".format(
                (commit.stderr or commit.stdout).strip()))
        baseline_head = _run_git(baseline, "rev-parse", "HEAD")

        clone = subprocess.run(
            [git, "clone", "--no-hardlinks", "--local", str(baseline), str(target)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        if clone.returncode != 0:
            raise SmokeWorkspaceError("git clone failed: {}".format(
                (clone.stderr or clone.stdout).strip()))
        _run_git(target, "switch", "-c", "smoke-run")
        cloned_head = _run_git(target, "rev-parse", "HEAD")
        if cloned_head != baseline_head:
            raise SmokeWorkspaceError(
                "Disposable clone HEAD {} does not match generated baseline HEAD {}.".format(
                    cloned_head, baseline_head))
    except Exception:
        if target.exists():
            shutil.rmtree(str(target), onerror=_remove_readonly)
        raise
    finally:
        if release_clone.exists():
            shutil.rmtree(str(release_clone), onerror=_remove_readonly)
        if baseline.exists():
            shutil.rmtree(str(baseline), onerror=_remove_readonly)

    return {
        "run_id": run_id,
        "profile": profile.upper(),
        "fixture": fixture,
        "source_checkout_path": str(source),
        "source_commit": source_commit,
        "baseline_branch": "main",
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
        "source_checkout_path": str(source),
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
            "source_checkout_path": str(source),
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

    shutil.rmtree(str(target), onerror=_remove_readonly)
    return {
        "run_id": run_id,
        "source_checkout_path": str(source),
        "run_directory": str(target),
        "destroyed": "true",
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage isolated SubhForge smoke workspaces.")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--source", required=True)
    create.add_argument("--source-commit", required=True)
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
            result = create_workspace(Path(args.source), args.source_commit, args.profile, args.fixture)
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
