# ARCHITECTURE - Generated CLI Sync-Skill Command

> 本文件只在需求影响结构时创建。它描述现有结构是什么，以及本次方案会如何改变结构。

## 0. 状态

| 字段 | 内容 |
|---|---|
| 状态 | 完成 |
| 创建原因 | 新增生成项目 CLI 子命令、调整生成脚本参数契约、扩展 audit 结构检查 |
| 最后更新 | 2026-06-15 |

## 1. 现有结构快照

| 模块 / 文件 | 当前职责 | 与本需求关系 |
|---|---|---|
| `src/skill_cli_kit/cli.py` | `skillcli` 参数解析、模板渲染、audit、update、sync | 修改生成模板和 audit |
| `tests/test_cli.py` | 回归测试 scaffold、audit、update、sync、uninstall | 增加生成命令和 audit 缺口测试 |
| `skill/SKILL.md` | agent 使用 skill-cli-kit 的 workflow 指南 | 更新生成项目合同和 audit 描述 |
| `skill/references/patterns.md` | skill+CLI pattern reference | 更新 sync-skill pattern |
| `docs/` | 项目 source-of-truth docs | 更新 SPEC/ARCHITECTURE/ROADMAP/DECISIONS |

## 2. 当前调用链 / 数据流

```text
skillcli init <project>
  -> render src/<package>/cli.py with status/doctor only
  -> render scripts/sync_skill.sh as the direct sync entry

skillcli audit <project>
  -> inspect pyproject, skill metadata, scripts, docs, tests, installed wrappers
  -> does not verify that <cli> sync-skill exists
```

## 3. 目标结构

```text
skillcli init <project>
  -> render src/<package>/cli.py with status/doctor/sync-skill
  -> render scripts/sync_skill.sh with --targets/--force/--dry-run

<cli> sync-skill --targets codex,agents --force
  -> project_root()
  -> subprocess.run([scripts/sync_skill.sh, --targets, ..., --force])
  -> scripts/sync_skill.sh performs target resolution, copying, marker writing, and bin/<cli> wrapper generation

skillcli audit <project>
  -> inspect src/<package>/cli.py
  -> warn if scripts/sync_skill.sh exists but CLI lacks sync-skill
  -> warn if sync-skill exists but does not clearly delegate to scripts/sync_skill.sh
```

## 4. 模块与接口契约

| 模块 / 文件 | 新增 / 修改 | 职责 | 不应依赖 |
|---|---|---|---|
| `SCAFFOLD_FILES["src/{{package_path}}/cli.py"]` | 修改 | 生成 `<cli> sync-skill` 参数解析和脚本委托 | 目标目录复制逻辑 |
| `SCAFFOLD_FILES["scripts/sync_skill.sh"]` | 修改 | 解析 targets/force/dry-run 并执行实际 sync | Python CLI parser |
| `audit_project()` | 修改 | 对缺失或不清晰委托的 CLI sync command 给 warning | 运行被审计项目的 sync 命令 |
| `tests/test_cli.py` | 修改 | 覆盖生成命令和旧项目缺失 warning | 外部服务 |

## 5. 数据、配置、资源变化

| 类型 | 路径 / 字段 | 变化 | 兼容性 |
|---|---|---|---|
| CLI 参数 | `<cli> sync-skill --targets --force --dry-run` | 新增生成项目命令 | 旧项目通过 audit warning 引导补齐 |
| 脚本参数 | `scripts/sync_skill.sh --targets --force --dry-run` | 新增模板支持 | 无参数仍默认 sync Codex |
| 文档合同 | `docs/SPEC.md`, `skill/SKILL.md`, `skill/references/patterns.md` | 新增 generated sync command contract | 与现有 update 语义并存 |

## 6. 测试与观测点

- `python3 -m unittest discover -s tests`
- `PYTHONPATH=src python3 -m skill_cli_kit.cli --help`
- 临时项目 `skillcli init` 后运行生成 CLI `--help` 和 `sync-skill --dry-run`
- `skillcli audit` 对缺失命令的旧式项目返回 warn
- `docdev audit /Users/chihoyo/Project/skill-cli-kit`
