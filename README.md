# SubhForge

**Subhadeep's personal AI-assisted engineering workflow.**

SubhForge combines the reusable Kilo workflow/configuration layer with the clean product-repository scaffold that previously lived in two separate repositories.

## Repository layout

```text
SubhForge/
├── forge/       # global Kilo config: AGENTS, agents, commands, contracts, skills, smoke
├── template/    # clean product-repository scaffold
├── tools/       # bootstrap and validation tooling
├── design/      # design specifications/history
├── poc/         # design-validation POCs on development branches
└── subhforge.ps1
```

## Branch model

- `main` is the integration branch for the Stable v0.1 candidate.
- `feature/v0.2.0` is the active v0.2 development branch.
- Stable releases are tagged only after their smoke/dogfood gates pass.

The v0.1 baseline is the structural consolidation of `kilo-configuration@stable_v_0.1.0` and `production-ai-project@main`. Existing workflow behavior is preserved before v0.2 behavior is introduced.

## Prerequisites

- Python 3.14+
- Git
- Kilo CLI available on `PATH`
- model/provider credentials configured outside Git

On Windows, `subhforge.ps1` tries a working `py -3`, then `python`, then `python3`. A stale `py` launcher does not block the other choices. By default the global Kilo configuration is `%USERPROFILE%\.config\kilo`. Override it with `--config-dir` or `KILO_CONFIG_DIR`.

## First-time setup

Clone SubhForge and use the stable branch:

```powershell
git clone https://github.com/subhadlearner/SubhForge.git
cd SubhForge
git switch main
```

### Validate the machine

```powershell
.\subhforge.ps1 doctor
```

or:

```powershell
python tools/subhforge.py doctor
```

### Install the global Kilo configuration

```powershell
.\subhforge.ps1 install
```

This synchronizes `forge/` into `%USERPROFILE%\.config\kilo`. If a configuration already exists, SubhForge first creates a timestamped sibling backup such as `kilo.backup-20260926-221500`.

### Create a new product project

```powershell
.\subhforge.ps1 init C:\Code\MFBeacon
```

This copies the complete `template/` scaffold into the target directory and runs `git init`. It does not run discovery, architecture, or `/project-init`; those remain normal workflow responsibilities.

SubhForge refuses to overwrite a non-empty target directory unless `--force` is explicitly supplied. Use `--no-git` if Git initialization is intentionally unwanted.

### One-command setup

For a new machine/project, the normal path is:

```powershell
.\subhforge.ps1 setup C:\Code\MFBeacon
```

`setup` performs:

```text
validate SubhForge source layout
        ↓
backup existing global Kilo config (if present)
        ↓
install forge/ as the global Kilo config
        ↓
copy template/ into the new product repository
        ↓
git init
        ↓
run SubhForge doctor
```

A non-zero result means setup/validation failed and should be corrected before trusting product workflow commands.

### Validate an installation and generated project

```powershell
.\subhforge.ps1 doctor --project C:\Code\MFBeacon
```

`doctor` checks Python, Git, the Kilo CLI, the SubhForge source layout, exact global-config equivalence with `forge/`, and optionally exact scaffold equivalence with `template/`. The generated project's `.git/` directory is ignored for the scaffold comparison.

## Stable v0.1 equivalence test

Before v0.2 implementation, `main` must prove that consolidation did not change Stable v0.1 behavior.

Install the exact candidate branch and validate the installation:

```powershell
git switch <release-candidate-branch>
.\subhforge.ps1 install
.\subhforge.ps1 doctor
```

Run smoke in Kilo with SubhForge installed. The harness creates its own disposable fixture from `template/`:

```text
/smoke FAST DEFAULT
/smoke FULL DEFAULT
```

The canonical Stable-v0.1 smoke definition is `forge/smoke/STABLE-V0.1-SMOKE-TEST-PLAN.md`.

## Bootstrap CLI reference

PowerShell wrapper:

```powershell
.\subhforge.ps1 install
.\subhforge.ps1 init C:\Code\VidyaBeacon
.\subhforge.ps1 setup C:\Code\VidyaBeacon
.\subhforge.ps1 doctor --project C:\Code\VidyaBeacon
```

Direct Python usage:

```powershell
python tools/subhforge.py install
python tools/subhforge.py init C:\Code\VidyaBeacon
python tools/subhforge.py setup C:\Code\VidyaBeacon
python tools/subhforge.py doctor --project C:\Code\VidyaBeacon
```

Custom global config location:

```powershell
python tools/subhforge.py --config-dir C:\Temp\kilo-config setup C:\Temp\my-project
```

Bootstrap unit tests:

```powershell
python -m unittest tools/test_subhforge.py -v
```

## Stable v0.1 product workflow

```text
/grill (optional)
  ↓
/prd
  ↓
/architect
  ↓
/project-init
  ↓
/spec
  ↓
/implement
  ↓
/verify
  ↓
/review
```

Repair and exception paths remain available through `/fix`, `/diagnose`, `/waive`, and `/adversarial-check`.

The global workflow policy is `forge/AGENTS.md`; project-side workflow documentation is under `template/docs/workflow/`.

## Scope

SubhForge is deliberately not a general-purpose developer platform. It exists to make Subhadeep's own software projects safer, clearer, cheaper, and easier to resume with AI assistance.
