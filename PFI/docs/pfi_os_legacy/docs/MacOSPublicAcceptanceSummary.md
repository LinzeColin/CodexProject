# macOS Public Acceptance Summary

`macOS Public Acceptance Summary` 用来把本机 runtime/UI 验收结果转换成 GitHub 可上传的摘要。

它读取本地 raw evidence：

```text
data/systemAudit/MacOSRuntimeAcceptance_latest.json
data/systemAudit/UIVisualAcceptance_latest.json
```

然后生成不含本机绝对路径、截图路径、浏览器可执行路径、PID、日志和私有数据的公开摘要：

```bash
$PFI_OS_HOME/scripts/macosPublicAcceptanceSummary.sh
```

默认输出：

```text
docs/evidence/MacOSAcceptancePublicSummary_YYYYMMDD.json
docs/evidence/MacOSAcceptancePublicSummary_latest.json
docs/evidence/MacOSAcceptancePublicSummary_latest.md
```

## 检查内容

输出 schema：

```text
PFIOSMacOSPublicAcceptanceSummaryV1
```

核心覆盖：

- App open-path runtime acceptance 是否通过。
- 本机 health、缓存删除保护、停止、停止后 health 和 cache dry-run 是否通过。
- UI 是否真实渲染 `PFI_OS`、`macOS 生命周期`、`运行时验收证据`。
- 生命周期按钮是否可见。
- 页面是否没有常见 Python/Streamlit 错误。
- 截图是否已在本机生成。

## 安全边界

该入口只读取已有 evidence，不启动服务、不打开浏览器、不删除缓存、不联网、不刷新行情、不连接券商、不创建订单、不付款、不写持仓。

它不会运行：

- `scripts/finalAcceptanceCheck.sh`
- `scripts/ciSmoke.sh`
- full pytest
- 行情刷新、券商连接、订单、付款或持仓写入

raw evidence 和截图继续只留本机；公开摘要只保存 schema、状态、计数、gate 名称和 sanitized pass/fail。
