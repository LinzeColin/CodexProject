# PFI 大数据模拟器中文 Owner 快速入口

- S6PAT02 中文 Owner 快速入口：用户可读优先；中文优先，默认全局中文。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02` 仍在逐项目进行，只补 Owner 路径，不改产品 canonical current_task；S5 结构验收回看任务为 `S5PCT01` / `ACC-S5PCT01`。
- 下一 Gate：`S6PA-GATE` 仍在进行中；S5PC/S5-GATE 的中文验收必须继续以本第一屏和 `docs/PFI_structure_report.md` 为准。
- 本轮边界：只补 Owner 可读路径，不改运行代码，不改算法，不移动 `qbvs/`、`config/`、`tests/`、`runs/`、`reports/`，不触发外部自动化。

| Owner 判断项 | 当前路径 | 状态 |
|---|---|---|
| active qbvs | `qbvs/` | 主动运行和算法代码，本轮不改 |
| config | `config/` | 输入配置层，本轮不改 |
| tests | `tests/` | 验证层，本轮不改 |
| runs/reports | `runs/`、`reports/` | 输出证据层，不作为源码事实 |
| contracts/tools | 根合同、`tools/` | 互操作、恢复、报告生成资料，不是默认算法入口 |

- 最小验证路径：进入 `PFI/大数据模拟器/`，运行 `python -B -m unittest tests.test_s3pct02_lifecycle -q`；本轮实测结果为 `Ran 1 test` / `OK`。
- active qbvs smoke：`S5PCT01_PFI_ACTIVE_QBVS_SMOKE_PASS specs=240 rows=120`，证据在 `governance/stage_gates/s5pc/pfi_smoke_tests.log`。
- 失败去向：若出现 `No module named pytest`，先按环境 blocker 处理依赖；若 lifecycle 或 active qbvs 断言失败，再查 `PFI/大数据模拟器/docs/PFI_structure_report.md` 和 `tests/`。
- 回滚：revert 本次 README/报告/gate 证据提交即可；本轮不改运行代码、不改算法、不移动文件、不触发外部自动化。

# 大数据模拟器（原 QBVS / Quant Behavior Validation System）

## Governance Baseline

Machine-readable sources are under `docs/governance/`; `VERSION` and `CHANGELOG.md` record the provisional product version and governance-only changes.

中文人类入口：`功能清单`、`开发记录`、`模型参数文件`。这三份文件必须直接保留 owner 可读的功能摘要、Roadmap/任务、模型/参数、证据状态、限制和下一步门禁；它们不是跳转页，也不是第二套可编辑机器事实源。机器真相仍以 `docs/governance/` 下的 Lean v2 文件为准。


GitHub 备份路径：`LinzeColin/CodexProject/PFI/大数据模拟器`

本目录是原 QBVS 的可继续开发备份。产品显示名改为“大数据模拟器”，历史模块名
`qbvs` 暂时保留，避免破坏现有 CLI、测试、QuantLab ReviewOnly adapter 和
handoff 契约。

独立行为策略验证系统，用于验证“追跌杀涨 + 技术指标”一类交易行为策略是否在随机压力测试、真实行情窗口和买入持有对比下成立。

## 边界

- 不导入 QuantLab 源码。
- 不修改 QuantLab 文件。
- 不写 QuantLab 数据库。
- 只在本目录下写入运行结果、CSV、JSON、PDF。
- 后续 QuantLab 可以读取本系统产出的 `strategy_summary.csv`、`validation_results.csv` 和 PDF 作为策略审批证据。

## S5PCT01 Structure Boundary

S5PCT01 binds the PFI/QBVS layout without changing algorithm code:

- Active QBVS package: `qbvs/` owns strategy generation, signal rules,
  backtest, cache, warehouse, validation, QuantLab bundle, and adapter code.
- Config and tests: `config/` contains reusable input templates and universe
  seed files; `tests/` contains the verification suite.
- Root contracts: `QUANTLAB_INTEGRATION_CONTRACT.json`,
  `HANDSHAKE_PROTOCOL.json`, `HANDOFF.md`, and `BACKUP_MANIFEST.md` are
  interoperability/recovery contracts and owner handoff documents, not runtime
  algorithm modules.
- Date-stamped scripts: `tools/generate_*_20260606.py` and
  `tools/generate_dev_handoff_package_20260615.py` are report/handoff
  generators. They remain non-default entry points and must not change active
  `qbvs/` behavior during structure migration.
- Runs and reports: `runs/` stores lightweight run state/evidence and
  `reports/` stores generated reports. They are output layers, not source truth
  for active algorithms.

PFI Wave 2 archive candidates remain checksum-bound by the shared S5PAT02
manifest. S5PCT01 moves no files and writes no archive; it only binds current
roles so future cleanup can be reviewed without redoing broad governance
calculation in every development action.

## 已内置能力

- 生成 200+ 个真实可解释的交易行为策略族。
- 支持 BOLL、RSI、MA、MACD、ATR、回撤风控等行为规则组合。
- 支持买入持有基准对比。
- 使用用户阈值：平均总收益相对买入持有不低于 8%，年化不低于 3%，回撤不明显变差。
- 支持随机路径压力测试。
- 支持本地 CSV 真实行情验证。
- 支持 Yahoo Chart API 只读获取公开行情样例。
- 支持滚动窗口和事件窗口验证。
- 支持随机压力测试本机多进程并行执行。
- 支持任务清单、逐任务 JSON 结果缓存和断点续跑。
- 支持标准 OHLCV 数据缓存、缓存索引和多标的 manifest。
- 支持跨 run 结果索引和分市场策略汇总。
- 支持 OHLCV 数据质量评分、资产类别/可交易性元数据。
- 支持 manifest 分片和运行预算估算。
- 支持 SQLite 结果仓库，用于跨 run 增量导入、查询和导出。
- 支持快速筛选引擎，用于在百万级任务前先压缩候选策略。
- 支持快速筛选与精确回测误差对比，防止筛选结果被误用为最终结论。
- 支持 QuantLab 外部证据包导出和校验。
- 支持 QuantLab 只读消费 adapter pack 生成和校验。
- 支持长任务 campaign 计划、分片运行命令和候选晋级门禁。
- 支持 Moomoo/OpenD 可用性探测和历史行情缓存入口。
- 支持 200+ 标的候选 universe seed 与显式缓存命令计划。
- 支持从 200+ seed 生成 Yahoo 公开行情 universe 和缓存计划，用作 Moomoo 未就绪时的只读真实历史数据回退验证。
- 支持支付宝基金净值 CSV 标准化为 OHLCV 缓存。
- 支持支付宝基金申购/赎回交易规则回测口径。
- 支持生成 Moomoo/支付宝可交易 universe 模板。
- 输出 CSV、JSON 和正式 PDF 报告。

## 快速运行

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-02/new-chat-2/outputs/quant_behavior_validation_system
PYTHONPATH=. python3 -m qbvs.cli list-strategies --limit 240 --output runs/strategy_catalog.csv
PYTHONPATH=. python3 -m qbvs.cli stress-random --strategies 20 --paths 100 --days 126 --output-dir runs/random_smoke
```

并行随机压力测试：

```bash
PYTHONPATH=. python3 -m qbvs.cli stress-random \
  --strategies 240 \
  --paths 100000 \
  --days 252 \
  --workers 4 \
  --chunk-size 50 \
  --output-dir runs/random_large
```

## 快速筛选层

快速筛选层用于大规模候选策略预筛选。它复用同一套策略信号，但使用向量化目标仓位近似回测，不生成逐笔交易明细。

重要边界：

- 快速筛选结果只能用于排序和缩小候选集。
- 最终策略审批必须重新运行精确回测引擎。
- QuantLab 读取快速筛选产物时，应同时读取误差基准报告。

运行快速筛选：

```bash
PYTHONPATH=. python3 -m qbvs.cli fast-screen-csv \
  --csv runs/sample_ohlcv.csv \
  --symbol SIMCSV \
  --market SIM \
  --strategies 240 \
  --output-dir runs/fast_screen
```

运行快速层与精确层对比：

```bash
PYTHONPATH=. python3 -m qbvs.cli fast-benchmark-csv \
  --csv runs/sample_ohlcv.csv \
  --symbol SIMCSV \
  --market SIM \
  --strategies 20 \
  --output-dir runs/fast_benchmark
```

主要产物：

- `fast_validation_results.csv`
- `fast_strategy_summary.csv`
- `Behavior_Strategy_Fast_Screen_Report.pdf`
- `fast_exact_comparison.csv`
- `fast_exact_summary.csv`
- `Behavior_Strategy_Fast_Exact_Benchmark_Report.pdf`

## 真实数据运行

```bash
PYTHONPATH=. python3 -m qbvs.cli validate-yahoo \
  --universe config/tradable_universe_sample.csv \
  --limit 5 \
  --strategies 20 \
  --output-dir runs/yahoo_validation
```

滚动窗口验证：

```bash
PYTHONPATH=. python3 -m qbvs.cli validate-yahoo \
  --universe config/tradable_universe_sample.csv \
  --limit 5 \
  --strategies 20 \
  --rolling-windows \
  --window-days 252,504,756,1260 \
  --step-days 63 \
  --output-dir runs/yahoo_rolling
```

事件窗口验证：

```bash
PYTHONPATH=. python3 -m qbvs.cli validate-yahoo \
  --universe config/tradable_universe_sample.csv \
  --limit 5 \
  --strategies 20 \
  --event-windows config/event_windows_sample.csv \
  --output-dir runs/yahoo_events
```

## 可恢复任务清单

先把原始行情落地为标准 OHLCV 缓存：

```bash
PYTHONPATH=. python3 -m qbvs.cli cache-csv \
  --csv runs/sample_ohlcv.csv \
  --symbol SIMCSV \
  --market SIM \
  --asset-class ETF \
  --tradability LIKELY_TRADABLE_NEEDS_ACCOUNT_CHECK \
  --cache-dir data_cache
```

单独评估一个 CSV 的数据质量：

```bash
PYTHONPATH=. python3 -m qbvs.cli assess-csv-quality \
  --csv runs/sample_ohlcv.csv \
  --symbol SIMCSV \
  --market SIM \
  --output runs/quality/simcsv_quality.json
```

## 真实可交易数据源

Moomoo/OpenD 探测：

```bash
PYTHONPATH=. python3 -m qbvs.cli probe-moomoo-opend \
  --host 127.0.0.1 \
  --port 11111 \
  --output runs/datasource_probe/moomoo_opend.json
```

返回码含义：

- `0`：OpenD 端口可达，且本机存在可用 SDK。
- `2`：OpenD 或 SDK 未就绪。系统不会伪造数据。

Moomoo/OpenD 历史行情缓存：

```bash
PYTHONPATH=. python3 -m qbvs.cli cache-moomoo-history \
  --symbol US.SPY \
  --market US \
  --start 2010-01-01 \
  --end 2026-06-04 \
  --cache-dir data_cache
```

支付宝基金净值 CSV 缓存：

```bash
PYTHONPATH=. python3 -m qbvs.cli cache-alipay-fund-nav \
  --csv path/to/alipay_fund_nav.csv \
  --symbol ALIPAY_FUND_CODE \
  --fund-name "基金名称" \
  --date-col date \
  --nav-col nav \
  --cache-dir data_cache
```

支付宝净值 CSV 至少需要：

- `date`
- `nav`

支付宝基金交易规则模板：

```bash
PYTHONPATH=. python3 -m qbvs.cli create-fund-rule-template \
  --output config/alipay_fund_rule_template.json
```

使用支付宝基金执行口径验证策略：

```bash
PYTHONPATH=. python3 -m qbvs.cli validate-fund-csv \
  --csv data_cache/ALIPAY_FUND/ALIPAY_FUND_CODE.csv \
  --symbol ALIPAY_FUND_CODE \
  --market ALIPAY_FUND \
  --strategies 20 \
  --rule config/alipay_fund_rule_template.json \
  --output-dir runs/alipay_fund_validation
```

该执行口径会考虑：

- 申购费
- 短持有赎回费
- 长持有赎回费
- 买入确认延迟
- 卖出到账延迟
- 最短持有天数

主要产物：

- `fund_validation_results.csv`
- `fund_strategy_summary.csv`
- `fund_trading_rule.json`
- `Alipay_Fund_Strategy_Validation_Report.pdf`

生成可交易 universe 模板：

```bash
PYTHONPATH=. python3 -m qbvs.cli create-tradable-universe-template \
  --kind mixed \
  --output config/tradable_universe_template.csv
```

生成 200+ 标的候选 universe seed：

```bash
PYTHONPATH=. python3 -m qbvs.cli create-seed-universe \
  --output config/tradable_universe_seed_220.csv \
  --limit 220
```

校验 seed：

```bash
PYTHONPATH=. python3 -m qbvs.cli verify-seed-universe \
  --universe config/tradable_universe_seed_220.csv \
  --min-symbols 200
```

从 seed 生成 Moomoo/OpenD 缓存命令计划：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-seed-cache-plan \
  --universe config/tradable_universe_seed_220.csv \
  --output-dir campaigns/seed_220_cache_plan \
  --start 2000-01-01 \
  --end 2026-06-05 \
  --cache-dir data_cache_seed_220
```

主要产物：

- `tradable_universe_seed_220.csv`
- `tradable_universe_seed_220.summary.json`
- `seed_cache_plan.csv`
- `seed_cache_commands.sh`
- `seed_cache_plan.summary.json`

注意：seed 是候选池，不是已确认可交易池。`seed_cache_commands.sh` 需要 Moomoo/OpenD、SDK、账户权限和行情权限就绪后显式执行。

从同一 seed 生成 Yahoo 公开行情 universe：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-seed-yahoo-universe \
  --universe config/tradable_universe_seed_220.csv \
  --output config/tradable_universe_seed_220_yahoo.csv
```

从 Yahoo universe 生成缓存计划：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-seed-yahoo-cache-plan \
  --universe config/tradable_universe_seed_220_yahoo.csv \
  --output-dir campaigns/seed_220_yahoo_cache_plan \
  --cache-dir data_cache_seed_220_yahoo \
  --limit 20
```

Yahoo 公开行情只用于推进真实历史数据验证闭环；它不是 Moomoo/支付宝账户级可交易性确认。

生成跨市场/资产类别的 Yahoo universe 样本：

```bash
PYTHONPATH=. python3 -m qbvs.cli sample-universe \
  --universe config/tradable_universe_seed_220_yahoo.csv \
  --max-symbols 40 \
  --output config/tradable_universe_seed_yahoo_balanced_40.csv \
  --seed 20260605 \
  --group-cols market,asset_class
```

该命令用于避免公开行情样本只集中在文件前部的 US ETF。当前 40 标的样本覆盖 US ETF、US 股票、港股、A 股 ETF，以及 ETF、股票、债券、商品、FX。

也可以从 Yahoo 公开行情缓存样例数据：

```bash
PYTHONPATH=. python3 -m qbvs.cli cache-yahoo \
  --universe config/tradable_universe_sample.csv \
  --limit 5 \
  --cache-dir data_cache
```

先生成任务清单：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-cache-manifest \
  --cache-index data_cache/cache_index.csv \
  --strategies 20 \
  --mode rolling \
  --window-days 252,504,756 \
  --step-days 63 \
  --output runs/manifests/simcsv_manifest.csv
```

直接生成“标的 × 策略”的可扩展任务清单：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-cache-pair-manifest \
  --cache-index config/yahoo_220_public_balanced_200_cache_index.csv \
  --strategies 200 \
  --mode rolling \
  --window-days 252,504,756,1260 \
  --step-days 126 \
  --min-bars 200 \
  --windows-per-pair 1 \
  --output runs/manifests/yahoo_public_200x200_pair_manifest.csv
```

该命令不会先展开全部滚动窗口，适合生成 200 标的 × 200 策略的可执行计划。`windows-per-pair=1` 表示每个“标的×策略”抽取一个代表性窗口；后续可以逐步提高到 2、3 或更多。

再执行任务清单：

```bash
PYTHONPATH=. python3 -m qbvs.cli run-manifest \
  --manifest runs/manifests/simcsv_manifest.csv \
  --max-tasks 100 \
  --min-quality-score 70 \
  --skip-low-quality \
  --run-dir runs/task_manifest_run/simcsv_resume
```

每个任务会写入 `task_results/<task_id>.json`。重复运行时默认跳过已完成任务，并重新聚合 `task_status.csv`、`validation_results.csv`、`strategy_summary.csv` 和 PDF。

当启用 `--skip-low-quality` 且 `quality_score` 低于 `--min-quality-score` 时，任务会记录为 `skipped_quality`，不会进入有效策略结论。

任务预算估算：

```bash
PYTHONPATH=. python3 -m qbvs.cli estimate-budget \
  --manifest runs/manifests/simcsv_manifest.csv \
  --seconds-per-task 0.05 \
  --workers 4 \
  --million-test-multiplier 1 \
  --output runs/manifests/simcsv_budget.json
```

manifest 分片：

```bash
PYTHONPATH=. python3 -m qbvs.cli split-manifest \
  --manifest runs/manifests/simcsv_manifest.csv \
  --chunk-size 10000 \
  --output-dir runs/manifests/simcsv_parts
```

生成分层抽样 manifest：

```bash
PYTHONPATH=. python3 -m qbvs.cli sample-manifest \
  --manifest runs/manifests/seed_yahoo_smoke_manifest.csv \
  --max-tasks 1000 \
  --output runs/manifests/seed_yahoo_stratified_1000_manifest.csv \
  --seed 20260605 \
  --group-cols symbol,strategy_id
```

该命令用于避免短跑只覆盖前几个排序任务。默认按 `symbol,strategy_id` 分层，使真实历史烟测能同时覆盖多标的、多策略、多周期。

## 长任务 Campaign

Campaign 用于把大规模 manifest 转换成可审查、可恢复、可分批执行的长任务计划。该命令只生成文件和命令，不会自动启动后台任务。

生成 campaign：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-campaign \
  --manifest runs/manifests/simcsv_manifest.csv \
  --output-dir campaigns/simcsv_campaign \
  --chunk-size 10000 \
  --workers 4 \
  --seconds-per-task 0.05 \
  --min-quality-score 70 \
  --skip-low-quality \
  --million-test-multiplier 1
```

校验 campaign：

```bash
PYTHONPATH=. python3 -m qbvs.cli verify-campaign \
  --campaign-dir campaigns/simcsv_campaign
```

主要产物：

- `campaign_plan.json`
- `campaign_manifest.csv`
- `manifest_parts/campaign_part_index.csv`
- `campaign_status.csv`
- `run_commands.sh`
- `campaign_verification.json`

执行方式：

```bash
bash campaigns/simcsv_campaign/run_commands.sh
```

注意：`run_commands.sh` 需要用户或外部调度器显式执行；系统不会在后台自动启动。

候选晋级：

```bash
PYTHONPATH=. python3 -m qbvs.cli promote-candidates \
  --summary runs/fund_validation_smoke/20260604_234605/fund_strategy_summary.csv \
  --output handoff/promotion_candidates.csv \
  --top-n 20 \
  --min-samples 1 \
  --min-pass-rate 0.60
```

晋级结果仍然是外部候选，不会写入 QuantLab 策略库。默认要求 QuantLab 复验和用户批准。

跨 run 汇总：

```bash
PYTHONPATH=. python3 -m qbvs.cli index-runs \
  --runs-dir runs \
  --output-dir runs/index
```

该命令会生成 `run_index.csv`、`all_validation_results.csv`、`all_strategy_summaries.csv`、`strategy_market_summary.csv` 和正式 PDF。

## SQLite 结果仓库

该仓库属于独立验证系统，不是 QuantLab 数据库。

初始化：

```bash
PYTHONPATH=. python3 -m qbvs.cli warehouse-init \
  --db warehouse/qbvs_results.sqlite
```

导入所有 run：

```bash
PYTHONPATH=. python3 -m qbvs.cli warehouse-import-runs \
  --runs-dir runs \
  --db warehouse/qbvs_results.sqlite
```

查看统计：

```bash
PYTHONPATH=. python3 -m qbvs.cli warehouse-stats \
  --db warehouse/qbvs_results.sqlite
```

导出 CSV：

```bash
PYTHONPATH=. python3 -m qbvs.cli warehouse-export \
  --db warehouse/qbvs_results.sqlite \
  --output-dir warehouse/export
```

如果本机 Python 证书链异常导致 `CERTIFICATE_VERIFY_FAILED`，可以临时加：

```bash
--allow-insecure-ssl
```

该选项只用于公开行情样例验证，不建议作为生产默认配置。

## CSV 格式

至少需要：

- `datetime` 或 `date`
- `close`

建议包含：

- `open`
- `high`
- `low`
- `volume`

## QuantLab 后续接入方式

建议 QuantLab 不直接调用内部函数，而是以外部证据文件方式接入：

1. QuantLab 触发本系统 CLI。
2. 本系统生成独立 run 目录。
3. QuantLab 只读取 `strategy_summary.csv` 和 PDF。
4. 只有通过用户阈值、压力测试和真实标的窗口验证的策略，才进入 QuantLab 策略库审批。

## QuantLab 证据包

证据包是当前推荐的互通方式。它把一个 QBVS run 目录转换成 QuantLab 可读取的外部证据，不写 QuantLab 源码或数据库。

导出证据包：

```bash
PYTHONPATH=. python3 -m qbvs.cli export-quantlab-bundle \
  --run-dir runs/csv_rolling_smoke/20260604_221746 \
  --output-dir handoff/quantlab_bundle_smoke \
  --top-n 10
```

校验证据包：

```bash
PYTHONPATH=. python3 -m qbvs.cli verify-quantlab-bundle \
  --bundle-dir handoff/quantlab_bundle_smoke
```

核心产物：

- `quantlab_bundle_manifest.json`
- `quantlab_ingestion_payload.json`
- `quantlab_candidate_strategies.csv`
- `quantlab_bundle_verification.json`
- `QuantLab_Integration_Bundle_Report.pdf`

边界：

- `ingestion_mode` 固定为 `external_evidence_only`。
- `writes_quantlab_database` 固定为 `false`。
- `writes_quantlab_source` 固定为 `false`。
- fast screening 来源的候选策略必须标记 `requires_exact_validation=true`。

## QuantLab 只读 Adapter Pack

adapter pack 是给 QuantLab 线程使用的参考实现。它只读取 QBVS 证据，不写 QuantLab 源码或数据库。

生成 adapter pack：

```bash
PYTHONPATH=. python3 -m qbvs.cli build-quantlab-adapter-pack \
  --output-dir handoff/quantlab_readonly_adapter_pack \
  --quantlab-root /Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-quantlab/outputs/CodexFinance \
  --default-bundle-dir handoff/quantlab_bundle_fund_smoke \
  --default-campaign-dir campaigns/simcsv_campaign_smoke \
  --default-promotion-candidates handoff/promotion_candidates_smoke.csv
```

校验 adapter pack：

```bash
PYTHONPATH=. python3 -m qbvs.cli verify-quantlab-adapter-pack \
  --pack-dir handoff/quantlab_readonly_adapter_pack
```

主要产物：

- `adapter_pack_manifest.json`
- `quantlab_qbvs_readonly_adapter.py`
- `test_quantlab_qbvs_readonly_adapter.py`
- `sample_ingestion_request.json`
- `README.md`
- `adapter_pack_verification.json`

建议 QuantLab 侧把读取结果登记为 `ReviewOnly`，并保留 `requires_exact_rerun`、`requires_fund_rule_review`、`requires_user_approval` 等标记。

## 当前限制

- Yahoo 公共行情不等于支付宝/Moomoo 真实可交易池。
- Moomoo/OpenD 需要本机 OpenD 已登录、端口可达、SDK 可导入；否则探测命令返回未就绪，系统不生成假数据。
- 支付宝基金目前支持用户导出的净值 CSV 进入标准缓存；自动登录支付宝或从 App 抓取净值不属于当前能力。
- 支付宝基金执行口径是简化规则模型；真实申赎费率、确认日、节假日、限购、最低持有、到账时间需要用具体基金条款覆盖默认模板。
- 100 年真实历史数据对大量 ETF/基金并不存在，需要按资产类别降级为“可得最长历史 + 事件窗口 + 合成压力测试”。
- 超大规模任务需要分布式/分批执行计划，不能用单次本地短跑替代。
- 当前并行能力是本机多进程批处理，不等同于集群级任务系统；10 万真实标的 × 每标的 1 万窗口需要另建任务队列、缓存和结果仓库。
- 快速筛选层不替代精确回测层；它用于候选压缩，最终结论必须使用精确回测和真实窗口验证。
- 当前任务清单优先使用标准 OHLCV 缓存；Yahoo/Moomoo/支付宝标的进入任务系统前，应先落地为标准 OHLCV 数据缓存。
- 当前已支持 SQLite 结果仓库；超大规模长期运行后续可继续升级为 DuckDB 或分区对象存储索引。
- Campaign 是长任务计划层，不是集群执行器；百万级任务仍需要用户或外部调度器显式运行 `run_commands.sh`。
- 数据质量评分是准入门槛，不是收益保证；低质量数据应进入待确认队列，不应直接参与最终策略结论。
- `quality_score` 缺失时不会自动跳过；这类任务应在报告中标记为待补充质量信息。
