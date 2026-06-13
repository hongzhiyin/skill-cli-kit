# ROADMAP - Native Installer Distribution

> 本文件追踪本次需求做到哪一步。它承接 SPEC 的验收标准，记录调研、门禁、任务和验证结果。

## 0. 当前状态

**阶段 / Phase**: 验证与发布准备
**当前 Step / Current Step**: Step 5 - 验证与收尾
**ARCHITECTURE 省略理由 / Architecture Omission Reason**: 不省略；本需求新增 release packaging、native install、update、uninstall 数据流，见 `ARCHITECTURE.md`。

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
| R-1 | 现有 CLI 入口 | `skillcli update <project>` 已用于源码 checkout 生命周期 | `src/skill_cli_kit/cli.py` | native release update 需要独立命令，避免语义冲突 |
| R-2 | 现有安装形态 | `install_cli.sh` 和 `sync_skill.sh` 面向本机源码仓库 | `scripts/install_cli.sh`, `scripts/sync_skill.sh` | release install 需要把源码、skill、脚本打进 artifact |
| R-3 | docs-driven-dev 参考 | native installer 使用 release asset、manifest、checksum 和 current symlink | `/Users/chihoyo/Project/docs-driven-dev/scripts/install_remote.sh` | 采用相同大方向，但保留 `skillcli` 自身命名与 env |
| R-4 | 自举定位 | 用户希望 `skill-cli-kit` 自己的项目结构成为后续 CLI 化其他 skill 的参考 | 本工作包 SPEC §1 | 本次优先改造本仓库自身结构 |

## 3. Step 状态总览

| Step | 内容 | 状态 |
|---|---|---|
| 0 | 建立需求工作包 | 完成 |
| 1 | 澄清需求与范围 | 完成 |
| 2 | 调研既有实现 | 完成 |
| 3 | 形成并确认方案 | 完成 |
| 4 | 实施代码与测试 | 完成 |
| 5 | 验证与收尾 | 进行中 |

---

## Step 0 - 建立需求工作包

**Goal**: 创建 SPEC / ROADMAP / DECISIONS / ARCHITECTURE。

**Tasks**:
- [x] 初始化工作包文档
- [x] 记录 ARCHITECTURE 需要及理由

**Acceptance**:
1. 工作包目录存在，且文档结构清晰。

---

## Step 1 - 澄清需求与范围

**Goal**: 把粗略需求转成可验收的行为描述。

**Tasks**:
- [x] 补全 SPEC 一句话目标
- [x] 补全范围 / 非目标
- [x] 列出开放问题

**Acceptance**:
1. 用户确认 SPEC 的目标、范围和非目标。

---

## Step 2 - 调研既有实现

**Goal**: 确认现有 source-checkout lifecycle、wrapper sync 和 docs contract。

**Tasks**:
- [x] 阅读 source-of-truth docs
- [x] 阅读 CLI parser 与脚本入口
- [x] 参考 docs-driven-dev native install 形态
- [x] 运行现有 audit / test 基线

**Acceptance**:
1. 方案不破坏现有 `skillcli update <project>` 与 skill wrapper 同步流程。

---

## Step 3 - 形成并确认方案

**Goal**: 决定把 native release layer 放在自举参考实现内。

**Tasks**:
- [x] 记录 D-001
- [x] 在主 docs 中记录 D-008
- [x] 明确 `native-update` 与 `update <project>` 的边界

**Acceptance**:
1. 主文档和本工作包都说明为什么选择 GitHub Releases/native installer。

---

## Step 4 - 实施代码与测试

**Goal**: 落地 packaging、install、update、uninstall 和对应文档。

**Tasks**:
- [x] 新增 `scripts/package_release.sh`
- [x] 新增 `scripts/install_remote.sh`
- [x] 新增 `scripts/install_remote.ps1`
- [x] 新增 `skillcli native-update`
- [x] 新增 `skillcli uninstall`
- [x] 更新 README、skill 说明和四件套文档

**Acceptance**:
1. 本仓库可作为 native-install reference implementation 阅读和执行。

---

## Step 5 - 验证与收尾

**Goal**: 证明本地 release asset 和 native installer 可用，并准备 GitHub public repo / release。

**Tasks**:
- [x] 运行单元测试
- [x] 打包本地 release assets
- [x] 使用 `file://` release assets 做 native install smoke
- [x] 验证 `native-update` 和 `uninstall --dry-run`
- [x] 运行 `skillcli audit`
- [x] 运行 `docdev audit`
- [ ] commit 并按用户要求创建公开 GitHub 仓库

**Acceptance**:
1. SPEC §8 的验收项全部有记录。

## 4. 验证记录

| 验收项 | 验证方式 | 结果 | 备注 |
|---|---|---|---|
| SPEC-1 | `python3 -m unittest discover -s tests` | 通过 | 6 tests OK |
| SPEC-2 | `scripts/package_release.sh --out /private/tmp/skillcli-release-assets-0.1.0` | 通过 | 产出 tarball、sha256、manifest、Unix installer、PowerShell installer |
| SPEC-3 | `SKILLCLI_RELEASE_BASE_URL=file:///private/tmp/skillcli-release-assets-0.1.0 scripts/install_remote.sh --no-sync-skill` | 通过 | installed version 0.1.0 under `/private/tmp/skillcli-smoke-root-0.1.0/releases/0.1.0` |
| SPEC-4 | native install 后执行 `skillcli --version` / `doctor --json` / `native-update` / `uninstall --dry-run` | 通过 | version `0.1.0`; source root 指向 native release root |
| SPEC-5 | `PYTHONPATH=src python3 -m skill_cli_kit.cli audit /Users/chihoyo/Project/skill-cli-kit --json` | 通过 | 0 error / 0 warn |
| SPEC-6 | `/Users/chihoyo/.local/bin/docdev audit /Users/chihoyo/Project/skill-cli-kit` | 通过 | No findings |

## 5. 风险与后续

| ID | 风险 / 后续 | 影响 | 处理 |
|---|---|---|---|
| F-1 | `skillcli init` 尚未自动生成完整 native release layer | 后续 CLI 化其他 skill 时仍需先参考本仓库手动迁移 | 后续处理 |
| F-2 | GitHub release install 需要真实 release assets 才能完整远程验证 | 本地 `file://` smoke 不能覆盖公网下载链路 | 发布后补远程 smoke |
| F-3 | Windows installer 当前以脚本审阅为主，尚未在 Windows 机器实测 | Windows 用户可能遇到 PowerShell/路径差异 | 后续处理 |
