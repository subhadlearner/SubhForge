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
import smoke_segments
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

    command_text = {
        name: read(f"command:{name}", config / "commands" / f"{name}.md")
        for name in REQUIRED_COMMANDS
    }
    grill = command_text["grill"]
    verify = command_text["verify"]
    waive = command_text["waive"]
    worker = read("agent:planning-worker", config / "agents/planning-worker.md")
    orchestrator = read("agent:smoke-orchestrator", config / "agents/smoke-orchestrator.md")
    router = read("agent:resume-router", config / "agents/resume-router.md")
    executor = read("agent:smoke-executor", config / "agents/smoke-executor.md")
    read("helper:smoke-handoff", config / "scripts/smoke_handoff.py")
    h08b = read("helper:smoke-h08b", config / "scripts/smoke_h08b.py")
    mechanics = read("helper:smoke-mechanics", config / "scripts/smoke_mechanics.py")
    resume = read("helper:smoke-resume", config / "scripts/smoke_resume.py")
    reroute = read("helper:smoke-reroute", config / "scripts/smoke_reroute.py")
    policy = read("policy:global", config / "AGENTS.md")
    architecture = read("policy:architecture", config / "commands/architect.md")
    contract = read("contract:installed", config / "contracts/implementation-state-evidence-v1.md")
    project_contract = read("contract:project", repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md")

    checks["h08b:helper"] = all(term in h08b for term in (
        "def seed_discovery(",
        "def score_discovery(",
        "def validate_refusal(",
        "H08B-REQUIRED-EVIDENCE.md",
        "docs/verification/waiver-refusals/",
    ))
    checks["h08b:grill-stable-decisions"] = all(term in grill for term in (
        "| Decision ID | Status | Decision / Value | Prerequisite Evidence |",
        "BLOCKED_ON_EVIDENCE",
        "preserve every already-settled decision ID",
        "DISCOVERY_BLOCKED",
    ))
    policy_pos = waive.find("## Stage 2 — Check Failure-Type Policy Eligibility")
    auth_pos = waive.find("## Stage 3 — Require Explicit Human Authorization")
    checks["h08b:verify-failure-type"] = all(term in verify for term in (
        "Failure Type taxonomy",
        "BEHAVIORAL_TEST",
        "DOCUMENTATION_QUALITY",
        "LINT_QUALITY",
        "Failure Summary",
    ))
    checks["h08b:waive-policy-before-auth"] = (
        policy_pos >= 0
        and auth_pos > policy_pos
        and "POLICY_INELIGIBLE" in waive
        and "AUTHORIZATION_MISSING" in waive
        and "docs/verification/waiver-refusals/" in waive
        and "authorization_requested" in waive
        and "authorization_receipt_present" in waive
        and "do **not** start or wait on a `WAIVER_AUTHORIZATION` gate" in waive
    )

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
    # Rooted smoke runs under Kilo --auto, which approves every non-denied
    # permission; paid Claude delegation must therefore be denied, not asked.
    checks["routing:claude-denied-autonomous"] = all(
        '"{}": deny'.format(name) in orchestrator
        for name in ("adversary-sonnet", "adversary-opus"))
    checks["routing:resume-router"] = (
        '"resume-router": allow' in orchestrator
        and "model: openai/gpt-5.6-luna" in router
        and "RESUME_STAGE:" in router
        and "task: deny" in router
        and "HANDOFF_PROBE_ONLY: true" in executor
        and "SMOKE_IMPLEMENT_HANDOFF_ACCEPTED" in executor
    )
    checks["routing:resume-router-no-leak"] = (
        router.count('"docs/verification/smoke/**": deny') >= 3
        and '"git status*": allow' not in router
        and all(term in router for term in (
            "read:",
            "glob:",
            "grep:",
            "smoke state, timing, mechanics, resume-probe, or checkpoint ledgers",
        ))
    )
    checks["resume:mechanics"] = all(term in resume for term in (
        "PROBE_EXPECTED",
        "prepared_snapshot_sha256",
        "record_handoff",
        "def status(",
        "attempt_count",
        '"NOT_SCORED"',
        "Scored resume probe is immutable and cannot be retried",
    ))
    checks["routing:upstream-reroute"] = (
        all(term in worker for term in (
            "UPSTREAM_ROUTE_PROBE_ONLY: true",
            "UPSTREAM_HANDOFF_PROBE_ONLY: true",
            "SMOKE_UPSTREAM_HANDOFF_ACCEPTED",
            "BLOCKED_STATUS:",
            "NEXT_COMMAND:",
        ))
        and all(term in executor for term in (
            "WORKFLOW: /fix",
            "UPSTREAM_ROUTE_PROBE_ONLY: true",
            "BLOCKED_STATUS: FIX_BLOCKED",
            "NEXT_COMMAND:",
        ))
        and all(term in orchestrator for term in (
            "scripts/smoke_reroute.py",
            "u01",
            "u08",
            "SMOKE_UPSTREAM_HANDOFF_ACCEPTED",
        ))
    )
    executor_smoke_deny = '"*docs/verification/smoke*": deny'
    executor_helper_deny = '"*smoke_reroute.py*": deny'
    checks["routing:upstream-reroute-no-leak"] = (
        worker.count('"docs/verification/smoke/**": deny') >= 3
        and worker.count('"**/smoke_reroute.py": deny') >= 3
        and "git diff *docs/verification/smoke*" in worker
        and "git log *docs/verification/smoke*" in worker
        and executor.count('"docs/verification/smoke/**": deny') >= 3
        and executor.count('"**/smoke_reroute.py": deny') >= 3
        and executor_smoke_deny in executor
        and executor_helper_deny in executor
        and executor.rfind(executor_smoke_deny) > executor.rfind('"git status*": allow')
        and executor.rfind(executor_helper_deny) > executor.rfind('"npm run build*": allow')
    )
    checks["reroute:mechanics"] = all(term in reroute for term in (
        "PROBE_PLAN",
        "prepared_snapshot_sha256",
        "regeneration_path",
        "record_handoff",
        "def status(",
        "attempt_count",
        '"NOT_SCORED"',
        "Scored reroute probe is immutable and cannot be retried",
    ))
    checks["verification:mutation-hook"] = (
        all(term in executor for term in (
            "VERIFICATION_MUTATION_ID",
            "fire-verification-mutation",
            "checkpoint_result=MISMATCH",
        ))
        and all(term in mechanics for term in (
            "VERIFICATION_MUTATION_PATH",
            "arm_verification_mutation",
            "fire_verification_mutation",
        ))
    )
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
        budget_scope = budget.get("segment_id") or state["profile"]
        failures.append("budget:{}:pinned-limit".format(budget_scope))
    metric = {
        "stage": "static-release-gate", "model": "deterministic",
        "elapsed_seconds": budget["elapsed_seconds"], "context_paths": [],
        "discovery_policy": "EXACT_ONLY", "result": "PASS" if passed else "FAIL",
    }
    completed = list(state["completed_scenarios"])
    if passed:
        completed.append("static-release-gate")
    pinned = smoke_segments.assert_config_intact(repo, run_id, config)
    required = pinned["required_scenarios"]
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
            smoke_segments.SegmentError, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 2


if __name__ == "__main__":
    sys.exit(main())
