#!/usr/bin/env python3
"""Deterministic Contract-v1 freshness preflight for review workflows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_mechanics


class ReviewPreflightError(RuntimeError):
    pass


def review_preflight(repo: Path, base_head: str, persisted_manifest: Path) -> dict[str, object]:
    repo = repo.resolve()
    persisted_manifest = persisted_manifest.resolve()
    if not persisted_manifest.is_file():
        raise ReviewPreflightError(f"Persisted verification manifest is missing: {persisted_manifest}")

    expected = persisted_manifest.read_bytes()
    current = smoke_mechanics.canonical_manifest(repo, base_head)
    current_identity = smoke_mechanics.identity(repo, base_head)

    return {
        "base_head": base_head,
        "freshness": "MATCH" if current == expected else "MISMATCH",
        "canonical_manifest_equal": current == expected,
        "current_fingerprint": current_identity["fingerprint"],
        "persisted_manifest_path": str(persisted_manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--base", required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()

    try:
        result = review_preflight(args.repo, args.base, args.manifest)
        print(json.dumps({"ok": True, **result}))
        return 0 if result["freshness"] == "MATCH" else 3
    except (ReviewPreflightError, smoke_mechanics.MechanicsError, OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "freshness": "UNRECONSTRUCTABLE", "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
