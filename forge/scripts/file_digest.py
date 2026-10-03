#!/usr/bin/env python3
"""Compute a SHA-256 digest for one repository-confined file."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


class FileDigestError(RuntimeError):
    pass


def digest(repo: Path, path: Path) -> dict[str, str]:
    repo = repo.resolve()
    if not repo.is_dir():
        raise FileDigestError("Repository does not exist: {}".format(repo))
    target = path if path.is_absolute() else repo / path
    target = target.resolve()
    try:
        rel = target.relative_to(repo).as_posix()
    except ValueError as exc:
        raise FileDigestError("Digest path escapes repository") from exc
    if not target.is_file():
        raise FileDigestError("Digest target does not exist: {}".format(target))
    if rel.startswith("docs/verification/smoke/"):
        raise FileDigestError("Hidden smoke evidence cannot be digested")
    if not (
        rel == "AGENTS.md"
        or rel.startswith("docs/verification/")
        or rel.startswith("docs/workflow/")
    ):
        raise FileDigestError(
            "Digest path is outside approved waiver evidence locations"
        )

    h = hashlib.sha256()
    with target.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            h.update(block)
    return {"path": rel, "sha256": h.hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--path", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps({"ok": True, **digest(args.repo, args.path)}))
        return 0
    except (FileDigestError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
