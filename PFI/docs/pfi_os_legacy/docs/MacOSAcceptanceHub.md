# macOS Acceptance Hub

`macOS Acceptance Hub` 是 PFI_OS 的统一 macOS 验收入口，用来减少日常使用时需要记住的一串脚本。

默认命令：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh
```

等价于：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode daily --summary-json
```

`daily` 模式只聚合轻量开发就绪和 GitHub-safe 公开验收摘要，不启动服务、不打开浏览器、不运行完整 SmokeTest。

## 模式

| Mode | 用途 | 是否可能启动服务 |
| --- | --- | --- |
| `daily` | 默认日常验收：开发就绪 + 公开验收摘要 | 否 |
| `app-entry` | 检查 Desktop、Downloads、Applications 的 `PFI_OS.app` 入口 | 否 |
| `lifecycle` | 只读检查启动、停止、缓存保护和 UI allowlist | 否 |
| `public-summary` | 只读取本机 evidence，生成/检查 GitHub-safe 摘要 | 否 |
| `runtime` | 受控启动、health、缓存保护、停止闭环验收 | 是 |
| `app-runtime` | 通过 Downloads `PFI_OS.app` 做真实打开路径验收 | 是 |
| `ui` | 用 headless Chrome 验证工作台真实渲染 | 是 |

查看所有模式：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --list-modes
```

## 推荐用法

日常开发或交接：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh
```

刷新本机真实运行证据：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode app-runtime --summary-json
```

刷新 UI 可见性证据：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode ui --summary-json
```

生成 GitHub-safe 摘要：

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode public-summary --summary-json
```

## 安全边界

该统一入口不会运行：

- `scripts/finalAcceptanceCheck.sh`
- `scripts/ciSmoke.sh`
- full pytest
- 行情刷新、券商连接、订单、付款或持仓写入

底层脚本仍保留，用于调试和追溯；日常使用优先从这个统一入口进入。
