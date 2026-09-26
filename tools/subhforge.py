#!/usr/bin/env python3
"""SubhForge bootstrap CLI for Stable v0.1.

Keeps setup deliberately simple:
- install: synchronize the repository's forge/ directory into the global Kilo config.
- init: create a new project from template/.
- setup: install + init in one command.
- doctor: validate prerequisites and the installed/project layout.
"""

from __future__ import print_function

import argparse
import datetime as _dt
import filecmp
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable, Optional, Tuple


MIN_PYTHON = (3, 8)
MANAGED_REQUIRED = (
    "AGENTS.md",
    "kilo.jsonc",
    "agents",
    "commands",
    "contracts",
    "skills",
    "smoke",
)
TEMPLATE_REQUIRED = (
    "AGENTS.md",
    "README.md",
    ".gitignore",
    ".kilo",
    "docs",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_kilo_config_dir() -> Path:
    override = os.environ.get("KILO_CONFIG_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".config" / "kilo").resolve()


def _assert_source_layout(root: Path) -> Tuple[Path, Path]:
    forge = root / "forge"
    template = root / "template"
    missing = []
    for rel in MANAGED_REQUIRED:
        if not (forge / rel).exists():
            missing.append("forge/" + rel)
    for rel in TEMPLATE_REQUIRED:
        if not (template / rel).exists():
            missing.append("template/" + rel)
    if missing:
        raise RuntimeError(
            "SubhForge source layout is incomplete: " + ", ".join(sorted(missing))
        )
    return forge, template


def _unique_backup_path(dest: Path) -> Path:
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = dest.with_name(dest.name + ".backup-" + stamp)
    counter = 1
    while candidate.exists():
        candidate = dest.with_name(dest.name + ".backup-" + stamp + "-" + str(counter))
        counter += 1
    return candidate


def _copy_tree_exact(source: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(str(dest))
    shutil.copytree(str(source), str(dest))


def install_config(config_dir: Path, root: Optional[Path] = None) -> Optional[Path]:
    root = root or repo_root()
    forge, _ = _assert_source_layout(root)
    config_dir = config_dir.expanduser().resolve()
    config_dir.parent.mkdir(parents=True, exist_ok=True)

    backup = None
    if config_dir.exists():
        backup = _unique_backup_path(config_dir)
        shutil.copytree(str(config_dir), str(backup))

    _copy_tree_exact(forge, config_dir)
    return backup


def _directory_nonempty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


def init_project(
    project_dir: Path,
    root: Optional[Path] = None,
    force: bool = False,
    git_init: bool = True,
) -> None:
    root = root or repo_root()
    _, template = _assert_source_layout(root)
    project_dir = project_dir.expanduser().resolve()

    if _directory_nonempty(project_dir) and not force:
        raise RuntimeError(
            "Project directory is not empty: {}. Use --force only when replacing it is intentional."
            .format(project_dir)
        )

    if project_dir.exists() and force:
        shutil.rmtree(str(project_dir))

    project_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(str(template), str(project_dir))

    if git_init:
        git = shutil.which("git")
        if not git:
            raise RuntimeError("Git is required for project initialization but was not found on PATH.")
        proc = subprocess.run(
            [git, "init", "-b", "main"],
            cwd=str(project_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if proc.returncode != 0:
            # Older Git versions may not support -b.
            proc = subprocess.run(
                [git, "init"],
                cwd=str(project_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        if proc.returncode != 0:
            raise RuntimeError("git init failed: " + (proc.stderr or proc.stdout).strip())


def _same_tree(
    source: Path,
    dest: Path,
    ignore: Tuple[str, ...] = (),
) -> Tuple[bool, str]:
    if not source.exists():
        return False, "source missing: {}".format(source)
    if not dest.exists():
        return False, "destination missing: {}".format(dest)

    comparison = filecmp.dircmp(str(source), str(dest), ignore=list(ignore))
    if comparison.left_only:
        return False, "missing: " + ", ".join(comparison.left_only)
    if comparison.right_only:
        return False, "unexpected: " + ", ".join(comparison.right_only)
    if comparison.funny_files:
        return False, "unreadable: " + ", ".join(comparison.funny_files)

    _, mismatches, errors = filecmp.cmpfiles(
        str(source), str(dest), comparison.common_files, shallow=False
    )
    if mismatches:
        return False, "content mismatch: " + ", ".join(mismatches)
    if errors:
        return False, "comparison error: " + ", ".join(errors)

    for name in comparison.common_dirs:
        ok, detail = _same_tree(source / name, dest / name, ignore=ignore)
        if not ok:
            return False, name + "/" + detail
    return True, "exact match"


def doctor(
    config_dir: Path,
    project_dir: Optional[Path] = None,
    root: Optional[Path] = None,
) -> int:
    root = root or repo_root()
    checks = []

    checks.append((
        "Python >= {}.{}".format(*MIN_PYTHON),
        sys.version_info[:2] >= MIN_PYTHON,
        "{}.{}.{}".format(*sys.version_info[:3]),
    ))
    checks.append(("Git on PATH", shutil.which("git") is not None, shutil.which("git") or "not found"))
    checks.append(("Kilo CLI on PATH", shutil.which("kilo") is not None, shutil.which("kilo") or "not found"))

    try:
        forge, template = _assert_source_layout(root)
        checks.append(("SubhForge source layout", True, str(root)))
    except RuntimeError as exc:
        checks.append(("SubhForge source layout", False, str(exc)))
        forge = root / "forge"
        template = root / "template"

    exact_config, config_detail = _same_tree(forge, config_dir.expanduser().resolve())
    checks.append(("Installed Kilo config", exact_config, config_detail))

    if project_dir is not None:
        project_dir = project_dir.expanduser().resolve()
        exact_project, project_detail = _same_tree(
            template, project_dir, ignore=(".git",)
        )
        checks.append(("Project scaffold", exact_project, project_detail))

    failed = False
    for label, ok, detail in checks:
        marker = "PASS" if ok else "FAIL"
        print("[{}] {} - {}".format(marker, label, detail))
        failed = failed or not ok

    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="subhforge",
        description="Bootstrap and validate SubhForge Stable v0.1.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=default_kilo_config_dir(),
        help="Global Kilo config directory (default: %(default)s; env: KILO_CONFIG_DIR).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("install", help="Install/synchronize forge/ into the global Kilo config.")

    init = sub.add_parser("init", help="Create a new project from template/.")
    init.add_argument("project_dir", type=Path)
    init.add_argument("--force", action="store_true")
    init.add_argument("--no-git", action="store_true")

    setup = sub.add_parser("setup", help="Install SubhForge and initialize a new project.")
    setup.add_argument("project_dir", type=Path)
    setup.add_argument("--force", action="store_true")
    setup.add_argument("--no-git", action="store_true")

    doc = sub.add_parser("doctor", help="Validate prerequisites and installed/project layout.")
    doc.add_argument("--project", type=Path)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()

    try:
        if args.command == "install":
            backup = install_config(args.config_dir, root)
            print("Installed SubhForge Kilo config -> {}".format(args.config_dir))
            if backup:
                print("Previous config backup -> {}".format(backup))
            return 0

        if args.command == "init":
            init_project(args.project_dir, root, force=args.force, git_init=not args.no_git)
            print("Initialized project -> {}".format(args.project_dir.expanduser().resolve()))
            return 0

        if args.command == "setup":
            backup = install_config(args.config_dir, root)
            init_project(args.project_dir, root, force=args.force, git_init=not args.no_git)
            print("Installed SubhForge Kilo config -> {}".format(args.config_dir))
            if backup:
                print("Previous config backup -> {}".format(backup))
            print("Initialized project -> {}".format(args.project_dir.expanduser().resolve()))
            return doctor(args.config_dir, args.project_dir, root)

        if args.command == "doctor":
            return doctor(args.config_dir, args.project, root)

    except (OSError, RuntimeError) as exc:
        print("SUBHFORGE_ERROR: {}".format(exc), file=sys.stderr)
        return 2

    return 2


if __name__ == "__main__":
    sys.exit(main())
