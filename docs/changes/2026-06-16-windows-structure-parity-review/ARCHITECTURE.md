# ARCHITECTURE - Windows structure parity review

> 本文件只在需求影响结构时创建。它描述现有结构是什么，以及本次方案会如何改变结构。

## 0. 状态

| 字段 | 内容 |
|---|---|
| 状态 | v0.1.3 发布准备中，待 Windows 真机 release smoke |
| 创建原因 | Windows native installer 的 launcher set、PATH 配置、release update dispatch 和 sync 参数传递会变化 |
| 最后更新 | 2026-06-16 |

## 1. 现有结构快照

| 模块 / 文件 | 当前职责 | 与本需求关系 |
|---|---|---|
| `scripts/install_remote.sh` | Unix remote native installer：下载 manifest/artifact、校验 checksum、安装 release、写 `~/.local/bin/skillcli` | 保持为 Unix backend；作为 smoke baseline |
| `scripts/install_remote.ps1` | Windows remote native installer：下载 manifest/artifact、校验 checksum、安装 release、写 `skillcli.ps1`、运行 doctor/sync | 需要按 `docs-driven-dev` 模式补 cmd launcher、PATH 和 diagnostics |
| `src/skill_cli_kit/cli.py` | 当前包含 scaffold、audit、status、update、uninstall、sync、doctor、native release dispatch 等逻辑 | 需要小改 `cmd_release_update()`；module split 另开后续 |
| `tests/test_cli.py` | 覆盖 scaffold、audit、update、uninstall、sync 等行为 | 需要增加 Windows installer static contract 和 update dispatch 测试 |
| `README.md` | 用户安装、更新、审计说明 | 需要补 Windows remote installer 命令和 PATH 行为 |
| `skill/SKILL.md` | agent workflow 和 CLI resolution 指南 | 需要补 Windows native install / update fallback |
| `/Users/chihoyo/Project/docs-driven-dev/scripts/install_remote.ps1` | 已验证的 Windows bare command installer 参考 | 只读参考，不直接共享代码 |
| `/Users/chihoyo/Project/docs-driven-dev/src/docs_driven_dev/release.py` | 已实现平台分支的 release update dispatch | 只读参考 |

## 2. 当前调用链 / 数据流

```text
Windows PowerShell install_remote.ps1
  -> download manifest and tarball
  -> verify SHA256
  -> extract release under $HOME\.local\share\skillcli\releases\<version>
  -> update $HOME\.local\share\skillcli\current junction
  -> write $HOME\.local\bin\skillcli.ps1
  -> run skillcli.ps1 doctor
  -> run skillcli.ps1 sync-skill --targets codex,agents --force

skillcli update
  -> cmd_release_update()
  -> scripts/install_remote.sh
```

Current Windows gaps:
- `skillcli.cmd` is not generated, so bare `skillcli` is not guaranteed in PowerShell / CMD.
- User PATH is not updated or diagnosed.
- There is no `-NoModifyPath` opt-out.
- PowerShell sync targets are not quoted.
- `skillcli update` does not dispatch to `install_remote.ps1` on Windows.

## 3. Target structure after approval

```text
Windows PowerShell install_remote.ps1 [-NoModifyPath]
  -> download manifest and tarball
  -> verify SHA256
  -> extract release under $InstallRoot\releases\<version>
  -> update $InstallRoot\current junction
  -> write $BinDir\skillcli.ps1
  -> write $BinDir\skillcli.cmd
  -> unless -NoModifyPath:
       ensure $BinDir is in User PATH
       refresh current process PATH when possible
       print write-after-read diagnostics
  -> run skillcli.ps1 doctor
  -> run skillcli.ps1 sync-skill --targets "codex,agents" --force unless -NoSyncSkill

skillcli update
  -> if Windows:
       powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/install_remote.ps1 ...
     else:
       scripts/install_remote.sh ...
```

The default sync target list remains `codex,agents` to preserve existing `skill-cli-kit` native installer behavior. Expanding default install-time sync to Cursor/Claude is a separate policy choice.

## 4. 模块与接口契约

| 模块 / 文件 | 新增 / 修改 | 职责 | 不应依赖 |
|---|---|---|---|
| `scripts/install_remote.ps1` | 修改 | Generate Windows launcher set, manage User PATH, support `-NoModifyPath`, preserve manifest/checksum/current/sync behavior | Source checkout paths, npm, profile aliases, system PATH mutation |
| `$BinDir\skillcli.cmd` | 新增生成物 | Windows bare command shim so `skillcli` resolves through PATH/PATHEXT | Tokens, source checkout, hard-coded temp paths |
| `$BinDir\skillcli.ps1` | 保留生成物 | Full PowerShell launcher fallback | User-written alias |
| `src/skill_cli_kit/cli.py` | 修改 | Platform dispatch for self-update; keep project update lifecycle untouched | Duplicated installer logic |
| `tests/test_cli.py` | 修改 | Static and dispatch contract coverage | Live Windows execution on macOS |
| README / root docs / skill | 修改 | Explain Windows install/update, PATH opt-out, and verification | npm-first instructions |

## 5. 数据、配置、资源变化

| 类型 | 路径 / 字段 | 变化 | 兼容性 |
|---|---|---|---|
| Generated launcher | `$BinDir\skillcli.cmd` | 新增 | `skillcli uninstall` already plans `.cmd` launcher candidates |
| Generated launcher | `$BinDir\skillcli.ps1` | 保留 | Existing full-path fallback continues |
| Env | `SKILLCLI_BIN_DIR` | 保留 | PATH operation follows custom bin dir |
| Env | `SKILLCLI_INSTALL_ROOT` | 保留 | Native release root unchanged |
| PowerShell parameter | `-NoModifyPath` | 新增 | Users can avoid User PATH writes |
| User environment | User `Path` | Default append / de-dup `$BinDir` | No system PATH or admin requirement |
| Process environment | `$env:Path` | Best-effort current process refresh | Cannot update a parent terminal started outside the script |

## 6. 测试与观测点

- Unit/static tests:
  - `install_remote.ps1` contains `skillcli.cmd` generation.
  - `install_remote.ps1` contains User PATH update, write-after-read diagnostics, and `-NoModifyPath`.
  - `install_remote.ps1` quotes `--targets "codex,agents"`.
  - `cmd_release_update()` dispatches PowerShell installer on Windows and shell installer on Unix.
  - `--no-sync-skill`, `--version`, `--release-base-url`, `--install-root`, `--bin-dir` are preserved.
- Package smoke:
  - `scripts/package_release.sh` still emits `manifest.json`, tarball, checksum, `install_remote.sh`, `install_remote.ps1`.
  - Unix local `file://` install smoke still works.
- Project checks:
  - `python3 -m unittest discover -s tests`
  - `PYTHONPATH=src python3 -m skill_cli_kit.cli audit /Users/chihoyo/Project/skill-cli-kit --json`
  - `docdev audit /Users/chihoyo/Project/skill-cli-kit`
- Windows live smoke after release:
  - Run latest PowerShell installer.
  - Open a new PowerShell and run `skillcli -v`.
  - Run `skillcli doctor`, `skillcli update`, and a no-sync update path.
