# SPEC - Update Self Release By Default

> 本文件描述本次需求应该满足什么。它不写实现细节、不追踪进度、不解释历史取舍。

## 0. 状态

| 字段 | 内容 |
|---|---|
| 状态 | 完成，v0.1.1 public release 已发布并验证 |
| 需求来源 | 2026-06-14 用户指出 `update` 不需要暴露 `native` 命名 |
| 工作包目录 | `docs/changes/2026-06-14-update-self-release-by-default/` |
| 最后更新 | 2026-06-14 |

## 1. 一句话目标

让用户使用 `skillcli update` 更新已安装的 `skillcli` release，同时保留 `skillcli update <project>` 更新某个源码项目的既有能力。

## 2. 背景与问题

- 当前行为：v0.1.0 引入 `skillcli native-update`，而 `skillcli update <project>` 用于源码 checkout lifecycle。
- 问题：`native-update` 把实现方式暴露到命令名里；普通用户想要的只是“更新 skillcli”，不需要理解 native release 细节。
- 期望收益：命令表面更自然：无参数 `update` 更新工具自身，带路径 `update <project>` 更新某个 skill-backed CLI source checkout。

## 3. 范围

### 3.1 本次要做

- 将 `skillcli update` 无 positional project 时解释为 release/self update。
- 继续将 `skillcli update <project>` 解释为 source checkout update lifecycle。
- 将 release update options 移到 `skillcli update` 主命令上。
- 将 `native-update` 从公开帮助中隐藏，只作为兼容别名暂时保留。
- 更新 README、skill 文档、source-of-truth docs 和 release version。

### 3.2 本次不做

- 不删除 v0.1.0 已发布的 `native-update` 命令。
- 不改变 source checkout update lifecycle 的步骤。
- 不引入新的包管理器发布渠道。

## 4. 用户场景 / 使用流程

| 场景 ID | 触发条件 | 期望结果 |
|---|---|---|
| S1 | 用户执行 `skillcli update` | 从 release channel 更新已安装的 `skillcli`，默认同步 installed skill wrapper |
| S2 | 用户执行 `skillcli update --no-sync-skill` | 只更新 CLI release，不写 agent skill homes |
| S3 | 用户执行 `skillcli update ~/Project/<tool> --force` | 跑该项目的 install/test/check/sync/check source lifecycle |
| S4 | 用户执行 `skillcli update ~/Project/<tool> --version 0.1.1` | 报错，因为 release update options 不能和 project path 混用 |

## 5. 功能需求

| ID | 需求 | 验收方式 | 状态 |
|---|---|---|---|
| R1 | `skillcli update` 无 project 时调用 release installer | 单测 monkeypatch release update dispatcher | 完成 |
| R2 | `skillcli update <project>` 继续调用 source checkout lifecycle | 既有 update lifecycle 单测 | 完成 |
| R3 | source-only flags 如 `--force` 在无 project 时必须提示需要 project path | 单测 | 完成 |
| R4 | release-only flags 如 `--version` 和 project path 混用时必须报错 | 单测 | 完成 |
| R5 | `skillcli --help` 不再公开推荐 `native-update` | CLI help smoke / 文档 grep | 完成 |

## 6. 约束与不变式

1. **#1**: `skillcli update <project>` 的 source checkout lifecycle 不得被破坏。
2. **#2**: `skillcli update` 的默认行为应该更新 `skillcli` 自身，而不是当前目录。
3. **#3**: `native-update` 作为兼容别名可以存在，但不能作为主文档入口。

## 7. 兼容性与默认行为

| 场景 | 默认行为 |
|---|---|
| 用户从 v0.1.0 文档记住 `native-update` | 暂时仍可运行，但帮助和文档不再推荐 |
| 用户想更新当前目录项目 | 显式运行 `skillcli update .` |
| 用户想更新任意项目 | 显式运行 `skillcli update /path/to/project` |
| 用户想更新 skillcli 自己 | 运行 `skillcli update` |

## 8. 验收标准

1. `skillcli update --version 0.1.1 --no-sync-skill` 进入 release update dispatcher。
2. `skillcli update <project> --force --json` 仍通过既有 lifecycle 测试。
3. `python3 -m unittest discover -s tests` 通过。
4. `skillcli --help` 不显示 `native-update`。
5. `docdev audit` 与 `skillcli audit` 通过。
6. v0.1.1 release 发布后，GitHub Release installer smoke 通过。

## 9. 开放问题

| ID | 问题 | 当前判断 | 是否阻塞实现 |
|---|---|---|---|
| Q1 | 何时彻底删除 `native-update` alias | 等至少一个 release 周期后再移除，避免打断 v0.1.0 用户 | 否 |
