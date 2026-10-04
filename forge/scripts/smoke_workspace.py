#!/usr/bin/env python3
"""Deterministic disposable workspace management for SubhForge smoke runs."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
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


def source_guard(source: Path) -> Dict[str, str]:
    """Fingerprint the source checkout so smoke stages can prove they did not mutate it."""
    source = source.resolve()
    if not source.is_dir():
        raise SmokeWorkspaceError("SubhForge source checkout does not exist: {}".format(source))
    _require_exact_git_root(source, "SubhForge source checkout")

    git = shutil.which("git")
    assert git is not None
    proc = subprocess.run(
        [git, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=str(source),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise SmokeWorkspaceError("git ls-files failed: {}".format(
            proc.stderr.decode("utf-8", errors="replace").strip()))

    digest = hashlib.sha256()
    digest.update(_run_git(source, "rev-parse", "HEAD").encode("ascii"))
    digest.update(b"\0")
    digest.update((_run_git(source, "branch", "--show-current") or "DETACHED").encode("utf-8"))
    digest.update(b"\0")

    raw_paths = [item for item in proc.stdout.split(b"\0") if item]
    for raw in sorted(raw_paths):
        rel = raw.decode("utf-8", errors="surrogateescape")
        path = source / rel
        digest.update(raw)
        digest.update(b"\0")
        if path.is_symlink():
            digest.update(b"SYMLINK\0")
            digest.update(os.readlink(path).encode("utf-8", errors="surrogateescape"))
        elif path.is_file():
            digest.update(b"FILE\0")
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        elif path.exists():
            digest.update(b"OTHER\0")
        else:
            digest.update(b"MISSING\0")
        digest.update(b"\0")

    return {
        "source_checkout_path": str(source),
        "fingerprint": digest.hexdigest(),
    }


def verify_source_guard(source: Path, expected: str) -> Dict[str, str]:
    current = source_guard(source)
    result = "MATCH" if current["fingerprint"] == expected else "MISMATCH"
    return {**current, "expected_fingerprint": expected, "result": result}


def _repo_name(source: Path) -> str:
    return source.name or "project"


def _run_root(source: Path) -> Path:
    return source.parent / ("{}-smoke-runs".format(_repo_name(source)))


def _new_run_id(profile: str, fixture: str) -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = uuid.uuid4().hex[:8]
    return "SMOKE-{}-{}-{}-{}".format(profile.upper(), fixture, stamp, suffix)


RUN_ID_PATTERN = re.compile(
    r"^SMOKE-(FAST|FULL)-[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*-"
    r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}$"
)
SMOKE_RUN_ID_CONFIG = "subhforge.smokeRunId"
SMOKE_BASELINE_HEAD_CONFIG = "subhforge.smokeBaselineHead"


def _require_exact_git_root(repo: Path, label: str) -> Path:
    repo = repo.resolve()
    if not repo.is_dir():
        raise SmokeWorkspaceError("{} does not exist: {}".format(label, repo))
    root = Path(_run_git(repo, "rev-parse", "--show-toplevel")).resolve()
    if root != repo:
        raise SmokeWorkspaceError("{} must itself be the Git top-level: {}".format(label, repo))
    return repo


def _read_subhforge_identity(config_path: Path) -> tuple[Optional[str], Optional[str]]:
    """Read only helper-owned identity keys without rejecting unrelated valid Git config."""

    try:
        lines = config_path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise SmokeWorkspaceError(
            "Disposable smoke repository local Git config is unreadable"
        ) from exc

    section = ""
    values: dict[str, str] = {}
    identity_keys = {
        "smokerunid": "run_id",
        "smokebaselinehead": "baseline_head",
    }
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            if not line.endswith("]"):
                raise SmokeWorkspaceError(
                    "Disposable smoke repository local Git config has a malformed section"
                )
            body = line[1:-1].strip()
            section = body.lower()
            continue
        if section != "subhforge":
            continue
        key_text, separator, value_text = line.partition("=")
        if not separator:
            continue
        canonical = identity_keys.get(key_text.strip().lower())
        if canonical is None:
            continue
        value = value_text.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        if canonical in values:
            raise SmokeWorkspaceError(
                "Disposable smoke repository ownership metadata is ambiguous"
            )
        values[canonical] = value

    return values.get("run_id"), values.get("baseline_head")


def _standalone_git_identity(
    repo: Path,
) -> tuple[str, Optional[str], Optional[str]]:
    """Read identity only from repo's own Git admin directory.

    Disposable smoke repositories are standalone clones created by this helper.
    Requiring an actual .git directory at the resolved target avoids Git's
    parent-directory discovery entirely and fails closed for linked worktrees.
    """
    git_dir = repo / ".git"
    if not git_dir.is_dir():
        raise SmokeWorkspaceError(
            "Disposable smoke repository must itself be the Git top-level: {}".format(repo)
        )

    try:
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SmokeWorkspaceError("Disposable smoke repository HEAD is unreadable") from exc
    prefix = "ref: refs/heads/"
    branch = head[len(prefix):] if head.startswith(prefix) else "DETACHED"

    recorded_run_id, recorded_baseline = _read_subhforge_identity(git_dir / "config")
    return branch, recorded_run_id, recorded_baseline


def _stamp_repository_identity(repo: Path, run_id: str, baseline_head: str) -> None:
    repo = _require_exact_git_root(repo, "Disposable smoke repository")
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise SmokeWorkspaceError("Invalid run ID")
    if _run_git(repo, "branch", "--show-current") != "smoke-run":
        raise SmokeWorkspaceError("Disposable smoke repository must be on smoke-run")
    _run_git(repo, "cat-file", "-e", "{}^{{commit}}".format(baseline_head))
    if _run_git(repo, "rev-parse", "HEAD") != baseline_head:
        raise SmokeWorkspaceError(
            "Disposable smoke repository HEAD must match baseline before ownership is stamped"
        )
    _run_git(repo, "config", "--local", SMOKE_RUN_ID_CONFIG, run_id)
    _run_git(repo, "config", "--local", SMOKE_BASELINE_HEAD_CONFIG, baseline_head)


def validate_repository_identity(
    repo: Path,
    run_id: Optional[str] = None,
    baseline_head: Optional[str] = None,
) -> Dict[str, str]:
    """Prove that repo itself is a helper-owned disposable smoke repository.

    Creation stamps ownership only after proving HEAD == baseline_head. Runtime
    validation reads branch/run/baseline identity from the target's own Git
    admin directory, then uses one Git process pinned to that exact admin
    directory to prove the recorded baseline remains an ancestor of HEAD.
    """
    repo = repo.resolve()
    if not repo.is_dir():
        raise SmokeWorkspaceError(
            "Disposable smoke repository does not exist: {}".format(repo)
        )
    branch, recorded_run_id, recorded_baseline = _standalone_git_identity(repo)
    if branch != "smoke-run":
        raise SmokeWorkspaceError(
            "Disposable smoke repository must be on smoke-run, found: {}".format(branch)
        )

    if (
        recorded_run_id is None
        or RUN_ID_PATTERN.fullmatch(recorded_run_id) is None
        or recorded_baseline is None
    ):
        raise SmokeWorkspaceError("Disposable smoke repository ownership metadata is missing")
    if run_id is not None and recorded_run_id != run_id:
        raise SmokeWorkspaceError(
            "Disposable smoke repository belongs to a different run: {}".format(
                recorded_run_id
            )
        )
    if baseline_head is not None and recorded_baseline != baseline_head:
        raise SmokeWorkspaceError("Disposable smoke repository baseline identity does not match")
    git_dir = repo / ".git"
    _run_git(
        repo,
        "--git-dir={}".format(git_dir),
        "--work-tree={}".format(repo),
        "merge-base",
        "--is-ancestor",
        recorded_baseline,
        "HEAD",
    )
    return {
        "run_directory": str(repo),
        "run_id": recorded_run_id,
        "baseline_head": recorded_baseline,
        "run_branch": branch,
    }


def _workspace_target(source: Path, run_id: str) -> tuple[Path, Path]:
    if not isinstance(run_id, str) or RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise SmokeWorkspaceError("Invalid run ID")

    root = _run_root(source).resolve()
    target = (root / run_id).resolve()
    if target.parent != root:
        raise SmokeWorkspaceError("Smoke run path escapes smoke run root.")
    return root, target


def create_workspace(source: Path, source_commit: str, profile: str, fixture: str) -> Dict[str, str]:
    """Provision a disposable project from SubhForge/template at an exact release commit."""
    source = source.resolve()
    if not source.is_dir():
        raise SmokeWorkspaceError("SubhForge source checkout does not exist: {}".format(source))
    _require_exact_git_root(source, "SubhForge source checkout")

    resolved_commit = _run_git(source, "rev-parse", "{}^{{commit}}".format(source_commit))
    if resolved_commit != source_commit:
        source_commit = resolved_commit

    root = _run_root(source).resolve()
    root.mkdir(parents=True, exist_ok=True)

    for _ in range(10):
        run_id = _new_run_id(profile, fixture)
        _, target = _workspace_target(source, run_id)
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
        _stamp_repository_identity(target, run_id, baseline_head)
        validate_repository_identity(target, run_id, baseline_head)
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
    source = _require_exact_git_root(source.resolve(), "SubhForge source checkout")
    _, target = _workspace_target(source, run_id)
    if not target.is_dir():
        raise SmokeWorkspaceError("Smoke run directory not found: {}".format(target))
    identity = validate_repository_identity(target, run_id)
    head = _run_git(target, "rev-parse", "HEAD")
    branch = identity["run_branch"]
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
    source = _require_exact_git_root(source.resolve(), "SubhForge source checkout")
    _, target = _workspace_target(source, run_id)
    if not target.exists():
        return {
            "run_id": run_id,
            "source_checkout_path": str(source),
            "run_directory": str(target),
            "destroyed": "false",
            "reason": "NOT_FOUND",
        }

    # Safety check: only delete a repository stamped by this helper for run_id.
    validate_repository_identity(target, run_id)

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

    guard = sub.add_parser("source-guard")
    guard.add_argument("--source", required=True)
    guard.add_argument("--expected")

    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "create":
            result = create_workspace(Path(args.source), args.source_commit, args.profile, args.fixture)
        elif args.command == "locate":
            result = locate_workspace(Path(args.source), args.run_id)
        elif args.command == "destroy":
            result = destroy_workspace(Path(args.source), args.run_id)
        elif args.expected:
            result = verify_source_guard(Path(args.source), args.expected)
            if result["result"] != "MATCH":
                print(json.dumps({"ok": False, **result}))
                return 3
        else:
            result = source_guard(Path(args.source))
    except SmokeWorkspaceError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2

    print(json.dumps({"ok": True, **result}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
