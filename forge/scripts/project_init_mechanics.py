#!/usr/bin/env python3
"""Deterministic mechanical setup for SubhForge project initialization."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

WORKFLOW_DIRS = (
    "docs/discovery",
    "docs/prd",
    "docs/architecture",
    "docs/adr",
    "docs/specs",
    "docs/diagnostics",
    "docs/verification",
    "docs/verification/waivers",
    "docs/verification/waiver-refusals",
    "docs/verification/smoke",
    "docs/reviews",
    "docs/workflow",
    ".kilo/rules",
    ".kilo/skills",
)

CONTRACT_DEST = "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"


class ProjectInitError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def prepare(repo: Path, contract: Path) -> dict[str, object]:
    repo = repo.resolve()
    contract = contract.resolve()
    if not repo.is_dir():
        raise ProjectInitError("Project repository does not exist: {}".format(repo))
    if not contract.is_file():
        raise ProjectInitError("Evidence contract does not exist: {}".format(contract))

    created = []
    for rel in WORKFLOW_DIRS:
        path = repo / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(rel)

    dest = repo / CONTRACT_DEST
    dest.parent.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(contract)
    if dest.exists() and sha256(dest) == source_hash:
        copied = False
    else:
        shutil.copyfile(str(contract), str(dest))
        copied = True

    if sha256(dest) != source_hash:
        raise ProjectInitError("Evidence contract synchronization failed")

    return {
        "created_directories": created,
        "contract_destination": CONTRACT_DEST,
        "contract_sha256": source_hash,
        "contract_copied": copied,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.repo, args.contract)
        print(json.dumps({"ok": True, **result}))
        return 0
    except (ProjectInitError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
