"""Repository policy checks for Python helper test coverage."""

import subprocess
import unittest
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[1]

# Use only for a genuinely non-behavioral production-script change where updating
# the paired test would add no value. Every exemption requires a concrete reason.
CHANGED_WITHOUT_TEST_EXEMPTIONS: dict[str, str] = {}


def production_scripts() -> list[Path]:
    return sorted(
        path
        for path in SCRIPTS_DIR.glob("*.py")
        if not path.name.startswith("test_")
    )


def paired_test(script: Path) -> Path:
    return script.with_name(f"test_{script.name}")


def changed_paths_from_main() -> set[str]:
    try:
        subprocess.run(
            ["git", "rev-parse", "--verify", "main^{commit}"],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
    except subprocess.CalledProcessError as exc:
        raise unittest.SkipTest("local main ref is unavailable") from exc

    result = subprocess.run(
        ["git", "diff", "--name-only", "main...HEAD", "--", "forge/scripts"],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


class ScriptTestPolicyTests(unittest.TestCase):
    def test_every_production_script_has_dedicated_test_module(self):
        missing = [
            script.name
            for script in production_scripts()
            if not paired_test(script).is_file()
        ]
        self.assertEqual(
            [],
            missing,
            "Every forge/scripts production module must have test_<module>.py",
        )

    def test_exemptions_have_documented_reasons(self):
        bad = [
            path
            for path, reason in CHANGED_WITHOUT_TEST_EXEMPTIONS.items()
            if not path.startswith("forge/scripts/") or not reason.strip()
        ]
        self.assertEqual([], bad, "Every script-test exemption requires a concrete reason")

    def test_changed_production_scripts_update_their_paired_tests(self):
        changed = changed_paths_from_main()
        violations: list[str] = []

        for script in production_scripts():
            rel_script = script.relative_to(REPO_ROOT).as_posix()
            if rel_script not in changed:
                continue
            if rel_script in CHANGED_WITHOUT_TEST_EXEMPTIONS:
                continue

            rel_test = paired_test(script).relative_to(REPO_ROOT).as_posix()
            if rel_test not in changed:
                violations.append(f"{rel_script} -> expected changed {rel_test}")

        self.assertEqual(
            [],
            violations,
            "Production Python script changes must update the paired regression test in the same branch",
        )


if __name__ == "__main__":
    unittest.main()
