from __future__ import annotations

import argparse
import hashlib
import json
import keyword
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from . import __version__


SKILL_NAME = "skill-cli-kit"
CLI_NAME = "skillcli"
PACKAGE_NAME = "skill_cli_kit"
SOURCE_ENV = "SKILLCLI_PROJECT_DIR"
VENV_ENV = "SKILLCLI_VENV_DIR"
GENERATED_SUBDIR = "_generated/skillcli"
TARGETS = ("codex", "cursor", "agents", "claude")
MARKER_NAME = ".skillcli-skill-source"
DEFAULT_RELEASE_REPO = "hongzhiyin/skill-cli-kit"


@dataclass
class Finding:
    level: str
    message: str
    path: str | None = None
    category: str = "general"
    recommendation: str | None = None

    def as_dict(self) -> dict[str, str | None]:
        return {
            "level": self.level,
            "category": self.category,
            "message": self.message,
            "path": self.path,
            "recommendation": self.recommendation,
        }


@dataclass
class ProjectMeta:
    project: Path
    skill_name: str | None
    cli_name: str | None
    package_name: str | None
    script_target: str | None
    source_env: str | None


@dataclass(frozen=True)
class UninstallAction:
    label: str
    path: Path
    action: str
    reason: str


def project_root_from_module() -> Path:
    return Path(__file__).resolve().parents[2]


def target_path_for(target: str, skill_name: str = SKILL_NAME) -> Path:
    if target == "codex":
        return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills" / skill_name
    if target == "cursor":
        return Path.home() / ".cursor" / "skills" / skill_name
    if target == "agents":
        return Path.home() / ".agents" / "skills" / skill_name
    if target == "claude":
        return Path.home() / ".claude" / "skills" / skill_name
    raise ValueError(f"Unknown target: {target}")


def read_marker_source(path: Path) -> Path | None:
    marker = path / MARKER_NAME
    if not marker.exists():
        return None
    raw = marker.read_text(encoding="utf-8").strip()
    return Path(raw).expanduser().resolve() if raw else None


def find_source_root() -> Path:
    env = os.environ.get(SOURCE_ENV)
    if env:
        return Path(env).expanduser().resolve()

    module_root = project_root_from_module()
    if (module_root / "skill" / "SKILL.md").exists():
        return module_root

    for candidate in (
        Path.home() / "Project" / "Idea" / SKILL_NAME,
        Path.home() / "Project" / SKILL_NAME,
        target_path_for("agents"),
        target_path_for("codex"),
        target_path_for("cursor"),
    ):
        marked = read_marker_source(candidate)
        if marked:
            return marked
        if (candidate / "skill" / "SKILL.md").exists():
            return candidate
        if (candidate / "SKILL.md").exists():
            return candidate

    return module_root


def skill_source_dir() -> Path:
    root = find_source_root()
    if (root / "skill" / "SKILL.md").exists():
        return root / "skill"
    return root


def normalize_skill_name(raw: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", raw.strip().lower()).strip("-")
    if not value or not re.fullmatch(r"[a-z0-9][a-z0-9-]*[a-z0-9]?", value):
        raise SystemExit(f"Invalid skill name: {raw!r}")
    return value


def derive_cli_name(skill_name: str, explicit: str | None) -> str:
    value = explicit.strip() if explicit else re.sub(r"[^a-z0-9]", "", skill_name)
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", value):
        raise SystemExit(f"Invalid CLI command name: {value!r}")
    return value


def derive_package_name(skill_name: str, explicit: str | None) -> str:
    value = explicit.strip() if explicit else skill_name.replace("-", "_")
    if not value.isidentifier() or keyword.iskeyword(value):
        raise SystemExit(f"Invalid Python package name: {value!r}")
    return value


def env_prefix_for(cli_name: str, explicit: str | None) -> str:
    raw = explicit or cli_name
    value = re.sub(r"[^A-Za-z0-9]+", "_", raw).strip("_").upper()
    if not value:
        raise SystemExit("Could not derive environment variable prefix")
    return value


def title_from_skill_name(skill_name: str) -> str:
    return " ".join(part.capitalize() for part in skill_name.split("-"))


def render(text: str, ctx: dict[str, str]) -> str:
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def scaffold_context(args: argparse.Namespace, project: Path) -> dict[str, str]:
    skill_name = normalize_skill_name(args.name or project.name)
    cli_name = derive_cli_name(skill_name, args.cli)
    package_name = derive_package_name(skill_name, args.package)
    env_prefix = env_prefix_for(cli_name, args.env_prefix)
    description = args.description or f"Portable skill and CLI project for {skill_name}."
    display_name = args.display_name or title_from_skill_name(skill_name)
    short_description = args.short_description or f"Build and run {skill_name} helper commands"
    return {
        "skill_name": skill_name,
        "cli_name": cli_name,
        "package_name": package_name,
        "package_path": package_name.replace(".", "/"),
        "source_env": f"{env_prefix}_PROJECT_DIR",
        "venv_env": f"{env_prefix}_VENV_DIR",
        "env_prefix": env_prefix,
        "description": description,
        "display_name": display_name,
        "short_description": short_description,
        "marker": f".{cli_name}-skill-source",
        "generated_subdir": f"_generated/{cli_name}",
    }


SCAFFOLD_FILES: dict[str, tuple[str, bool]] = {
    "pyproject.toml": (
        """[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "{{skill_name}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.10"
dependencies = []

[project.scripts]
{{cli_name}} = "{{package_name}}.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
""",
        False,
    ),
    "README.md": (
        """# {{skill_name}}

{{description}}

## Quick start

```bash
./scripts/install_cli.sh
./.venv/bin/{{cli_name}} doctor
./.venv/bin/{{cli_name}} sync-skill --targets codex --dry-run
./scripts/check_install.sh
```

## Skill + CLI boundary

The skill owns workflow judgment, fallback choice, and user-facing interpretation.
The CLI owns deterministic operations that should not be rewritten in every
agent turn.
""",
        False,
    ),
    "AGENTS.md": (
        """# AGENTS.md

This project uses the skill + CLI pattern.

Read `skill/SKILL.md` for the agent workflow and `src/{{package_name}}/cli.py`
for deterministic command behavior. Keep policy and fallback judgment in the
skill; keep repeatable filesystem, parsing, audit, and sync work in the CLI.
""",
        False,
    ),
    "src/{{package_path}}/__init__.py": (
        '''"""{{description}}"""\n\n__version__ = "0.1.0"\n''',
        False,
    ),
    "src/{{package_path}}/cli.py": (
        """from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Iterable


TOOL_NAME = "{{cli_name}}"
SKILL_NAME = "{{skill_name}}"
SOURCE_ENV = "{{source_env}}"


def project_root() -> Path:
    env = os.environ.get(SOURCE_ENV)
    if env:
        return Path(env).expanduser().resolve()
    return Path(__file__).resolve().parents[2]


def cmd_status(args: argparse.Namespace) -> int:
    root = project_root()
    payload = {
        "tool": TOOL_NAME,
        "skill": SKILL_NAME,
        "source_root": str(root),
        "skill_source": str(root / "skill"),
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    print(f"{TOOL_NAME} source root: {root}")
    print(f"skill: {SKILL_NAME}")
    print(f"skill source: {root / 'skill'}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    root = project_root()
    skill = root / "skill" / "SKILL.md"
    payload = {
        "tool": TOOL_NAME,
        "source_root": str(root),
        "python": sys.version.split()[0],
        "skill": {"ok": skill.exists(), "path": str(skill)},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if skill.exists() else 1
    print(f"{TOOL_NAME} source root: {root}")
    print(f"python: {sys.version.split()[0]}")
    print(f"skill: {'ok' if skill.exists() else 'missing'} ({skill})")
    return 0 if skill.exists() else 1


def cmd_sync_skill(args: argparse.Namespace) -> int:
    root = project_root()
    script = root / "scripts" / "sync_skill.sh"
    if not script.exists():
        print(f"missing sync script: {script}", file=sys.stderr)
        return 1
    command = [str(script), "--targets", args.targets]
    if args.force:
        command.append("--force")
    if args.dry_run:
        command.append("--dry-run")
    return subprocess.run(command, check=False).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=TOOL_NAME, description="{{description}}")
    sub = parser.add_subparsers(dest="command", required=True)
    status = sub.add_parser("status", help="Show project metadata.")
    status.add_argument("--json", action="store_true", help="Print structured JSON.")
    status.set_defaults(func=cmd_status)
    doctor = sub.add_parser("doctor", help="Check local source checkout state.")
    doctor.add_argument("--json", action="store_true", help="Print structured JSON.")
    doctor.set_defaults(func=cmd_doctor)
    sync = sub.add_parser("sync-skill", help="Sync installed skill copies via scripts/sync_skill.sh.")
    sync.add_argument("--targets", default="codex", help="Comma list: codex,cursor,agents,claude,all.")
    sync.add_argument("--force", action="store_true", help="Replace marked or explicitly approved existing targets.")
    sync.add_argument("--dry-run", action="store_true", help="Print planned targets without writing.")
    sync.set_defaults(func=cmd_sync_skill)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
""",
        False,
    ),
    "skill/SKILL.md": (
        """---
name: {{skill_name}}
description: {{description}} Use when an agent needs this reusable workflow, should call deterministic helper commands, or must sync/update this skill-backed CLI project.
metadata:
  requires:
    bins: ["{{cli_name}}"]
  cliHelp: "{{cli_name}} --help"
---

# {{display_name}}

## Goal

Use this skill to perform the reusable workflow described by this project. The
skill is the decision layer; deterministic operations belong in `{{cli_name}}`.

## CLI

Resolve helper commands in this order:

1. Run `{{cli_name}} <command>` if it is on `PATH`.
2. If this installed skill path is visible, run `bin/{{cli_name}} <command>`.
3. If `{{source_env}}` points to the source checkout, run:

```bash
{{source_env}}="${{source_env}}" PYTHONPATH="${{source_env}}/src" \
  python3 -m {{package_name}}.cli <command>
```

If none of those work, ask the user to run `./scripts/install_cli.sh` and
`./scripts/sync_skill.sh` from the source checkout.

## Default Workflow

1. Read the user request and decide which parts are judgment and which parts
   should be deterministic CLI work.
2. Run the smallest relevant `{{cli_name}}` command.
3. Use CLI outputs as evidence; do not reimplement deterministic helpers in
   chat unless the CLI is missing and the user asks for a one-off fallback.
4. If behavior changes, update `skill/SKILL.md`, CLI code, and tests together.

## Useful Commands

```bash
{{cli_name}} status
{{cli_name}} doctor
{{cli_name}} sync-skill --targets codex,agents --force
./scripts/check_install.sh
./scripts/sync_skill.sh
```

## Boundary

- Skill: policy, fallback choice, interpretation, and when to ask the user.
- CLI: parsing, filesystem writes, numbering, audit, sync, and repeatable checks.
- Scripts: source-checkout wrappers for install, sync, and local verification.
""",
        False,
    ),
    "skill/agents/openai.yaml": (
        """interface:
  display_name: "{{display_name}}"
  short_description: "{{short_description}}"
  default_prompt: "Use ${{skill_name}} for this reusable skill-backed CLI workflow."
policy:
  allow_implicit_invocation: true
""",
        False,
    ),
    "scripts/install_cli.sh": (
        """#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
VENV_DIR=${{{venv_env}}:-"$PROJECT_DIR/.venv"}
BIN_DIR="$VENV_DIR/bin"
BIN="$BIN_DIR/{{cli_name}}"

mkdir -p "$BIN_DIR"
cat > "$BIN" <<EOF
#!/usr/bin/env sh
{{source_env}}="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src\\${PYTHONPATH:+:\\$PYTHONPATH}" exec python3 -m {{package_name}}.cli "\\$@"
EOF
chmod +x "$BIN"

echo "Installed {{cli_name}} wrapper at $BIN"
echo "Try: $BIN doctor"
""",
        True,
    ),
    "scripts/sync_skill.sh": (
        """#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TARGETS="codex"
FORCE=0
DRY_RUN=0
AGENTS_SYNCED=0

usage() {
  echo "Usage: sync_skill.sh [--targets codex,cursor,agents,claude,all] [--force] [--dry-run]" >&2
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --targets)
      shift
      TARGETS="${1:?--targets requires a value}"
      ;;
    --targets=*)
      TARGETS="${1#--targets=}"
      ;;
    --force)
      FORCE=1
      ;;
    --dry-run)
      DRY_RUN=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
  shift
done

target_path() {
  case "$1" in
    codex)
      printf '%s\\n' "${CODEX_HOME:-"$HOME/.codex"}/skills/{{skill_name}}"
      ;;
    cursor)
      printf '%s\\n' "$HOME/.cursor/skills/{{skill_name}}"
      ;;
    agents)
      printf '%s\\n' "$HOME/.agents/skills/{{skill_name}}"
      ;;
    claude)
      printf '%s\\n' "$HOME/.claude/skills/{{skill_name}}"
      ;;
    *)
      echo "Unknown target: $1" >&2
      exit 2
      ;;
  esac
}

write_cli_wrapper() {
  target_dir="$1"
  mkdir -p "$target_dir/bin"
  cat > "$target_dir/bin/{{cli_name}}" <<EOF
#!/usr/bin/env sh
{{source_env}}="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src" exec python3 -m {{package_name}}.cli "\\$@"
EOF
  chmod +x "$target_dir/bin/{{cli_name}}"
}

sync_one() {
  target="$1"
  target_dir=$(target_path "$target")
  if [ "$DRY_RUN" = "1" ]; then
    echo "$target: would sync to $target_dir"
    return 0
  fi
  if [ -e "$target_dir" ] && [ ! -f "$target_dir/{{marker}}" ]; then
    if [ "$FORCE" != "1" ]; then
      echo "$target_dir exists; pass --force to replace it" >&2
      exit 2
    fi
  fi
  rm -rf "$target_dir"
  mkdir -p "$target_dir"
  cp -R "$PROJECT_DIR/skill/." "$target_dir/"
  printf '%s\\n' "$PROJECT_DIR" > "$target_dir/{{marker}}"
  write_cli_wrapper "$target_dir"
  echo "$target: synced -> $target_dir"
}

link_claude() {
  claude_dir=$(target_path claude)
  agents_link="../../.agents/skills/{{skill_name}}"
  if [ "$DRY_RUN" = "1" ]; then
    echo "claude: would link $claude_dir -> $agents_link"
    return 0
  fi
  if [ -e "$claude_dir" ] || [ -L "$claude_dir" ]; then
    if [ -L "$claude_dir" ] && [ "$(readlink "$claude_dir")" = "$agents_link" ]; then
      echo "claude: already linked -> $claude_dir"
      return 0
    fi
    if [ "$FORCE" != "1" ]; then
      echo "$claude_dir exists; pass --force to replace it" >&2
      exit 2
    fi
    rm -rf "$claude_dir"
  fi
  mkdir -p "$(dirname "$claude_dir")"
  ln -s "$agents_link" "$claude_dir"
  echo "claude: linked -> $claude_dir"
}

expanded_targets=$(printf '%s' "$TARGETS" | tr ',' ' ')
if [ "$TARGETS" = "all" ]; then
  expanded_targets="codex cursor agents claude"
fi

for target in $expanded_targets; do
  case "$target" in
    agents)
      sync_one agents
      AGENTS_SYNCED=1
      ;;
    claude)
      if [ "$AGENTS_SYNCED" != "1" ]; then
        sync_one agents
        AGENTS_SYNCED=1
      fi
      link_claude
      ;;
    codex|cursor)
      sync_one "$target"
      ;;
    *)
      echo "Unknown target: $target" >&2
      exit 2
      ;;
  esac
done
""",
        True,
    ),
    "scripts/check_install.sh": (
        """#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

{{source_env}}="$PROJECT_DIR" PYTHONPATH="$PROJECT_DIR/src" \
  python3 -m {{package_name}}.cli doctor
""",
        True,
    ),
    "scripts/update_cli.sh": (
        """#!/usr/bin/env sh
set -eu

PROJECT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)

"$PROJECT_DIR/scripts/install_cli.sh"

if [ -d "$PROJECT_DIR/tests" ]; then
  PYTHONPATH="$PROJECT_DIR/src${PYTHONPATH:+:$PYTHONPATH}" \
    python3 -m unittest discover -s "$PROJECT_DIR/tests"
fi

"$PROJECT_DIR/scripts/check_install.sh"
"$PROJECT_DIR/scripts/sync_skill.sh" "$@"
"$PROJECT_DIR/scripts/check_install.sh"
""",
        True,
    ),
    "tests/test_cli.py": (
        """from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from {{package_name}} import cli


class CliTest(unittest.TestCase):
    def test_status_runs(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["status"]), 0)

    def test_sync_skill_dry_run(self) -> None:
        with redirect_stdout(io.StringIO()):
            self.assertEqual(cli.main(["sync-skill", "--targets", "codex", "--dry-run"]), 0)


if __name__ == "__main__":
    unittest.main()
""",
        False,
    ),
    "docs/SPEC.md": (
        """# SPEC - {{skill_name}}

## 1. One-Sentence Goal

Provide a portable skill plus deterministic CLI for {{skill_name}}.

## 2. Decision Table

| ID | Decision | Choice | Notes |
|---|---|---|---|
| A | Boundary | Skill owns judgment; CLI owns deterministic work | Fill with project-specific rationale |
| B | Runtime | Python 3.10+ stdlib-first CLI | Add dependencies only when needed |
| C | Distribution | Source checkout wrapper plus installed skill-local wrapper | Keeps agents from losing paths |

## 3. Commands

| Command | Purpose | Side effects |
|---|---|---|
| `{{cli_name}} status` | Show source metadata | No |
| `{{cli_name}} doctor` | Check local source checkout state | No |
| `{{cli_name}} sync-skill` | Delegate installed skill sync to `scripts/sync_skill.sh` | Writes selected skill target dirs unless `--dry-run` is passed |

## 4. Invariants

1. **#1**: The installed skill remains a decision layer.
2. **#2**: Deterministic repeatable work belongs in CLI or scripts.
3. **#3**: Synced skill copies include `bin/{{cli_name}}`.
""",
        False,
    ),
    "docs/ARCHITECTURE.md": (
        """# ARCHITECTURE - {{skill_name}}

## 1. Layer View

```text
User / Agent
  -> {{skill_name}} skill
      -> {{cli_name}} CLI
          -> deterministic local operations
```

## 2. Module Table

| Module | Path | Responsibility |
|---|---|---|
| Skill | `skill/SKILL.md` | Workflow and decision guidance |
| CLI | `src/{{package_name}}/cli.py` | Deterministic command behavior |
| Scripts | `scripts/` | Install, sync, and check wrappers |
""",
        False,
    ),
    "docs/ROADMAP.md": (
        """# ROADMAP - {{skill_name}}

## Current Progress

**Phase**: Phase 0 - scaffold
**Current Step**: Step 0 ready for domain implementation

## Step 0 - Fill domain behavior

**Goal**: Replace the placeholder command surface with useful deterministic helpers.

**Tasks**:
- [ ] Add the first domain command.
- [ ] Update `skill/SKILL.md` with the workflow.
- [ ] Add tests.

**Acceptance**:
1. `./scripts/check_install.sh` passes.
2. The skill clearly tells agents when to run the CLI.
3. The installed skill wrapper can run the CLI from another project.
""",
        False,
    ),
    "docs/DECISIONS.md": (
        """# DECISIONS - {{skill_name}}

## Maintenance Rules

1. D-XXX numbers are monotonic.
2. Keep deterministic behavior in CLI/scripts.
3. Keep workflow judgment in the skill.

## D-001 - Scaffold as skill plus CLI

**Date**: pending

**Context**:

**Options**:
- A.
- B.
- C.

**Chosen**:

**Rationale**:
-

**Risks**:
-
""",
        False,
    ),
}


def write_project_file(project: Path, rel: str, content: str, executable: bool, force: bool) -> str:
    path = project / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        return "skipped"
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)
    return "wrote"


def cmd_init(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    ctx = scaffold_context(args, project)
    project.mkdir(parents=True, exist_ok=True)

    wrote: list[str] = []
    skipped: list[str] = []
    for rel_template, (template, executable) in SCAFFOLD_FILES.items():
        rel = render(rel_template, ctx)
        content = render(template, ctx)
        status = write_project_file(project, rel, content, executable, args.force)
        (wrote if status == "wrote" else skipped).append(rel)

    generated = project / "docs" / ctx["generated_subdir"]
    generated.mkdir(parents=True, exist_ok=True)
    (generated / ".gitkeep").touch()

    print(f"Initialized skill + CLI project at {project}")
    print(f"Skill: {ctx['skill_name']}")
    print(f"CLI: {ctx['cli_name']}")
    print(f"Package: {ctx['package_name']}")
    if wrote:
        print("Wrote: " + ", ".join(sorted(wrote)))
    if skipped:
        print("Skipped existing: " + ", ".join(sorted(skipped)))
    print(f"Next: {project / 'scripts' / 'install_cli.sh'}")
    return 0


def read_pyproject_scripts(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    scripts: dict[str, str] = {}
    in_scripts = False
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_scripts = line == "[project.scripts]"
            continue
        if in_scripts and "=" in line:
            key, value = line.split("=", 1)
            scripts[key.strip()] = value.strip().strip("\"'")
    return scripts


def frontmatter_name(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.strip().startswith("name:"):
            return line.split(":", 1)[1].strip().strip("\"'")
    return None


def derive_meta(project: Path, args: argparse.Namespace) -> ProjectMeta:
    scripts = read_pyproject_scripts(project / "pyproject.toml")
    cli_name = args.cli or (next(iter(scripts)) if scripts else None)
    script_target = scripts.get(cli_name) if cli_name else None
    package_name = args.package
    if not package_name and script_target and script_target.endswith(".cli:main"):
        package_name = script_target.removesuffix(".cli:main")
    skill_name = args.name or frontmatter_name(project / "skill" / "SKILL.md") or project.name
    source_env = f"{env_prefix_for(cli_name, args.env_prefix)}_PROJECT_DIR" if cli_name else None
    return ProjectMeta(project, skill_name, cli_name, package_name, script_target, source_env)


def file_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frontmatter_text(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    return text[:end] if end != -1 else ""


def add_finding(
    findings: list[Finding],
    level: str,
    category: str,
    message: str,
    path: Path | str | None = None,
    recommendation: str | None = None,
) -> None:
    findings.append(Finding(level, message, str(path) if path is not None else None, category, recommendation))


def audit_project(project: Path, args: argparse.Namespace) -> tuple[list[Finding], dict[str, object]]:
    meta = derive_meta(project, args)
    findings: list[Finding] = []
    scripts = read_pyproject_scripts(project / "pyproject.toml")
    skill_path = project / "skill" / "SKILL.md"
    skill_text = skill_path.read_text(encoding="utf-8") if skill_path.exists() else ""
    frontmatter = frontmatter_text(skill_path)
    docs_dir = project / "docs"
    references_dir = project / "skill" / "references"
    installed_targets: dict[str, dict[str, object]] = {}

    summary: dict[str, object] = {
        "project": str(project),
        "skill_name": meta.skill_name,
        "cli_name": meta.cli_name,
        "package_name": meta.package_name,
        "script_target": meta.script_target,
        "script_names": sorted(scripts.keys()),
        "has_tests": (project / "tests").exists(),
        "has_update_script": (project / "scripts" / "update_cli.sh").exists(),
        "has_docs_contract": all((docs_dir / name).exists() for name in ("SPEC.md", "ARCHITECTURE.md", "ROADMAP.md", "DECISIONS.md")),
        "reference_count": len(list(references_dir.glob("*.md"))) if references_dir.exists() else 0,
    }

    required_files = {
        "pyproject.toml": ("packaging", "Add pyproject.toml with [project.scripts] so the CLI command is discoverable."),
        "skill/SKILL.md": ("skill", "Add skill/SKILL.md as the agent workflow and decision layer."),
        "scripts/install_cli.sh": ("install", "Add a source-checkout install wrapper that creates .venv/bin/<cli> without package-index dependence."),
        "scripts/sync_skill.sh": ("sync", "Add a sync script that copies skill/ into installed agent skill directories and writes bin/<cli>."),
        "scripts/check_install.sh": ("verification", "Add a check script that runs the project doctor/audit commands from the source checkout."),
    }
    for rel, (category, recommendation) in required_files.items():
        path = project / rel
        if not path.exists():
            add_finding(findings, "error", category, f"missing {rel}", path, recommendation)

    if not meta.cli_name:
        add_finding(
            findings,
            "error",
            "cli",
            "pyproject.toml has no [project.scripts] CLI entry",
            project / "pyproject.toml",
            "Declare the CLI command in [project.scripts], for example mytool = \"my_package.cli:main\".",
        )
    elif not meta.script_target:
        add_finding(
            findings,
            "error",
            "cli",
            f"pyproject.toml has no script target for {meta.cli_name}",
            project / "pyproject.toml",
            "Make the script entry point target an importable module function.",
        )

    cli_path: Path | None = None
    if meta.package_name:
        cli_path = project / "src" / meta.package_name.replace(".", "/") / "cli.py"
        if not cli_path.exists():
            add_finding(
                findings,
                "error",
                "cli",
                f"missing CLI module for package {meta.package_name}",
                cli_path,
                "Place deterministic command handlers in src/<package>/cli.py.",
            )
        expected = f"{meta.package_name}.cli:main"
        if meta.script_target and meta.script_target != expected:
            add_finding(
                findings,
                "warn",
                "cli",
                f"script target is {meta.script_target}, expected {expected}",
                project / "pyproject.toml",
                "This can be valid, but the conventional target makes audits and generated wrappers simpler.",
            )

    skill_name = frontmatter_name(skill_path)
    if skill_path.exists():
        if meta.skill_name and skill_name and skill_name != meta.skill_name:
            add_finding(
                findings,
                "warn",
                "skill",
                f"skill frontmatter name is {skill_name}, expected {meta.skill_name}",
                skill_path,
                "Keep the folder name, SKILL.md frontmatter, and installed target name aligned.",
            )
        if "## CLI" not in skill_text:
            add_finding(findings, "warn", "skill", "skill has no ## CLI section", skill_path, "Add a concise CLI resolution section.")
        if meta.cli_name and meta.cli_name not in skill_text:
            add_finding(findings, "warn", "skill", f"skill does not mention CLI command {meta.cli_name}", skill_path, "Tell agents the exact CLI command to run.")
        if meta.source_env and meta.source_env not in skill_text:
            add_finding(
                findings,
                "warn",
                "portability",
                f"skill does not mention source env {meta.source_env}",
                skill_path,
                "Document the source-checkout fallback env var so agents can run the module when PATH is unavailable.",
            )
        if meta.cli_name and f"bin/{meta.cli_name}" not in skill_text:
            add_finding(
                findings,
                "warn",
                "portability",
                f"skill does not mention installed skill-local bin/{meta.cli_name}",
                skill_path,
                "Mention the installed skill-local wrapper so agents can find the CLI from arbitrary projects.",
            )
        if meta.cli_name and ("requires:" not in frontmatter or "bins:" not in frontmatter or meta.cli_name not in frontmatter):
            add_finding(
                findings,
                "warn",
                "metadata",
                f"skill frontmatter does not declare required CLI bin {meta.cli_name}",
                skill_path,
                "Add metadata.requires.bins so agent hosts can surface the CLI dependency.",
            )
        if meta.cli_name and "cliHelp:" not in frontmatter:
            add_finding(
                findings,
                "warn",
                "metadata",
                f"skill frontmatter does not declare cliHelp for {meta.cli_name}",
                skill_path,
                "Add metadata.cliHelp with the command's help invocation.",
            )
        if len(skill_text.splitlines()) > 500 and not references_dir.exists():
            add_finding(
                findings,
                "warn",
                "context",
                "large SKILL.md has no references directory",
                skill_path,
                "Move optional details into skill/references/ so agents load them only when needed.",
            )

    for rel in ("scripts/install_cli.sh", "scripts/sync_skill.sh", "scripts/check_install.sh"):
        path = project / rel
        if path.exists() and not os.access(path, os.X_OK):
            add_finding(findings, "warn", "scripts", f"{rel} is not executable", path, "Run chmod +x on source-checkout helper scripts.")

    update_script = project / "scripts" / "update_cli.sh"
    if not update_script.exists():
        add_finding(
            findings,
            "warn",
            "update",
            "scripts/update_cli.sh is missing; updates will need skillcli update or manual sequencing",
            update_script,
            "Add scripts/update_cli.sh so source updates can install, test, check, sync, and verify in one project-local command.",
        )
    elif not os.access(update_script, os.X_OK):
        add_finding(findings, "warn", "update", "scripts/update_cli.sh is not executable", update_script, "Run chmod +x scripts/update_cli.sh.")

    sync_path = project / "scripts" / "sync_skill.sh"
    if sync_path.exists() and meta.cli_name:
        text = sync_path.read_text(encoding="utf-8")
        if f"bin/{meta.cli_name}" not in text and "sync-skill" not in text:
            add_finding(
                findings,
                "warn",
                "sync",
                f"sync script does not generate bin/{meta.cli_name}",
                sync_path,
                "Generate an installed skill-local bin/<cli> wrapper during sync.",
            )
        if cli_path and cli_path.exists():
            cli_text = cli_path.read_text(encoding="utf-8")
            if "sync-skill" not in cli_text:
                add_finding(
                    findings,
                    "warn",
                    "sync",
                    f"CLI command {meta.cli_name} sync-skill is missing",
                    cli_path,
                    "Add a sync-skill subcommand that forwards --targets, --force, and --dry-run to scripts/sync_skill.sh.",
                )
            elif "scripts/sync_skill.sh" not in cli_text:
                add_finding(
                    findings,
                    "warn",
                    "sync",
                    f"CLI command {meta.cli_name} sync-skill does not clearly delegate to scripts/sync_skill.sh",
                    cli_path,
                    "Keep scripts/sync_skill.sh as the sync implementation and make the CLI command a thin wrapper.",
                )

    install_path = project / "scripts" / "install_cli.sh"
    if install_path.exists():
        install_text = install_path.read_text(encoding="utf-8")
        if meta.package_name and meta.package_name not in install_text:
            add_finding(
                findings,
                "warn",
                "install",
                f"install script does not mention package {meta.package_name}",
                install_path,
                "Make install_cli.sh create a source-checkout wrapper that runs python3 -m <package>.cli.",
            )
        if "PYTHONPATH" not in install_text:
            add_finding(
                findings,
                "warn",
                "install",
                "install script does not set PYTHONPATH",
                install_path,
                "Set PYTHONPATH to the source checkout src/ to avoid package-index and editable-install friction.",
            )

    check_path = project / "scripts" / "check_install.sh"
    if check_path.exists():
        check_text = check_path.read_text(encoding="utf-8")
        if "doctor" not in check_text and "audit" not in check_text:
            add_finding(
                findings,
                "warn",
                "verification",
                "check_install.sh does not appear to run doctor or audit",
                check_path,
                "Use check_install.sh as the fastest local proof that CLI, source, and installed skill are aligned.",
            )

    docs_contract_names = ("SPEC.md", "ARCHITECTURE.md", "ROADMAP.md", "DECISIONS.md")
    has_any_docs_contract = any((docs_dir / name).exists() for name in docs_contract_names)
    has_boundary_doc = (docs_dir / "skill-cli-boundary.md").exists()
    if not (docs_dir / "SPEC.md").exists() and not has_boundary_doc:
        add_finding(
            findings,
            "warn",
            "docs",
            "docs/SPEC.md is missing; document the boundary before expanding commands",
            docs_dir / "SPEC.md",
            "Add docs/SPEC.md or a concise docs/skill-cli-boundary.md so future agents can preserve the skill/CLI split.",
        )
    if has_any_docs_contract:
        for doc_name in ("ARCHITECTURE.md", "ROADMAP.md", "DECISIONS.md"):
            path = docs_dir / doc_name
            if docs_dir.exists() and not path.exists():
                add_finding(
                    findings,
                    "warn",
                    "docs",
                    f"docs/{doc_name} is missing",
                    path,
                    "For projects maintained with docs-driven development, keep SPEC, ARCHITECTURE, ROADMAP, and DECISIONS together.",
                )

    if not (project / "tests").exists():
        add_finding(
            findings,
            "warn",
            "tests",
            "tests directory is missing",
            project / "tests",
            "Add focused tests for CLI parsing, generated artifacts, sync wrappers, and update lifecycle behavior.",
        )
    if not (project / "README.md").exists():
        add_finding(findings, "warn", "docs", "README.md is missing", project / "README.md", "Add a short README with install, update, and audit commands.")
    if not (project / "AGENTS.md").exists():
        add_finding(
            findings,
            "warn",
            "handoff",
            "AGENTS.md is missing",
            project / "AGENTS.md",
            "Add AGENTS.md with the first-read rules for future coding agents.",
        )
    if not (project / "skill" / "agents" / "openai.yaml").exists():
        add_finding(
            findings,
            "warn",
            "metadata",
            "skill/agents/openai.yaml is missing",
            project / "skill" / "agents" / "openai.yaml",
            "Add UI metadata so the skill is easy to identify in agent surfaces.",
        )

    source_skill_hash = file_sha256(skill_path)
    if meta.skill_name and meta.cli_name and source_skill_hash:
        for target in TARGETS:
            target_dir = target_path_for(target, meta.skill_name)
            target_skill = target_dir / "SKILL.md"
            target_bin = target_dir / "bin" / meta.cli_name
            state = "missing"
            if target_dir.exists() or target_dir.is_symlink():
                state = "installed"
                target_hash = file_sha256(target_skill)
                if target_hash and target_hash != source_skill_hash:
                    add_finding(
                        findings,
                        "warn",
                        "installed",
                        f"{target} installed SKILL.md differs from source",
                        target_skill,
                        "Run the project update lifecycle or sync script so installed agents see the latest skill.",
                    )
                if not target_bin.exists():
                    add_finding(
                        findings,
                        "warn",
                        "installed",
                        f"{target} installed skill is missing bin/{meta.cli_name}",
                        target_bin,
                        "Regenerate installed skill wrappers during sync so agents can run the CLI without PATH guesses.",
                    )
            installed_targets[target] = {
                "state": state,
                "path": str(target_dir),
                "has_skill": target_skill.exists(),
                "has_bin": target_bin.exists(),
            }

    generated_dir = docs_dir / GENERATED_SUBDIR
    summary["generated_dir"] = str(generated_dir)
    summary["installed_targets"] = installed_targets
    summary["finding_counts"] = {
        "error": sum(1 for item in findings if item.level == "error"),
        "warn": sum(1 for item in findings if item.level == "warn"),
    }
    category_counts: dict[str, int] = {}
    for item in findings:
        category_counts[item.category] = category_counts.get(item.category, 0) + 1
    summary["category_counts"] = category_counts

    return findings, summary


def cmd_audit(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    findings, summary = audit_project(project, args)
    payload = {
        "ok": not any(item.level == "error" for item in findings),
        "summary": summary,
        "findings": [item.as_dict() for item in findings],
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Project: {project}")
        for key in ("skill_name", "cli_name", "package_name", "script_target"):
            print(f"{key}: {summary.get(key) or '?'}")
        if findings:
            for item in findings:
                suffix = f" ({item.path})" if item.path else ""
                print(f"[{item.level}][{item.category}] {item.message}{suffix}")
                if item.recommendation:
                    print(f"  recommendation: {item.recommendation}")
        else:
            print("No findings.")

    if args.write_report:
        report_dir = project / "docs" / GENERATED_SUBDIR
        report_dir.mkdir(parents=True, exist_ok=True)
        report = report_dir / "audit.json"
        report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if not args.json:
            print(f"Wrote {report}")

    return 1 if any(item.level == "error" for item in findings) else 0


def cmd_status(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    findings, summary = audit_project(project, args)
    errors = sum(1 for item in findings if item.level == "error")
    warnings = sum(1 for item in findings if item.level == "warn")
    payload = {
        "ok": errors == 0,
        "summary": summary,
        "finding_counts": {"error": errors, "warn": warnings},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if errors == 0 else 1
    print(f"Project: {project}")
    print(f"Skill: {summary.get('skill_name') or '?'}")
    print(f"CLI: {summary.get('cli_name') or '?'}")
    print(f"Package: {summary.get('package_name') or '?'}")
    print(f"Findings: {errors} error(s), {warnings} warning(s)")
    return 0 if errors == 0 else 1


def command_text(command: list[str]) -> str:
    return " ".join(command)


def command_env(project: Path) -> dict[str, str]:
    env = os.environ.copy()
    src = str(project / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src + (os.pathsep + existing if existing else "")
    return env


def run_step(name: str, command: list[str], cwd: Path, env: dict[str, str] | None = None) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "name": name,
        "command": command,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def print_step_result(step: dict[str, object]) -> None:
    print(f"[{step['exit_code']}] {step['name']}: {command_text(step['command'])}")  # type: ignore[arg-type]
    stdout = str(step.get("stdout") or "").strip()
    stderr = str(step.get("stderr") or "").strip()
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)


def update_payload(project: Path, steps: list[dict[str, object]], skipped: list[str]) -> dict[str, object]:
    return {
        "ok": all(int(step["exit_code"]) == 0 for step in steps),
        "project": str(project),
        "steps": steps,
        "skipped": skipped,
    }


def append_stage(
    steps: list[dict[str, object]],
    *,
    name: str,
    command: list[str],
    cwd: Path,
    env: dict[str, str] | None,
    json_output: bool,
) -> bool:
    step = run_step(name, command, cwd, env)
    steps.append(step)
    if not json_output:
        print_step_result(step)
    return int(step["exit_code"]) == 0


def source_update_flags(args: argparse.Namespace) -> list[str]:
    flags: list[str] = []
    for name, flag in (
        ("pull", "--pull"),
        ("allow_dirty", "--allow-dirty"),
        ("force", "--force"),
        ("skip_install", "--skip-install"),
        ("skip_tests", "--skip-tests"),
        ("skip_precheck", "--skip-precheck"),
        ("skip_sync", "--skip-sync"),
        ("skip_postcheck", "--skip-postcheck"),
        ("dry_run", "--dry-run"),
        ("json", "--json"),
    ):
        if getattr(args, name, False):
            flags.append(flag)
    if getattr(args, "sync_arg", None):
        flags.append("--sync-arg")
    return flags


def release_update_flags(args: argparse.Namespace) -> list[str]:
    flags: list[str] = []
    for name, flag in (
        ("version", "--version"),
        ("release_base_url", "--release-base-url"),
        ("install_root", "--install-root"),
        ("bin_dir", "--bin-dir"),
    ):
        if getattr(args, name, None):
            flags.append(flag)
    if getattr(args, "sync_skill", None) is not None:
        flags.append("--sync-skill" if args.sync_skill else "--no-sync-skill")
    return flags


def cmd_update_project(args: argparse.Namespace) -> int:
    project = Path(args.project).expanduser().resolve()
    steps: list[dict[str, object]] = []
    skipped: list[str] = []
    env = command_env(project)

    if args.dry_run:
        plan = ["optional git pull --ff-only" if args.pull else "no git pull"]
        if not args.skip_install:
            plan.append("scripts/install_cli.sh")
        if not args.skip_tests and (project / "tests").exists():
            plan.append("python3 -m unittest discover -s tests")
        if not args.skip_precheck:
            plan.append("scripts/check_install.sh")
        if not args.skip_sync:
            plan.append("scripts/sync_skill.sh" + (" --force" if args.force else ""))
        if not args.skip_postcheck:
            plan.append("scripts/check_install.sh")
        payload = {"ok": True, "project": str(project), "dry_run": True, "plan": plan}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Update plan for {project}:")
            for item in plan:
                print(f"- {item}")
        return 0

    if args.pull:
        if not (project / ".git").exists():
            step = {"name": "git-preflight", "command": ["git"], "exit_code": 1, "stdout": "", "stderr": "project is not a git checkout"}
            steps.append(step)
            if not args.json:
                print_step_result(step)
            payload = update_payload(project, steps, skipped)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        if not args.allow_dirty:
            dirty = run_step("git-status", ["git", "status", "--porcelain"], project, env)
            steps.append(dirty)
            if not args.json:
                print_step_result(dirty)
            if int(dirty["exit_code"]) != 0 or str(dirty["stdout"]).strip():
                if str(dirty["stdout"]).strip():
                    dirty["exit_code"] = 1
                    dirty["stderr"] = "dirty worktree; pass --allow-dirty to pull anyway"
                payload = update_payload(project, steps, skipped)
                if args.json:
                    print(json.dumps(payload, ensure_ascii=False, indent=2))
                return 1
        if not append_stage(steps, name="git-pull", command=["git", "pull", "--ff-only"], cwd=project, env=env, json_output=args.json):
            payload = update_payload(project, steps, skipped)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1

    install = project / "scripts" / "install_cli.sh"
    if args.skip_install:
        skipped.append("install")
    elif not install.exists():
        step = {"name": "install", "command": [str(install)], "exit_code": 1, "stdout": "", "stderr": "missing scripts/install_cli.sh"}
        steps.append(step)
        if not args.json:
            print_step_result(step)
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    elif not append_stage(steps, name="install", command=[str(install)], cwd=project, env=env, json_output=args.json):
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    tests = project / "tests"
    if args.skip_tests:
        skipped.append("tests")
    elif tests.exists():
        if not append_stage(
            steps,
            name="tests",
            command=["python3", "-m", "unittest", "discover", "-s", str(tests)],
            cwd=project,
            env=env,
            json_output=args.json,
        ):
            payload = update_payload(project, steps, skipped)
            if args.json:
                print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
    else:
        skipped.append("tests-missing")

    check = project / "scripts" / "check_install.sh"
    if args.skip_precheck:
        skipped.append("precheck")
    elif not check.exists():
        step = {"name": "precheck", "command": [str(check)], "exit_code": 1, "stdout": "", "stderr": "missing scripts/check_install.sh"}
        steps.append(step)
        if not args.json:
            print_step_result(step)
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    elif not append_stage(steps, name="precheck", command=[str(check)], cwd=project, env=env, json_output=args.json):
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    sync = project / "scripts" / "sync_skill.sh"
    sync_args = list(args.sync_arg or [])
    if args.force and "--force" not in sync_args:
        sync_args.append("--force")
    if args.skip_sync:
        skipped.append("sync")
    elif not sync.exists():
        step = {"name": "sync", "command": [str(sync), *sync_args], "exit_code": 1, "stdout": "", "stderr": "missing scripts/sync_skill.sh"}
        steps.append(step)
        if not args.json:
            print_step_result(step)
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1
    elif not append_stage(steps, name="sync", command=[str(sync), *sync_args], cwd=project, env=env, json_output=args.json):
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    if args.skip_postcheck:
        skipped.append("postcheck")
    elif not append_stage(steps, name="postcheck", command=[str(check)], cwd=project, env=env, json_output=args.json):
        payload = update_payload(project, steps, skipped)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 1

    payload = update_payload(project, steps, skipped)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def resolve_native_install_root(raw: str | None = None) -> Path:
    if raw:
        return Path(raw).expanduser()
    env = os.environ.get("SKILLCLI_INSTALL_ROOT")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".local" / "share" / "skillcli"


def resolve_native_bin_dir(raw: str | None = None) -> Path:
    if raw:
        return Path(raw).expanduser()
    env = os.environ.get("SKILLCLI_BIN_DIR")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".local" / "bin"


def cmd_release_update(args: argparse.Namespace) -> int:
    source_root = find_source_root()
    installer = source_root / "scripts" / "install_remote.sh"
    if not installer.exists():
        raise SystemExit(f"Native installer script missing: {installer}")

    command = [str(installer)]
    if args.version:
        command.extend(["--version", args.version])
    if args.release_base_url:
        command.extend(["--release-base-url", args.release_base_url])
    if args.install_root:
        command.extend(["--install-root", args.install_root])
    if args.bin_dir:
        command.extend(["--bin-dir", args.bin_dir])
    sync_skill = True if args.sync_skill is None else bool(args.sync_skill)
    command.append("--sync-skill" if sync_skill else "--no-sync-skill")

    env = os.environ.copy()
    env.setdefault("SKILLCLI_INSTALL_LOG_PREFIX", "[skillcli update]")
    return subprocess.run(command, check=False, env=env).returncode


def cmd_update(args: argparse.Namespace) -> int:
    if args.project is None:
        invalid = source_update_flags(args)
        if invalid:
            raise SystemExit(
                "skillcli update without a project updates the installed skillcli release; "
                f"{', '.join(invalid)} require an explicit project path, for example: "
                "skillcli update /path/to/project --force"
            )
        return cmd_release_update(args)

    invalid = release_update_flags(args)
    if invalid:
        raise SystemExit(
            "release update options require no project path; use `skillcli update "
            f"{' '.join(invalid)}` or update a source project without those options"
        )
    return cmd_update_project(args)


def launcher_candidates(bin_dir: Path) -> list[Path]:
    return [bin_dir / CLI_NAME, bin_dir / f"{CLI_NAME}.ps1", bin_dir / f"{CLI_NAME}.cmd"]


def dangerous_removal_path(path: Path) -> bool:
    resolved = path.expanduser().resolve(strict=False)
    home = Path.home().resolve(strict=False)
    return resolved in {
        Path("/"),
        home,
        home / ".local",
        home / ".local" / "share",
        home / ".local" / "bin",
        home / ".codex",
        home / ".cursor",
        home / ".agents",
        home / ".claude",
    }


def launcher_is_skillcli_owned(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    if path.is_symlink():
        try:
            target = os.readlink(path)
        except OSError:
            return False
        if not path.exists():
            return "skillcli" in target or "skill-cli-kit" in target
    if not path.is_file():
        return False
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")[:4096]
    except OSError:
        return False
    return f"{PACKAGE_NAME}.cli" in text and (SOURCE_ENV in text or "PYTHONPATH" in text)


def plan_native_uninstall(install_root: Path, bin_dir: Path, keep_skills: bool) -> list[UninstallAction]:
    actions: list[UninstallAction] = []
    if install_root.exists() or install_root.is_symlink():
        if dangerous_removal_path(install_root):
            actions.append(UninstallAction("install root", install_root, "skip", "unsafe parent path"))
        else:
            actions.append(UninstallAction("install root", install_root, "remove", "native release install root"))
    else:
        actions.append(UninstallAction("install root", install_root, "skip", "missing"))

    for launcher in launcher_candidates(bin_dir):
        if not launcher.exists() and not launcher.is_symlink():
            actions.append(UninstallAction("launcher", launcher, "skip", "missing"))
        elif launcher_is_skillcli_owned(launcher):
            actions.append(UninstallAction("launcher", launcher, "remove", "generated skillcli launcher"))
        else:
            actions.append(UninstallAction("launcher", launcher, "skip", "not generated by skillcli"))

    if keep_skills:
        actions.append(UninstallAction("skill targets", Path("(all)"), "skip", "--keep-skills"))
        return actions

    seen: set[Path] = set()
    for target in TARGETS:
        path = target_path_for(target)
        key = path.expanduser().absolute()
        if key in seen:
            continue
        seen.add(key)
        label = f"skill {target}"
        if path.is_symlink():
            actions.append(UninstallAction(label, path, "remove", "owned symlink target"))
        elif path.exists() and (path / MARKER_NAME).exists():
            actions.append(UninstallAction(label, path, "remove", "marked skill-cli-kit skill target"))
        elif path.exists():
            actions.append(UninstallAction(label, path, "skip", "unmarked skill target"))
        else:
            actions.append(UninstallAction(label, path, "skip", "missing"))
    return actions


def remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def print_uninstall_plan(actions: list[UninstallAction]) -> None:
    print("skillcli uninstall plan:")
    for item in actions:
        print(f"  {item.action}: {item.label}: {item.path} ({item.reason})")


def cmd_uninstall(args: argparse.Namespace) -> int:
    install_root = resolve_native_install_root(args.install_root)
    bin_dir = resolve_native_bin_dir(args.bin_dir)
    actions = plan_native_uninstall(install_root, bin_dir, keep_skills=args.keep_skills)
    print_uninstall_plan(actions)

    if args.dry_run:
        return 0
    if not args.yes:
        print("Refusing to uninstall without --yes. Use --dry-run to preview only.", file=sys.stderr)
        return 2

    for item in actions:
        if item.action == "remove":
            remove_path(item.path)
            print(f"removed: {item.path}")
        else:
            print(f"skipped: {item.path} ({item.reason})")
    return 0


def parse_targets(raw: str) -> list[str]:
    aliases = {"all": TARGETS, "default": TARGETS}
    result: list[str] = []
    for part in [item.strip() for item in raw.split(",") if item.strip()]:
        expanded = aliases.get(part, (part,))
        for target in expanded:
            if target not in TARGETS:
                raise SystemExit(f"Unknown target: {target}")
            if target not in result:
                result.append(target)
    return result


def source_root_for_skill_source(source: Path) -> Path:
    marked = read_marker_source(source)
    if marked:
        return marked
    if source.name == "skill" and (source.parent / "src" / PACKAGE_NAME).exists():
        return source.parent.resolve()
    if (source / "src" / PACKAGE_NAME).exists():
        return source.resolve()
    return find_source_root()


def write_installed_skill_wrapper(target: Path, source: Path) -> None:
    source_root = source_root_for_skill_source(source)
    bin_dir = target / "bin"
    wrapper = bin_dir / CLI_NAME
    bin_dir.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(
        "#!/usr/bin/env sh\n"
        f'{SOURCE_ENV}="{source_root}" PYTHONPATH="{source_root}/src" '
        f'exec python3 -m {PACKAGE_NAME}.cli "$@"\n',
        encoding="utf-8",
    )
    wrapper.chmod(0o755)


def copy_skill(source: Path, target: Path, force: bool) -> str:
    if target.exists() or target.is_symlink():
        marker = target / MARKER_NAME if not target.is_symlink() else None
        if not force and not (marker and marker.exists()):
            return "exists; pass --force to replace"
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, target)
    (target / MARKER_NAME).write_text(str(source_root_for_skill_source(source)) + "\n", encoding="utf-8")
    write_installed_skill_wrapper(target, source)
    return "copied"


def link_claude_to_agents(force: bool) -> str:
    target = target_path_for("claude")
    agents_target = Path("..") / ".." / ".agents" / "skills" / SKILL_NAME
    if target.exists() or target.is_symlink():
        if target.is_symlink() and os.readlink(target) == str(agents_target):
            return "already linked"
        if not force:
            return "exists; pass --force to replace"
        if target.is_symlink() or target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.symlink_to(agents_target)
    return "linked to ~/.agents"


def cmd_sync_skill(args: argparse.Namespace) -> int:
    source = Path(args.source).expanduser().resolve() if args.source else skill_source_dir()
    if not (source / "SKILL.md").exists():
        raise SystemExit(f"Skill source missing SKILL.md: {source}")

    targets = parse_targets(args.targets)
    if args.dry_run:
        for target in targets:
            print(f"{target}: {target_path_for(target)}")
        return 0

    if "claude" in targets and "agents" not in targets:
        targets.insert(0, "agents")

    for target in targets:
        if target == "claude":
            status = link_claude_to_agents(args.force)
        else:
            status = copy_skill(source, target_path_for(target), args.force)
        print(f"{target}: {status} -> {target_path_for(target)}")
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    source_root = find_source_root()
    source = skill_source_dir()
    targets: dict[str, dict[str, str]] = {}
    for target in TARGETS:
        path = target_path_for(target)
        state = "installed" if path.exists() or path.is_symlink() else "missing"
        link = os.readlink(path) if path.is_symlink() else ""
        targets[target] = {"state": state, "path": str(path), "link": link}
    payload = {
        "tool": CLI_NAME,
        "source_root": str(source_root),
        "skill_source": str(source),
        "python": sys.version.split()[0],
        "targets": targets,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if (source / "SKILL.md").exists() else 1
    print(f"{CLI_NAME} source root: {source_root}")
    print(f"skill source: {source}")
    print(f"python: {sys.version.split()[0]}")
    for target, data in targets.items():
        state = data["state"]
        if data["link"]:
            state += f" -> {data['link']}"
        print(f"{target}: {state} ({data['path']})")
    return 0 if (source / "SKILL.md").exists() else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog=CLI_NAME, description="Skill + CLI project scaffolding and audit toolkit.")
    parser.add_argument("-v", "--version", action="version", version=f"{CLI_NAME} {__version__}")
    visible_commands = "{init,audit,status,update,uninstall,sync-skill,doctor}"
    sub = parser.add_subparsers(dest="command", required=True, metavar=visible_commands)

    init = sub.add_parser("init", help="Create a portable skill + CLI source project.")
    init.add_argument("project")
    init.add_argument("--name", help="Skill name. Defaults to the project directory name.")
    init.add_argument("--cli", help="CLI command name. Defaults to the skill name without hyphens.")
    init.add_argument("--package", help="Python package name. Defaults to skill name with underscores.")
    init.add_argument("--env-prefix", help="Environment variable prefix. Defaults to the CLI name.")
    init.add_argument("--description", help="Project and skill description.")
    init.add_argument("--display-name", help="Human-facing skill display name.")
    init.add_argument("--short-description", help="Human-facing one-line skill description.")
    init.add_argument("--force", action="store_true", help="Overwrite existing scaffold files.")
    init.set_defaults(func=cmd_init)

    audit = sub.add_parser("audit", help="Audit a skill + CLI source project.")
    audit.add_argument("project", nargs="?", default=".")
    audit.add_argument("--name")
    audit.add_argument("--cli")
    audit.add_argument("--package")
    audit.add_argument("--env-prefix")
    audit.add_argument("--json", action="store_true")
    audit.add_argument("--write-report", action="store_true")
    audit.set_defaults(func=cmd_audit)

    status = sub.add_parser("status", help="Show discovered project metadata and finding counts.")
    status.add_argument("project", nargs="?", default=".")
    status.add_argument("--name")
    status.add_argument("--cli")
    status.add_argument("--package")
    status.add_argument("--env-prefix")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    def add_release_update_args(command: argparse.ArgumentParser) -> None:
        command.add_argument("--version", default=None, help="Install a specific release version when updating skillcli itself.")
        command.add_argument("--release-base-url", default=None, help="Manifest/artifact base URL when updating skillcli itself.")
        command.add_argument("--install-root", default=None, help="Override SKILLCLI_INSTALL_ROOT when updating skillcli itself.")
        command.add_argument("--bin-dir", default=None, help="Override SKILLCLI_BIN_DIR when updating skillcli itself.")
        command.add_argument("--sync-skill", dest="sync_skill", action="store_true", default=None, help="Refresh installed skill targets after updating skillcli itself. Default.")
        command.add_argument("--no-sync-skill", dest="sync_skill", action="store_false", help="Update skillcli itself only; skip refreshing skill targets.")

    update = sub.add_parser("update", help="Update skillcli itself, or update a source project when PROJECT is provided.")
    update.add_argument("project", nargs="?", default=None, help="Optional source checkout to update.")
    update.add_argument("--pull", action="store_true", help="Run git pull --ff-only before local verification.")
    update.add_argument("--allow-dirty", action="store_true", help="Allow --pull with a dirty worktree.")
    update.add_argument("--force", action="store_true", help="Pass --force to scripts/sync_skill.sh.")
    update.add_argument("--sync-arg", action="append", help="Extra argument passed through to scripts/sync_skill.sh. Repeat as needed.")
    update.add_argument("--skip-install", action="store_true")
    update.add_argument("--skip-tests", action="store_true")
    update.add_argument("--skip-precheck", action="store_true")
    update.add_argument("--skip-sync", action="store_true")
    update.add_argument("--skip-postcheck", action="store_true")
    update.add_argument("--dry-run", action="store_true")
    update.add_argument("--json", action="store_true")
    add_release_update_args(update)
    update.set_defaults(func=cmd_update)

    native_update = sub.add_parser("native-update", help=argparse.SUPPRESS)
    add_release_update_args(native_update)
    native_update.set_defaults(func=cmd_release_update)
    sub._choices_actions = [item for item in sub._choices_actions if item.dest != "native-update"]

    uninstall = sub.add_parser("uninstall", help="Remove a native release install and owned skill targets.")
    uninstall.add_argument("--install-root", default=None, help="Override SKILLCLI_INSTALL_ROOT.")
    uninstall.add_argument("--bin-dir", default=None, help="Override SKILLCLI_BIN_DIR.")
    uninstall.add_argument("--keep-skills", action="store_true", help="Remove only the native CLI install; keep agent skill targets.")
    uninstall.add_argument("--dry-run", action="store_true", help="Preview planned removals without deleting files.")
    uninstall.add_argument("--yes", action="store_true", help="Confirm destructive uninstall.")
    uninstall.set_defaults(func=cmd_uninstall)

    sync = sub.add_parser("sync-skill", help="Sync the skill-cli-kit skill to agent skill homes.")
    sync.add_argument("--targets", default="all", help="Comma list: codex,cursor,agents,claude,all")
    sync.add_argument("--source", default=None)
    sync.add_argument("--force", action="store_true")
    sync.add_argument("--dry-run", action="store_true")
    sync.set_defaults(func=cmd_sync_skill)

    doctor = sub.add_parser("doctor", help="Show source checkout and installed skill state.")
    doctor.add_argument("--json", action="store_true")
    doctor.set_defaults(func=cmd_doctor)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
