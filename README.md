# skill-cli-kit

Portable toolkit for turning reusable agent behavior into skill-backed CLI
projects.

## Quick start

Native install from GitHub Releases:

```bash
curl -fsSL https://github.com/hongzhiyin/skill-cli-kit/releases/latest/download/install_remote.sh | sh
```

If `~/.local/bin` is not on `PATH`, run `~/.local/bin/skillcli` directly or add
that directory yourself.

Native installs use:

```text
~/.local/share/skillcli/releases/<version>/
~/.local/share/skillcli/current
~/.local/bin/skillcli
```

Source checkout development:

```bash
./scripts/install_cli.sh
./.venv/bin/skillcli doctor
./.venv/bin/skillcli init /tmp/my-skill --name my-skill --cli mytool
./.venv/bin/skillcli audit /tmp/my-skill
```

## Updating skillcli

For native installs, update `skillcli` itself from the release channel:

```bash
skillcli update
```

Use `--no-sync-skill` only when you want to refresh the CLI release without
writing Codex / Agents skill copies.

## Updating A Tool

Each skill-backed CLI should have one editable source checkout, usually under
`~/Project/<tool>`. After changing or pulling source code, update the installed
skill copy from that source checkout:

```bash
skillcli update ~/Project/<tool> --force
```

For this project:

```bash
./scripts/update_cli.sh --force --sync-arg=--targets --sync-arg=codex,agents
```

The update lifecycle installs the local wrapper, runs tests, runs
`check_install`, syncs the skill, then runs `check_install` again.

Generated skill-backed CLIs should also expose their own sync entrypoint:

```bash
mytool sync-skill --targets codex,agents --force
```

That command should only delegate to the project's `scripts/sync_skill.sh`; the
script remains the single implementation of target resolution, copying, and
installed `bin/<cli>` wrapper generation.

Build release assets:

```bash
./scripts/package_release.sh
```

Local release smoke:

```bash
SKILLCLI_RELEASE_BASE_URL="file:///path/to/release-assets" ./scripts/install_remote.sh
```

## Reviewing Existing CLI Skills

Use `audit` on any existing source checkout under `~/Project`:

```bash
skillcli audit ~/Project/bilibili-video-reading
skillcli audit ~/Project/docs-driven-dev --json
```

The report distinguishes required structural errors from optimization warnings,
and each finding includes a category plus recommendation.

## What It Generalizes

This project captures the pattern proven by `bvr` and `docdev`:

- the skill explains when and why to use the behavior;
- the CLI performs deterministic work and emits checkable output;
- scripts install local wrappers without package-index dependence;
- native installers can install a released CLI without cloning the source repo;
- sync writes installed skill-local `bin/<cli>` wrappers so agents can find the
  command from unrelated project directories.
- generated domain CLIs expose `<cli> sync-skill` as the discoverable sync
  entrypoint while delegating to `scripts/sync_skill.sh`.

## Documentation map

This project's source of truth lives in `docs/`. Any code change must be
consistent with these documents; conflicts get resolved by editing the docs
first, then code.

| File | Contents |
|---|---|
| [docs/SPEC.md](docs/SPEC.md) | Rules, invariants, command list, default behaviour |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layers, module table, data flow, config |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Step list, acceptance, current progress |
| [docs/DECISIONS.md](docs/DECISIONS.md) | D-XXX trade-off log |
