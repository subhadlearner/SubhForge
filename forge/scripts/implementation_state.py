#!/usr/bin/env python3
"""Shared deterministic Contract-v1 implementation-state reconstruction."""

from __future__ import annotations

import os
import stat
import subprocess
from pathlib import Path

EXCLUDED = ("docs/verification/", "docs/reviews/", "docs/diagnostics/")


class ImplementationStateError(RuntimeError):
    pass


def git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise ImplementationStateError(
            "git {} failed: {}".format(
                " ".join(args),
                result.stderr.decode("utf-8", "replace").strip(),
            )
        )
    return result.stdout


def _name(raw: bytes) -> str:
    try:
        name = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise ImplementationStateError("Non-UTF-8 repository path") from exc
    if not name or any(char in name for char in "\t\r\n"):
        raise ImplementationStateError("Unrepresentable repository path")
    return name


def excluded(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in EXCLUDED)


def repo_root(repo: Path) -> Path:
    root = Path(os.fsdecode(git(repo, "rev-parse", "--show-toplevel").strip())).resolve()
    if root != repo.resolve():
        raise ImplementationStateError("Use the repository root")
    return root


def _index(repo: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for raw in git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if not raw:
            continue
        meta, path = raw.split(b"\t", 1)
        mode, _, stage = meta.decode("ascii").split()
        if stage != "0":
            raise ImplementationStateError("Unmerged index is UNRECONSTRUCTABLE")
        entries[_name(path)] = mode
    return entries


def _hash_paths(repo: Path, names: list[str]) -> dict[str, str]:
    """Return raw Git blob OIDs for repository paths with one git process.

    Contract-v1 paths are already required to be UTF-8 and free of newlines,
    making git hash-object --stdin-paths safe and unambiguous here.
    """
    if not names:
        return {}
    payload = ("\n".join(names) + "\n").encode("utf-8")
    raw = git(repo, "hash-object", "--no-filters", "--stdin-paths", input_bytes=payload)
    oids = [line.decode("ascii") for line in raw.splitlines() if line]
    if len(oids) != len(names):
        raise ImplementationStateError("Git returned an incomplete batch hash result")
    return dict(zip(names, oids))


def canonical_manifest(repo: Path, base: str) -> bytes:
    """Return Contract-v1 canonical manifest or fail closed."""
    repo = repo_root(repo)
    git(repo, "cat-file", "-e", f"{base}^{{commit}}")
    index = _index(repo)
    changed = {
        _name(p)
        for p in git(repo, "diff", "--name-only", "-z", base, "--").split(b"\0")
        if p
    }
    untracked = {
        _name(p)
        for p in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0")
        if p
    }

    names = [
        name
        for name in sorted(changed | untracked, key=lambda n: n.encode("utf-8"))
        if not excluded(name)
    ]
    filemode = git(repo, "config", "--bool", "core.filemode").strip()

    modes: dict[str, str] = {}
    hash_names: list[str] = []
    deleted: set[str] = set()

    for name in names:
        path = repo / name
        try:
            info = path.lstat()
        except FileNotFoundError:
            if name not in index and name not in changed:
                raise ImplementationStateError("Path disappeared during reconstruction")
            deleted.add(name)
            continue

        if stat.S_ISLNK(info.st_mode):
            modes[name] = "120000"
        elif stat.S_ISREG(info.st_mode):
            indexed = index.get(name)
            if indexed == "160000":
                raise ImplementationStateError("Gitlink mode is UNRECONSTRUCTABLE")

            if os.name == "nt" or filemode == b"false":
                if indexed is None:
                    modes[name] = "100644"
                elif indexed not in ("100644", "100755"):
                    raise ImplementationStateError("File mode is UNRECONSTRUCTABLE")
                else:
                    modes[name] = indexed
            else:
                modes[name] = "100755" if info.st_mode & 0o111 else "100644"
        else:
            raise ImplementationStateError("Unsupported file type is UNRECONSTRUCTABLE")
        hash_names.append(name)

    hashes = _hash_paths(repo, hash_names)
    entries: list[str] = []
    for name in names:
        if name in deleted:
            entries.append(f"{name}\tDELETED\tDELETED\n")
        else:
            entries.append(f"{name}\t{modes[name]}\t{hashes[name]}\n")

    return "".join(entries).encode("utf-8")


def fingerprint(repo: Path, manifest: bytes) -> str:
    oid = git(repo, "hash-object", "--stdin", input_bytes=manifest).strip().decode("ascii")
    return "GIT_BLOB_OID:" + oid


def identity(repo: Path, base: str) -> dict[str, str]:
    manifest = canonical_manifest(repo, base)
    return {
        "base_head": base,
        "manifest": manifest.decode("utf-8"),
        "fingerprint": fingerprint(repo, manifest),
    }
