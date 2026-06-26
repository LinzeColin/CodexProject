# macOS Lifecycle Readiness

`macOS Lifecycle Readiness` 是 PFI_OS 的只读生命周期验收入口，用于确认启动、停止、自动关闭、缓存清理保护、UI allowlist 和 app 入口验收是否已经具备真实 macOS 验收基础。

## 目的

- 把分散在 `StartPFIOS.command`、`statusPFIOS.sh`、`stopPFIOS.sh`、`cleanCache.sh`、Streamlit UI 和 shutdown monitor 的证据汇总成一个机器可读 contract。
- 日常开发时先判断生命周期链路是否 ready，避免一上来运行完整 `finalAcceptanceCheck.sh` 或 `ciSmoke.sh`。
- 给 UI Shell 一个可点击的开发检查和只读生命周期验收按钮。
- 为后续真实 macOS 验收提供低 token、低噪音、可交接的前置证据。

## 使用命令

查看摘要：

```bash
$PFI_OS_HOME/scripts/macosLifecycleReadiness.sh --summary-json
```

给 agent 或交接读取完整 JSON：

```bash
$PFI_OS_HOME/scripts/macosLifecycleReadiness.sh --json
```

写入本地验收证据：

```bash
$PFI_OS_HOME/scripts/macosLifecycleReadiness.sh --output-dir data/systemAudit
```

写入的 JSON 会包含本机 project root 和本机 app 路径。默认只作为本地验收证据；提交公共 GitHub 前必须脱敏或确认这些路径可以公开。

## 检查内容

输出 schema：

```text
PFIOSMacOSLifecycleReadinessV1
```

核心检查：

- `StartPFIOS.command`、`startPFIOS.sh`、`stopPFIOS.sh`、`statusPFIOS.sh`、`cleanCache.sh`、`macosAppAcceptanceLite.sh` 是否可执行。
- 启动命令是否使用本地 runtime resolver、绑定 `127.0.0.1`、禁用 file watcher 和浏览器统计。
- `.app` 启动路径是否使用 launch lock，避免重复启动。
- `pfi_os.system.shutdown_monitor`、`PFI_HEARTBEAT_URL` 和 120 秒 heartbeat timeout 是否接入。
- Streamlit 是否注入 sanitized localhost heartbeat。
- shutdown monitor 是否要求先见过 heartbeat 再按 timeout 关闭服务。
- stop 脚本是否只停止当前 checkout 的 Streamlit 进程，而不是全局 kill。
- cache cleanup 是否在服务运行时拒绝 delete mode，并只删除可再生缓存。
- UI lifecycle panel 是否只运行 allowlisted 本地脚本。
- UI lifecycle panel 是否提供 `scripts/devReadyCheck.sh` 默认开发检查入口。
- `macosAppAcceptanceLite.sh` 是否通过。

## 不做什么

该 readiness 不会运行：

- `scripts/finalAcceptanceCheck.sh`
- `scripts/ciSmoke.sh`
- full pytest
- 浏览器自动化
- app 启动
- 服务停止
- cache delete mode
- 行情刷新、回测、券商连接、订单、付款或持仓写入

完整 release gate 仍可手动运行 `scripts/finalAcceptanceCheck.sh`，但日常生命周期验证优先使用这个只读入口。
