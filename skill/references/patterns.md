# Skill + CLI Patterns

## Boundary Test

Move behavior into the CLI when it is:

- deterministic
- repeatedly rewritten by agents
- easy to verify with files, JSON, status codes, or tests
- sensitive to local paths or install state

Keep behavior in the skill when it is:

- user-intent interpretation
- fallback choice
- safety policy
- result synthesis
- deciding whether to ask a question

## Proven Command Surface

- `init`: create a portable source project
- `audit`: report structural drift
- `status`: summarize current metadata
- `doctor`: inspect local tool and sync state
- `sync-skill`: copy skill content and generate installed wrappers

Domain projects add their own commands beside this surface, but should keep a
business CLI `sync-skill` command available. That command should forward
`--targets`, `--force`, and `--dry-run` to `scripts/sync_skill.sh` instead of
duplicating target resolution or copy logic.
