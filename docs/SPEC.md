# SPEC - skill-cli-kit

> Source of truth for expected behaviour.

## 1. One-Sentence Goal

Provide a portable toolkit that helps agents turn reusable behavior into a
skill-backed, deterministic CLI project with install, sync, audit, and wrapper
contracts.

## 2. Decision Table

| ID | Decision | Choice | Notes |
|---|---|---|---|
| A | Boundary | Skill owns judgment; CLI owns deterministic scaffolding, audit, status, sync, and doctor | See D-001 |
| B | Runtime | Python 3.10+ stdlib-only CLI | See D-001 |
| C | Scaffold shape | `pyproject.toml`, `src/`, `skill/`, `scripts/`, `tests/`, and `docs/` | See D-002 |
| D | Distribution | Source checkout wrapper plus installed skill-local wrapper | See D-003 |
| E | Sync targets | Codex, Cursor, shared agents, and Claude symlink to shared agents | See D-003 |
| F | Audit strictness | Missing core files are errors; portability gaps are warnings | See D-002 |
| G | Agent-readable output | Status, doctor, and audit commands support JSON | See D-004 |
| H | Skill metadata | Generated skills declare required CLI bins and `cliHelp` | See D-004 |
| I | Update lifecycle | Source update is followed by install, test, check, sync, and verify | See D-005 |
| J | Existing project review | Audit reports categorize required gaps and optimization opportunities | See D-006 |
| K | Source checkout location | `skill-cli-kit` itself should live as a top-level `~/Project/skill-cli-kit` source checkout | See D-007 |
| L | Native release install | Released `skillcli` installs under `~/.local/share/skillcli` with a `~/.local/bin/skillcli` launcher | See D-008 |

## 3. Derived Rules

### 3.1 Skill + CLI Boundary

| Layer | Owns | Refuses |
|---|---|---|
| Skill | Triggering, workflow, fallback choice, safety, interpretation | deterministic file operations repeated across turns |
| CLI | Scaffolding, audit, status, sync, wrapper generation, machine-checkable output | deciding product policy or user intent |
| Scripts | Source-checkout install, sync, and check wrappers | long-lived behavior that belongs in the CLI |

### 3.2 Commands

| Command | Purpose | Side effects |
|---|---|---|
| `skillcli init <project>` | Create a portable skill + CLI source project | Writes scaffold files under project |
| `skillcli audit <project>` | Check skill/CLI portability structure and optimization opportunities | Optional `docs/_generated/skillcli/audit.json` |
| `skillcli status <project> [--json]` | Show discovered metadata and finding counts | No |
| `skillcli update <project>` | Run the standard post-source-update lifecycle | Runs project scripts and syncs installed skill |
| `skillcli native-update` | Update a native release install | Downloads and installs release assets |
| `skillcli uninstall` | Remove native release install and owned skill targets | Deletes only owned/generated paths after confirmation |
| `skillcli sync-skill` | Sync this skill to agent skill homes and generate `bin/skillcli` | Writes skill target dirs |
| `skillcli doctor [--json]` | Show source checkout and installed skill state | No |

### 3.3 Native Release Contract

Public release assets should include:

```text
skillcli-<version>.tar.gz
skillcli-<version>.tar.gz.sha256
manifest.json
install_remote.sh
install_remote.ps1
```

The Unix native installer downloads `manifest.json`, verifies the artifact
checksum, installs into `~/.local/share/skillcli/releases/<version>/`, updates
`~/.local/share/skillcli/current`, writes `~/.local/bin/skillcli`, runs
`skillcli doctor`, and syncs the skill unless explicitly skipped.

### 3.4 Generated Scaffold Contract

A generated project should include:

```text
pyproject.toml
src/<package>/cli.py
skill/SKILL.md
skill/agents/openai.yaml
scripts/install_cli.sh
scripts/sync_skill.sh
scripts/check_install.sh
scripts/update_cli.sh
tests/
docs/
```

Generated skills should include frontmatter metadata that advertises the CLI:

```yaml
metadata:
  requires:
    bins: ["<cli>"]
  cliHelp: "<cli> --help"
```

## 4. Default Handling

| Scenario | Default behaviour |
|---|---|
| `--name` omitted during init | Use the target directory name as the skill name |
| `--cli` omitted during init | Remove hyphens from the skill name |
| `--package` omitted during init | Replace skill name hyphens with underscores |
| Existing scaffold file | Skip unless `--force` is passed |
| Existing unmarked installed skill target | Refuse replacement unless `--force` is passed |
| Audit report requested | Write under `docs/_generated/skillcli/` |
| Agent needs current state | Prefer `status --json`, `doctor --json`, or `audit --json` |
| Source has just been updated | Run `skillcli update <project> --force`, or the project's `scripts/update_cli.sh --force` |
| User needs `skillcli` on a machine without the source checkout | Use the native installer from GitHub Releases |
| Native launcher exists but is not on `PATH` | Use `~/.local/bin/skillcli` directly |
| Git pull is requested | Use `skillcli update <project> --pull`; refuse dirty worktrees unless `--allow-dirty` is passed |
| Existing CLI skill project is reviewed | Treat missing package/script/skill as errors, portability/documentation/update gaps as warnings |
| `skill-cli-kit` source checkout is moved | Reinstall the local wrapper, refresh global/user-facing entrypoints, sync installed skills, then verify `doctor` and `audit` |

## 5. Module Contracts

### 5.1 CLI

```python
def main(argv: Iterable[str] | None = None) -> int:
    """Run a skillcli command and return a process exit code."""
```

Constraints:
- Input domain: project paths, skill names, CLI names, package names, sync targets.
- Output domain: scaffold files, console status, optional JSON audit report.
- Error categories: invalid names, missing core files, unsafe target replacement.
- Related invariants: #1, #2, #3, #4, #5.

### 5.2 Update Lifecycle

```text
optional git pull --ff-only
  -> scripts/install_cli.sh
  -> python3 -m unittest discover -s tests
  -> scripts/check_install.sh
  -> scripts/sync_skill.sh
  -> scripts/check_install.sh
```

The lifecycle must fail before sync if install, tests, or pre-sync checks fail,
unless the caller explicitly skips that stage.

### 5.3 Review Finding

```python
@dataclass
class Finding:
    level: str
    message: str
    path: str | None = None
    category: str = "general"
    recommendation: str | None = None
```

Constraints:
- Required structure findings use `error`.
- Optimization and portability opportunities use `warn`.
- Output must stay JSON-serializable for reports.

## 6. Non-Goals

- No package-index or network install requirement.
- No package-index install requirement; native release install may use network
  only when the user chooses remote release installation.
- No semantic judgment of whether a domain skill is well designed.
- No automatic migration of existing domain code into CLI commands.
- No hidden mutation outside the requested project or explicit sync targets.
- No long-term reliance on a scratch or umbrella project directory as the
  canonical source checkout for `skill-cli-kit`.

## 7. Invariants

1. **#1**: Generated or audited projects preserve the skill-as-judgment and CLI-as-determinism boundary.
2. **#2**: `skillcli` remains stdlib-only and runnable from a source checkout.
3. **#3**: Installed skill copies generated by sync include `bin/skillcli`.
4. **#4**: Sync never replaces an unmarked existing skill directory unless `--force` is passed.
5. **#5**: Generated audit reports live under `docs/_generated/skillcli/`.
6. **#6**: Agent-facing state commands must have structured JSON output.
7. **#7**: Generated skills declare their required CLI bin in metadata.
8. **#8**: Installed skills are updated only from the source checkout after local verification.
9. **#9**: Audit findings include enough category and recommendation context to guide optimization work.
10. **#10**: `skill-cli-kit`'s canonical editable source checkout is
    `~/Project/skill-cli-kit`; installed wrappers may point there, but installed
    skill directories must not become source-of-truth.
11. **#11**: Native release installers must verify artifact checksums before
    switching the `current` launcher target.
