#!/usr/bin/env python3
"""Deterministic bootstrap for a newly provisioned SubhForge smoke run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget
import smoke_h08b
import smoke_state
import smoke_segments
import smoke_static
import smoke_workspace


class SmokeBootstrapError(RuntimeError):
    pass


def _installed_config_root() -> Path:
    """Resolve <global-config> from this installed helper's own location."""
    return Path(__file__).resolve().parent.parent


def _fixture_definition(config_root: Path, fixture_id: str) -> dict[str, object]:
    registry = config_root / "smoke" / "fixtures.json"
    try:
        payload = json.loads(registry.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise SmokeBootstrapError("Smoke fixture registry is unreadable") from exc
    fixtures = payload.get("fixtures")
    if not isinstance(fixtures, list):
        raise SmokeBootstrapError("Smoke fixture registry is malformed")
    for item in fixtures:
        if isinstance(item, dict) and item.get("id") == fixture_id:
            return item
    raise SmokeBootstrapError("Unknown smoke fixture: {}".format(fixture_id))


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
    source: Path | None = None,
) -> dict[str, object]:
    repo = repo.resolve()
    resolved_config = (config_root or _installed_config_root()).resolve()

    # Validate the selected live profile and (for FULL) the canonical invocation
    # spec before creating any run state.
    smoke_segments.build_snapshot(resolved_config, profile)
    if source is None:
        raise SmokeBootstrapError("Smoke bootstrap requires the exact SubhForge source checkout")
    try:
        source_fingerprint = smoke_workspace.source_guard(source.resolve())["fingerprint"]
    except smoke_workspace.SmokeWorkspaceError as exc:
        raise SmokeBootstrapError("Smoke source guard failed: {}".format(exc)) from exc

    parity = smoke_static.contract_parity(required_contracts, optional_contracts)
    if not parity["contract_equal"]:
        raise SmokeBootstrapError("Required canonical Contract-v1 copies differ")

    fixture_definition = _fixture_definition(resolved_config, fixture)
    if profile not in fixture_definition.get("profiles", []):
        raise SmokeBootstrapError(
            "Fixture {} is not valid for profile {}".format(fixture, profile)
        )

    state = smoke_state.init(
        repo,
        run_id,
        profile,
        fixture,
        source_commit,
        baseline_head,
    )
    if profile == "FULL":
        waiver_policy = fixture_definition.get("waiver_policy")
        if not isinstance(waiver_policy, dict):
            raise SmokeBootstrapError(
                "FULL smoke fixture must define a fixed waiver_policy"
            )
        smoke_h08b.write_fixture_policy(repo, waiver_policy)

    budget = smoke_budget.start(repo, run_id)
    smoke_segments.pin_qualification(
        repo,
        run_id,
        resolved_config,
        budget["started_at_utc"],
        source_fingerprint=source_fingerprint,
    )

    state = smoke_state.load(repo, run_id)
    context = dict(state.get("context_index") or {})
    context["contract_parity"] = parity
    context["budget_started_at_utc"] = budget["started_at_utc"]
    smoke_state.set_values(repo, run_id, {"context_index": context})

    gate = smoke_static.release_gate(
        resolved_config,
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
    parser.add_argument("--source", type=Path, required=True)
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
            source=args.source,
        )
        ok = bool(result["release_gate"]["ok"])
        print(json.dumps({"ok": ok, **result}))
        return 0 if ok else 3
    except (
        SmokeBootstrapError,
        smoke_h08b.H08bError,
        smoke_state.SmokeStateError,
        smoke_budget.BudgetError,
        smoke_static.StaticGateError,
        smoke_segments.SegmentError,
        OSError,
        ValueError,
        KeyError,
    ) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
