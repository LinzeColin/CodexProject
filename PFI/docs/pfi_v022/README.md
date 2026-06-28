# PFI v0.2.2 数据库治理资料区

本目录记录 `PFI v0.2.2` 的数据库治理、E2E 逻辑优化、参数治理、Interconnection、Runtime Diff 和 Agent Review 交付资料。

## Stage 0 范围

本轮只做准备和现状盘点：

- 读取 v0.2.2 roadmap、Task Pack、参数草案、6 Agent 交叉验证草案和 HTML 审查模板。
- 对照当前 `PFI/` 三基文件、Stage 2-6 数据逻辑、v0.2.1 Stage 8 收尾状态。
- 生成中文 baseline report。
- 新增 Stage 0 合同测试。

本轮明确不做：

- 不修改 `PFI/web/index.html`。
- 不修改 `PFI/web/app/shell.js`。
- 不新增 `PFI/web/pfi_v022_logic_review.html`。
- 不新增 `PFI/config/pfi_parameters.yaml`。
- 不新增标签数据库 schema。
- 不改变 v0.2.1 UIUX 展示。

## Stage 1 范围

本轮完成参数治理，不改前端：

- 重构 `PFI/模型参数文件.md`，建立中文参数总目录。
- 新增 `PFI/config/pfi_parameters.yaml`，作为唯一机器可读参数源。
- 新增 `PFI/tests/test_pfi_parameters_consistency.py`，验证 Markdown、YAML、前端合同和 HTML 中的核心参数一致。
- 公式补中文名称、用途、输入、输出、计算逻辑和示例。
- 阈值补当前值、存在原因、影响页面和是否允许用户修改。
- 公式变量补中文别名。
- 继续不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`，不新增 `PFI/web/pfi_v022_logic_review.html`。

## Stage 2 范围

本轮完成 CNY 基准与汇率规则：

- 将当前主显示口径锁定为 `CNY`，原始币种仅作为辅助显示。
- 顶部汇率徽标使用 `AUD/CNY=4.69（YYYYMMDD--HH:MM）`，含义为 `1 AUD = 4.69 CNY`。
- 新增真实本地快照 `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json`。
- 新增 `PFI/src/pfi_v02/stage_v022_fx.py`，实现 06:00 有效日、普通运行不联网、显式刷新、快照 hash 和账本金额字段。
- 新增 `PFI/tests/test_v022_fx_effective_date.py`，验证 Stage 2 acceptance criteria 和 stop condition。
- 不实现 Stage 3 数据源结构，不新增参数中心页面，不做真实交易、自动投资、支付或券商提交。

## Stage 3 范围

本轮完成数据源、账户角色与可扩展结构：

- 新增 `PFI/src/pfi_v02/stage_v022_source_profile.py`，建立 source profile、capabilities、account role 和 role effective date 合同。
- 新增 `PFI/tests/test_v022_stage3_source_account_profiles.py`，验证 `S3-P1-T1..S3-P2-T3`。
- 新增 `PFI/docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md`，提供中文验收入口。
- `PFI/config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage3`，记录 `source_profile_schema`、`other_source_template`、`account_role_schema` 和 role/event 计算策略。
- 不实现 Stage 4 `economic_event_id` / `interconnection_group_id`，不修改 v0.2.1 Web Shell 交互架构，不做真实交易、自动投资、支付或券商提交。

## Stage 4 范围

本轮完成 Economic Event 与 Interconnection 逻辑：

- 新增 `PFI/src/pfi_v02/stage_v022_interconnection.py`，建立 `InterconnectionRecord`、`EventTypePolicy`、`aggregate_core_metrics()` 和 Metric Dependency Graph。
- 新增 `economic_event_id`，同一真实经济事件只能有一个 ID。
- 新增 `interconnection_group_id`，同一资金链路归入同一关联组。
- 新增 `PFI/docs/pfi_v02/INTERCONNECTION_MATRIX.md`，覆盖普通消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、信用卡还款、内部转账、收入、费用、汇率兑换。
- `PFI/config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage4`，记录 event type affects flags、matrix fields 和 metric dependency graph。
- 新增 `PFI/tests/test_v022_interconnection_no_double_count.py` 和 `PFI/tests/test_v022_consumption_investment_outflow.py`，验证同一 `economic_event_id` 只计算一次、投资入金/基金申购进入消费总流出但不进入生活消费、信用卡还款不重复计入生活消费。
- Stop condition：`投资入金未进入消费总流出`、`基金申购未进入消费总流出`、`投资入金错误进入生活消费`、同一 `interconnection_group_id` 重复进入核心金额。
- Agent 1 复核消费/投资/现金流口径；Agent 2 复核 source -> transaction -> group -> economic event -> ledger -> metric 链路。
- 本轮不实现 Stage 5 分类 taxonomy，不修改 v0.2.1 Web Shell UIUX 基线，不做真实交易、自动投资、支付或券商提交。

## 文件

| 文件 | 用途 |
| --- | --- |
| `STAGE0_BASELINE_REPORT.md` | Stage 0 中文 baseline report。 |
| `STAGE0_REDO_ACCEPTANCE_20260628.md` | Stage 0 独立补做验收记录，方便 GitHub 单独检查。 |
| `STAGE1_PARAMETER_GOVERNANCE.md` | Stage 1 参数治理验收报告。 |
| `STAGE2_CNY_FX_GOVERNANCE.md` | Stage 2 CNY 与汇率治理验收报告。 |
| `STAGE3_SOURCE_ACCOUNT_PROFILE.md` | Stage 3 数据源 Profile、账户角色和生效期验收报告。 |
| `STAGE4_INTERCONNECTION.md` | Stage 4 Economic Event、Interconnection Matrix、no-double-count 和双消费口径验收报告。 |
| `SOURCE_TASK_PACK_MANIFEST.md` | Downloads 来源文件、SHA-256 和使用边界。 |
| `ROADMAP_LOCK.md` | v0.2.2 Stage / Phase / Task / Acceptance / Stop / Validation 锁定摘要。 |
