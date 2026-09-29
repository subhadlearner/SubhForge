#!/usr/bin/env python3
"""Deterministic, fail-closed mechanics for disposable SubhForge smoke runs.

This is a smoke utility, not a replacement for /verify, /review, or /fix.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import implementation_state

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

VERIFICATION_MUTATION_PATH = ".subhforge-verification-mutation.txt"
VERIFICATION_MUTATION_BYTES = b"SUBHFORGE_VERIFICATION_MUTATION\n"

MechanicsError = implementation_state.ImplementationStateError
git = implementation_state.git
canonical_manifest = implementation_state.canonical_manifest
identity = implementation_state.identity


def _target(repo: Path, name: str) -> Path:
    if not name or name.startswith("/") or "\\" in name or any(
        part in ("", ".", "..") for part in name.split("/")):
        raise MechanicsError("Invalid repository path")
    if implementation_state.excluded(name) or name.startswith(".git/") or name == ".git":
        raise MechanicsError("Refusing to mutate evidence or Git metadata")
    leaf = name.rsplit("/", 1)[-1].lower()
    if leaf == ".env" or leaf.startswith(".env.") or leaf.endswith((".pem", ".key")):
        raise MechanicsError("Refusing to mutate a sensitive file")
    path = repo / name
    if path.parent.resolve() != (repo / name).parent.absolute():
        raise MechanicsError("Parent symlink escapes the repository")
    return path


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


def _has_active_mutation(data: dict) -> bool:
    return any(not item.get("restored", False) for item in data["mutations"].values())


def checkpoint(repo: Path, run_id: str, label: str) -> dict:
    path = _ledger(repo, run_id)
    data = _read(path)
    if label in data["checkpoints"]:
        raise MechanicsError("Checkpoint already exists")
    if _has_active_mutation(data):
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
    return {
        "checkpoint": label,
        "result": "MATCH" if current["manifest"] == saved["manifest"] else "MISMATCH",
        "base_head": saved["base_head"],
        "expected_fingerprint": saved["fingerprint"],
        "current_fingerprint": current["fingerprint"],
    }


def mutate(repo: Path, run_id: str, mutation_id: str, checkpoint_label: str,
           recipe: str, name: str, old: str, new: str) -> dict:
    if recipe not in RECIPES or not old or old == new:
        raise MechanicsError("Unsupported recipe or invalid anchored replacement")
    if recipe == "verification-mutation":
        raise MechanicsError(
            "verification-mutation must use arm-verification-mutation/fire-verification-mutation"
        )
    path = _ledger(repo, run_id)
    data = _read(path)
    if mutation_id in data["mutations"]:
        raise MechanicsError("Mutation ID already exists")
    if _has_active_mutation(data):
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
        "path": name, "operation": "replace",
        "before_sha256": hashlib.sha256(before).hexdigest(),
        "after_sha256": hashlib.sha256(after).hexdigest(), "old": old, "new": new,
        "applied": True, "restored": False}
    try:
        _save(path, data)
    except Exception:
        target.write_bytes(before)
        raise
    return {"mutation_id": mutation_id, "path": name, "recipe": recipe}


def arm_verification_mutation(
    repo: Path, run_id: str, mutation_id: str, checkpoint_label: str
) -> dict:
    path = _ledger(repo, run_id)
    data = _read(path)
    if not mutation_id:
        raise MechanicsError("Mutation ID is required")
    if mutation_id in data["mutations"]:
        raise MechanicsError("Mutation ID already exists")
    if _has_active_mutation(data):
        raise MechanicsError("Only one active mutation is allowed")
    if check_checkpoint(repo, run_id, checkpoint_label)["result"] != "MATCH":
        raise MechanicsError("Checkpoint drifted; refusing verification mutation")
    target = _target(repo, VERIFICATION_MUTATION_PATH)
    if target.exists() or target.is_symlink():
        raise MechanicsError("Verification mutation target already exists")
    data["mutations"][mutation_id] = {
        "checkpoint": checkpoint_label,
        "recipe": "verification-mutation",
        "path": VERIFICATION_MUTATION_PATH,
        "operation": "create",
        "after_sha256": hashlib.sha256(VERIFICATION_MUTATION_BYTES).hexdigest(),
        "applied": False,
        "restored": False,
    }
    _save(path, data)
    return {"mutation_id": mutation_id, "checkpoint": checkpoint_label,
            "recipe": "verification-mutation", "path": VERIFICATION_MUTATION_PATH,
            "state": "ARMED"}


def fire_verification_mutation(repo: Path, run_id: str, mutation_id: str) -> dict:
    path = _ledger(repo, run_id)
    data = _read(path)
    entry = data["mutations"].get(mutation_id)
    if (not entry or entry.get("restored")
            or entry.get("recipe") != "verification-mutation"
            or entry.get("operation") != "create"
            or entry.get("applied")):
        raise MechanicsError("Verification mutation is not armed")
    if check_checkpoint(repo, run_id, entry["checkpoint"])["result"] != "MATCH":
        raise MechanicsError("Checkpoint drifted before verification mutation hook")
    target = _target(repo, entry["path"])
    if target.exists() or target.is_symlink():
        raise MechanicsError("Verification mutation target already exists")
    target.write_bytes(VERIFICATION_MUTATION_BYTES)
    try:
        if hashlib.sha256(target.read_bytes()).hexdigest() != entry["after_sha256"]:
            raise MechanicsError("Verification mutation bytes are not deterministic")
        result = check_checkpoint(repo, run_id, entry["checkpoint"])
        if result["result"] != "MISMATCH":
            raise MechanicsError(
                "Verification mutation did not change Contract-v1 implementation identity"
            )
        entry["applied"] = True
        _save(path, data)
    except Exception:
        if target.is_file() and not target.is_symlink():
            target.unlink()
        raise
    return {"mutation_id": mutation_id, "checkpoint": entry["checkpoint"],
            "recipe": entry["recipe"], "path": entry["path"], "state": "APPLIED",
            "checkpoint_result": "MISMATCH"}


def restore(repo: Path, run_id: str, mutation_id: str) -> dict:
    path = _ledger(repo, run_id)
    data = _read(path)
    entry = data["mutations"].get(mutation_id)
    if not entry or entry.get("restored"):
        raise MechanicsError("Unknown or already restored mutation")
    operation = entry.get("operation", "replace")
    target = _target(repo, entry["path"])

    if operation == "create":
        if not entry.get("applied", False):
            if target.exists() or target.is_symlink():
                raise MechanicsError("Unfired verification mutation target unexpectedly exists")
            if check_checkpoint(repo, run_id, entry["checkpoint"])["result"] != "MATCH":
                raise MechanicsError("Checkpoint drifted; refusing mutation disarm")
            entry["restored"] = True
            _save(path, data)
            return {"mutation_id": mutation_id, "checkpoint": entry["checkpoint"],
                    "result": "MATCH", "state": "RESTORED"}
        if not target.is_file() or target.is_symlink():
            raise MechanicsError("Verification mutation target changed type")
        after = target.read_bytes()
        if hashlib.sha256(after).hexdigest() != entry["after_sha256"]:
            raise MechanicsError("Verification mutation drifted; refusing restoration")
        target.unlink()
        if check_checkpoint(repo, run_id, entry["checkpoint"])["result"] != "MATCH":
            target.write_bytes(after)
            raise MechanicsError("Restoration failed checkpoint comparison")
        entry["restored"] = True
        try:
            _save(path, data)
        except Exception:
            target.write_bytes(after)
            raise
        return {"mutation_id": mutation_id, "checkpoint": entry["checkpoint"],
                "result": "MATCH", "state": "RESTORED"}

    if operation != "replace":
        raise MechanicsError("Unknown mutation operation")
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
    arm = actions.add_parser("arm-verification-mutation")
    arm.add_argument("--mutation-id", required=True)
    arm.add_argument("--checkpoint", required=True)
    fire = actions.add_parser("fire-verification-mutation")
    fire.add_argument("--mutation-id", required=True)
    actions.add_parser("restore").add_argument("--mutation-id", required=True)
    manifest = actions.add_parser("manifest")
    manifest.add_argument("--base", required=True)
    args = parser.parse_args()
    try:
        repo = implementation_state.repo_root(args.repo)
        if args.action == "manifest":
            result = identity(repo, args.base)
        elif args.action == "checkpoint":
            result = checkpoint(repo, args.run_id, args.label)
        elif args.action == "check-checkpoint":
            result = check_checkpoint(repo, args.run_id, args.label)
        elif args.action == "mutate":
            result = mutate(repo, args.run_id, args.mutation_id, args.checkpoint,
                            args.recipe, args.path, args.old, args.new)
        elif args.action == "arm-verification-mutation":
            result = arm_verification_mutation(
                repo, args.run_id, args.mutation_id, args.checkpoint
            )
        elif args.action == "fire-verification-mutation":
            result = fire_verification_mutation(repo, args.run_id, args.mutation_id)
        else:
            result = restore(repo, args.run_id, args.mutation_id)
        print(json.dumps({"ok": True, **result}))
        return 0
    except (MechanicsError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
