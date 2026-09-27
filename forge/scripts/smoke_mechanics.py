#!/usr/bin/env python3
"""Deterministic, fail-closed mechanics for disposable SubhForge smoke runs.

This is a smoke utility, not a replacement for /verify, /review, or /fix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Optional


EXCLUDED = ("docs/verification/", "docs/reviews/", "docs/diagnostics/")
RECIPES = {
    "obvious-deterministic-defect",
    "ambiguous-normalization-defect",
    "ambiguous-persistence-defect",
    "trivial-documentation-or-waivable-quality-gate",
    "content-freshness-mismatch",
    "mode-type-mismatch-when-supported",
    "verification-mutation",
    "pre-review-blocker",
}


class MechanicsError(RuntimeError):
    pass


def git(repo: Path, *args: str, input_bytes: Optional[bytes] = None) -> bytes:
    result = subprocess.run(
        ["git", *args], cwd=repo, input=input_bytes, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if result.returncode:
        raise MechanicsError("git {} failed: {}".format(
            " ".join(args), result.stderr.decode("utf-8", "replace").strip()))
    return result.stdout


def _name(raw: bytes) -> str:
    try:
        name = raw.decode("utf-8", "strict")
    except UnicodeDecodeError as exc:
        raise MechanicsError("Non-UTF-8 repository path") from exc
    if not name or any(char in name for char in "\t\r\n"):
        raise MechanicsError("Unrepresentable repository path")
    return name


def _excluded(name: str) -> bool:
    return any(name.startswith(prefix) for prefix in EXCLUDED)


def _root(repo: Path) -> Path:
    root = Path(os.fsdecode(git(repo, "rev-parse", "--show-toplevel").strip())).resolve()
    if root != repo.resolve():
        raise MechanicsError("Use the disposable repository root")
    return root


def _target(repo: Path, name: str) -> Path:
    if not name or name.startswith("/") or "\\" in name or any(
        part in ("", ".", "..") for part in name.split("/")):
        raise MechanicsError("Invalid repository path")
    if _excluded(name) or name.startswith(".git/") or name == ".git":
        raise MechanicsError("Refusing to mutate evidence or Git metadata")
    leaf = name.rsplit("/", 1)[-1].lower()
    if leaf == ".env" or leaf.startswith(".env.") or leaf.endswith((".pem", ".key")):
        raise MechanicsError("Refusing to mutate a sensitive file")
    path = repo / name
    if path.parent.resolve() != (repo / name).parent.absolute():
        raise MechanicsError("Parent symlink escapes the repository")
    return path


def _index(repo: Path) -> dict[str, str]:
    entries = {}
    for raw in git(repo, "ls-files", "--stage", "-z").split(b"\0"):
        if not raw:
            continue
        meta, path = raw.split(b"\t", 1)
        mode, _, stage = meta.decode("ascii").split()
        if stage != "0":
            raise MechanicsError("Unmerged index is UNRECONSTRUCTABLE")
        entries[_name(path)] = mode
    return entries


def canonical_manifest(repo: Path, base: str) -> bytes:
    """Contract v1 manifest, or fail closed when a mode/type is uncertain."""
    repo = _root(repo)
    git(repo, "cat-file", "-e", "{}^{{commit}}".format(base))
    index = _index(repo)
    changed = {_name(p) for p in git(repo, "diff", "--name-only", "-z", base, "--").split(b"\0") if p}
    untracked = {_name(p) for p in git(repo, "ls-files", "--others", "--exclude-standard", "-z").split(b"\0") if p}
    entries = []
    for name in sorted(changed | untracked, key=lambda n: n.encode("utf-8")):
        if _excluded(name):
            continue
        path = repo / name
        try:
            info = path.lstat()
        except FileNotFoundError:
            if name not in index and name not in changed:
                raise MechanicsError("Path disappeared during reconstruction")
            entries.append("{}\tDELETED\tDELETED\n".format(name))
            continue
        if stat.S_ISLNK(info.st_mode):
            mode = "120000"
        elif stat.S_ISREG(info.st_mode):
            indexed = index.get(name)
            if indexed == "160000":
                raise MechanicsError("Gitlink mode is UNRECONSTRUCTABLE")
            # On Windows executable bits are not reliably observable. Git's
            # index is the effective mode when core.filemode is false.
            filemode = git(repo, "config", "--bool", "core.filemode").strip()
            if os.name == "nt" or filemode == b"false":
                if indexed is None:
                    # Git records new regular files as non-executable when
                    # core.filemode is false; the OS bit is not authoritative.
                    mode = "100644"
                elif indexed not in ("100644", "100755"):
                    raise MechanicsError("File mode is UNRECONSTRUCTABLE")
                else:
                    mode = indexed
            else:
                mode = "100755" if info.st_mode & 0o111 else "100644"
        else:
            raise MechanicsError("Unsupported file type is UNRECONSTRUCTABLE")
        oid = git(repo, "hash-object", "--no-filters", "--", name).strip().decode("ascii")
        entries.append("{}\t{}\t{}\n".format(name, mode, oid))
    return "".join(entries).encode("utf-8")


def identity(repo: Path, base: str) -> dict[str, str]:
    manifest = canonical_manifest(repo, base)
    oid = git(repo, "hash-object", "--stdin", input_bytes=manifest).strip().decode("ascii")
    return {"base_head": base, "manifest": manifest.decode("utf-8"),
            "fingerprint": "GIT_BLOB_OID:" + oid}


def _ledger(repo: Path, run_id: str) -> Path:
    if not run_id.startswith("SMOKE-") or not all(c.isalnum() or c == "-" for c in run_id):
        raise MechanicsError("Invalid run ID")
    if git(repo, "branch", "--show-current").strip() != b"smoke-run":
        raise MechanicsError("Mutation is restricted to the smoke-run branch")
    folder = repo / "docs/verification/smoke"
    if not folder.is_dir():
        raise MechanicsError("Smoke evidence directory is missing")
    return folder / (run_id + ".mechanics.json")


def _read(path: Path) -> dict:
    if not path.exists():
        return {"checkpoints": {}, "mutations": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if set(data) != {"checkpoints", "mutations"}:
        raise MechanicsError("Malformed mechanics ledger")
    return data


def _save(path: Path, data: dict) -> None:
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temp.replace(path)


def checkpoint(repo: Path, run_id: str, label: str) -> dict:
    path = _ledger(repo, run_id)
    data = _read(path)
    if label in data["checkpoints"]:
        raise MechanicsError("Checkpoint already exists")
    if any(not item["restored"] for item in data["mutations"].values()):
        raise MechanicsError("Restore active mutation before checkpointing")
    base = git(repo, "rev-parse", "HEAD").strip().decode("ascii")
    result = identity(repo, base)
    data["checkpoints"][label] = result
    _save(path, data)
    return result


def check_checkpoint(repo: Path, run_id: str, label: str) -> dict:
    saved = _read(_ledger(repo, run_id))["checkpoints"].get(label)
    if not saved:
        raise MechanicsError("Unknown checkpoint")
    current = identity(repo, saved["base_head"])
    return {"checkpoint": label, "result": "MATCH" if current["manifest"] == saved["manifest"] else "MISMATCH",
            "expected_fingerprint": saved["fingerprint"], "current_fingerprint": current["fingerprint"]}


def mutate(repo: Path, run_id: str, mutation_id: str, checkpoint_label: str,
           recipe: str, name: str, old: str, new: str) -> dict:
    if recipe not in RECIPES or not old or old == new:
        raise MechanicsError("Unsupported recipe or invalid anchored replacement")
    path = _ledger(repo, run_id)
    data = _read(path)
    if mutation_id in data["mutations"]:
        raise MechanicsError("Mutation ID already exists")
    if any(not item["restored"] for item in data["mutations"].values()):
        raise MechanicsError("Only one active mutation is allowed")
    if check_checkpoint(repo, run_id, checkpoint_label)["result"] != "MATCH":
        raise MechanicsError("Checkpoint drifted; refusing mutation")
    target = _target(repo, name)
    if not target.is_file() or target.is_symlink():
        raise MechanicsError("Mutation requires a regular existing file")
    before = target.read_bytes()
    old_bytes, new_bytes = old.encode("utf-8"), new.encode("utf-8")
    if before.count(old_bytes) != 1:
        raise MechanicsError("Anchor must occur exactly once")
    after = before.replace(old_bytes, new_bytes, 1)
    target.write_bytes(after)
    data["mutations"][mutation_id] = {"checkpoint": checkpoint_label, "recipe": recipe,
        "path": name, "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(), "old": old, "new": new,
        "restored": False}
    try:
        _save(path, data)
    except Exception:
        target.write_bytes(before)
        raise
    return {"mutation_id": mutation_id, "path": name, "recipe": recipe}


def restore(repo: Path, run_id: str, mutation_id: str) -> dict:
    path = _ledger(repo, run_id)
    data = _read(path)
    entry = data["mutations"].get(mutation_id)
    if not entry or entry["restored"]:
        raise MechanicsError("Unknown or already restored mutation")
    target = _target(repo, entry["path"])
    if not target.is_file() or target.is_symlink():
        raise MechanicsError("Mutated path changed type")
    after = target.read_bytes()
    if hashlib.sha256(after).hexdigest() != entry["after_sha256"]:
        raise MechanicsError("Mutation drifted; refusing restoration")
    old_bytes, new_bytes = entry["old"].encode(), entry["new"].encode()
    if after.count(new_bytes) != 1:
        raise MechanicsError("Replacement is no longer unique")
    before = after.replace(new_bytes, old_bytes, 1)
    if hashlib.sha256(before).hexdigest() != entry["before_sha256"]:
        raise MechanicsError("Restoration does not reproduce original bytes")
    target.write_bytes(before)
    if check_checkpoint(repo, run_id, entry["checkpoint"])["result"] != "MATCH":
        target.write_bytes(after)
        raise MechanicsError("Restoration failed checkpoint comparison")
    entry["restored"] = True
    _save(path, data)
    return {"mutation_id": mutation_id, "checkpoint": entry["checkpoint"], "result": "MATCH"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    actions = parser.add_subparsers(dest="action", required=True)
    for action in ("checkpoint", "check-checkpoint"):
        actions.add_parser(action).add_argument("--label", required=True)
    mutation = actions.add_parser("mutate")
    for key in ("mutation-id", "checkpoint", "recipe", "path", "old", "new"):
        mutation.add_argument("--" + key, required=True)
    actions.add_parser("restore").add_argument("--mutation-id", required=True)
    manifest = actions.add_parser("manifest")
    manifest.add_argument("--base", required=True)
    args = parser.parse_args()
    try:
        repo = _root(args.repo)
        if args.action == "manifest":
            result = identity(repo, args.base)
        elif args.action == "checkpoint":
            result = checkpoint(repo, args.run_id, args.label)
        elif args.action == "check-checkpoint":
            result = check_checkpoint(repo, args.run_id, args.label)
        elif args.action == "mutate":
            result = mutate(repo, args.run_id, args.mutation_id, args.checkpoint,
                            args.recipe, args.path, args.old, args.new)
        else:
            result = restore(repo, args.run_id, args.mutation_id)
        print(json.dumps({"ok": True, **result}))
        return 0
    except (MechanicsError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
