# DECISIONS - Windows structure parity review

> 本文件记录这次需求中为什么这么选。只写真实取舍，不为机械改动补仪式性决策。

## 维护规则

1. `D-XXX` 在本工作包内单调递增，不复用。
2. 每条记录 2-3 个真实选项；不要编造凑数选项。
3. 写清选择、理由、风险和对应文件。
4. 决策被推翻时，新增一条 D-XXX 引用旧决策，旧决策保留原文。

---

## D-001 - Step 3 - Prioritize Windows native installer parity

**日期 / Date**: 2026-06-16

**上下文 / Context**:
`docs-driven-dev` 在 Windows 上的 latest installer 已经跑通，并把真实反馈沉淀到 `docdev.cmd`、User PATH、`-NoModifyPath`、platform update dispatch 和 quoted sync targets。`skill-cli-kit` 当前 audit 干净，但 PowerShell remote installer 和 self-update dispatch 还停在更早的 reference shape。

**选项 / Options**:
- A. 只记录调研，不做结构优化 - 风险最低，但会让 `skill-cli-kit` 继续落后于它正在参考的 `docs-driven-dev` Windows install 经验。
- B. 先补 `skillcli` Windows native installer parity - 直接改善跨机器安装体验，范围可控，但需要更新脚本、CLI dispatch、docs 和 tests。
- C. 同时重构 sync 模型、module split、generated Windows scripts 和 native scaffold - 能一次性追平更多结构，但会把多个独立取舍混在一起，增加回归风险。

**选择 / Chosen**: B

**理由 / Rationale**:
- Windows 裸命令和 update dispatch 是用户已经在 `docs-driven-dev` 真机验证过的最高价值反馈。
- 这个切片能复用现有 native release 合同，不改变 `skillcli update <project>` 和 generated `<cli> sync-skill` 的核心不变式。
- 将 sync 模型和 monolithic `cli.py` 拆分留给后续，避免静默推翻 SPEC invariant #3。

**风险 / Risks**:
- `skillcli.cmd` 仍是 installer-owned shim，不是严格二进制；如果需要 `skillcli.exe`，应另开 packaging 决策。
- User PATH 写入在受管 Windows 环境可能失败；需要保留 `-NoModifyPath` 和清晰诊断。
- 本轮只做 static/unit/package smoke；最终仍需要 Windows live smoke 才能确认新终端裸命令体验。

**对应代码 / 文档**:
- SPEC §3, §6, §9
- ROADMAP Step 3
- ARCHITECTURE §3
- `scripts/install_remote.ps1`
- `src/skill_cli_kit/cli.py`
- `tests/test_cli.py`
