# Data Trust Audit

Data Trust Audit 是 PFIOS 的只读证据审计层，用来回答一个核心问题：当前研究系统里的文件、数据、策略、实验和报告，哪些可以进入研究证据链，哪些只能观察，哪些必须复核或拒绝。

它不刷新行情、不启动 Moomoo、不打开 Streamlit、不修改持仓、不生成交易指令。

## What It Checks

当前审计覆盖：

| 范围 | 检查重点 | 结论用途 |
| --- | --- | --- |
| 项目控制文件 | `AGENTS.md`、`HANDOFF.md`、`README.md`、`pyproject.toml`、文档和任务包文件 | 判断项目规则、交接、依赖和文档是否可追溯 |
| 数据源 | Moomoo、Yahoo、AKShare、TuShare、Polygon、Alpha Vantage、CSV、Sample Provider | 判断数据入口是否有统一实现和质量检查入口 |
| 策略库 | 策略基类、内置策略、策略画像、策略模板、策略确认记录 | 判断策略是否具备版本、参数、假设和确认链路 |
| 持仓 | `HoldingsBook.json`、`HoldingsBook.csv`、导入候选、同步历史、锁文件 | 区分正式持仓、候选持仓、待确认订单和运行残留 |
| ResearchBus | 互通审计、快照、共享 SQLite、来源日志 | 判断跨系统输入输出是否可追溯 |
| Entity Registry | 持仓代码、行情代理、缺失代码和 ResearchBus 映射摘要 | 防止把基金名称、代理 ETF 和真实可交易代码混为一谈 |
| 验证任务 | `ValidationTasks.json` 和锁文件 | 防止把待验证任务误当成已验证结论 |
| 独立验证 | 独立验证运行 JSON | 区分 completed、planned、dry-run、blocked、failed |
| 实验记录 | 参数扫描 `summary.csv`、`runs.json`、稳定性、样本外和 walk-forward 文件 | 判断实验是否完整，是否存在验证缺口 |
| 报告目录 | Word、JSON、CSV、Markdown、PDF 报告和元数据 | 判断报告输出是否存在且可进入报告中心 |

## Status Meaning

| 状态 | 含义 | 处理方式 |
| --- | --- | --- |
| `RAW_IMPORTED` | 原始导入，来源可见但未充分验证 | 只能作为原始证据，不直接得出结论 |
| `PARSED_CANDIDATE` | 已解析候选，例如 OCR、视频、实验候选 | 需要用户确认或交叉验证 |
| `NEEDS_REVIEW` | 缺失、结构不完整或需要人工确认 | 进入待复核清单 |
| `USER_CONFIRMED` | 用户或确认流程已确认 | 可进入研究链，但不等于策略有效 |
| `RECONCILED` | 文件成对、结构可读或链路闭合 | 可作为研究证据的一部分 |
| `ARCHIVED` | 已归档或仅作历史观察 | 复盘时再精查 |
| `REJECTED` | 损坏、失败或不能用于证据链 | 禁止用于研究结论 |

## Run Command

```bash
cd $PFI_OS_HOME
PYTHONPYCACHEPREFIX=/private/tmp/pfi_os-pycache PYTHONPATH=src .venv/bin/python -m pfi_os.examples.data_trust_audit --output-dir data/systemAudit
```

默认输出目录是项目内 `data/systemAudit`。如果当前环境没有写入权限，使用 `/private/tmp/pfi_os-data-trust`。

输出文件包括：

| 文件 | 用途 |
| --- | --- |
| `PFIOSDataTrustAudit_DDMMYYYY.json` | 机器可读完整审计 |
| `PFIOSDataTrustAudit_DDMMYYYY.csv` | 表格复核和筛选 |
| `PFIOSDataTrustAudit_DDMMYYYY.md` | 人工阅读摘要 |
| `PFIOSDataTrustAudit_DDMMYYYY.pdf` | 正式轻量审计摘要 |

Entity Registry 派生输出位于：

```text
data/entityRegistry/EntityRegistry.json
data/entityRegistry/EntityRegistry.csv
data/entityRegistry/EntityRegistry.md
```

这些文件只用于统一实体口径、审计代理映射和拦截缺失代码对象，不覆盖原始持仓文件。

## Current Result

2026-06-07 当前实测：

- Data Trust Audit：`Pass`。
- 记录数：145。
- 状态分布：`ARCHIVED=55`，`PARSED_CANDIDATE=18`，`RAW_IMPORTED=2`，`RECONCILED=68`，`USER_CONFIRMED=2`。
- `NEEDS_REVIEW=0`，`REJECTED=0`。
- 正式产物：
  - `data/systemAudit/PFIOSDataTrustAudit_07062026.json`
  - `data/systemAudit/PFIOSDataTrustAudit_07062026.csv`
  - `data/systemAudit/PFIOSDataTrustAudit_07062026.md`
  - `data/systemAudit/PFIOSDataTrustAudit_07062026.pdf`

旧参数扫描实验的 `train_test_validation.json` 和 `walk_forward_validation.json` 被明确标记为 `InsufficientData`。这表示旧实验缺少重建样本外验证所需的原始价格序列和切分元数据，不能被解读为验证通过。

## Acceptance Standard

用于真实研究前，最低要求：

1. 没有 `REJECTED` 关键数据、策略或报告记录。
2. 真实行情结果必须有数据质量检查或多源交叉校验记录。
3. 策略进入正式回测前必须有策略版本、参数、假设、失效环境和确认记录。
4. 参数扫描结论必须有 `summary.csv`、`runs.json`，并尽量补齐稳定性、样本外和 walk-forward 文件。
5. OCR、视频、聊天框输入和候选持仓不能直接升级为正式结论。

## Known Limits

Data Trust Audit 只判断本地证据链完整性，不证明策略盈利能力。

如果行情源本身延迟、缺权、缺分钟线或 OpenD 额度耗尽，审计只会暴露缺口，不会伪造数据。
