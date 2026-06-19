# macOS UI Visual Acceptance

`macOS UI Visual Acceptance` 是 PFI_OS 的轻量浏览器可见性验收入口，用来证明本机 Streamlit 工作台不仅 health 可用，而且页面真实渲染出 `工作台状态`、`macOS 生命周期` 和 `运行时验收证据`。

## 使用命令

输出低 token 摘要：

```bash
$PFI_OS_HOME/scripts/uiVisualAcceptance.sh --summary-json
```

写入本地证据：

```bash
$PFI_OS_HOME/scripts/uiVisualAcceptance.sh --output-dir data/systemAudit
```

如果已有本机服务：

```bash
$PFI_OS_HOME/scripts/uiVisualAcceptance.sh --url http://127.0.0.1:8501 --summary-json
```

## 检查内容

输出 schema：

```text
PFIOSUIVisualAcceptanceV1
```

核心检查：

- 本机 `/_stcore/health` 可用；没有服务时脚本会启动 `scripts/startPFIOS.sh`。
- Playwright 可加载，并使用本机 Chrome/Chromium/Edge 的 headless 浏览器。
- 首页可见文本包含 `PFI_OS`、`工作台状态`、`macOS 生命周期`、`运行时验收证据`、`开发检查`、`轻量验收`、`生命周期验收` 和 `缓存预览`。
- 页面正文不是空白，并生成本地截图。
- 页面不显示 `Traceback`、`ModuleNotFoundError`、`ImportError:` 或 `Connection lost`。

## 安全边界

该验收不会运行：

- `scripts/finalAcceptanceCheck.sh`
- `scripts/ciSmoke.sh`
- full pytest
- 行情刷新、回测、券商连接、订单、付款或持仓写入

如果脚本自己启动了服务，结束时只停止本次启动的 PFI_OS Streamlit 服务；如果检测到已有服务，则只复用页面，不主动停止用户正在使用的工作台。

## 产物

默认写入：

```text
data/systemAudit/UIVisualAcceptance_*.json
data/systemAudit/UIVisualAcceptance_latest.json
data/systemAudit/UIVisualAcceptance_*.png
```

这些文件包含本机 URL、浏览器路径和截图，默认只作为本机验收证据，已在 `.gitignore` 中排除。
