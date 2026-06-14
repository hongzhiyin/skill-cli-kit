# DECISIONS - skill-cli-kit

> Source of truth for rationale.

## Maintenance Rules

1. D-XXX numbers are monotonic: do not reuse and do not skip.
2. Reversing a decision means adding a new D-XXX and marking the old entry as
   superseded; do not rewrite old conclusions.
3. Each non-trivial decision should include at least three options.
4. Risk registration is required, even if the risk is "no known risk".

---

## D-001 - Create a dedicated skill-backed CLI toolkit

**Date**: 2026-06-08

**Context**:
The Bilibili and docs-driven-dev projects both converged on the same shape:
skill prose for judgment, stdlib CLI for deterministic work, local install
wrappers, sync scripts, and installed skill-local CLI wrappers. Repeating that
from memory would be brittle.

**Options**:
- A. Keep using docs-driven-dev as the only helper - convenient for docs, but
  too domain-specific for scaffolding arbitrary skill + CLI projects.
- B. Write a checklist reference only - simple, but agents would still have to
  recreate files and wrapper scripts by hand.
- C. Create `skill-cli-kit` with a `skillcli` CLI that scaffolds, audits, and
  syncs the reusable pattern.

**Chosen**: C

**Rationale**:
- It makes the pattern executable instead of conversational.
- It keeps the skill/CLI boundary explicit for future projects.
- It directly addresses the failure mode where agents have skill context but
  cannot find the corresponding CLI path.

**Risks**:
- The scaffold may be too generic. Mitigation: keep v1 small, then refine after
  using it on a third real project.

**Related code / docs**:
- SPEC §2 A-D
- `src/skill_cli_kit/cli.py`
- `skill/SKILL.md`

---

## D-002 - Scaffold a complete source project, not just a skill folder

**Date**: 2026-06-08

**Context**:
A portable behavior needs more than `SKILL.md`: it needs deterministic code,
tests, install scripts, sync scripts, metadata, and a durable place for intent.

**Options**:
- A. Generate only `skill/SKILL.md` - fast, but leaves CLI and install shape
  undefined.
- B. Generate a Python package only - useful for commands, but loses agent
  workflow guidance.
- C. Generate a full source project with `pyproject.toml`, `src/`, `skill/`,
  `scripts/`, `tests/`, and `docs/`.

**Chosen**: C

**Rationale**:
- Future agents can inspect a familiar project layout.
- Tests and audit checks make portability regressions visible.
- The source checkout remains the editable truth; installed copies are outputs.

**Risks**:
- The generated docs may feel heavy for tiny helpers. Mitigation: keep generated
  docs concise and allow projects to prune only with an explicit decision.

**Related code / docs**:
- SPEC §3.3
- `src/skill_cli_kit/cli.py`

---

## D-003 - Use installed skill-local wrappers to remove path guessing

**Date**: 2026-06-08

**Context**:
The recurring portability problem is that an agent may load a skill from an
installed skill directory while the actual CLI code lives in a source checkout
that is not on `PATH`.

**Options**:
- A. Require global shell PATH edits - simple locally, but unreliable across
  tool hosts and agent sessions.
- B. Require an env var only - better, but still depends on environment
  propagation.
- C. Generate `bin/<cli>` inside synced skill copies, pointing back to the
  source checkout.

**Chosen**: C

**Rationale**:
- The skill can tell agents to run a nearby wrapper.
- The source checkout remains the only CLI implementation.
- Moving a checkout has a clear fix: rerun sync.

**Risks**:
- Wrappers become stale if the source checkout moves. Mitigation: `doctor` and
  `audit` expose install state, and sync is cheap to rerun.

**Related code / docs**:
- SPEC §2 D-E
- `scripts/sync_skill.sh`
- `src/skill_cli_kit/cli.py`

---

## D-004 - Borrow agent-native CLI contracts from external practice and LarkCLI

**Date**: 2026-06-08

**Context**:
After the first `skillcli` version worked locally, the next question was how to
avoid making a private one-off convention. Python packaging, CLI output docs,
and LarkCLI all point toward explicit command entrypoints, structured machine
output, and skills that advertise required CLI tools.

**Options**:
- A. Keep v1 as-is until a third project fails - stable, but misses obvious
  agent-readability improvements.
- B. Add a large framework for output formats and plugin metadata - powerful,
  but heavy for a local stdlib toolkit.
- C. Add focused support: generated skill metadata for required bins,
  `status/doctor --json`, audit warnings for missing metadata, and a reference
  note for Lark-style shared/domain skill layering.

**Chosen**: C

**Rationale**:
- It keeps the CLI stdlib-only and small.
- It makes generated projects easier for agents to discover and verify.
- It copies the most relevant LarkCLI idea: a real CLI execution surface paired
  with skills that teach routing, safety, and domain-specific judgment.

**Risks**:
- Metadata formats may differ between agent hosts. Mitigation: keep this as
  advisory frontmatter and wrapper-based execution remains the hard guarantee.

**Related code / docs**:
- SPEC §2 G-H
- `skill/references/external-practices.md`
- `src/skill_cli_kit/cli.py`

---

## D-005 - Treat updates as a source-checkout verification and sync lifecycle

**Date**: 2026-06-08

**Context**:
The user's expected steady state is one source checkout per CLI under
`~/Project/<tool>`, with installed skills as generated copies for other agents.
After a source checkout is updated like software, the installed skill copy must
be refreshed so agents see the latest instructions and wrappers.

**Options**:
- A. Ask users to remember `install_cli`, tests, `check_install`, and
  `sync_skill` manually - flexible, but easy to forget and inconsistent.
- B. Make `sync_skill` pull source updates and run all checks - direct, but it
  overloads a script whose job is copying skill content.
- C. Add a separate update lifecycle command/script that can optionally pull,
  then install, test, check, sync, and verify.

**Chosen**: C

**Rationale**:
- It keeps source mutation, verification, and sync as explicit stages.
- It works for both central `skillcli update <project>` and project-local
  `scripts/update_cli.sh`.
- It prevents broken source updates from being copied into installed skills by
  default.

**Risks**:
- Some projects may need custom test commands. Mitigation: allow skipping
  stages and rely on each project's `scripts/check_install.sh` for domain
  checks.

**Related code / docs**:
- SPEC §3.2, §5.2
- `src/skill_cli_kit/cli.py`
- `scripts/update_cli.sh`

---

## D-006 - Make audit useful for existing CLI skills, not only generated projects

**Date**: 2026-06-08

**Context**:
The user wants `skillcli` to review existing skill + CLI projects such as
`bvr` and `docdev`, checking whether the project folder has the expected
content, conforms to the portable pattern, and has optimization opportunities.

**Options**:
- A. Keep audit strict to generated `skillcli` projects - simple, but not useful
  for the existing projects that motivated the toolkit.
- B. Add a separate heavy "lint" subsystem - clearer separation, but more code
  and a new command surface before the current audit has matured.
- C. Extend `audit` with categorized findings and recommendations that work for
  both generated and existing CLI skill projects.

**Chosen**: C

**Rationale**:
- One command can answer "is this project portable and agent-friendly?"
- Existing projects do not need to be regenerated to be reviewed.
- Findings can identify optimization work without turning every difference into
  a hard failure.

**Risks**:
- Heuristic warnings can be noisy. Mitigation: keep them as warnings, report
  categories, and refine after real reviews.

**Related code / docs**:
- SPEC §2 J, §5.3
- `src/skill_cli_kit/cli.py`
- `tests/test_cli.py`

---

## D-007 - Promote `skill-cli-kit` to a top-level Project checkout

**Date**: 2026-06-08

**Context**:
The toolkit expects each CLI-backed skill to have one editable source checkout
under `~/Project/<tool>`, with installed skills and wrappers generated from
that checkout. The first `skill-cli-kit` implementation lived under
`~/Project/Idea/skill-cli-kit`, which works locally but makes the source root
look like a nested scratch project rather than a durable CLI project.

**Options**:
- A. Keep `~/Project/Idea/skill-cli-kit` as the source checkout - minimal work,
  but inconsistent with the rule the toolkit teaches.
- B. Add only a symlink from `~/Project/skill-cli-kit` to the current nested
  directory - convenient, but the canonical source remains ambiguous.
- C. Move or copy the checkout to `/Users/chihoyo/Project/skill-cli-kit`, then
  reinstall, resync, and verify all wrappers point to that canonical source.

**Chosen**: C

**Rationale**:
- It makes `skill-cli-kit` match `docs-driven-dev` and `bilibili-video-reading`
  as a first-class CLI project.
- It keeps installed skill directories as generated outputs, not editable
  source.
- It reduces future path confusion when other agents run `skillcli doctor`,
  `skillcli update`, or a skill-local `bin/skillcli`.

**Risks**:
- Existing wrappers can keep pointing to the old nested checkout. Mitigation:
  rerun install and sync from the canonical checkout, refresh the global
  symlink, and verify with `doctor` plus `audit`.

**Related code / docs**:
- SPEC §2 K, §4, invariant #10
- ARCHITECTURE §2.1
- ROADMAP Step 4a

---

## D-008 - Make `skill-cli-kit` its own native-install reference

**Date**: 2026-06-13

**Context**:
The user wants `skill-cli-kit` to be more than a local helper: it should be the
reference implementation for turning reusable skills into native-installable
CLI projects. Since `skill-cli-kit` itself was born by solidifying a skill into
a CLI, its own project structure should demonstrate the install and release
shape it will later recommend to generated projects.

**Options**:
- A. Keep only source-checkout wrappers - already healthy locally, but it leaves
  the reference project one step behind the native-install shape proven by
  `docs-driven-dev`.
- B. Replace `skillcli update <project>` with native self-update - closer to
  `docdev`, but breaks an existing command whose purpose is updating arbitrary
  skill-backed source checkouts.
- C. Add a native release layer beside the source-checkout lifecycle:
  `scripts/package_release.sh`, remote installers, `~/.local/bin/skillcli`,
  `skillcli native-update`, and confirmed uninstall.

**Chosen**: C

**Rationale**:
- The source checkout remains the editable implementation and still supports
  scaffold/audit/update work for other projects.
- Native install gives future users and agents a no-clone path to `skillcli`.
- Keeping `native-update` separate preserves the existing `skillcli update
  <project>` contract.
- The project can now serve as a concrete reference for later generated native
  install scaffolds.

**Risks**:
- There is now one more lifecycle to document and test. Mitigation: keep native
  release scripts small, checksum-verified, and covered by local file:// smoke.
- Generated project templates do not yet fully emit this native release layer.
  Mitigation: record this as follow-up after the self-hosting reference is
  proven by a public release.

**Related code / docs**:
- SPEC §2 L, §3.3, invariant #11
- ROADMAP Step 4b
- `scripts/package_release.sh`
- `scripts/install_remote.sh`
- `scripts/install_remote.ps1`
- `src/skill_cli_kit/cli.py`

---

## D-009 - Make `update` the self-release update command

**Date**: 2026-06-14

**Context**:
After v0.1.0 introduced `skillcli native-update`, the user pointed out that the
command does not need `native` in its public name. The implementation detail is
native release installation, but the user intent is simply to update
`skillcli`.

**Options**:
- A. Keep `native-update` as the documented command - smallest change, but it
  exposes an implementation detail.
- B. Replace project update entirely with self-update - simple command surface,
  but it breaks `skillcli update <project>` for source checkout maintenance.
- C. Make `skillcli update` update the installed release when no project is
  provided, keep `skillcli update <project>` for source checkout updates, and
  retain `native-update` only as a hidden compatibility alias.

**Chosen**: C

**Rationale**:
- `skillcli update` is the natural self-update command for users and agents.
- Explicit project paths keep the source checkout lifecycle unambiguous:
  `skillcli update .` or `skillcli update ~/Project/<tool>`.
- Hiding `native-update` reduces new-user command surface while preserving a
  transition path for v0.1.0 users.

**Risks**:
- Users relying on old no-argument `skillcli update` as current-directory
  project update must now pass `.` explicitly. Mitigation: source-only flags
  without a project emit an error that names the required project path.
- Release-update options and project-update options share one subcommand.
  Mitigation: mixed release options plus project path are rejected.

**Related code / docs**:
- SPEC §2 I, §3.2, invariant #12
- ROADMAP Step 4b
- `docs/changes/2026-06-14-update-self-release-by-default/`
- `src/skill_cli_kit/cli.py`
- `tests/test_cli.py`

---

## D-010 - Generate a domain CLI `sync-skill` wrapper

**Date**: 2026-06-15

**Context**:
Generated projects already include `scripts/sync_skill.sh`, but agents prefer
discoverable business CLI commands over remembering project-local script paths.
At the same time, duplicating target resolution and copy logic in both the CLI
and script would make generated projects drift-prone.

**Options**:
- A. Keep only `scripts/sync_skill.sh` - preserves one implementation, but
  hides an important lifecycle operation outside the generated CLI surface.
- B. Reimplement sync behavior inside generated `<cli> sync-skill` - gives a
  direct command, but creates two implementations of target resolution, force
  handling, and wrapper generation.
- C. Generate `<cli> sync-skill` as a thin wrapper that forwards
  `--targets`, `--force`, and `--dry-run` to `scripts/sync_skill.sh`.

**Chosen**: C

**Rationale**:
- Agents get a stable, discoverable command in the generated business CLI.
- `scripts/sync_skill.sh` remains the single sync implementation for source
  checkout update flows and direct script use.
- Audit can identify older projects that have the script but not the CLI
  command, without treating the gap as a hard structural error.

**Risks**:
- Projects with intentionally custom sync behavior may receive an advisory
  warning. Mitigation: keep the finding at `warn` level with a concrete
  recommendation rather than blocking audit success.

**Related code / docs**:
- SPEC §2 M, §3.4, invariant #13
- ROADMAP Step 4d
- `docs/changes/2026-06-15-generated-cli-sync-skill-command/`
- `src/skill_cli_kit/cli.py`
- `tests/test_cli.py`
