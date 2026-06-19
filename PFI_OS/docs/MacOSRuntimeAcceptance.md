# macOS Runtime Acceptance

`macOS Runtime Acceptance` 是 PFI_OS 的受控真实运行验收入口，用于验证本机启动、health、运行中缓存清理保护、停止服务和停止后缓存 dry-run 是否形成闭环。

## 目的

- 用真实本机 Streamlit 服务验证启动和停止链路。
- 验证 `/_stcore/health` 在启动后可用、停止后消失。
- 验证 `cleanCache.sh` 在服务运行时拒绝 delete mode。
- 验证停止后 cache dry-run 能正常输出结构化 JSON。
- 给 macOS 真实验收一个低噪音、低 token、可交接的 gate，避免直接运行完整 `finalAcceptanceCheck.sh` 或 `ciSmoke.sh`。

## 使用命令

查看摘要：

```bash
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --summary-json
```

真实 `.app` 打开验收：

```bash
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --launch-method app --app-path ~/Downloads/PFI_OS.app --summary-json
```

`--launch-method app` 在未显式传入 `--start-timeout` 时使用 300 秒等待窗口，用于覆盖 macOS `open`、启动锁等待和 Streamlit 首次 ready 的真实耗时。

给 agent 或交接读取完整 JSON：

```bash
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --json
```

写入本地验收证据：

```bash
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --output-dir data/systemAudit
```

写入的 JSON 会包含本机 project root 和本机端口状态。默认只作为本地验收证据；提交公共 GitHub 前必须脱敏或确认这些路径可以公开。

统一 Workspace 的 `macOS 生命周期` 面板会把本地
`data/systemAudit/MacOSRuntimeAcceptance_latest.json` ingest 到 private
Operational Store，然后只读显示脱敏 read model，包括状态、检查通过数、
最近运行时间、启动方式和失败检查摘要。页面不会自动运行 runtime
acceptance；生成或刷新该证据仍必须在 Terminal 中显式执行上面的命令。

## 安全默认值

默认情况下，如果 8501-8510 已经存在健康的 PFI_OS / PFIOS 服务，脚本会 fail-closed，不会启动第二个服务，也不会停止现有服务。

如果确实要把已有服务纳入验收，必须显式传入：

```bash
$PFI_OS_HOME/scripts/macosRuntimeAcceptance.sh --allow-existing-service --summary-json
```

日常建议不用这个参数，避免误停当前工作台。

## 检查内容

输出 schema：

```text
PFIOSMacOSRuntimeAcceptanceV1
```

核心检查：

- App 轻量验收是否通过。
- 启动前是否没有 pre-existing service。
- `scripts/startPFIOS.sh` 是否能受控后台启动本地服务，或 `--launch-method app` 是否能打开真实 `PFI_OS.app`。
- 8501-8510 是否出现 `/_stcore/health`。
- `scripts/statusPFIOS.sh` 是否能看到运行服务。
- 服务运行时 `scripts/cleanCache.sh --json` 是否返回拒绝清理。
- `scripts/stopPFIOS.sh` 是否完成。
- 停止后 `/_stcore/health` 是否消失。
- 停止后 `scripts/statusPFIOS.sh` 是否显示未运行。
- 停止后 `scripts/cleanCache.sh --dry-run --json` 是否能输出 `PFICacheCleanupReportV1`。

## 不做什么

该 runtime acceptance 不会运行：

- `scripts/finalAcceptanceCheck.sh`
- `scripts/ciSmoke.sh`
- full pytest
- 浏览器自动化
- script mode 不打开浏览器；app mode 可能打开默认浏览器，用于真实 `.app` 入口验收
- 行情刷新、回测、券商连接、订单、付款或持仓写入

该脚本会真实启动和停止本地服务，因此不放入 Streamlit UI allowlist。页面只展示命令，实际执行应在 Terminal 中完成。
