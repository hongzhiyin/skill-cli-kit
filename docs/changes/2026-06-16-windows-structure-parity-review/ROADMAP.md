# ROADMAP - Windows structure parity review

> 本文件追踪本次需求做到哪一步。它承接 SPEC 的验收标准，记录调研、门禁、任务和验证结果。

## 0. 当前状态

**阶段 / Phase**: 发布准备中
**当前 Step / Current Step**: Step 5 - 本机验证完成，准备发布 v0.1.3
**ARCHITECTURE 省略理由 / Architecture Omission Reason**: 不省略。本需求涉及 Windows native installer、launcher、PATH、self-update dispatch、sync 参数和后续 module boundary 的结构判断。

## 1. Gates

### Pre-Implementation Gate

- [x] 用户目标已用一句话确认
- [x] 范围和非目标已写入 SPEC
- [x] 现有实现、调用点、测试和配置已调研
- [x] 关键约束 / 不变式已写入 SPEC
- [x] 需要的 DECISIONS 条目已记录或标记为阻塞
- [x] 实现步骤和验收方式已写清
- [x] 用户已确认实现方案

### Completion Gate

- [x] 所有实施任务完成或有明确跳过理由
- [x] 验收标准逐条验证
- [x] 文档与最终实现一致
- [x] 剩余风险和后续工作已记录

## 2. 调研记录

| ID | 主题 | 发现 | 证据 / 文件 | 结论 |
|---|---|---|---|---|
| R-1 | `skill-cli-kit` 当前结构 | 根结构已具备 `src/`、`skill/`、`scripts/`、`tests/`、`docs/`、native installer 和 release packager；`skillcli audit` 无 findings | `rg --files`；`skillcli audit /Users/chihoyo/Project/skill-cli-kit --json` | 当前不是结构损坏，而是需要吸收 Windows installer 经验 |
| R-2 | `docs-driven-dev` 当前状态 | 已完成 Step 6j，`v0.1.8` Windows installer follow-up published；最新 change packet 是 `2026-06-15-windows-bare-command-install` | `docdev status /Users/chihoyo/Project/docs-driven-dev` | 可作为本轮 Windows parity 的直接参考 |
| R-3 | 文件结构差异 | `docs-driven-dev` 有 `scripts/install.ps1`、`install_cli.ps1`、`update_cli.ps1`，且 `src/docs_driven_dev/` 已拆成 `commands.py`、`paths.py`、`release.py`、`sync.py`、`audit.py`、`templates.py`；`skill-cli-kit` 仍主要集中在 `src/skill_cli_kit/cli.py` | 两个项目的 `rg --files`；`wc -l` | PowerShell source scripts 和 module split 是后续优化候选，不建议和本轮 installer parity 混做 |
| R-4 | `skill-cli-kit` PowerShell remote installer | 当前只写 `skillcli.ps1`；没有 `skillcli.cmd`、`-NoModifyPath`、User PATH 更新、PATH 写后诊断；默认 sync 调用是 `--targets codex,agents` 未引用 | `scripts/install_remote.ps1` | Windows 裸命令体验尚未达到 `docs-driven-dev` 已验证水位 |
| R-5 | `docs-driven-dev` PowerShell remote installer | 写 `docdev.ps1` 和 `docdev.cmd`；支持 `-NoModifyPath`；默认加入 User PATH 并验证；sync 调用引用 `--targets "codex,cursor,agents,claude"` | `/Users/chihoyo/Project/docs-driven-dev/scripts/install_remote.ps1` | 这些改动可以以 `skillcli` 命名移植，targets 保持当前 `codex,agents` 默认 |
| R-6 | self-update dispatch | `skill-cli-kit` 的 `cmd_release_update()` 固定调用 `scripts/install_remote.sh`；`docs-driven-dev` 在 Windows 下调用 `powershell.exe ... install_remote.ps1`，Unix 下调用 shell installer | `src/skill_cli_kit/cli.py`; `/Users/chihoyo/Project/docs-driven-dev/src/docs_driven_dev/release.py` | `skillcli update` 在 Windows 上需要平台分支 |
| R-7 | sync model divergence | `skill-cli-kit` SPEC invariant #3 要求 installed skill copies include `bin/skillcli`；`docs-driven-dev` 后续已把普通 CLI 入口收敛到 native launcher / PATH，sync 只同步 skill 内容 | `docs/SPEC.md`; `/Users/chihoyo/Project/docs-driven-dev/docs/DECISIONS.md` D-025 | 不应在 Windows installer parity 中静默改 sync 模型 |
| R-8 | `docs-driven-dev` 被 `skillcli audit` 的信号 | `skillcli audit /Users/chihoyo/Project/docs-driven-dev --json` 报 9 个 warn：缺 `docdev sync-skill` CLI wrapper，已安装 skill 与 source drift，缺 `bin/docdev` | `skillcli audit /Users/chihoyo/Project/docs-driven-dev --json` | 这说明 `skillcli` 当前审计规则仍偏向旧 wrapper 模型；后续需单独校准 audit 规则 |

## 3. Step 状态总览

| Step | 内容 | 状态 |
|---|---|---|
| 0 | 建立需求工作包 | 完成 |
| 1 | 澄清需求与范围 | 完成 |
| 2 | 调研既有实现 | 完成 |
| 3 | 形成并确认方案 | 完成 |
| 4 | 实施代码与测试 | 完成 |
| 5 | 验证与收尾 | 完成，剩余 Windows 真机 release smoke |

---

## Step 0 - 建立需求工作包

**Goal**: 创建 SPEC / ROADMAP / DECISIONS / ARCHITECTURE，并决定本轮是否需要结构文档。

**Tasks**:
- [x] 初始化工作包文档
- [x] 记录 ARCHITECTURE 需要及理由

**Acceptance**:
1. 工作包目录存在，且文档结构清晰。

---

## Step 1 - 澄清需求与范围

**Goal**: 把“参考 docs-driven-dev 结构看是否要优化”转成可验收的结构评审。

**Tasks**:
- [x] 补全 SPEC 一句话目标
- [x] 补全范围 / 非目标
- [x] 列出开放问题

**Acceptance**:
1. SPEC 能回答本轮是否建议优化，以及建议先做哪一块。

---

## Step 2 - 调研既有实现

**Goal**: 对照两个项目当前文件结构、docs、脚本、CLI dispatch 和 audit 输出。

**Tasks**:
- [x] 读取 `skill-cli-kit` root SPEC / ROADMAP / ARCHITECTURE / DECISIONS。
- [x] 对照 `docs-driven-dev` root docs 和 Windows bare command change packet。
- [x] 对比两个项目的 file list、installer scripts、release update dispatch、tests coverage 和 audit 输出。
- [x] 记录 module split、PowerShell source scripts、installed wrapper 模型的差异。

**Acceptance**:
1. 调研记录列出当前缺口、可复用结构和不应混做的后续优化。

---

## Step 3 - 形成并确认方案

**Goal**: 在实现前确认最小优化切片。

**推荐方案**:
先做 `skillcli` Windows native installer parity，不同时重构 sync 模型或拆分 monolithic CLI。

**Implementation Plan after approval**:
- [ ] 更新 root `docs/SPEC.md`：增加 Windows native layout、`skillcli.cmd`、User PATH / `-NoModifyPath`、platform update dispatch 规则。
- [ ] 更新 root `docs/ARCHITECTURE.md`：补 Windows PowerShell install flow、cmd launcher、PATH 配置、update dispatch。
- [ ] 追加 root `docs/DECISIONS.md` D-011：记录 installer-owned Windows command shim 的取舍。
- [ ] 更新 root `docs/ROADMAP.md`：追加 Step 4e 或等价小步，写清验收。
- [ ] 修改 `scripts/install_remote.ps1`：生成 `skillcli.ps1` 和 `skillcli.cmd`；新增 `-NoModifyPath`；默认添加 / 验证 User PATH；引用 sync targets。
- [ ] 修改 `src/skill_cli_kit/cli.py`：让 release self-update 在 Windows 上调用 PowerShell installer，在 Unix 上保持 shell installer；保留 project update path。
- [ ] 更新 `tests/test_cli.py`：覆盖 Windows installer static contract、quoted targets、PowerShell update dispatch、docs wording。
- [ ] 更新 README 和 `skill/SKILL.md`：补 Windows install/update 命令、PATH 注意事项和 opt-out。

**Acceptance**:
1. 用户确认后才能修改 production code 和 root source-of-truth docs。已确认。

---

## Step 4 - 实施代码与测试

**Goal**: 让 Windows release install/update 具备 `docs-driven-dev` 已验证的裸命令结构。

**Tasks**:
- [x] 更新 root `docs/SPEC.md`：增加 Windows native layout、`skillcli.cmd`、User PATH / `-NoModifyPath`、platform update dispatch 规则。
- [x] 更新 root `docs/ARCHITECTURE.md`：补 Windows PowerShell install flow、cmd launcher、PATH 配置、update dispatch。
- [x] 追加 root `docs/DECISIONS.md` D-011：记录 installer-owned Windows command shim 的取舍。
- [x] 更新 root `docs/ROADMAP.md`：追加 Step 4e 并写清验收。
- [x] 修改 `scripts/install_remote.ps1`：生成 `skillcli.ps1` 和 `skillcli.cmd`；新增 `-NoModifyPath`；默认添加 / 验证 User PATH；引用 sync targets。
- [x] 修改 `src/skill_cli_kit/cli.py`：让 release self-update 在 Windows 上调用 PowerShell installer，在 Unix 上保持 shell installer；保留 project update path。
- [x] 更新 `tests/test_cli.py`：覆盖 Windows installer static contract、quoted targets、PowerShell update dispatch、docs wording。
- [x] 更新 README 和 `skill/SKILL.md`：补 Windows install/update 命令、PATH 注意事项和 opt-out。

**Acceptance**:
1. Unit tests 覆盖 Windows launcher / PATH / update dispatch 合同。
2. Unix installer / update 行为不回退。
3. Project audit 无 findings。

---

## Step 5 - 验证与收尾

**Goal**: 证明变更没有破坏本机和 release smoke。

**Planned Verification**:
- [x] `python3 -m unittest discover -s tests`
- [x] `./scripts/package_release.sh --out <tmp>`
- [x] `./scripts/install_remote.sh --release-base-url file://<tmp> --install-root <tmp>/root --bin-dir <tmp>/bin --no-sync-skill`
- [x] `PYTHONPATH=src python3 -m skill_cli_kit.cli audit /Users/chihoyo/Project/skill-cli-kit --json`
- [x] `docdev audit /Users/chihoyo/Project/skill-cli-kit`
- [ ] Windows live smoke：发布后在 Windows PowerShell 运行 latest installer 并验证 `skillcli -v`

**Acceptance**:
1. 验收标准逐条验证或留下明确剩余风险。

## 4. 验证记录

| 验收项 | 验证方式 | 结果 | 备注 |
|---|---|---|---|
| SPEC-1 | `docdev new-change windows-structure-parity-review /Users/chihoyo/Project/skill-cli-kit --with-architecture` | 通过 | 已创建工作包 |
| SPEC-2 | `skillcli audit /Users/chihoyo/Project/skill-cli-kit --json` | 通过 | 当前 project audit 无 findings |
| SPEC-3 | `skillcli audit /Users/chihoyo/Project/docs-driven-dev --json` | 通过但有 warn | 发现 sync wrapper / installed wrapper 模型差异 |
| SPEC-4 | `docdev status /Users/chihoyo/Project/docs-driven-dev` | 通过 | Step 6j complete; v0.1.8 Windows installer follow-up published |
| SPEC-5 | `docdev audit /Users/chihoyo/Project/skill-cli-kit` | 通过 | No findings |
| SPEC-6 | `python3 -m unittest discover -s tests` | 通过 | 14 tests OK |
| SPEC-7 | `./scripts/package_release.sh --out /private/tmp/skillcli-release-assets-0.1.3` | 通过 | 生成 `skillcli-0.1.3.tar.gz`、checksum、manifest、Unix / Windows installers |
| SPEC-8 | `./scripts/install_remote.sh --release-base-url file:///private/tmp/skillcli-release-assets-0.1.3 --install-root /private/tmp/skillcli-013-smoke-root --bin-dir /private/tmp/skillcli-013-smoke-bin --no-sync-skill` | 通过 | checksum OK；隔离 launcher 输出 `skillcli 0.1.3` |
| SPEC-9 | `PYTHONPATH=src python3 -m skill_cli_kit.cli audit /Users/chihoyo/Project/skill-cli-kit --json` | 通过 | No findings after installed skill sync |
| SPEC-10 | `/private/tmp/skillcli-win-parity-smoke-bin-20260616/skillcli audit /Users/chihoyo/Project/skill-cli-kit --json` | 通过 | Packaged release CLI audit No findings |
| SPEC-11 | `./scripts/sync_skill.sh --targets codex,cursor,agents,claude --force` | 通过 | Installed skill copies refreshed so audit no longer reports drift |

## 5. 风险与后续

| ID | 风险 / 后续 | 影响 | 处理 |
|---|---|---|---|
| F-1 | Windows PATH 修改可能只影响新终端，或受 Codex / managed environment 限制 | 用户安装后当前终端可能仍找不到 `skillcli` | 复用 `docs-driven-dev` 的写后验证和诊断输出；文档提示重开终端 |
| F-2 | `skillcli.cmd` 是 installer-owned shim，不是严格二进制 | 如果用户要求完全无 shim，需要 `skillcli.exe` 打包 | 本轮接受 shim；二进制打包作为后续 |
| F-3 | PowerShell 逗号参数会被拆分 | 自动 sync 可能失败 | sync targets 必须作为 quoted single string 传给 launcher |
| F-4 | `skillcli` audit 规则仍偏向 installed skill-local wrapper 模型 | 它会把 `docs-driven-dev` 的新 sync 模型报为 warn | 后续单独校准 audit 规则，不混入本轮 |
| F-5 | `src/skill_cli_kit/cli.py` 已接近 1900 行 | 后续 Windows / release 逻辑会让 monolith 更难维护 | 本轮只做小改；后续单开 module split |
| F-6 | 本机无法直接证明 Windows 新终端 PATH 解析 | 需要发布后或复制 assets 到 Windows 做 live smoke | 保留为 release 前后手工验证项 |
