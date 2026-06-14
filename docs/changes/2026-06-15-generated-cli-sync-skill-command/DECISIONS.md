# DECISIONS - Generated CLI Sync-Skill Command

> 本文件记录这次需求中为什么这么选。只写真实取舍，不为机械改动补仪式性决策。

## 维护规则

1. `D-XXX` 在本工作包内单调递增，不复用。
2. 每条记录 2-3 个真实选项；不要编造凑数选项。
3. 写清选择、理由、风险和对应文件。
4. 决策被推翻时，新增一条 D-XXX 引用旧决策，旧决策保留原文。

---

## D-001 - 生成 CLI 只薄封装 sync 脚本

**日期 / Date**: 2026-06-15

**上下文 / Context**:
生成项目已经有 `scripts/sync_skill.sh`，但业务 CLI 缺少显式
`sync-skill` 入口。用户要求新增 CLI 入口，同时明确不要复制第二套同步逻辑。

**选项 / Options**:
- A. 继续只提供脚本入口 - 最小变更，但 agent 不容易从业务 CLI 发现 sync 生命周期。
- B. 在生成 CLI 中重新实现 target resolution、复制和 wrapper 写入 - CLI 入口完整，但和脚本形成两套同步逻辑。
- C. 生成 `<cli> sync-skill`，仅负责参数解析并执行 `scripts/sync_skill.sh`。

**选择 / Chosen**: C

**理由 / Rationale**:
- 满足“业务 CLI 有显式 sync-skill 子命令”。
- 保持 `scripts/sync_skill.sh` 是唯一同步实现，降低模板和旧项目后续漂移风险。
- audit 可以用结构性 warning 指引旧项目补齐，不需要执行项目 sync 命令。

**风险 / Risks**:
- audit 只能通过源码文本判断是否存在命令和脚本委托，无法证明项目运行时行为完全正确。
  缓解：保留 warning 级别，并用生成项目 dry-run 和单测覆盖标准模板。

**对应代码 / 文档**:
- SPEC §6 #1
- ARCHITECTURE §3
- ROADMAP Step 4
- `src/skill_cli_kit/cli.py`
- `tests/test_cli.py`
