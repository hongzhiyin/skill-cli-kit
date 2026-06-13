# SPEC - Native Installer Distribution

> 本文件描述本次需求应该满足什么。它不写实现细节、不追踪进度、不解释历史取舍。

## 0. 状态

| 字段 | 内容 |
|---|---|
| 状态 | 完成，v0.1.0 public release 已发布 |
| 需求来源 | 2026-06-13 用户要求 `skill-cli-kit` 先把自己做成 native-install 参考实现 |
| 工作包目录 | `docs/changes/2026-06-13-native-installer-distribution/` |
| 最后更新 | 2026-06-13 |

## 1. 一句话目标

让 `skill-cli-kit` 本身可以作为一个可发布、可安装、可更新、可卸载的 native CLI 项目，并把这套结构作为后续把其他 skill 固化为 CLI 的参考样板。

## 2. 背景与问题

- 当前行为：源码仓库已经有 `skillcli` CLI、skill wrapper 同步脚本、docs-driven 四件套和 `skillcli audit`，但主要入口仍假设存在一个源码 checkout。
- 问题：`skill-cli-kit` 的使命是把其他 skill 固化成 CLI；如果它自己没有 native install 的项目形状，后续生成或改造其他 skill 时缺少可直接参考的仓库级样板。
- 期望收益：用户可以从 GitHub Releases 安装 `skillcli`，本仓库可以用自己的 release/install/update/uninstall 结构示范 CLI 化后的目标状态。

## 3. 范围

### 3.1 本次要做

- 增加 release artifact 打包脚本，产出 tarball、checksum、manifest 和远程安装脚本。
- 增加 Unix 和 Windows native installer，使 released CLI 不依赖用户手动 clone 源码仓库。
- 增加 `skillcli native-update`，用于从 release channel 更新 native 安装。
- 增加 `skillcli uninstall`，用于安全移除 native 安装和已同步 skill wrapper。
- 更新 README、skill 说明和 source-of-truth docs，使 `skill-cli-kit` 的自举结构成为可解释的参考实现。

### 3.2 本次不做

- 不把 `skillcli init` 立即改成默认生成完整 native release 工具链；先把本仓库作为经过验证的参考样板。
- 不引入 npm、pipx、Homebrew tap 或系统级包管理发布。
- 不改变 `skillcli update <project>` 的既有含义；它仍然表示更新一个源码 checkout。
- 不要求未明确选择 release install 的本地开发流程访问网络。

## 4. 用户场景 / 使用流程

| 场景 ID | 触发条件 | 期望结果 |
|---|---|---|
| S1 | 用户在新机器执行 GitHub Releases 的 install script | `skillcli` 被安装到用户 bin 目录，并可执行 `skillcli doctor` |
| S2 | 已安装用户执行 `skillcli native-update` | installer 从 release channel 获取 manifest、校验 artifact、切换 `current` |
| S3 | 用户不再需要 native 安装并执行 `skillcli uninstall --yes` | 只移除 `skillcli` 管理的 launcher、release root 和可选 skill wrappers |
| S4 | 开发者需要发布新版本 | `scripts/package_release.sh` 产出可上传到 release 的完整 asset set |

## 5. 功能需求

| ID | 需求 | 验收方式 | 状态 |
|---|---|---|---|
| R1 | release packaging 必须产出 tarball、`.sha256`、`manifest.json`、Unix installer 和 PowerShell installer | 执行 `scripts/package_release.sh --out <tmp>` 并检查 assets | 完成 |
| R2 | Unix installer 必须支持 GitHub release 和 `file://` base URL，并在切换 `current` 前校验 sha256 | 使用本地 `file://` release assets 做 smoke install | 完成 |
| R3 | native launcher 必须通过 released project root 的 `src` 运行 `skill_cli_kit.cli` | smoke install 后执行 `<tmp-bin>/skillcli --version` 和 `doctor` | 完成 |
| R4 | `skillcli native-update` 必须复用 installer 语义，不和 `update <project>` 混淆 | CLI help / smoke command 检查 | 完成 |
| R5 | `skillcli uninstall` 必须默认 dry-run 提示，只有 `--yes` 才实际删除，且避免删除危险目录 | 单测或 dry-run smoke 检查 | 完成 |
| R6 | source-of-truth docs 必须声明 native release contract 和自举参考实现定位 | `docdev audit` | 完成 |

## 6. 约束与不变式

1. **#1**: Native installer 在 sha256 校验通过前不得切换 `current`。
2. **#2**: `skillcli update <project>` 继续表示源码 checkout 生命周期，不得被重解释为 release update。
3. **#3**: uninstall 只能删除 `skill-cli-kit` 自己生成或拥有的路径，不得删除父目录、home 目录、根目录或任意用户路径。
4. **#4**: installed skill wrapper 仍然是可同步的副本，canonical source 仍是本仓库。

## 7. 兼容性与默认行为

| 场景 | 默认行为 |
|---|---|
| 已有源码 checkout 用户 | 继续使用 `scripts/update_cli.sh`、`SKILLCLI_PROJECT_DIR` 或源码内 `python3 -m skill_cli_kit.cli` |
| 已安装旧 wrapper 用户 | `sync-skill --force` 可刷新 installed skill；native installer 默认同步 Codex 和 Agents skill |
| 机器没有源码 checkout | 推荐使用 GitHub Releases native installer |
| 用户只想本地 smoke test | 使用 `SKILLCLI_RELEASE_BASE_URL=file://...`、`SKILLCLI_INSTALL_ROOT`、`SKILLCLI_BIN_DIR` 指向临时目录 |

## 8. 验收标准

1. 本地 release packaging 和 `file://` native install smoke 通过。
2. `skillcli --version`、`doctor`、`native-update`、`uninstall --dry-run` 在 native 安装路径下可运行。
3. `python3 -m unittest discover -s tests` 通过。
4. `skillcli audit /Users/chihoyo/Project/skill-cli-kit --json` 为 0 error / 0 warn。
5. `/Users/chihoyo/.local/bin/docdev audit /Users/chihoyo/Project/skill-cli-kit` 无 findings。
6. GitHub Releases 的 `install_remote.sh` 可以从公网安装 `skillcli 0.1.0`。

## 9. 开放问题

| ID | 问题 | 当前判断 | 是否阻塞实现 |
|---|---|---|---|
| Q1 | `skillcli init` 何时生成 native release 工具链 | 本次先让本仓库自举成参考样板，后续在模板生成稳定后推进 | 否 |
| Q2 | 是否需要 Homebrew tap / pipx / npm | 当前 GitHub Releases native installer 更贴近用户目标；生态包管理可后续评估 | 否 |
