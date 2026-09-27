#!/usr/bin/env python3
"""Deterministic bootstrap for a newly provisioned SubhForge smoke run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget
import smoke_state
import smoke_static


class SmokeBootstrapError(RuntimeError):
    pass


def _installed_config_root() -> Path:
    """Resolve <global-config> from this installed helper's own location."""
    return Path(__file__).resolve().parent.parent


def bootstrap(
    repo: Path,
    run_id: str,
    profile: str,
    fixture: str,
    source_commit: str,
    baseline_head: str,
    required_contracts: list[Path],
    optional_contracts: list[Path],
    config_root: Path | None = None,
) -> dict[str, object]:
    repo = repo.resolve()

    parity = smoke_static.contract_parity(required_contracts, optional_contracts)
    if not parity["contract_equal"]:
        raise SmokeBootstrapError("Required canonical Contract-v1 copies differ")

    state = smoke_state.init(
        repo,
        run_id,
        profile,
        fixture,
        source_commit,
        baseline_head,
    )
    budget = smoke_budget.start(repo, run_id)

    context = dict(state.get("context_index") or {})
    context["contract_parity"] = parity
    context["budget_started_at_utc"] = budget["started_at_utc"]
    smoke_state.set_values(repo, run_id, {"context_index": context})

    gate = smoke_static.release_gate(
        (config_root or _installed_config_root()).resolve(),
        repo,
        run_id,
    )
    state = smoke_state.load(repo, run_id)

    return {
        "state_path": str(smoke_state.state_path(repo, run_id)),
        "budget_started_at_utc": budget["started_at_utc"],
        "contract_parity": parity,
        "release_gate": gate,
        "state": state,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--fixture", required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--baseline-head", required=True)
    parser.add_argument("--required-contract", action="append", type=Path, default=[])
    parser.add_argument("--optional-contract", action="append", type=Path, default=[])
    args = parser.parse_args()

    try:
        result = bootstrap(
            args.repo,
            args.run_id,
            args.profile,
            args.fixture,
            args.source_commit,
            args.baseline_head,
            args.required_contract,
            args.optional_contract,
        )
        ok = bool(result["release_gate"]["ok"])
        print(json.dumps({"ok": ok, **result}))
        return 0 if ok else 3
    except (
        SmokeBootstrapError,
        smoke_state.SmokeStateError,
        smoke_budget.BudgetError,
        smoke_static.StaticGateError,
        OSError,
        ValueError,
        KeyError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
