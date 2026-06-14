---
name: skill-cli-kit
description: Turn a reusable agent behavior or skill into a portable skill-backed CLI project. Use when the user wants to CLI-ify a skill, scaffold a skill plus deterministic helper CLI, audit skill/CLI portability, sync installed skill wrappers, or avoid agents losing tool paths.
metadata:
  requires:
    bins: ["skillcli"]
  cliHelp: "skillcli --help"
---

# Skill CLI Kit

## Goal

Convert reusable agent behavior into a portable source project with:

- `skill/SKILL.md` as the decision and workflow layer
- `src/<package>/cli.py` as the deterministic helper layer
- `scripts/install_cli.sh`, `scripts/sync_skill.sh`, `scripts/check_install.sh`, and `scripts/update_cli.sh`
- installed skill-local `bin/<cli>` wrappers so agents can run the CLI from other projects
- optional docs under `docs/` for SPEC / ARCHITECTURE / ROADMAP / DECISIONS

The durable boundary is: CLI owns deterministic operations; skill owns judgment,
fallback selection, and interpretation.

## CLI

Resolve helper commands in this order:

1. Run `skillcli <command>` if it is on `PATH`.
2. On Unix-like systems, if the native release launcher exists but `skillcli` is
   not on `PATH`, run `~/.local/bin/skillcli <command>`.
3. If this installed skill path is visible, run `bin/skillcli <command>`.
4. If `SKILLCLI_PROJECT_DIR` points to the source checkout, run:

```bash
SKILLCLI_PROJECT_DIR="$SKILLCLI_PROJECT_DIR" PYTHONPATH="$SKILLCLI_PROJECT_DIR/src" \
  python3 -m skill_cli_kit.cli <command>
```

If none of those work, ask the user to run the native installer or install/sync
from the source checkout.

```bash
./scripts/install_cli.sh
./scripts/sync_skill.sh --targets codex,agents --force
```

For native release installs:

```bash
curl -fsSL https://github.com/hongzhiyin/skill-cli-kit/releases/latest/download/install_remote.sh | sh
```

## Commands

```bash
skillcli init /path/to/project --name my-skill --cli mytool
skillcli audit /path/to/project --write-report
skillcli status /path/to/project --json
skillcli update
skillcli update /path/to/project --force --json
skillcli sync-skill --targets codex,cursor,agents,claude --force
skillcli uninstall --dry-run
skillcli doctor --json
```

## Workflow A - CLI-ify A Reusable Behavior

Use when the user has a skill, repeated agent workflow, or fragile helper
sequence that should become portable.

1. Identify the repeated deterministic work: parsing, filesystem writes,
   numbering, export, conversion, audit, install, or sync.
2. Identify the judgment work that must stay in the skill: when to use the
   behavior, fallback choice, safety rules, ambiguity handling, and final
   interpretation.
3. Choose a short CLI name and a source env var prefix.
4. Run `skillcli init` to create the source project.
5. Replace placeholder CLI commands with the real deterministic commands.
6. Update `skill/SKILL.md` so agents resolve the CLI by PATH, skill-local
   `bin/<cli>`, then `<PREFIX>_PROJECT_DIR`, and declare `metadata.requires.bins`.
7. Make status/check commands produce structured JSON for agent consumption.
8. Run tests and `skillcli audit`.
9. Sync the skill so installed copies include `bin/<cli>`.

## Workflow B - Update A Source Checkout

Use after updating a project's source code by editing files, switching branches,
or pulling from Git. Do not edit installed skill directories directly.

```bash
skillcli update ~/Project/<tool> --force
```

If the project itself has the generated helper script, this is equivalent:

```bash
~/Project/<tool>/scripts/update_cli.sh --force
```

Default lifecycle:

1. install or refresh the source-checkout CLI wrapper;
2. run `python3 -m unittest discover -s tests` when `tests/` exists;
3. run `scripts/check_install.sh` before sync;
4. run `scripts/sync_skill.sh`;
5. run `scripts/check_install.sh` again.

When the source should be pulled from Git first:

```bash
skillcli update ~/Project/<tool> --pull --force
```

`--pull` uses `git pull --ff-only` and refuses a dirty worktree unless
`--allow-dirty` is passed.

## Workflow B2 - Update skillcli Itself

Use this when the installed `skillcli` release should be refreshed from GitHub
Releases. This is different from updating a generated project's source
checkout.

```bash
skillcli update
```

To skip refreshing installed skill copies:

```bash
skillcli update --no-sync-skill
```

## Workflow C - Audit Existing Skill + CLI Projects

Use this before copying a skill into agent homes, after moving a source
checkout, when a new project does not yet have an update script, or when the
user asks whether an existing CLI-backed skill conforms to the pattern.

```bash
skillcli audit /path/to/project --write-report
skillcli audit /path/to/project --json
```

Audit checks are structural. They verify the project has a script entrypoint,
CLI module, skill frontmatter, CLI instructions, install/sync/check scripts, and
skill-local wrapper generation. They also warn when the skill does not declare
its required CLI bin and help command. They do not judge whether the domain
behavior is good.

Findings include:

- `level`: `error` for required missing structure, `warn` for optimization work.
- `category`: `cli`, `skill`, `metadata`, `install`, `sync`, `update`,
  `installed`, `docs`, `tests`, `handoff`, or similar.
- `recommendation`: the next concrete improvement to consider.

For installed copies that already exist, audit compares installed `SKILL.md`
with the source `skill/SKILL.md` and checks installed `bin/<cli>` wrappers.

## Project Contract

A portable skill + CLI project should include:

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

Generated or installed skill copies should not become the editable source of
truth. Edit the source checkout, then update/sync.

## Anti-Patterns

- A skill that tells agents to remember a hard-coded source path but provides no
  wrapper.
- A CLI that decides user-facing policy instead of performing deterministic work.
- Installed skill copies that preserve old scripts and drift from the source
  project.
- Network or package-index installation as the only way to run the local CLI.
- Pulling or syncing over a dirty source checkout without explicitly checking
  what changed.
- Treating every audit warning as mandatory; warnings identify optimization
  candidates, not necessarily broken behavior.
