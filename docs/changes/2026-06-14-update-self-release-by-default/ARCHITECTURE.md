# ARCHITECTURE - Update Self Release By Default

> 本文件只记录本次需求引入或改变的结构、数据流、配置和边界。

## 1. Existing Structure Snapshot

| 模块 / 文件 | 当前职责 | 与本需求关系 |
|---|---|---|
| `src/skill_cli_kit/cli.py` | CLI parser、update lifecycle、release installer wrapper | 修改 `update` dispatch |
| `scripts/install_remote.sh` | 下载 manifest/artifact、校验 checksum、安装 native release | 继续作为 self-update backend |
| `tests/test_cli.py` | CLI 行为回归测试 | 增加 dispatch 边界测试 |
| `README.md`, `skill/SKILL.md`, `docs/*` | 用户和 agent 面向的命令契约 | 替换主入口描述 |

## 2. Previous Flow

```text
skillcli update <project>
  -> source checkout install/test/check/sync/check

skillcli native-update
  -> scripts/install_remote.sh
```

## 3. Target Flow

```text
skillcli update
  -> cmd_update
  -> cmd_release_update
  -> scripts/install_remote.sh

skillcli update <project>
  -> cmd_update
  -> cmd_update_project
  -> source checkout install/test/check/sync/check

skillcli native-update
  -> hidden compatibility alias
  -> cmd_release_update
```

## 4. Option Boundary

| Option group | Valid with no project | Valid with project |
|---|---|---|
| Release options: `--version`, `--release-base-url`, `--install-root`, `--bin-dir`, `--sync-skill`, `--no-sync-skill` | Yes | No |
| Source options: `--pull`, `--allow-dirty`, `--force`, `--sync-arg`, `--skip-*`, `--dry-run`, `--json` | No | Yes |

## 5. Compatibility

- `native-update` remains accepted but hidden from help.
- Users who previously relied on `skillcli update` meaning current directory must run `skillcli update .`.
- v0.1.1 release becomes the first release where `skillcli update` updates the native install by default.

## 6. Testing and Observation

- Unit tests cover no-project dispatch, source flag misuse, release flag misuse, and existing project lifecycle.
- CLI help smoke ensures `native-update` is not advertised.
- Release smoke installs v0.1.1 from GitHub and verifies `skillcli --version`.
