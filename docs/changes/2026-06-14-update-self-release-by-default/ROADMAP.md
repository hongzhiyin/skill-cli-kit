# ROADMAP - Update Self Release By Default

> 本文件追踪本次需求做到哪一步。它承接 SPEC 的验收标准，记录调研、门禁、任务和验证结果。

## 0. 当前状态

**阶段 / Phase**: 发布准备
**当前 Step / Current Step**: Step 5 - 发布与公网验证
**ARCHITECTURE 省略理由 / Architecture Omission Reason**: 不省略；本需求改变 `update` 命令的 public dispatch 语义。

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
- [ ] 验收标准逐条验证
- [ ] 文档与最终实现一致
- [ ] 剩余风险和后续工作已记录

## 2. 调研记录

| ID | 主题 | 发现 | 证据 / 文件 | 结论 |
|---|---|---|---|---|
| R-1 | 当前 parser | `update` 的 `project` 参数原本是可选 positional，但默认 `.` | `src/skill_cli_kit/cli.py` | 可改成 default `None` 来区分 self update 和 project update |
| R-2 | release update 入口 | `cmd_native_update` 只是包装 `scripts/install_remote.sh` | `src/skill_cli_kit/cli.py`, `scripts/install_remote.sh` | 可复用为 `cmd_release_update` |
| R-3 | 文档入口 | README、skill、SPEC、ARCHITECTURE、change packet 都写了 `native-update` | `rg native-update` | 需要统一替换为 `skillcli update` 主入口 |

## 3. Step 状态总览

| Step | 内容 | 状态 |
|---|---|---|
| 0 | 建立需求工作包 | 完成 |
| 1 | 澄清需求与范围 | 完成 |
| 2 | 调研既有实现 | 完成 |
| 3 | 形成方案 | 完成 |
| 4 | 实施代码与测试 | 完成 |
| 5 | 验证与收尾 | 进行中 |

---

## Step 4 - 实施代码与测试

**Goal**: 让 `skillcli update` 成为 self release update 的主入口，并保留显式项目更新。

**Tasks**:
- [x] 将原 source update 实现拆为 `cmd_update_project`
- [x] 将 release installer 包装命名为 `cmd_release_update`
- [x] 修改 parser，使 `project=None` 时 dispatch 到 release update
- [x] 隐藏但保留 `native-update` alias
- [x] 增加 dispatch 边界单测
- [x] 更新主 docs、README、skill 和旧 change packet 中的主入口说明
- [x] bump version 到 `0.1.1`

**Acceptance**:
1. `update` 无 project 与有 project 的行为边界都有测试。
2. 用户文档不再把 `native-update` 作为主入口。

## 4. 验证记录

| 验收项 | 验证方式 | 结果 | 备注 |
|---|---|---|---|
| SPEC-1 | `python3 -m unittest discover -s tests` | 通过 | 9 tests OK |
| SPEC-2 | `PYTHONPATH=src python3 -m skill_cli_kit.cli --help` | 通过 | 顶层 help 只显示 `init,audit,status,update,uninstall,sync-skill,doctor` |
| SPEC-3 | `PYTHONPATH=src python3 -m skill_cli_kit.cli update --release-base-url file:///private/tmp/skillcli-release-assets-0.1.1 --install-root /private/tmp/skillcli-update-smoke-root-0.1.1 --bin-dir /private/tmp/skillcli-update-smoke-bin-0.1.1 --no-sync-skill` | 通过 | installed `skillcli 0.1.1` into temp native layout |
| SPEC-4 | `PYTHONPATH=src python3 -m skill_cli_kit.cli audit /Users/chihoyo/Project/skill-cli-kit --json` | 通过 | 0 error / 0 warn |
| SPEC-5 | `/Users/chihoyo/.local/bin/docdev audit /Users/chihoyo/Project/skill-cli-kit` | 通过 | No findings |
| SPEC-6 | GitHub Release installer smoke for v0.1.1 | 待验证 | 发布后执行 |

## 5. 风险与后续

| ID | 风险 / 后续 | 影响 | 处理 |
|---|---|---|---|
| F-1 | `native-update` alias 保留时间过长可能造成双入口认知负担 | 文档搜索或用户记忆仍可能看到旧命令 | 下个 release 后评估删除 |
| F-2 | 无参 `update` 不再更新当前目录 | 依赖旧默认 `.` 的用户需要改成 `skillcli update .` | 在 docs 和错误提示中明确 |
