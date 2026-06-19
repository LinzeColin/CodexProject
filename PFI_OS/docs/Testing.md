# Testing

## Automated Tests

日常开发默认先跑统一 macOS 验收入口。它聚合轻量开发就绪和 GitHub-safe 公开验收摘要；不会运行最终验收、CI smoke、完整测试、浏览器自动化、行情刷新、券商连接或策略 smoke gate。

Run the unified macOS acceptance hub first during normal development. It combines lightweight development readiness and the GitHub-safe public acceptance summary; it does not run release acceptance, CI smoke, the full suite, browser automation, market refresh, broker connections, or strategy smoke gates.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh
```

报告/验证链路日常检查先跑合并入口。它只输出 compact 摘要，不写报告产物、不追加验证队列、不执行验证任务、不刷新行情。

Run the merged report validation hub for daily report checks. It prints compact summaries only; it does not write report artifacts, append the validation queue, execute validation tasks, or refresh market data.

```bash
$PFI_OS_HOME/scripts/reportValidation.sh
```

查看可选模式：

List optional modes:

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --list-modes
```

运行完整测试。

Run the full test suite.

```bash
cd $PFI_OS_HOME
PYTHONPATH=src .venv/bin/pytest -q
```

运行 macOS app 入口轻量验收。日常排查优先使用这个命令，它不运行完整 smoke。

Run the lightweight macOS app entry acceptance. Use this first for daily checks; it does not run full smoke.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode app-entry --summary-json
```

运行 macOS 生命周期只读验收。它检查启动、停止、自动关闭、缓存清理保护和 UI allowlist，不启动服务、不停止服务、不删除缓存。

Run read-only macOS lifecycle readiness. It checks start, stop, auto-shutdown, cache-clean guards, and UI allowlist without starting, stopping, or deleting cache.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode lifecycle --summary-json
```

运行 macOS 受控运行验收。它会真实启动本地服务、检查 health、验证运行中缓存清理拒绝、停止服务并复核，不打开浏览器。

Run controlled macOS runtime acceptance. It starts the local service, checks health, verifies cache cleanup refuses while running, stops the service, and verifies post-stop state without opening a browser.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode runtime --summary-json
```

运行真实 `.app` 打开路径验收。

Run real `.app` open-path acceptance.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode app-runtime --summary-json
```

运行 macOS UI 可见性验收。它会用 headless Chrome 检查页面真实渲染和截图，不运行完整 smoke。

Run macOS UI visual acceptance. It uses headless Chrome to verify rendered page visibility and screenshot capture without running full smoke.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode ui --summary-json
```

生成 GitHub-safe macOS 公开验收摘要。它只读取已有 runtime/UI evidence，不启动服务、不打开浏览器、不运行完整 smoke。

Generate a GitHub-safe macOS public acceptance summary. It only reads existing runtime/UI evidence without starting services, opening a browser, or running full smoke.

```bash
$PFI_OS_HOME/scripts/macosAcceptance.sh --mode public-summary --summary-json
```

运行最终成品验收。仅在明确发布闸门或完整验收时运行；默认本地误触发会被拒绝。

Run final product acceptance. Use this only for deliberate release gates or full acceptance; accidental local runs are blocked by default.

```bash
PFI_OS_ALLOW_HEAVY_SMOKE=1 $PFI_OS_HOME/scripts/finalAcceptanceCheck.sh
```

运行单标的示例回测。

Run the single-symbol sample backtest.

```bash
PYTHONPATH=src .venv/bin/python -m pfi_os.examples.run_sample_backtest
```

该命令生成的 RunMetadata 应包含 `PFIOSReportEvidenceV1`，用于验证报告证据层是否随报告输出。

运行参数扫描示例。

Run the parameter scan example.

```bash
PYTHONPATH=src .venv/bin/python -m pfi_os.examples.run_parameter_scan
```

运行只读证据审计。

Run the read-only Data Trust audit.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache PYTHONPATH=src .venv/bin/python -m pfi_os.examples.data_trust_audit --output-dir /private/tmp/pfi_os-data-trust
```

运行日常就绪检查。

Run Daily Readiness.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache PYTHONPATH=src .venv/bin/python -m pfi_os.examples.daily_check
```

生成日常就绪 JSON、Markdown 和 PDF。

Generate Daily Readiness JSON, Markdown, and PDF.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache PYTHONPATH=src .venv/bin/python -m pfi_os.examples.daily_check --output-dir data/systemAudit
```

## Manual Tests

启动 Streamlit 工作台并打开浏览器。

Start the Streamlit workspace and open the browser.

```bash
PYTHONPATH=src .venv/bin/streamlit run src/pfi_os/app/streamlit_app.py
```

确认单标的回测、组合回测和参数扫描都能运行。

Confirm that single backtest, portfolio backtest, and parameter scan all run successfully.

## Real Data Smoke Tests

测试 Yahoo Finance 数据源。

Test the Yahoo Finance provider.

```bash
PYTHONPATH=src .venv/bin/python -m pfi_os.examples.fetch_real_data --provider "Yahoo Finance" --symbol AAPL --market US
```

测试 AKShare A 股数据源。

Test the AKShare A-share provider.

```bash
PYTHONPATH=src .venv/bin/python -m pfi_os.examples.fetch_real_data --provider AKShare --symbol 000001 --market CN
```

检查 Moomoo 只读行情环境。

Check the Moomoo quote-only environment.

```bash
$PFI_OS_HOME/scripts/checkMoomoo.sh
```

严格模式会在 Moomoo 未就绪时返回非零退出码，适合验收环境使用。

Strict mode returns a non-zero exit code when Moomoo is not ready, which is useful for acceptance environments.

```bash
$PFI_OS_HOME/scripts/checkMoomoo.sh --strict
```

检查报告命名规则。

Check the report naming rule.

```bash
PYTHONPATH=src .venv/bin/pytest tests/test_reports.py -q
```

检查持仓簿同步、待确认订单隔离、情绪分析指标和热点分析指标。

Check holdings-book sync, pending-order separation, sentiment metrics, and hotspot metrics.

```bash
PYTHONPATH=src .venv/bin/pytest tests/test_holdings_book.py tests/test_sentiment.py tests/test_market_hotspots.py -q
```
