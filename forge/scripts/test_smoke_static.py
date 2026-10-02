"""Tests for path-aware static smoke gates."""

import sys
import tempfile
import unittest
import shutil
import json
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import smoke_static
import smoke_budget
import smoke_segments
import smoke_state


class SmokeStaticTests(unittest.TestCase):
    def _gate_fixture(self, root):
        source = Path(__file__).resolve().parents[1]
        config = root / "config"
        for folder in ("commands", "agents", "contracts", "smoke"):
            shutil.copytree(source / folder, config / folder)
        (config / "scripts").mkdir()
        shutil.copy2(source / "scripts/smoke_handoff.py", config / "scripts/smoke_handoff.py")
        shutil.copy2(source / "scripts/smoke_h08b.py", config / "scripts/smoke_h08b.py")
        shutil.copy2(source / "scripts/smoke_mechanics.py", config / "scripts/smoke_mechanics.py")
        shutil.copy2(source / "scripts/smoke_resume.py", config / "scripts/smoke_resume.py")
        shutil.copy2(source / "scripts/smoke_reroute.py", config / "scripts/smoke_reroute.py")
        shutil.copy2(source / "scripts/smoke_segments.py", config / "scripts/smoke_segments.py")
        shutil.copy2(source / "AGENTS.md", config / "AGENTS.md")
        repo = root / "repo"
        evidence = repo / "docs/verification/smoke"
        evidence.mkdir(parents=True)
        project_contract = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
        project_contract.parent.mkdir(parents=True)
        shutil.copy2(config / "contracts/implementation-state-evidence-v1.md", project_contract)
        run_id = "SMOKE-FULL-test-20260927T000000Z-12345678"
        smoke_state.init(repo, run_id, "FULL", "full-minimal-api", "sha", "base")
        budget = smoke_budget.start(
            repo,
            run_id,
            now=dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=42),
        )
        smoke_segments.pin_qualification(
            repo,
            run_id,
            config,
            budget["started_at_utc"],
            source_fingerprint="a" * 64,
        )
        smoke_state.set_values(
            repo,
            run_id,
            {
                "context_index": {
                    "budget_started_at_utc": budget["started_at_utc"],
                    "contract_parity": {"contract_equal": True},
                }
            },
        )
        return config, repo, run_id

    def test_release_gate_persists_real_timing_and_scenarios(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertTrue(result["ok"], result["failures"])
            self.assertGreaterEqual(result["stage_metric"]["elapsed_seconds"], 42)
            state = smoke_state.load(repo, run_id)
            self.assertEqual(["static-release-gate"], state["completed_scenarios"])
            self.assertNotIn("static-release-gate", state["pending_scenarios"])
            self.assertEqual("grill", state["current_stage"])

    def test_release_gate_blocks_h08b_luna_hidden_scorer_access(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            agent = config / "agents/h08b-luna-probe.md"
            agent.write_text(
                agent.read_text(encoding="utf-8").replace(
                    '"**/smoke_h08b.py": deny',
                    '"**/smoke_h08b.py": allow',
                    1,
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("h08b:luna-probe-isolation", result["failures"])

    def test_release_gate_blocks_grill_decision_id_contract_drift(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            grill = config / "commands/grill.md"
            grill.write_text(
                grill.read_text(encoding="utf-8").replace(
                    "| Decision ID | Status | Decision / Value | Prerequisite Evidence |",
                    "| Decision | Status | Value | Evidence |",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("h08b:grill-stable-decisions", result["failures"])

    def test_release_gate_blocks_refusal_records_becoming_active_waivers(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            review = config / "commands/review.md"
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "never treat records under the sibling",
                    "consider records under the sibling",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("h08b:refusal-not-active-waiver", result["failures"])

    def test_release_gate_blocks_missing_project_init_waiver_policy_trace(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            project_init = config / "commands/project-init.md"
            project_init.write_text(
                project_init.read_text(encoding="utf-8").replace(
                    "Waiver Policy SHA-256:",
                    "Policy digest:",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn(
                "h08b:project-init-policy-propagation",
                result["failures"],
            )

    def test_release_gate_blocks_missing_verify_failure_type_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            verify = config / "commands/verify.md"
            verify.write_text(
                verify.read_text(encoding="utf-8").replace(
                    "Failure Type taxonomy",
                    "Failure classification",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("h08b:verify-failure-type", result["failures"])

    def test_release_gate_blocks_waive_policy_after_authorization(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            waive = config / "commands/waive.md"
            text = waive.read_text(encoding="utf-8")
            text = text.replace(
                "## Stage 2 — Check Failure-Type Policy Eligibility",
                "## Stage 4 — Check Failure-Type Policy Eligibility",
            )
            waive.write_text(text, encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("h08b:waive-policy-before-auth", result["failures"])

    def test_release_gate_blocks_missing_mode_without_false_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            worker = config / "agents/planning-worker.md"
            worker.write_text(worker.read_text(encoding="utf-8").replace("`RECONCILE_ONLY`", "reconcile-only"), encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("planning:modes", result["failures"])
            state = smoke_state.load(repo, run_id)
            self.assertEqual("BLOCKED", state["state"])
            self.assertEqual([], state["completed_scenarios"])

    def test_release_gate_blocks_contract_drift_and_expired_budget(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            project = repo / "docs/workflow/IMPLEMENTATION-STATE-EVIDENCE-V1.md"
            project.write_text("drift", encoding="utf-8")
            state = smoke_state.load(repo, run_id)
            context = dict(state["context_index"])
            runtime = dict(context["segment_runtime"])
            runtime["active_started_at_utc"] = (
                dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=81)
            ).isoformat()
            context["segment_runtime"] = runtime
            state["context_index"] = context
            smoke_state._validate_full_state(state, expected_run_id=run_id)
            smoke_state._save(smoke_state.state_path(repo, run_id), state)

            result = smoke_static.release_gate(config, repo, run_id)
            self.assertIn("contract:parity", result["failures"])
            self.assertIn("budget:S1:pinned-limit", result["failures"])

    def test_release_gate_blocks_missing_smoke_handoff_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            (config / "scripts/smoke_handoff.py").unlink()
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("helper:smoke-handoff", result["failures"])

    def test_release_gate_blocks_paid_claude_left_at_ask_under_autonomous_mode(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            orchestrator = config / "agents/smoke-orchestrator.md"
            orchestrator.write_text(orchestrator.read_text(encoding="utf-8").replace(
                '"adversary-opus": deny', '"adversary-opus": ask'), encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:claude-denied-autonomous", result["failures"])

    def test_release_gate_blocks_missing_verification_mutation_hook(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            executor = config / "agents/smoke-executor.md"
            executor.write_text(
                executor.read_text(encoding="utf-8").replace(
                    "fire-verification-mutation",
                    "missing-verification-mutation-hook",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("verification:mutation-hook", result["failures"])

    def test_release_gate_blocks_missing_smoke_mechanics_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            (config / "scripts/smoke_mechanics.py").unlink()
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("helper:smoke-mechanics", result["failures"])
            self.assertIn("verification:mutation-hook", result["failures"])

    def test_release_gate_blocks_missing_resume_router_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            router = config / "agents/resume-router.md"
            router.write_text(
                router.read_text(encoding="utf-8").replace(
                    "model: openai/gpt-5.6-luna",
                    "model: deepseek/deepseek-flash",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:resume-router", result["failures"])

    def test_release_gate_blocks_resume_router_smoke_ledger_read_access(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            router = config / "agents/resume-router.md"
            router.write_text(
                router.read_text(encoding="utf-8").replace(
                    '"docs/verification/smoke/**": deny',
                    '"docs/verification/smoke/**": allow',
                    1,
                ),
                encoding="utf-8",
            )

            result = smoke_static.release_gate(config, repo, run_id)

            self.assertFalse(result["ok"])
            self.assertIn("routing:resume-router-no-leak", result["failures"])

    def test_release_gate_blocks_resume_router_git_status_leak_surface(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            router = config / "agents/resume-router.md"
            router.write_text(
                router.read_text(encoding="utf-8").replace(
                    '    "git branch --show-current*": allow',
                    '    "git status*": allow\n    "git branch --show-current*": allow',
                ),
                encoding="utf-8",
            )

            result = smoke_static.release_gate(config, repo, run_id)

            self.assertFalse(result["ok"])
            self.assertIn("routing:resume-router-no-leak", result["failures"])

    def test_release_gate_blocks_missing_resume_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            (config / "scripts/smoke_resume.py").unlink()
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("helper:smoke-resume", result["failures"])
            self.assertIn("resume:mechanics", result["failures"])

    def test_release_gate_blocks_missing_resume_handoff_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            executor = config / "agents/smoke-executor.md"
            executor.write_text(
                executor.read_text(encoding="utf-8").replace(
                    "SMOKE_IMPLEMENT_HANDOFF_ACCEPTED",
                    "MISSING_HANDOFF_ACCEPTED_TOKEN",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:resume-router", result["failures"])

    def test_release_gate_blocks_missing_reroute_helper(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            (config / "scripts/smoke_reroute.py").unlink()
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("helper:smoke-reroute", result["failures"])
            self.assertIn("reroute:mechanics", result["failures"])

    def test_release_gate_blocks_missing_planning_reroute_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            worker = config / "agents/planning-worker.md"
            worker.write_text(
                worker.read_text(encoding="utf-8").replace(
                    "SMOKE_UPSTREAM_HANDOFF_ACCEPTED",
                    "MISSING_UPSTREAM_HANDOFF_TOKEN",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:upstream-reroute", result["failures"])

    def test_release_gate_blocks_missing_fix_reroute_contract(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            executor = config / "agents/smoke-executor.md"
            executor.write_text(
                executor.read_text(encoding="utf-8").replace(
                    "BLOCKED_STATUS: FIX_BLOCKED",
                    "MISSING_FIX_BLOCKED_ROUTE_TOKEN",
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:upstream-reroute", result["failures"])

    def test_release_gate_blocks_reroute_helper_answer_leak_access(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            worker = config / "agents/planning-worker.md"
            worker.write_text(
                worker.read_text(encoding="utf-8").replace(
                    '"**/smoke_reroute.py": deny',
                    '"**/smoke_reroute.py": allow',
                    1,
                ),
                encoding="utf-8",
            )
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:upstream-reroute-no-leak", result["failures"])

    def test_release_gate_blocks_executor_shell_deny_precedence_regression(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            executor = config / "agents/smoke-executor.md"
            content = executor.read_text(encoding="utf-8")
            content = content.replace(
                '    "*docs/verification/smoke*": deny\n',
                "",
                1,
            )
            content = content.replace(
                '    "git status*": allow\n',
                '    "*docs/verification/smoke*": deny\n    "git status*": allow\n',
                1,
            )
            executor.write_text(content, encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertFalse(result["ok"])
            self.assertIn("routing:upstream-reroute-no-leak", result["failures"])

    def test_release_gate_detects_broken_agent_model_route(self):
        with tempfile.TemporaryDirectory() as temp:
            config, repo, run_id = self._gate_fixture(Path(temp))
            executor = config / "agents/smoke-executor.md"
            executor.write_text(executor.read_text(encoding="utf-8").replace(
                "model: deepseek/deepseek-flash", "model: anthropic/claude-sonnet"), encoding="utf-8")
            result = smoke_static.release_gate(config, repo, run_id)
            self.assertIn("routing:default", result["failures"])

    def test_required_equal_optional_missing_does_not_fail_parity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.md"
            b = root / "b.md"
            missing = root / "optional.md"
            a.write_text("same\n", encoding="utf-8")
            b.write_text("same\n", encoding="utf-8")

            result = smoke_static.contract_parity([a, b], [missing])

            self.assertTrue(result["contract_equal"])
            self.assertEqual([str(missing.resolve())], result["missing_optional"])

    def test_required_mismatch_fails_parity(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.md"
            b = root / "b.md"
            a.write_text("one\n", encoding="utf-8")
            b.write_text("two\n", encoding="utf-8")

            result = smoke_static.contract_parity([a, b], [])

            self.assertFalse(result["contract_equal"])

    def test_missing_required_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            a = root / "a.md"
            a.write_text("same\n", encoding="utf-8")

            with self.assertRaises(smoke_static.StaticGateError):
                smoke_static.contract_parity([a, root / "missing.md"], [])


if __name__ == "__main__":
    unittest.main()
