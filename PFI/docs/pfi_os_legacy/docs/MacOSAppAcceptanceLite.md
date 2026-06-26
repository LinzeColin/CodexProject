# macOS App Acceptance Lite

`macOS App Acceptance Lite` 是 PFI_OS 的轻量本机验收入口，用于快速确认 Desktop、Downloads、Applications 三个 `PFI_OS.app` 入口仍然指向当前本地项目并能通过 launcher dry-run。

## 目的

- 快速验证 `.app` 入口没有退回 GitHub。
- 快速验证 `Contents/Resources/PFI_OS_PROJECT_ROOT` 指向当前 checkout。
- 快速验证 native launcher、Info.plist、codesign、状态脚本和本地 Streamlit health。
- 给 UI Shell 一个可点击的只读验收按钮。
- 避免为了日常检查反复运行完整 `finalAcceptanceCheck.sh` 或 `ciSmoke.sh`。

## 使用命令

查看摘要：

```bash
$PFI_OS_HOME/scripts/macosAppAcceptanceLite.sh
```

给 agent 或交接读取 JSON：

```bash
$PFI_OS_HOME/scripts/macosAppAcceptanceLite.sh --json
```

写入本地验收证据：

```bash
$PFI_OS_HOME/scripts/macosAppAcceptanceLite.sh --output-dir data/systemAudit
```

写入的 JSON 会包含本机 app 路径和当前 checkout 路径。默认只作为本地验收证据；提交公共 GitHub 前必须确认这些路径已经脱敏或确实可以公开。

## 检查内容

输出 schema：

```text
PFIOSMacOSAppAcceptanceLiteV1
```

核心检查：

- Source template、Desktop、Downloads、Applications app bundle 是否存在。
- `Contents/MacOS/PFI_OS` 是否可执行。
- `Info.plist` 是否显示 `PFI_OS` 且 executable 为 `PFI_OS`。
- 已安装 app 的 `PFI_OS_PROJECT_ROOT` 是否指向当前 checkout。
- app binary 是否不包含 GitHub fallback URL。
- `codesign --verify --deep` 是否通过。
- `PFI_OS_APP_LAUNCH_DRY_RUN=1` 是否返回 `mode=spawn-command`、兼容旧 `mode=open-command` 或已运行服务 URL。
- `StartPFIOS.command` 和 `scripts/statusPFIOS.sh` 是否可执行。
- 8501-8510 的 `_stcore/health` 是否有正在运行的本地服务。

## 不做什么

该轻量验收不会运行：

- `scripts/finalAcceptanceCheck.sh`
- `scripts/ciSmoke.sh`
- full pytest
- 浏览器自动化
- 行情刷新、回测、券商连接、订单、付款或持仓写入

完整 release gate 仍可手动运行 `scripts/finalAcceptanceCheck.sh`，但日常开发和 UI Shell 验证优先使用这个轻量入口。
