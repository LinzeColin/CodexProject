# Testing

## Automated Tests

运行完整测试。

Run the full test suite.

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance
PYTHONPATH=src .venv/bin/pytest -q
```

运行最终成品验收。

Run final product acceptance.

```bash
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/finalAcceptanceCheck.sh
```

运行单标的示例回测。

Run the single-symbol sample backtest.

```bash
PYTHONPATH=src .venv/bin/python -m quantlab.examples.run_sample_backtest
```

该命令生成的 RunMetadata 应包含 `QuantLabReportEvidenceV1`，用于验证报告证据层是否随报告输出。

运行参数扫描示例。

Run the parameter scan example.

```bash
PYTHONPATH=src .venv/bin/python -m quantlab.examples.run_parameter_scan
```

运行只读证据审计。

Run the read-only Data Trust audit.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/quantlab-pycache PYTHONPATH=src .venv/bin/python -m quantlab.examples.data_trust_audit --output-dir /private/tmp/quantlab-data-trust
```

运行日常就绪检查。

Run Daily Readiness.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/quantlab-pycache PYTHONPATH=src .venv/bin/python -m quantlab.examples.daily_check
```

生成日常就绪 JSON、Markdown 和 PDF。

Generate Daily Readiness JSON, Markdown, and PDF.

```bash
PYTHONPYCACHEPREFIX=/private/tmp/quantlab-pycache PYTHONPATH=src .venv/bin/python -m quantlab.examples.daily_check --output-dir data/systemAudit
```

## Manual Tests

启动 Streamlit 工作台并打开浏览器。

Start the Streamlit workspace and open the browser.

```bash
PYTHONPATH=src .venv/bin/streamlit run src/quantlab/app/streamlit_app.py
```

确认单标的回测、组合回测和参数扫描都能运行。

Confirm that single backtest, portfolio backtest, and parameter scan all run successfully.

## Real Data Smoke Tests

测试 Yahoo Finance 数据源。

Test the Yahoo Finance provider.

```bash
PYTHONPATH=src .venv/bin/python -m quantlab.examples.fetch_real_data --provider "Yahoo Finance" --symbol AAPL --market US
```

测试 AKShare A 股数据源。

Test the AKShare A-share provider.

```bash
PYTHONPATH=src .venv/bin/python -m quantlab.examples.fetch_real_data --provider AKShare --symbol 000001 --market CN
```

检查 Moomoo 只读行情环境。

Check the Moomoo quote-only environment.

```bash
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/checkMoomoo.sh
```

严格模式会在 Moomoo 未就绪时返回非零退出码，适合验收环境使用。

Strict mode returns a non-zero exit code when Moomoo is not ready, which is useful for acceptance environments.

```bash
/Users/linzezhang/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/outputs/CodexFinance/scripts/checkMoomoo.sh --strict
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
