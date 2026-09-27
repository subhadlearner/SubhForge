#!/usr/bin/env python3
"""Deterministic static parity checks for SubhForge smoke gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_budget
import smoke_state


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


REQUIRED_COMMANDS = (
    "grill", "prd", "architect", "project-init", "spec", "implement",
    "verify", "review", "fix", "diagnose", "waive", "adversarial-check",
)


def release_gate(config: Path, repo: Path, run_id: str) -> dict[str, object]:
    """Run Phase 0 once and persist its evidence without shell-built JSON."""
    config, repo = config.resolve(), repo.resolve()
    state = smoke_state.load(repo, run_id)
    if state["state"] != "IN_PROGRESS" or state["current_stage"] != "static-release-gate":
        raise StaticGateError("Static release gate is not the current in-progress stage")
    if "static-release-gate" in state["completed_scenarios"]:
        raise StaticGateError("Static release gate is already complete")

    checks: dict[str, bool] = {}

    def read(key: str, path: Path) -> str:
        checks[key] = path.is_file()
        return path.read_text(encoding="utf-8") if checks[key] else ""

    for name in REQUIRED_COMMANDS:
        read(f"command:{name}", config / "commands" / f"{name}.md")
    worker = read("agent:planning-worker", config / "agents/planning-worker.md")
    orchestrator = read("agent:smoke-orchestrator", config / "agents/smoke-orchestrator.md")
    executor = read("agent:smoke-executor", config / "agents/smoke-executor.md")
    policy = read("policy:global", config / "AGENTS.md")
    architecture = read("policy:architecture", config / "commands/architect.md")
    contract = read("contract:installed", config / "contracts/implementation-state-evidence-v1.md")
    project_contract = read("contract:project", repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md")

    checks["planning:modes"] = all(f"`{mode}`" in worker for mode in
                                    ("AUTHOR", "CONTINUE", "RECONCILE_ONLY"))
    checks["planning:missing-mode"] = "WORKER_MODE_REQUIRED" in worker
    checks["routing:default"] = all(term in orchestrator for term in
        ("planning-worker", "smoke-executor", "pre-reviewer", "code-reviewer",
         "GPT-5.6 Sol", "DeepSeek")) and (
        "model: openai/gpt-5.6-luna" in orchestrator and
        "model: deepseek/deepseek-flash" in executor and
        all(term in policy for term in ("GPT-5.6 Sol", "GPT-5.6 Luna", "DeepSeek Flash")))
    checks["routing:claude-optional"] = ("explicit approval" in orchestrator and
        "not part of the default smoke run" in orchestrator and
        "do **not** use Claude" in policy)
    checks["policy:cost"] = all(term in policy.lower()
        for term in ("fixed monthly cost", "variable cost", "storage cost",
                     "network/data-transfer cost", "observability cost", "scaling behavior",
                     "operational burden")) and all(term in architecture.lower()
        for term in ("fixed recurring cost", "usage-based cost", "operational burden",
                     "cost drivers", "cost risks", "irreversible"))
    checks["contract:parity"] = bool(contract) and contract == project_contract
    checks["contract:terms"] = all(term in contract for term in (
        "canonical implementation-state manifest", "repository-relative path",
        "Git mode/type", "blob", "MATCH", "MISMATCH", "UNRECONSTRUCTABLE",
        "Workflow Evidence Exclusion Set", "Git-ignored", "Verification Environment Boundary",
        "Waiver Binding", "Fail-Closed Rule"))

    budget = smoke_budget.check(repo, run_id)
    passed = all(checks.values()) and budget["result"] == "WITHIN_BUDGET"
    failures = [name for name, ok in checks.items() if not ok]
    if budget["result"] != "WITHIN_BUDGET":
        failures.append("budget:30-minutes")
    metric = {
        "stage": "static-release-gate", "model": "deterministic",
        "elapsed_seconds": budget["elapsed_seconds"], "context_paths": [],
        "discovery_policy": "EXACT_ONLY", "result": "PASS" if passed else "FAIL",
    }
    completed = list(state["completed_scenarios"])
    if passed:
        completed.append("static-release-gate")
    profiles = json.loads((config / "smoke/profiles.json").read_text(encoding="utf-8"))
    required = profiles["profiles"][state["profile"]]["required_scenarios"]
    smoke_state.set_values(repo, run_id, {
        "completed_scenarios": completed,
        "pending_scenarios": [item for item in required if item not in completed],
        "current_stage": "grill" if passed and state["profile"] == "FULL" else
                         ("project-init" if passed else "static-release-gate"),
        "state": "IN_PROGRESS" if passed else "BLOCKED",
        "blocker": None if passed else {"code": "STATIC_RELEASE_GATE_FAILED", "checks": failures},
        "stage_metrics": {**state["stage_metrics"], "static-release-gate": metric},
    })
    return {"ok": passed, "checks": checks, "failures": failures,
            "stage_metric": metric, "state_path": str(smoke_state.state_path(repo, run_id))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)

    parity = sub.add_parser("contract-parity")
    parity.add_argument("--required", action="append", type=Path, default=[])
    parity.add_argument("--optional", action="append", type=Path, default=[])

    gate = sub.add_parser("release-gate")
    gate.add_argument("--config", type=Path, required=True)
    gate.add_argument("--repo", type=Path, required=True)
    gate.add_argument("--run-id", required=True)

    args = parser.parse_args()
    try:
        if args.action == "contract-parity":
            result = contract_parity(args.required, args.optional)
            print(json.dumps({"ok": bool(result["contract_equal"]), **result}))
            return 0 if result["contract_equal"] else 3
        if args.action == "release-gate":
            result = release_gate(args.config, args.repo, args.run_id)
            print(json.dumps(result))
            return 0 if result["ok"] else 3
        raise StaticGateError("Unsupported static gate action")
    except (StaticGateError, smoke_state.SmokeStateError, smoke_budget.BudgetError,
            OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
