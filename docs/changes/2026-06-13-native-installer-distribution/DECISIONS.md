# DECISIONS - Native Installer Distribution

> 本文件记录这次需求中为什么这么选。只写真实取舍，不为机械改动补仪式性决策。

## 维护规则

1. `D-XXX` 在本工作包内单调递增，不复用。
2. 每条记录 2-3 个真实选项；不要编造凑数选项。
3. 写清选择、理由、风险和对应文件。
4. 决策被推翻时，新增一条 D-XXX 引用旧决策，旧决策保留原文。

---

## D-001 - Native release layer beside source checkout lifecycle

**日期 / Date**: 2026-06-13

**上下文 / Context**:
`skill-cli-kit` 本身既是 skill，又是把 skill 固化成 CLI 的工具。用户希望它先把自己改造成 native-install 项目结构，后续改造其他 skill 时可以直接参考它自己的结构。

**选项 / Options**:
- A. 只保留源码 checkout + wrapper 同步 - 改动最小，但不能示范跨机器 install/update/release 结构。
- B. 直接改用 npm / pipx / Homebrew - 可以利用生态分发，但会把本次目标转成包管理生态选择。
- C. 在现有源码生命周期旁增加 GitHub Releases/native installer layer - 保留开发流程，同时给出可发布、可更新、可卸载的参考结构。

**选择 / Chosen**: C

**理由 / Rationale**:
- 用户核心目标是让别的机器也能简单安装、使用和更新，并让本仓库成为后续 skill CLI 化的参考样板。
- GitHub Releases/native installer 可以把 `src/`、skill、脚本和 launcher contract 一起发布，不要求用户先理解 Python packaging。
- `native-update` 使用独立命令，避免改变既有 `update <project>` 语义。

**风险 / Risks**:
- 当前只是把 `skill-cli-kit` 自己做成参考结构，`skillcli init` 还不会自动生成完整 native release layer。
- Windows installer 需要后续真实 Windows 环境验证。

**对应代码 / 文档**:
- SPEC §3, §5, §6
- ROADMAP Step 3, Step 4, Step 5
- `docs/changes/2026-06-13-native-installer-distribution/ARCHITECTURE.md`
- `docs/DECISIONS.md` D-008
- `scripts/package_release.sh`
- `scripts/install_remote.sh`
- `scripts/install_remote.ps1`
- `src/skill_cli_kit/cli.py`
