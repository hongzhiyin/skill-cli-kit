# ARCHITECTURE - skill-cli-kit

> Source of truth for current structure.

## 1. Layer View

```text
User / Agent
  -> skill-cli-kit skill
      -> skillcli CLI
          -> scaffold files
          -> audit report
          -> installed skill wrappers

Generated project
  -> skill/SKILL.md
  -> src/<package>/cli.py
  -> scripts/install_cli.sh / sync_skill.sh / check_install.sh / update_cli.sh
```

## 2. Module Table

| Module | Path | Responsibility | Does not depend on |
|---|---|---|---|
| CLI package | `src/skill_cli_kit/` | Argument parsing, scaffold rendering, audit, status, doctor, skill sync | external packages |
| Skill source | `skill/SKILL.md` | Agent workflow for CLI-ifying reusable behavior | local install paths |
| Installed wrapper | `<skill-target>/bin/skillcli` | Cross-project entrypoint back to this source checkout | shell PATH |
| References | `skill/references/` | Optional pattern notes loaded only when improving the toolkit | CLI execution |
| Scripts | `scripts/` | Source-checkout install/sync/check/update plus native release packaging/install | package index |
| Tests | `tests/` | Scaffold and audit behavior checks | external services |
| Docs | `docs/` | Source-of-truth project intent | generated audit output |

## 2.1 Source Checkout

The canonical editable checkout for this toolkit is:

```text
/Users/chihoyo/Project/skill-cli-kit
```

Older or temporary copies under umbrella folders such as
`/Users/chihoyo/Project/Idea/skill-cli-kit` are migration sources only. After a
move, local wrappers, global symlinks, and installed skill-local `bin/skillcli`
wrappers must be regenerated from the canonical checkout.

## 3. Data Flow

### 3.1 Init

```text
skillcli init <project>
  -> normalize skill/CLI/package/env names
  -> render scaffold templates
  -> create scripts, skill, source package, tests, and docs
  -> create docs/_generated/<cli>/.gitkeep
```

### 3.2 Audit

```text
skillcli audit <project>
  -> read pyproject script entry
  -> read skill frontmatter, metadata, and CLI instructions
  -> inspect scripts, tests, docs, references, wrappers, and update lifecycle
  -> emit categorized findings and optional docs/_generated/skillcli/audit.json
```

### 3.3 Sync

```text
skillcli sync-skill
  -> resolve source skill directory
  -> copy to Codex / Cursor / shared agents targets
  -> write .skillcli-skill-source marker
  -> write each copied target's bin/skillcli wrapper
  -> link Claude target to shared agents target
```

### 3.4 Update Project

```text
skillcli update <project>
  -> optionally git pull --ff-only
  -> run scripts/install_cli.sh
  -> run unittest if tests/ exists
  -> run scripts/check_install.sh before sync
  -> run scripts/sync_skill.sh with caller-provided sync args
  -> run scripts/check_install.sh after sync
  -> emit JSON summary when --json is passed
```

### 3.5 Native Release Install

```text
scripts/package_release.sh
  -> dist/releases/skillcli-<version>.tar.gz
  -> dist/releases/skillcli-<version>.tar.gz.sha256
  -> dist/releases/manifest.json
  -> dist/releases/install_remote.sh / install_remote.ps1

scripts/install_remote.sh
  -> download manifest and artifact from GitHub Release or file:// base
  -> verify SHA256
  -> install release under ~/.local/share/skillcli/releases/<version>
  -> update ~/.local/share/skillcli/current
  -> write ~/.local/bin/skillcli launcher
  -> run skillcli doctor and optionally sync skill targets

skillcli native-update
  -> delegate to scripts/install_remote.sh from the current release/source root
```

## 4. Data Model

### 4.1 Finding

```python
@dataclass
class Finding:
    level: str
    message: str
    path: str | None = None
    category: str = "general"
    recommendation: str | None = None
```

### 4.2 ProjectMeta

```python
@dataclass
class ProjectMeta:
    project: Path
    skill_name: str | None
    cli_name: str | None
    package_name: str | None
    script_target: str | None
    source_env: str | None
```

## 5. Configuration

| Field / Env | Default | Meaning | Required |
|---|---|---|---|
| `SKILLCLI_PROJECT_DIR` | auto-detected | Source checkout for installed wrappers | no |
| `SKILLCLI_VENV_DIR` | `.venv` | Local wrapper directory used by install script | no |
| `CODEX_HOME` | `~/.codex` | Codex skill target root | no |
| `PYTHONPATH` | project `src` prepended during tests | Lets source-checkout tests import the package | no |
| `SKILLCLI_INSTALL_ROOT` | `~/.local/share/skillcli` | Native release install root | no |
| `SKILLCLI_BIN_DIR` | `~/.local/bin` | Native launcher directory | no |
| `SKILLCLI_RELEASE_BASE_URL` | GitHub latest release URL | Override release asset base for testing/private installs | no |

## 6. Process Model

- Entry: native `skillcli` launcher, source `.venv/bin/skillcli`, or installed
  skill-local `bin/skillcli`.
- Shutdown: commands exit after a single operation.
- Background work: none.
- Network: none.

## 7. Inspiration Snapshot

Current implementation borrows from:

- Python `argparse` subcommands and PyPA `console_scripts` entrypoints for a
  standard stdlib command surface.
- LarkCLI's agent-native split: shared CLI execution, domain skills, required
  bin metadata, shortcut commands, structured output, doctor/update flows, and
  explicit safe write controls.
- Modern CLI output practice: JSON for machine handoff; human output kept
  readable but not required for agents.

## 8. Known Constraints

- Audit checks are structural, not semantic.
- Generated scaffold commands are placeholders until a domain project fills them.
- Moving the source checkout requires rerunning sync to refresh installed wrappers.
- `skillcli update --pull` uses `git pull --ff-only`; it does not resolve merge
  conflicts or choose update branches.
- `skillcli native-update` is intentionally separate from `skillcli update
  <project>` because the latter updates arbitrary source checkouts.
- Review recommendations are heuristic; they indicate likely optimization work
  rather than a guarantee that the project is wrong.
