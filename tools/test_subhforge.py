import tempfile
import unittest
from pathlib import Path
import sys

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
            ok, detail = subhforge._same_tree(self.root / "forge", config)
            self.assertTrue(ok, detail)

            (config / "local-change.txt").write_text("changed", encoding="utf-8")
            backup = subhforge.install_config(config, self.root)
            self.assertIsNotNone(backup)
            self.assertTrue((backup / "local-change.txt").is_file())
            ok, detail = subhforge._same_tree(self.root / "forge", config)
            self.assertTrue(ok, detail)

    def test_init_is_exact_template_copy(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "sample"
            subhforge.init_project(project, self.root, git_init=False)
            ok, detail = subhforge._same_tree(self.root / "template", project)
            self.assertTrue(ok, detail)

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
