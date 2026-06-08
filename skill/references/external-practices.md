# External Practice Notes

Use this reference when improving `skillcli` or designing a new generated
skill-backed CLI project.

## Python CLI Basics

- Keep stdlib `argparse` for small local CLIs unless the behavior requires a
  richer parser.
- Use subcommands plus `set_defaults(func=...)` so each command has a clear
  handler.
- Keep `[project.scripts]` in `pyproject.toml`; it is the package-level command
  advertisement and gives installers a standard way to create wrappers.

Sources:
- Python argparse docs: https://docs.python.org/3/library/argparse.html
- PyPA entry points spec: https://packaging.python.org/en/latest/specifications/entry-points/

## Agent-Readable Output

- Human output is useful, but agent workflows need stable structured output.
- Prefer JSON for status, doctor, audit, and machine handoff commands.
- Keep tables and pretty output optional; do not make agents parse decorative
  formatting.
- For future richer CLIs, consider a global output format flag similar to
  `--format json|table|quiet` only after several commands need it.

Sources:
- AWS CLI output formats: https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-output-format.html
- Hugging Face CLI formatting modes: https://huggingface.co/docs/huggingface_hub/main/en/guides/cli

## LarkCLI-Inspired Skill + CLI Design

LarkCLI is an especially relevant model because it is built for both humans and
AI agents, ships domain skills, and keeps a real CLI as the execution surface.

Patterns worth copying:

- Declare required bins in skill metadata, for example `metadata.requires.bins`.
- Keep shared setup, identity, auth, permission, security, and update handling
  in a shared skill instead of duplicating it in every domain skill.
- Give each domain skill a small routing map and references, not one giant
  always-loaded manual.
- Prefer shortcut commands for common agent workflows, lower-level API commands
  for precise operations, and raw API escape hatches only when needed.
- Include `--dry-run` for write/delete style commands.
- Expose update and doctor flows explicitly.

Sources:
- LarkCLI GitHub README: https://github.com/larksuite/cli
- LarkCLI blog: https://www.larksuite.com/en_us/blog/lark-cli
