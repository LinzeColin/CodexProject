# AI-Research-System HANDOFF

最后更新：2026-06-06 Australia/Sydney

本文件用于后续对话、上下文压缩、接手开发或自动化排查时快速恢复 AI-Research-System 状态。继续任务时，应以当前真实文件、测试结果和用户最新指令为准；本文件只作为状态索引。

## 项目定位

AI-Research-System 是用户个人权益行研、仓位研究、报告生成、证据检查和投资决策质量控制系统。

边界：

- 只做研究、报告、复盘、验证队列和风险提示。
- 不执行真实交易、不下单、不连接实盘交易。
- 报告和建议必须可追溯到 source log、政策桥接、账户证据、PFIOS 验证或 ResearchBus 产物。
- 证据不足时降级为观察、待验证或需要人工复核。

## 当前真实工程路径

```text
<LEGACY_AI_RESEARCH_SYSTEM_ROOT>
```

正式行研 PDF 输出目录：

```text
~/Downloads/行研报告
```

## 当前状态

- 现有系统已包含日报、周报、K 线报告、质量门禁、automation health、支付宝持仓/交易导入、政策桥接、PFIOS 验证队列和 ResearchBus 同步。
- 本项目在 2026-06-06 前缺项目级 `HANDOFF.md` 和 `AGENTS.md`；当前已补齐 `HANDOFF.md`、`AGENTS.md`、Run Contract、doctor/setup/Makefile 和固定验证入口。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Data Trust Layer v1。新增只读审计模块 `src/monitoring/data_trust.py`、CLI 命令 `data-trust-audit`、文档 `docs/DataTrustLayer.md`、测试 `tests/test_data_trust.py`，并生成正式 PDF `data/report_artifacts/system_audit/data_trust_audit_2026-06-06.pdf`。本层不刷新 OpenD/moomoo/支付宝/政策系统/ResearchBus，不改变日报、周报、K 线报告生产口径。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Reconciliation Layer v1。新增只读对账模块 `src/monitoring/reconciliation.py`、CLI 命令 `reconciliation-audit`、文档 `docs/ReconciliationLayer.md`、测试 `tests/test_reconciliation.py`，并生成正式 PDF `data/report_artifacts/system_audit/reconciliation_audit_2026-06-06.pdf`。本层对比 Data Trust、source log、Markdown、PDF、ResearchBus bridge、PFIOS bridge、policy bridge、automation health、README 和 HANDOFF；不刷新外部数据，不改变报告生产口径。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Manual Review Queue v1。新增只读复核队列模块 `src/monitoring/manual_review.py`、CLI 命令 `manual-review-audit`、文档 `docs/ManualReviewQueue.md`、测试 `tests/test_manual_review.py`，并生成正式 PDF `data/report_artifacts/system_audit/manual_review_queue_2026-06-06.pdf`。本层把 Data Trust / Reconciliation 的 `NEEDS_REVIEW`、`REJECTED`、`warn`、`fail` 转为可处理队列，标注优先级、责任方、是否需要用户确认、阻断范围和下一步动作；不刷新外部数据，不改变报告生产口径。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Entity Registry / Alias Map v1。新增只读实体注册模块 `src/monitoring/entity_registry.py`、CLI 命令 `entity-registry-audit`、文档 `docs/EntityRegistry.md`、测试 `tests/test_entity_registry.py`，并生成正式 PDF `data/report_artifacts/system_audit/entity_registry_2026-06-06.pdf`。本层从现有本地证据生成稳定实体表和别名表，覆盖金融标的、报告、数据源、政策文件、账户、系统、策略、验证任务、验证运行、复核项和系统审计产物；不刷新外部数据，不改变报告生产口径。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Evidence Classification / Decision Grade Matrix v1。新增只读证据决策矩阵模块 `src/monitoring/evidence_decision.py`、CLI 命令 `evidence-decision-audit`、文档 `docs/EvidenceDecisionMatrix.md`、测试 `tests/test_evidence_decision.py`，并生成正式 PDF `data/report_artifacts/system_audit/evidence_decision_matrix_2026-06-06.pdf`。本层汇总 Data Trust、Reconciliation、Manual Review、Entity Registry 和 Alias Map 冲突，把关键结论统一标注为 `FACT/INFERENCE/OPINION/OBSERVATION` 和 `Actionable/Watch/Observe/Reject`；不刷新外部数据，不修复上游阻断，不改变报告生产口径。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Report Layer v1。新增只读报告层审计模块 `src/monitoring/report_layer.py`、CLI 命令 `report-layer-audit`、文档 `docs/ReportLayer.md`、测试 `tests/test_report_layer.py`，并生成正式 PDF `data/report_artifacts/system_audit/report_layer_audit_2026-06-06.pdf`。本层把 Evidence Decision Matrix 转换为正式报告质量门禁和结论上限；当前结论上限为 `ResearchOnlyBlocked`，报告只能作为研究复盘和证据缺口清单，不能作为交易执行依据。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Codex Workflow Layer v1。新增项目级 `AGENTS.md`、`doctor.py`、`setup.sh`、`Makefile`、`docs/RunContract.md`、`docs/CodexWorkflowLayer.md`、测试 `tests/test_workflow_layer.py`，并生成正式 PDF `data/report_artifacts/system_audit/codex_workflow_doctor_2026-06-06.pdf` 和 `data/report_artifacts/system_audit/codex_workflow_layer_2026-06-06.pdf`。本层提供固定 doctor/setup/test/audit-stack 入口，不刷新外部数据，不改变报告生产口径。
- 2026-06-06 system upgrade continuation：已完成 AI-Research-System Alias Map hardening v1。`src/monitoring/entity_registry.py` 现在使用 `alias_scope + normalized_alias` 判定冲突，避免 `Alipay` 系统/账户来源与 `alipay` 策略名互相误报；ResearchBus 中 `market=CN` 的金融标的会优先使用 watchlist 的 `SSE/SZSE` 市场口径。重跑后 Alias conflict 从 18 降到 0，Entity Registry 状态从 `Review` 变为 `Pass`。

## 最新 Data Trust 产物

```text
data/report_artifacts/system_audit/data_trust_audit_2026-06-06.json
data/report_artifacts/system_audit/data_trust_audit_2026-06-06.csv
data/report_artifacts/system_audit/data_trust_audit_2026-06-06.md
data/report_artifacts/system_audit/data_trust_audit_2026-06-06.pdf
```

本轮审计结果：

- 总记录：61
- 状态：`Blocked`
- 分布：`ARCHIVED=1`、`NEEDS_REVIEW=17`、`PARSED_CANDIDATE=20`、`RAW_IMPORTED=1`、`RECONCILED=18`、`REJECTED=1`、`USER_CONFIRMED=3`
- 唯一 `REJECTED`：`automation_health_2026-06-05_execution_ready_required.json`

解释：

- `Blocked` 是正确的 fail-closed 输出，表示执行准备健康检查存在失败；这不等于系统不可运行，而是说明相关报告不能直接支撑可执行交易动作。
- 支付宝视频可见持仓、待确认订单、视频候选、fallback 行情、PFIOS `NeedsMoreEvidence/Review` 行和 automation health `warn` 均进入 `NEEDS_REVIEW`，不能提升行动等级。

## 最新 Reconciliation 产物

```text
data/report_artifacts/system_audit/reconciliation_audit_2026-06-06.json
data/report_artifacts/system_audit/reconciliation_audit_2026-06-06.csv
data/report_artifacts/system_audit/reconciliation_audit_2026-06-06.md
data/report_artifacts/system_audit/reconciliation_audit_2026-06-06.pdf
```

本轮对账结果：

- 总检查：21
- 状态：`Blocked`
- 分布：`pass=15`、`warn=3`、`fail=3`
- 失败项：
  - `data_trust_active_rejected`：Data Trust 仍含 1 个 active `REJECTED`，来源为 `automation_health_2026-06-05_execution_ready_required.json`。
  - `source_log_markdown_pairing`：2 个历史周报 source log 缺匹配 Markdown：`周一报告_03062026.md`、`周五报告_03062026.md`。
  - `source_log_pdf_pairing`：3 个 source log 缺匹配正式 PDF：`周一报告_03062026.pdf`、`周五报告_03062026.pdf`、`行业报告_半导体_2026-06-03.pdf`。
- 警告项：17 条 Data Trust 复核项、PFIOS bridge 10 条弱证据结果、2026-06-06 automation health warn。

解释：

- `Blocked` 是正确的 fail-closed 输出，表示证据链存在断点；报告仍可阅读，但不能直接支撑可执行交易动作。
- 本轮重跑了 Data Trust 后再跑 Reconciliation，已消除上一次 Data Trust hash 漂移。

## 最新 Manual Review Queue 产物

```text
data/report_artifacts/system_audit/manual_review_queue_2026-06-06.json
data/report_artifacts/system_audit/manual_review_queue_2026-06-06.csv
data/report_artifacts/system_audit/manual_review_queue_2026-06-06.md
data/report_artifacts/system_audit/manual_review_queue_2026-06-06.pdf
```

本轮复核队列结果：

- 总项目：34
- 状态：`Blocked`
- 优先级分布：`P0=2`、`P1=32`
- 责任方分布：`System=22`、`User=13`
- 需要用户确认：13 项，主要来自支付宝、视频可见持仓、待确认订单和账户证据。
- P0 项：
  - Data Trust：`automation_health_2026-06-05_execution_ready_required.json`，问题为 execution-ready health failed。
  - Reconciliation：`data_trust_active_rejected`，问题为 Data Trust 仍含 active `REJECTED`。

解释：

- 两个 P0 指向同一条执行准备阻断链：一个是原始失败证据，一个是对账层确认该失败仍在影响证据链。
- 队列不会自动修复或删除历史文件；它只把下一步动作拆成用户确认项和系统修复项。

## 最新 Entity Registry / Alias Map 产物

```text
data/report_artifacts/system_audit/entity_registry_2026-06-06.json
data/report_artifacts/system_audit/entity_registry_2026-06-06.csv
data/report_artifacts/system_audit/alias_map_2026-06-06.csv
data/report_artifacts/system_audit/entity_registry_2026-06-06.md
data/report_artifacts/system_audit/entity_registry_2026-06-06.pdf
```

本轮实体注册结果：

- 状态：`Pass`
- 实体：647
- 别名：1334
- Alias conflict：0
- 实体类型分布：`Account=1`、`DataSource=8`、`FinancialInstrument=71`、`PolicyDocument=2`、`Report=16`、`ReviewItem=34`、`Strategy=2`、`System=6`、`SystemArtifact=3`、`ValidationRun=4`、`ValidationTask=500`

解释：

- 初始别名冲突过高，已收紧规则：不再把 `status`、`priority`、`asset_type`、`research_group`、`source_domain`、`research_topic` 等上下文字段当作实体 alias。
- 已完成 hardening：`Alipay/alipay` 通过实体类型 scope 区分，A 股代码通过 watchlist 市场口径归一，当前 alias conflict 为 0。

## 最新 Evidence Classification / Decision Grade Matrix 产物

```text
data/report_artifacts/system_audit/evidence_decision_matrix_2026-06-06.json
data/report_artifacts/system_audit/evidence_decision_matrix_2026-06-06.csv
data/report_artifacts/system_audit/evidence_decision_matrix_2026-06-06.md
data/report_artifacts/system_audit/evidence_decision_matrix_2026-06-06.pdf
```

本轮矩阵结果：

- 状态：`Blocked`
- 总行数：763
- 来源层分布：`DataTrust=61`、`EntityRegistry=647`、`ManualReview=34`、`Reconciliation=21`
- 证据等级：`FACT=159`、`OBSERVATION=604`
- 决策等级：`Actionable=77`、`Observe=23`、`Reject=6`、`Watch=657`
- 优先级：`P0=4`、`P1=672`、`P2=87`
- blocker_count：6

解释：

- `Blocked` 是正确的 fail-closed 输出，因为上游仍有 active `Reject/P0` 阻断链和多个 `Watch/OBSERVATION` 弱证据项。
- 矩阵不修复阻断，也不提高任何证据等级；它把阻断、复核项、实体冲突和证据等级集中到一张可审计表，供后续 Report Layer、质量门禁和总系统整合使用。
- JSON/CSV 保留完整 763 行；PDF 只展示摘要、阻断项、用户确认项和 P1 样例，避免正式 PDF 变成低价值超长清单。当前不再包含 AliasMap 行，因为 alias conflict 已清零。

## 最新 Report Layer 产物

```text
data/report_artifacts/system_audit/report_layer_audit_2026-06-06.json
data/report_artifacts/system_audit/report_layer_audit_2026-06-06.csv
data/report_artifacts/system_audit/report_layer_audit_2026-06-06.md
data/report_artifacts/system_audit/report_layer_audit_2026-06-06.pdf
```

本轮报告层审计结果：

- 状态：`Blocked`
- 结论上限：`ResearchOnlyBlocked`
- Gate 行数：4
- 状态分布：`Blocked=2`、`Review=2`
- 决策等级分布：`Reject=2`、`Watch=2`
- 优先级分布：`P0=2`、`P1=2`
- 输入 Evidence Matrix 行数：763
- Quality Gate Issues：2

质量门禁问题：

- `P0=4`、`Reject=6`、`blocker_count=6`，正式报告结论必须降级为 research-only，直到阻断项解决。
- `Watch/weak rows=674`、`OBSERVATION=604`、`OPINION=0`，弱证据必须标记为观察或证据缺口，不能作为可执行支持。

解释：

- Report Layer 不修复上游阻断，也不提高证据等级。
- 它把 Evidence Decision Matrix 的阻断、弱证据和用户确认缺口转成正式报告质量门禁。
- 当前报告仍可用于研究复盘、证据链审计和缺口清单；不能表述为交易执行依据。
- `src.reporting.quality_gate.run_report_quality_gate()` 已接入 Report Layer；优先使用 `report_layer_audit_YYYY-MM-DD.json`，缺失时退回 Evidence Decision Matrix，旧日期两者都不存在时不凭空生成阻断。

## 最新 Codex Workflow Layer 产物

```text
AGENTS.md
docs/RunContract.md
docs/CodexWorkflowLayer.md
docs/ReportLayer.md
doctor.py
setup.sh
Makefile
data/report_artifacts/system_audit/codex_workflow_doctor_2026-06-06.json
data/report_artifacts/system_audit/codex_workflow_doctor_2026-06-06.md
data/report_artifacts/system_audit/codex_workflow_doctor_2026-06-06.pdf
data/report_artifacts/system_audit/codex_workflow_layer_2026-06-06.pdf
```

本轮 workflow doctor 结果：

- 状态：`Pass`
- 检查项：51
- 分布：`pass=51`

解释：

- `doctor.py` 默认只读；只有 `--write-report` 会写入自己的 workflow doctor JSON/MD/PDF。
- `setup.sh` 不联网、不安装包、不打开应用、不刷新数据，只创建必要目录并运行 doctor。
- `Makefile` 固定了 `doctor`、`setup`、`audit-stack`、`test-monitoring`、`test`、`py-compile` 和 `clean-cache` 入口。

## 修改文件

- `src/monitoring/data_trust.py`
- `src/monitoring/reconciliation.py`
- `src/monitoring/manual_review.py`
- `src/monitoring/entity_registry.py`
- `src/monitoring/evidence_decision.py`
- `src/monitoring/report_layer.py`
- `src/reporting/quality_gate.py`
- `doctor.py`
- `src/cli.py`
- `AGENTS.md`
- `Makefile`
- `setup.sh`
- `tests/test_data_trust.py`
- `tests/test_reconciliation.py`
- `tests/test_manual_review.py`
- `tests/test_entity_registry.py`
- `tests/test_evidence_decision.py`
- `tests/test_report_layer.py`
- `tests/test_workflow_layer.py`
- `docs/DataTrustLayer.md`
- `docs/ReconciliationLayer.md`
- `docs/ManualReviewQueue.md`
- `docs/EntityRegistry.md`
- `docs/EvidenceDecisionMatrix.md`
- `docs/ReportLayer.md`
- `docs/RunContract.md`
- `docs/CodexWorkflowLayer.md`
- `README.md`
- `HANDOFF.md`

## 验证

- 语法检查：`py_compile src/monitoring/data_trust.py src/cli.py tests/test_data_trust.py` 通过。
- 新增测试：`tests/test_data_trust.py` 3 passed。
- 相关旧测试：`tests/test_data_trust.py tests/test_quality_gate.py tests/test_research_bus_bridge.py` 81 passed。
- 全量测试：`tests` 172 passed，9 subtests passed。
- CLI 真实产物：`python3 -m src.cli data-trust-audit --date 2026-06-06 --json` 成功。
- 产物检查：JSON 可解析；CSV 61 行；PDF 为有效 1.4 PDF，4 页。
- Reconciliation 新增测试：`tests/test_reconciliation.py` 3 passed。
- Reconciliation 相关旧测试：`tests/test_reconciliation.py tests/test_data_trust.py tests/test_quality_gate.py tests/test_research_bus_bridge.py` 84 passed。
- 全量测试更新：`tests` 175 passed，9 subtests passed。
- CLI 真实产物：先重跑 `data-trust-audit`，再运行 `python3 -m src.cli reconciliation-audit --date 2026-06-06 --json` 成功。
- Reconciliation 产物检查：JSON 可解析；CSV 21 行；PDF 为有效 1.4 PDF，2 页。
- Manual Review 新增测试：`tests/test_manual_review.py` 3 passed。
- Manual Review 相关旧测试：`tests/test_manual_review.py tests/test_reconciliation.py tests/test_data_trust.py tests/test_quality_gate.py tests/test_research_bus_bridge.py` 87 passed。
- 全量测试更新：`tests` 178 passed，9 subtests passed。
- CLI 真实产物：依次运行 `data-trust-audit`、`reconciliation-audit`、`manual-review-audit` 成功。
- Manual Review 产物检查：JSON 可解析；CSV 35 行；PDF 为有效 1.4 PDF，6 页。
- Entity Registry 新增测试：`tests/test_entity_registry.py` 4 passed。
- Entity Registry 相关旧测试：`tests/test_entity_registry.py tests/test_manual_review.py tests/test_reconciliation.py tests/test_data_trust.py tests/test_research_bus_bridge.py` 19 passed。
- 全量测试更新：`tests` 182 passed，9 subtests passed。
- CLI 真实产物：依次运行前置审计后，`python3 -m src.cli entity-registry-audit --date 2026-06-06 --json` 成功。
- Entity Registry 产物检查：JSON 可解析；实体 CSV 652 行；Alias CSV 1339 行；PDF 为有效 1.4 PDF，7 页。
- Evidence Decision 新增测试：`tests/test_evidence_decision.py` 3 passed。
- Evidence Decision 相关测试：`tests/test_evidence_decision.py tests/test_entity_registry.py tests/test_manual_review.py tests/test_reconciliation.py tests/test_data_trust.py tests/test_research_bus_bridge.py` 22 passed。
- 全量测试更新：`tests` 185 passed，9 subtests passed。
- CLI 真实产物：依次运行前置审计后，`python3 -m src.cli evidence-decision-audit --date 2026-06-06 --json` 成功。
- Evidence Decision 产物检查：JSON 可解析；CSV 785 行且等于 JSON `row_count`；PDF 为有效 1.4 PDF。
- Codex Workflow 新增测试：`tests/test_workflow_layer.py` 4 passed。
- Workflow/Monitoring 相关测试：`tests/test_workflow_layer.py tests/test_data_trust.py tests/test_reconciliation.py tests/test_manual_review.py tests/test_entity_registry.py tests/test_evidence_decision.py` 20 passed。
- 全量测试更新：`tests` 189 passed，9 subtests passed。
- 固定入口验证：`./setup.sh 2026-06-06` 成功；`make py-compile` 成功；`make doctor DATE=2026-06-06` 成功；`make test-monitoring` 成功；`make test` 成功；`make audit-stack DATE=2026-06-06` 成功。
- Workflow Doctor 产物检查：`codex_workflow_doctor_2026-06-06.json/md/pdf` 已生成，doctor 状态 `Pass`，46 项全通过。
- Alias Map hardening 新增测试：`tests/test_entity_registry.py` 6 passed。
- Alias Map hardening 相关测试：`make test-monitoring` 22 passed。
- 全量测试更新：`tests` 191 passed，9 subtests passed。
- 固定审计栈更新：`make audit-stack DATE=2026-06-06` 成功；Entity Registry `Pass`，Alias conflict `0`；Evidence Decision Matrix 763 行，仍为 `Blocked`，原因是上游 Data Trust / Manual Review 存在真实阻断。
- Report Layer 新增测试：`tests/test_report_layer.py` 已纳入 `make test-monitoring`。
- Report Layer / Monitoring 相关测试：`PYTHONPYCACHEPREFIX=/private/tmp/ai-research-pycache make test-monitoring` 29 passed。
- 语法检查更新：`PYTHONPYCACHEPREFIX=/private/tmp/ai-research-pycache make py-compile` 成功。
- 固定审计栈更新：`PYTHONPYCACHEPREFIX=/private/tmp/ai-research-pycache make audit-stack DATE=2026-06-06` 成功；Report Layer `Blocked`，结论上限 `ResearchOnlyBlocked`，Gate 行数 4，Quality Gate Issues 2；Workflow Doctor `Pass`，51 项全通过。
- Report Layer 产物检查：JSON schema 为 `AIResearchReportLayerAuditV1`；CSV 4 行且等于 JSON `row_count`；PDF header 为 `%PDF-1.4`。
- 全量测试更新：授权环境下 `PYTHONPYCACHEPREFIX=/private/tmp/ai-research-pycache make test` 成功，198 passed，9 subtests passed。非授权沙箱下曾因写入 `data/report_artifacts/.../_pfi_os` 和跨系统 ResearchBus 访问受限失败，授权重跑已通过。
- 缓存清理：`make clean-cache` 和 `rm -rf /private/tmp/ai-research-pycache` 已完成；复查无 `__pycache__`、`.pytest_cache` 和本轮 `/private/tmp/ai-research-pycache` 残留。

测试环境说明：

- 系统 Python 有 `certifi/reportlab`，但缺 `pytest`。
- Codex bundled Python 有 `pytest/reportlab`，但缺 `certifi`。
- 本轮测试使用 bundled Python，并把系统 Python 的 site-packages 追加到 `sys.path` 末尾，只用于补 `certifi`；CLI 产物使用系统 Python 生成。

## 下一步建议

1. 报告链修复任务：处理历史 `周一报告_03062026`、`周五报告_03062026` 与正式 PDF/Markdown 命名不一致，以及 `行业报告_半导体_2026-06-03.pdf` 缺失问题；该任务应单独 Run，避免伪造历史报告。
2. 总系统整合 v1：把 AI-Research-System 的 Data Trust、Reconciliation、Manual Review、Entity Registry、Evidence Decision、Report Layer 审计摘要暴露给统一研究中台或 ResearchBus，只同步状态和证据索引，不复制敏感原始账户数据。

## 边界

- 不自动执行交易、支付、转账或真实资金操作。
- 不把视频候选、缓存政策或弱验证结果当成确认事实。
- 不在未验证 OpenD/数据源/账户证据时提高报告行动等级。
