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
AGENTS_PATH = "AGENTS.md"
WAIVER_TRACE_PREFIXES = (
    "Waiver Policy Source:",
    "Waiver Policy SHA-256:",
    "Non-waivable Failure Types:",
    "Waivable Failure Types:",
)


class ProjectInitError(RuntimeError):
    pass


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            h.update(block)
    return h.hexdigest()


def _repo_relative(repo: Path, path: Path) -> tuple[str, Path]:
    resolved = path if path.is_absolute() else repo / path
    resolved = resolved.resolve()
    try:
        rel = resolved.relative_to(repo).as_posix()
    except ValueError as exc:
        raise ProjectInitError("Waiver policy escapes project repository") from exc
    return rel, resolved


def _policy_trace(repo: Path, waiver_policy: Path) -> dict[str, object]:
    rel, policy = _repo_relative(repo, waiver_policy)
    if not policy.is_file():
        raise ProjectInitError("Waiver policy does not exist: {}".format(policy))
    try:
        payload = json.loads(policy.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise ProjectInitError("Waiver policy is not valid JSON") from exc

    non_waivable = payload.get("non_waivable_failure_types")
    waivable = payload.get("waivable_failure_types")
    for name, values in (
        ("non_waivable_failure_types", non_waivable),
        ("waivable_failure_types", waivable),
    ):
        if (
            not isinstance(values, list)
            or not values
            or not all(isinstance(item, str) and item.strip() for item in values)
        ):
            raise ProjectInitError(
                "Waiver policy {} must be a non-empty string list".format(name)
            )

    agents = repo / AGENTS_PATH
    if not agents.is_file():
        raise ProjectInitError(
            "Project AGENTS.md must exist before waiver policy traceability is applied"
        )
    trace = {
        "Waiver Policy Source:": "Waiver Policy Source: {}".format(rel),
        "Waiver Policy SHA-256:": "Waiver Policy SHA-256: {}".format(sha256(policy)),
        "Non-waivable Failure Types:": "Non-waivable Failure Types: {}".format(
            ", ".join(non_waivable)
        ),
        "Waivable Failure Types:": "Waivable Failure Types: {}".format(
            ", ".join(waivable)
        ),
    }
    original = agents.read_text(encoding="utf-8")
    rendered_lines: list[str] = []
    seen: set[str] = set()
    for line in original.splitlines(keepends=True):
        bare = line.rstrip("\r\n")
        matched = next(
            (prefix for prefix in WAIVER_TRACE_PREFIXES if bare.startswith(prefix)),
            None,
        )
        if matched is None:
            rendered_lines.append(line)
            continue
        if matched in seen:
            continue
        newline = "\r\n" if line.endswith("\r\n") else "\n"
        rendered_lines.append(trace[matched] + newline)
        seen.add(matched)

    rendered = "".join(rendered_lines)
    if rendered and not rendered.endswith(("\n", "\r")):
        rendered += "\n"
    if len(seen) < len(WAIVER_TRACE_PREFIXES):
        if rendered and not rendered.endswith("\n\n"):
            rendered += "\n"
        rendered += "\n".join(
            trace[prefix]
            for prefix in WAIVER_TRACE_PREFIXES
            if prefix not in seen
        ) + "\n"

    changed = original != rendered
    if changed:
        agents.write_text(rendered, encoding="utf-8")
    return {
        "waiver_policy_source": rel,
        "waiver_policy_sha256": sha256(policy),
        "non_waivable_failure_types": list(non_waivable),
        "waivable_failure_types": list(waivable),
        "waiver_policy_trace_updated": changed,
    }


def prepare(
    repo: Path,
    contract: Path,
    waiver_policy: Path | None = None,
) -> dict[str, object]:
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

    result = {
        "created_directories": created,
        "contract_destination": CONTRACT_DEST,
        "contract_sha256": source_hash,
        "contract_copied": copied,
    }
    if waiver_policy is not None:
        result.update(_policy_trace(repo, waiver_policy))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--waiver-policy", type=Path)
    args = parser.parse_args()
    try:
        result = prepare(args.repo, args.contract, args.waiver_policy)
        print(json.dumps({"ok": True, **result}))
        return 0
    except (ProjectInitError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
