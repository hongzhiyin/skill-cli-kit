# SPEC - Generated CLI Sync-Skill Command

> 本文件描述本次需求应该满足什么。它不写实现细节、不追踪进度、不解释历史取舍。

## 0. 状态

| 字段 | 内容 |
|---|---|
| 状态 | 完成 |
| 需求来源 | 用户要求把“生成项目的业务 CLI 应提供显式 sync-skill 子命令”沉淀进生成器、审计和文档合同 |
| 工作包目录 | `docs/changes/2026-06-15-generated-cli-sync-skill-command/` |
| 最后更新 | 2026-06-15 |

## 1. 一句话目标

让 `skillcli init` 生成的 skill+CLI 项目同时拥有
`scripts/sync_skill.sh` 和可发现的 `<cli> sync-skill` 命令，并让 audit
能提醒旧项目补齐该入口。

## 2. 背景与问题

- 当前行为：生成模板提供 `scripts/sync_skill.sh`，生成 CLI 只包含
  `status` 和 `doctor`；audit 会检查 sync 脚本和 installed wrapper，但不检查业务
  CLI 是否暴露 sync 入口。
- 问题：agent 使用生成项目时更容易发现 `<cli> ...` 命令，而不是记住脚本路径；但把
  sync 逻辑复制到 CLI 会造成两套目标解析和复制行为。
- 期望收益：新项目的业务 CLI 有显式 sync 生命周期入口，旧项目 audit 能获得可执行的
  warn 和修复建议，同时保持脚本是唯一 sync 实现。

## 3. 范围

### 3.1 本次要做

- 更新生成器模板，使新生成的 `src/<package>/cli.py` 包含
  `<cli> sync-skill`。
- 更新生成的 `scripts/sync_skill.sh`，支持 `--targets`, `--force`,
  `--dry-run`。
- 保证 `<cli> sync-skill` 只是薄封装项目内的 `scripts/sync_skill.sh`。
- 更新 `skillcli audit`，对已有项目缺少 `<cli> sync-skill` 给出 `warn` 和修复建议。
- 更新根文档、skill 指南、pattern reference 和生成项目文档模板。
- 补充单测覆盖生成项目包含该命令，以及 audit 能发现缺失项。

### 3.2 本次不做

- 不改变 `skillcli update --sync-skill/--no-sync-skill` 的 release update 语义。
- 不把生成项目的 sync 逻辑迁移到 CLI 模块内部。
- 不为已有第三方项目自动改写源码。

## 4. 用户场景 / 使用流程

| 场景 ID | 触发条件 | 期望结果 |
|---|---|---|
| S1 | 用户运行 `skillcli init /tmp/my-skill --cli mytool` | 生成项目的 `mytool --help` 展示 `sync-skill`，并且 `mytool sync-skill --targets codex --dry-run` 可运行 |
| S2 | 用户对旧 CLI-backed skill 项目运行 `skillcli audit --json` | 若项目有 `scripts/sync_skill.sh` 但 CLI 缺少 `sync-skill`，返回 `warn` 和补齐建议 |
| S3 | 用户运行 `skillcli update --no-sync-skill` | 仍只更新 `skillcli` release，不写 agent skill homes |

## 5. 功能需求

| ID | 需求 | 验收方式 | 状态 |
|---|---|---|---|
| R1 | 生成项目包含 `<cli> sync-skill` 子命令 | 单测检查生成 CLI 文本和 help 输出 | 完成 |
| R2 | `<cli> sync-skill` 转发 `--targets`, `--force`, `--dry-run` 到脚本 | 临时生成项目执行 dry-run；代码审查确认 CLI 不复制同步逻辑 | 完成 |
| R3 | 生成脚本支持 `--targets`, `--force`, `--dry-run` | 生成项目 dry-run smoke 和生成项目 tests | 完成 |
| R4 | audit 对缺失业务 CLI sync 命令给 warn 和 recommendation | 单测构造旧式 CLI 模块并断言 finding | 完成 |
| R5 | 文档合同同步更新 | `docdev audit` 和人工检查相关文档 | 完成 |

## 6. 约束与不变式

1. **#1**: `scripts/sync_skill.sh` 是生成项目的唯一 sync 实现；`<cli> sync-skill`
   只能薄封装它。
2. **#2**: `skillcli update --sync-skill/--no-sync-skill` 现有语义保持不变。
3. **#3**: audit 对旧项目缺少 `<cli> sync-skill` 的判断是 warning，不是 error。

## 7. 兼容性与默认行为

| 场景 | 默认行为 |
|---|---|
| 旧生成项目没有 `<cli> sync-skill` | audit 返回 warn 和修复建议；项目不因此 audit 失败 |
| 新生成项目直接运行 `scripts/sync_skill.sh` | 仍可使用脚本入口，并获得同一套 targets/force/dry-run 行为 |
| `skillcli update --no-sync-skill` | 保持 release update 跳过 skill target 刷新的语义 |

## 8. 验收标准

1. 新生成项目包含 `<cli> sync-skill`，且 help 和 dry-run smoke 可观察。
2. audit 能发现旧项目缺少 `<cli> sync-skill` 并给出 warn/recommendation。
3. 单测、CLI help、临时生成项目、audit、`docdev audit` 通过。

## 9. 开放问题

| ID | 问题 | 当前判断 | 是否阻塞实现 |
|---|---|---|---|
| Q1 | 生成脚本默认 sync 哪些 targets | 保持旧模板无参数时只写 Codex；多目标通过 `--targets` 显式选择 | 否 |
