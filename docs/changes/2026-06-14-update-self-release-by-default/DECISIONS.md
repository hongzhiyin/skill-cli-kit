# DECISIONS - Update Self Release By Default

> 本文件记录这次需求中为什么这么选。只写真实取舍，不为机械改动补仪式性决策。

## 维护规则

1. `D-XXX` 在本工作包内单调递增，不复用。
2. 每条记录 2-3 个真实选项；不要编造凑数选项。
3. 写清选择、理由、风险和对应文件。
4. 决策被推翻时，新增一条 D-XXX 引用旧决策，旧决策保留原文。

---

## D-001 - Make `update` the self-release update entry

**日期 / Date**: 2026-06-14

**上下文 / Context**:
v0.1.0 增加了 `skillcli native-update`，但用户指出 `update` 不需要额外暴露 `native`。命令应该以用户意图命名：更新 `skillcli` 自身，或更新一个显式传入的项目。

**选项 / Options**:
- A. 保留 `native-update` 为主入口 - 实现改动最少，但暴露安装机制细节。
- B. 让 `skillcli update` 始终更新自身，另起 `update-project` 更新项目 - 命名清楚，但破坏已有 `skillcli update <project>` contract。
- C. 让 `skillcli update` 无 project 时更新自身，有 project 时更新项目，并隐藏保留 `native-update` alias。

**选择 / Chosen**: C

**理由 / Rationale**:
- `skillcli update` 是用户自然会尝试的 self-update 命令。
- 显式 project path 足以区分 source checkout lifecycle，且保留已有 `skillcli update <project>` 用法。
- 隐藏 alias 给 v0.1.0 用户留出过渡期，同时避免新文档继续推广 `native-update`。

**风险 / Risks**:
- 旧默认 `skillcli update` 等价 `skillcli update .` 的行为会改变。缓解：source lifecycle flags 在无 project 时直接报错，并提示显式项目路径。
- 两套 update 选项共用一个 subcommand，可能误混。缓解：release-only options 和 project path 混用时报错。

**对应代码 / 文档**:
- SPEC §3, §5, §7
- ROADMAP Step 4
- ARCHITECTURE §3
- `src/skill_cli_kit/cli.py`
- `tests/test_cli.py`
