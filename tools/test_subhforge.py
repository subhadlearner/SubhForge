import tempfile
import unittest
from pathlib import Path
import sys
import subprocess
import contextlib
import io

sys.path.insert(0, str(Path(__file__).resolve().parent))
import subhforge


class SubhForgeBootstrapTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]

    def test_source_layout_is_complete(self):
        forge, template = subhforge._assert_source_layout(self.root)
        self.assertTrue((forge / "AGENTS.md").is_file())
        self.assertTrue((template / "AGENTS.md").is_file())

    def test_install_is_exact_copy_and_creates_backup(self):
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "kilo"
            backup = subhforge.install_config(config, self.root)
            self.assertIsNone(backup)
            manifest_path = config / ".subhforge-install.json"
            self.assertTrue(manifest_path.is_file())
            import json
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(str(self.root.resolve()), manifest["source_checkout_path"])
            with subhforge._committed_forge(self.root, manifest["source_commit"]) as committed:
                ok, detail = subhforge._same_tree(
                    committed, config, ignore=(".subhforge-install.json",))
            self.assertTrue(ok, detail)

            (config / "local-change.txt").write_text("changed", encoding="utf-8")
            backup = subhforge.install_config(config, self.root)
            self.assertIsNotNone(backup)
            self.assertTrue((backup / "local-change.txt").is_file())
            with subhforge._committed_forge(self.root, manifest["source_commit"]) as committed:
                ok, detail = subhforge._same_tree(
                    committed, config, ignore=(".subhforge-install.json",))
            self.assertTrue(ok, detail)

    def test_install_records_and_copies_exact_commit_even_when_forge_is_dirty(self):
        with tempfile.TemporaryDirectory() as temp:
            source = Path(temp) / "source"
            subprocess.run(["git", "clone", "--local", str(self.root), str(source)],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            expected = (source / "forge/README.md").read_bytes()
            (source / "forge/README.md").write_text("dirty edit\n", encoding="utf-8")
            (source / "forge/untracked.txt").write_text("uncommitted\n", encoding="utf-8")
            config = Path(temp) / "config"

            subhforge.install_config(config, source)

            self.assertEqual(expected, (config / "README.md").read_bytes())
            self.assertFalse((config / "untracked.txt").exists())
            import json
            manifest = json.loads((config / ".subhforge-install.json").read_text(encoding="utf-8"))
            self.assertEqual(subhforge._source_commit(source), manifest["source_commit"])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                subhforge.doctor(config, root=source)
            self.assertIn("[PASS] Installed Kilo config - exact match", output.getvalue())

    def test_init_is_exact_template_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "sample"
            subhforge.init_project(project, self.root, git_init=False)
            ok, detail = subhforge._same_tree(self.root / "template", project)
            self.assertTrue(ok, detail)

    def test_init_with_git_creates_baseline_commit(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "sample"
            subhforge.init_project(project, self.root, git_init=True)
            head = subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=str(project),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(0, head.returncode, head.stderr)
            subject = subprocess.run(
                ["git", "log", "-1", "--format=%s"],
                cwd=str(project),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertEqual(
                "Initialize project from SubhForge template",
                subject.stdout.strip(),
            )

    def test_project_comparison_ignores_git_metadata(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "sample"
            subhforge.init_project(project, self.root, git_init=False)
            (project / ".git").mkdir()
            (project / ".git" / "HEAD").write_text("ref: refs/heads/main", encoding="utf-8")
            ok, detail = subhforge._same_tree(
                self.root / "template", project, ignore=(".git",)
            )
            self.assertTrue(ok, detail)

    def test_init_refuses_nonempty_directory_without_force(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "sample"
            project.mkdir()
            (project / "keep.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(RuntimeError):
                subhforge.init_project(project, self.root, git_init=False)


if __name__ == "__main__":
    unittest.main()
