# ROADMAP - Generated CLI Sync-Skill Command

> 本文件追踪本次需求做到哪一步。它承接 SPEC 的验收标准，记录调研、门禁、任务和验证结果。

## 0. 当前状态

**阶段 / Phase**: 完成
**当前 Step / Current Step**: Step 5 complete - 验证与收尾完成
**ARCHITECTURE 省略理由 / Architecture Omission Reason**: 不省略；本需求新增生成项目 CLI 子命令和 audit 检查，影响命令接口和模板结构。

## 1. Gates

### Pre-Implementation Gate

- [x] 用户目标已用一句话确认
- [x] 范围和非目标已写入 SPEC
- [x] 现有实现、调用点、测试和配置已调研
- [x] 关键约束 / 不变式已写入 SPEC
- [x] 需要的 DECISIONS 条目已记录或标记为阻塞
- [x] 实现步骤和验收方式已写清
- [x] 用户已确认实现方案（用户明确要求“请做”并列出实现与验证项）

### Completion Gate

- [x] 所有实施任务完成或有明确跳过理由
- [x] 验收标准逐条验证
- [x] 文档与最终实现一致
- [x] 剩余风险和后续工作已记录

## 2. 调研记录

| ID | 主题 | 发现 | 证据 / 文件 | 结论 |
|---|---|---|---|---|
| R-1 | 生成 CLI 模板 | 生成的 `src/<package>/cli.py` 只有 `status` 和 `doctor` | `src/skill_cli_kit/cli.py` SCAFFOLD_FILES | 需要新增 generated `sync-skill` parser 和 handler |
| R-2 | 生成 sync 脚本 | 现有模板只写 Codex target，且只用首个 `--force` 判断 replacement | `src/skill_cli_kit/cli.py` 的 `scripts/sync_skill.sh` 模板 | 要补 `--targets`, `--force`, `--dry-run` |
| R-3 | audit 现状 | audit 检查 sync 脚本是否生成 installed `bin/<cli>`，但不检查业务 CLI sync 命令 | `audit_project()` | 增加 warn，不设为 error |
| R-4 | update 语义 | `update --sync-skill/--no-sync-skill` 属于 release update options；项目 update 仍走 explicit project path | `cmd_update()`, `cmd_release_update()` | 本次不改 update dispatcher |

## 3. Step 状态总览

| Step | 内容 | 状态 |
|---|---|---|
| 0 | 建立需求工作包 | 完成 |
| 1 | 澄清需求与范围 | 完成 |
| 2 | 调研既有实现 | 完成 |
| 3 | 形成并确认方案 | 完成 |
| 4 | 实施代码与测试 | 完成 |
| 5 | 验证与收尾 | 完成 |

---

## Step 0 - 建立需求工作包

**Goal**: 创建 SPEC / ROADMAP / DECISIONS / ARCHITECTURE。

**Tasks**:
- [x] 初始化工作包文档
- [x] 记录 ARCHITECTURE 创建原因

**Acceptance**:
1. 工作包目录存在，且文档结构清晰。

## Step 1 - 澄清需求与范围

**Goal**: 把用户请求转成可验收的行为描述。

**Tasks**:
- [x] 补全 SPEC 一句话目标
- [x] 补全范围 / 非目标
- [x] 列出开放问题

**Acceptance**:
1. 目标、范围、非目标和不变式可直接映射到测试与文档更新。

## Step 2 - 调研既有实现

**Goal**: 找到模板、audit 和测试的最小改动面。

**Tasks**:
- [x] 阅读 `docs/SPEC.md`, `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`
- [x] 阅读 `skill/SKILL.md`
- [x] 阅读生成器模板和 audit 检查
- [x] 阅读现有 tests 和 pattern reference

**Acceptance**:
1. 调研记录能说明每个将修改的文件为什么相关。

## Step 3 - 形成并确认方案

**Goal**: 选择不复制 sync 逻辑的实现方案。

**Tasks**:
- [x] 记录 DECISIONS D-001
- [x] 在 SPEC 写入不变式
- [x] 明确 update release flags 非目标

**Acceptance**:
1. 方案满足用户列出的四条目标约束。

## Step 4 - 实施代码与测试

**Goal**: 更新模板、audit、文档和测试。

**Tasks**:
- [x] 更新生成 CLI 模板，新增 `<cli> sync-skill`
- [x] 更新生成 sync 脚本模板，支持 `--targets`, `--force`, `--dry-run`
- [x] 更新 audit warning 和 recommendation
- [x] 更新根 docs、README、skill 指南和 pattern reference
- [x] 添加生成命令和 audit 缺失项测试

**Acceptance**:
1. 代码和文档都体现同一条 contract：CLI 入口薄封装脚本实现。

## Step 5 - 验证与收尾

**Goal**: 跑完用户指定验证并回填结果。

**Tasks**:
- [x] 单测
- [x] CLI help
- [x] 临时生成项目
- [x] audit
- [x] docdev audit
- [x] 回填 verification table 和主 ROADMAP 状态

**Acceptance**:
1. 验证表中每条 SPEC 验收都有结果。

## 4. 验证记录

| 验收项 | 验证方式 | 结果 | 备注 |
|---|---|---|---|
| SPEC-1 | `python3 -m unittest discover -s tests` | 通过 | 10 tests OK |
| SPEC-2 | `PYTHONPATH=src python3 -m skill_cli_kit.cli --help` | 通过 | 顶层 help 显示 `sync-skill` |
| SPEC-3 | 临时目录运行 `skillcli init`，再执行生成 CLI `--help` 与 `sync-skill --dry-run` | 通过 | `/private/tmp/skillcli-sync-skill-smoke.PXkCMR/demo-skill`; help 显示 `sync-skill`; dry-run 输出 Codex 和 Agents targets |
| SPEC-4 | 单测构造旧式项目并运行 `skillcli audit --json` | 通过 | `test_audit_warns_when_cli_sync_skill_command_is_missing` 断言 sync warning 和 recommendation |
| SPEC-5 | `skillcli audit /Users/chihoyo/Project/skill-cli-kit --json` | 通过 | 隔离 `HOME=/private/tmp/skillcli-audit-home` 时 warn0；普通 HOME 下 ok true 但提示已安装 Codex/Agents skill 与 source 不同 |
| SPEC-6 | `docdev audit /Users/chihoyo/Project/skill-cli-kit` | 通过 | No findings |

## 5. 风险与后续

| ID | 风险 / 后续 | 影响 | 处理 |
|---|---|---|---|
| F-1 | audit 通过文本启发式识别 CLI sync command 和脚本委托 | 可能对高度自定义项目给出 advisory warning | 接受；warning 不阻塞 audit |
