# SPEC - Windows structure parity review

> 本文件描述本次需求应该满足什么。它不写实现细节、不追踪进度、不解释历史取舍。

## 0. 状态

| 字段 | 内容 |
|---|---|
| 状态 | v0.1.3 发布准备中，待 Windows 真机 release smoke |
| 需求来源 | 用户请求：参考 `/Users/chihoyo/Project/docs-driven-dev` 在 Windows 上跑通后的当前文件结构，判断是否需要优化 `/Users/chihoyo/Project/skill-cli-kit` |
| 工作包目录 | `docs/changes/2026-06-16-windows-structure-parity-review/` |
| 最后更新 | 2026-06-16 |

## 1. 一句话目标

让 `skill-cli-kit` 吸收 `docs-driven-dev` Windows 真机安装经验中已经验证的结构改进，优先补齐跨机器 native install / update 的 Windows 裸命令路径，同时避免一次性重构掉现有生成器和 sync 合同。

## 2. 背景与问题

- 当前行为：`skill-cli-kit` 已有 native release、Unix remote installer、PowerShell remote installer、`skillcli update`、`skillcli uninstall`、`skillcli sync-skill` 和生成项目 `<cli> sync-skill` 合同；`skillcli audit /Users/chihoyo/Project/skill-cli-kit --json` 当前无 findings。
- 参考项目状态：`docs-driven-dev` 已到 Step 6j，`v0.1.8` Windows installer follow-up 已发布；Windows 真机已确认 GitHub latest install 后新终端可运行 `docdev -v`。
- 问题：`skill-cli-kit/scripts/install_remote.ps1` 仍只生成 `skillcli.ps1`，没有 `skillcli.cmd`、User PATH 管理、`-NoModifyPath`、PATH 写后诊断，也没有 Windows 平台的 `skillcli update` PowerShell dispatch；其默认 PowerShell sync 调用还使用未引用的逗号参数。
- 期望收益：Windows 用户安装 `skillcli` 后可以获得与 `docdev` 类似的裸命令体验；agent 和用户仍能保持 GitHub Releases / native installer 优先，不被 npm-first 或手写 alias 牵走。

## 3. 范围

### 3.1 本次要做

- 对照 `docs-driven-dev` 当前文件结构、Windows installer packet、root docs、installer/update 脚本和 audit 输出，形成 `skill-cli-kit` 的优化判断。
- 推荐一个最小实现切片：补齐 `skillcli` 自身 Windows native installer parity。
- 为后续实现列出需要修改的 production files、测试和验收命令。
- 在实现门禁前停止，等待用户确认后再改 production code。

### 3.2 本次不做

- 不在本轮直接修改 `src/skill_cli_kit/cli.py`、`scripts/install_remote.ps1`、README、root docs 或 tests。
- 不把 `skill-cli-kit` 改成 npm-first 分发，也不要求用户安装 Node.js。
- 不在本轮引入 `skillcli.exe` 二进制打包；严格无 shim 的 Windows 二进制是后续可选增强。
- 不在同一切片里推翻现有 installed skill-local `bin/skillcli` invariant；这个 sync 模型需要单独决策，因为它影响 SPEC invariant #3。
- 不在本轮把生成项目 scaffold 扩展为完整 native release scaffold；先把 `skill-cli-kit` 自身 reference path 硬化。

## 4. 用户场景 / 使用流程

| 场景 ID | 触发条件 | 期望结果 |
|---|---|---|
| S1 | Windows 用户通过 GitHub latest release 安装 `skillcli` | 新 PowerShell / CMD 终端可运行 `skillcli -v` 或 `skillcli --version` |
| S2 | 已安装用户在 Windows 上运行 `skillcli update` | CLI 选择 PowerShell remote installer，而不是 Unix shell installer |
| S3 | 受管 Windows 环境不希望修改 PATH | 用户可选择不修改 PATH，并保留完整 `skillcli.ps1` 路径 fallback |
| S4 | installer 自动 sync skill | PowerShell 把 targets 作为单个逗号分隔参数传给 `skillcli sync-skill` |
| S5 | 维护者继续评估更深结构优化 | module split、generated PowerShell scripts、native release scaffold 作为后续独立切片处理 |

## 5. 功能需求

| ID | 需求 | 验收方式 | 状态 |
|---|---|---|---|
| R1 | 工作包必须记录 `docs-driven-dev` 与 `skill-cli-kit` 的文件结构差异和当前 audit 信号 | ROADMAP research log | 完成 |
| R2 | 推荐方案必须明确 Windows native installer parity 的最小生产变更范围 | ROADMAP implementation gate | 完成 |
| R3 | 推荐方案必须保护现有 checksum、native install root、self-update、generated sync-skill delegation 合同 | SPEC invariants；后续 tests | 完成 |
| R4 | 推荐方案必须把 installed skill-local wrapper 模型作为单独待确认取舍，而不是随 Windows parity 静默修改 | 开放问题 Q2；DECISIONS D-001 | 完成 |
| R5 | 实现前必须等待用户确认 | ROADMAP gate | 完成 |

## 6. 约束与不变式

1. **#1**: Native installer 仍必须在 sha256 校验通过前不得切换 active `current` release。
2. **#2**: `skillcli update` 不带 project path 时仍表示更新 installed `skillcli` release；source checkout update 仍必须传显式项目路径。
3. **#3**: GitHub Releases / native installer 仍是默认普通用户安装方向；不新增 package-index 依赖。
4. **#4**: Generated `<cli> sync-skill` 仍必须委托 `scripts/sync_skill.sh`，不能复制 sync 实现。
5. **#5**: 本轮不得静默移除 `skillcli sync-skill` 生成 installed skill-local `bin/skillcli` 的现有合同；若要改，必须另开决策。

## 7. 兼容性与默认行为

| 场景 | 默认行为 |
|---|---|
| 现有 Unix installer | 保持 `~/.local/bin/skillcli` launcher、checksum、file:// smoke 和 `--no-sync-skill` 行为 |
| 现有 PowerShell installer | 后续实现可新增 `skillcli.cmd` 与 PATH 管理；`skillcli.ps1` 继续保留 |
| 现有 `skillcli update <project>` | 保持 source checkout lifecycle，不受 self-update Windows dispatch 影响 |
| 现有 installed skill targets | 本轮不改变 `bin/skillcli` 生成规则 |
| 当前 generated projects | 本轮不要求重新生成或迁移 |

## 8. 验收标准

1. Change packet 清楚说明是否需要优化：需要，优先补 Windows native installer parity。
2. 实现方案列出 production files、docs、tests、验证命令和剩余风险。
3. `docdev audit /Users/chihoyo/Project/skill-cli-kit` 通过。
4. 后续用户确认后，production 实现必须通过 unit tests、package release smoke、`skillcli audit` 和 `docdev audit`。

## 9. 开放问题

| ID | 问题 | 当前判断 | 是否阻塞实现 |
|---|---|---|---|
| Q1 | 是否按推荐方案先实现 `skillcli` Windows native installer parity？ | 推荐做；这是最直接继承 `docs-driven-dev` Windows 真机反馈的优化 | 是 |
| Q2 | `skill-cli-kit` 是否应像 `docs-driven-dev` 后续那样让 sync 只同步 skill 内容、移除 installed skill-local `bin/skillcli`？ | 暂不建议混入本轮；当前 SPEC invariant #3 仍要求 installed skill copies include `bin/skillcli` | 否，本轮先不做 |
| Q3 | 是否要把 generated project scaffold 也扩展出 PowerShell source install / update scripts 和 native release scripts？ | 推荐作为 Windows parity 后的后续 Step；先硬化 reference project | 否 |
| Q4 | 是否要像 `docs-driven-dev` 一样拆分 `src/skill_cli_kit/cli.py`？ | 推荐后续做，但排在 Windows installer parity 之后 | 否 |
