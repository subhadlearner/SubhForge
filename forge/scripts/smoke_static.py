#!/usr/bin/env python3
"""Deterministic static parity checks for SubhForge smoke gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


class StaticGateError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contract_parity(required: list[Path], optional: list[Path]) -> dict[str, object]:
    if len(required) < 2:
        raise StaticGateError("At least two required canonical contract paths are required")

    required_results: list[dict[str, object]] = []
    required_hashes: list[str] = []
    for raw in required:
        path = raw.resolve()
        if not path.is_file():
            raise StaticGateError(f"Required canonical contract is missing: {path}")
        digest = _sha256(path)
        required_hashes.append(digest)
        required_results.append({
            "path": str(path),
            "exists": True,
            "sha256": digest,
        })

    optional_results: list[dict[str, object]] = []
    for raw in optional:
        path = raw.resolve()
        exists = path.is_file()
        optional_results.append({
            "path": str(path),
            "exists": exists,
            "sha256": _sha256(path) if exists else None,
        })

    return {
        "contract_equal": len(set(required_hashes)) == 1,
        "required": required_results,
        "optional": optional_results,
        "missing_optional": [
            item["path"] for item in optional_results if not item["exists"]
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    parity = sub.add_parser("contract-parity")
    parity.add_argument("--required", action="append", type=Path, default=[])
    parity.add_argument("--optional", action="append", type=Path, default=[])

    args = parser.parse_args()
    try:
        if args.action == "contract-parity":
            result = contract_parity(args.required, args.optional)
            print(json.dumps({"ok": bool(result["contract_equal"]), **result}))
            return 0 if result["contract_equal"] else 3
        raise StaticGateError("Unsupported static gate action")
    except (StaticGateError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
