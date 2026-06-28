# PFI Handoff

Last updated: 2026-06-28 Australia/Sydney

## Current Goal

PFI v0.2.2 Stage 5 收口：完成统一账本事件类型表、消费总流出 / 生活消费双口径、12 大类 / 50 中类消费分类 taxonomy、Stage 5 合同测试和中文验收文档；本轮不实现 Stage 6 标签持久化，不修改 v0.2.1 Web Shell UIUX 基线。

## Current Status

- Correct and only active PFI project root is `PFI/`.
- QBVS is independent top-level system `QBVS/`; PFI does not own or cover QBVS.
- Active QBVS runtime path is `QBVS/qbvs`.
- User raw-data archive root is `MetaDatabase/`; current PFI Alipay raw and processed data are under `MetaDatabase/PFI/alipay_daily/`.
- Former app shell source has been moved into `PFI/src/pfi_os`,
  `PFI/scripts`, `PFI/macos`, `PFI/assets`, `PFI/web`, `PFI/shared`, and
  `PFI/systems`.
- Installed app target is now `PFI.app`, bound by `PFI_PROJECT_ROOT`.
- Installed app entries in `/Applications`, `~/Downloads`, and `~/Desktop`
  resolve to this checkout.
- Local runtime data home is now `~/.pfi` or explicit `$PFI_DATA_HOME`.
- Current app URL after migration verification: `http://localhost:8501`.
- Stage 1 contracts remain in `src/pfi_v02/stage1_ia.py`, `src/pfi_v02/core_models.py`, and `src/pfi_v02/classification_rules.py`.
- Stage 2 registry is implemented in `src/pfi_v02/stage2_registry.py`.
- Stage 2 import pipeline is implemented in `src/pfi_v02/stage2_import.py`.
- Stage 2 non-CSV and reconciliation contracts are implemented in `src/pfi_v02/stage2_contracts.py`.
- Stage 2 record is `docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md`.
- Stage 2 acceptance audit is `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`.
- Stage 2 local contract acceptance is complete for phases 2A-2H.
- Stage 3 read-model is implemented in `src/pfi_v02/stage3_read_mvp.py`.
- Stage 3 record is `docs/pfi_v02/STAGE3_READABLE_MVP.md`.
- Stage 3 local readable MVP acceptance is complete for phases 3A-3D.
- Stage 4 analysis read-model is implemented in `src/pfi_v02/stage4_analysis_mvp.py`.
- Stage 4 record is `docs/pfi_v02/STAGE4_ANALYSIS_MVP.md`.
- Stage 4 local analysis MVP acceptance is complete for phases 4A-4B.
- Stage 5 advice/report/export model is implemented in `src/pfi_v02/stage5_advice_report_alpha.py`.
- Stage 5 record is `docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md`.
- Stage 5 local advice/report/Alpha-read-only export acceptance is complete for phases 5A-5C.
- Stage 6 E2E stabilization model is implemented in `src/pfi_v02/stage6_e2e_stabilization.py`.
- Stage 6 record is `docs/pfi_v02/STAGE6_E2E_STABILIZATION.md`.
- Stage 6 local synthetic E2E, regression governance, delivery rollback, 20 gate audit, and ACC-* taskpack audit acceptance is complete for phases 6A-6C.
- Stage 0 preparation audit is `docs/pfi_v02/STAGE0_PREPARATION_AUDIT_20260627.md`.
- Stage 1-5 acceptance audit is `docs/pfi_v02/STAGE1_5_ACCEPTANCE_AUDIT_20260627.md`.
- v0.2.1 前端优化记录是 `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`。
- v0.2.1 Stage 0/1 合同是 `src/pfi_v02/stage_v021_frontend_contract.py`，测试是 `tests/test_v021_stage0_frontend_contract.py` 和 `tests/test_v021_stage1_navigation_contract.py`。
- v0.2.1 Stage 2 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage2_contract()`，测试是 `tests/test_v021_stage2_copy_cleanup_contract.py`。
- v0.2.1 Stage 3 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage3_contract()`，测试是 `tests/test_v021_stage3_settings_search_contract.py`。
- v0.2.1 Stage 4 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage4_contract()`，测试是 `tests/test_v021_stage4_trend_contract.py`。
- v0.2.1 Stage 5 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage5_contract()`，测试是 `tests/test_v021_stage5_upload_import_contract.py`。
- v0.2.1 Stage 6 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage6_contract()`；SQLite 服务是 `src/pfi_v02/stage_v021_holdings_persistence.py`；测试是 `tests/test_v021_stage6_holdings_persistence.py`。
- v0.2.1 Stage 7 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage7_contract()`；Web Shell 点击安全函数是 `buildClickSafeInventory()` / `bindClickSafeFeedback()` / `setActionFeedback()`；测试是 `tests/test_v021_stage7_clicksafe_feedback.py`。
- v0.2.1 Stage 8 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage8_contract()`；最终验收审计是 `docs/pfi_v02/STAGE_V021_FINAL_ACCEPTANCE_AUDIT.md`；测试是 `tests/test_v021_stage8_final_acceptance.py`。
- v0.2.1 UI 货币基准已锁定为 CNY；历史徽标为 `CNY/AUD=4.70（YYYYMMDD--HH:MM）`。v0.2.2 Stage 2 当前徽标改为 `AUD/CNY=4.69（YYYYMMDD--HH:MM）`，含义为 `1 AUD = 4.69 CNY`，读取本地 06:00 Australia/Sydney 有效快照。
- v0.2.1 正式前端目标是 `PFI/web` HTML Web Shell；多模态反馈、触感、声音、视觉、通知和运行反馈控制台后续必须收敛到设置页。
- Web shell default homepage now restores owner workflow after consuming runtime summaries: 上传支付宝账单、同步全部、处理待复核、查看建议、生成报告、单标的回测、盘感训练。Stage 6 closeout status remains report/evidence content and must not replace homepage core actions.
- Web shell shows one unified 15-entry navigation list: 首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、首页、市场、研究、持仓、策略实验室、数据与系统、设置.
- v0.2.2 当前路线是数据库治理和 E2E 逻辑优化，不是前端重做；Stage 0 资料区为 `docs/pfi_v022/`。
- v0.2.2 Stage 0 baseline report 是 `docs/pfi_v022/STAGE0_BASELINE_REPORT.md`。
- v0.2.2 roadmap lock 是 `docs/pfi_v022/ROADMAP_LOCK.md`；来源资料 manifest 是 `docs/pfi_v022/SOURCE_TASK_PACK_MANIFEST.md`。
- v0.2.2 Stage 0 task IDs 是 `S0-P1-T1`、`S0-P1-T2`、`S0-P1-T3`、`S0-P2-T1`、`S0-P2-T2`。
- v0.2.2 Stage 0 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage0_contract()`；测试是 `tests/test_v022_stage0_database_governance.py`。
- v0.2.2 Stage 0 已新增参数变更记录 `config/parameter_changelog.md`；后续参数、公式、阈值、分类、标签、Interconnection 和汇率规则变化必须记录旧值、新值、原因和影响范围。
- v0.2.2 Stage 1 task IDs 是 `S1-P1-T1`、`S1-P1-T2`、`S1-P1-T3`、`S1-P2-T1`、`S1-P2-T2`、`S1-P2-T3`。
- v0.2.2 Stage 1 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage1_contract()`；机器参数读取函数是 `load_v022_parameter_catalog()`。
- v0.2.2 Stage 1 机器可读参数源是 `config/pfi_parameters.yaml`；参数草案中的 `config/pfi_v022_parameters.yaml` 已作为 draft alias 记录，不新增第二个漂移文件。
- v0.2.2 Stage 1 验收报告是 `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`；一致性测试是 `tests/test_pfi_parameters_consistency.py`。
- v0.2.2 Stage 2 task IDs 是 `S2-P1-T1`、`S2-P1-T2`、`S2-P1-T3`、`S2-P2-T1`、`S2-P2-T2`、`S2-P2-T3`。
- v0.2.2 Stage 2 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage2_contract()`；汇率读取模块是 `src/pfi_v02/stage_v022_fx.py`。
- v0.2.2 Stage 2 当前真实快照是 `data/fx_snapshots/AUD_CNY/2026-06-28.json`，`snapshot_id=fx_AUD_CNY_20260628`，`rate=4.6874`，来源 `Frankfurter v2 public API`，hash `2e0d770f16f07543bfe03f9189f1be923b2ef4518a346c79788655600040018b`。
- v0.2.2 Stage 2 普通本地运行只读 `data/fx_snapshots/`，不默认联网；显式刷新必须调用 `pfi_v02.stage_v022_fx refresh --allow-network`。
- v0.2.2 Stage 2 账本金额字段锁定为 `原始金额`、`原始币种`、`CNY金额`、`汇率快照ID`；缺失当日有效快照时显示 `汇率数据待更新`，不得伪造实时汇率。
- v0.2.2 Stage 3 task IDs 是 `S3-P1-T1`、`S3-P1-T2`、`S3-P1-T3`、`S3-P2-T1`、`S3-P2-T2`、`S3-P2-T3`。
- v0.2.2 Stage 3 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage3_contract()`；source/account profile 模块是 `src/pfi_v02/stage_v022_source_profile.py`。
- v0.2.2 Stage 3 验收报告是 `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md`；合同测试是 `tests/test_v022_stage3_source_account_profiles.py`。
- v0.2.2 Stage 3 机器可读参数源是 `config/pfi_parameters.yaml`，Stage 4 后当前 schema 已升级为 `PFIParametersV022Stage4`，Stage 3 source/account profile 参数仍保留。
- v0.2.2 Stage 3 当前 source profile 支持 `wallet`、`bank`、`broker`、`fund_platform`、`bullion_platform`、`payment_platform`、`manual_snapshot`、`other`；capabilities 覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。
- v0.2.2 Stage 3 账户角色字段锁定为 `account_id`、`source_id`、`role`、`role_effective_from`、`role_effective_to`；未知角色进入复核队列。
- v0.2.2 Stage 3 指标计算策略为 `role_and_event_type`，不得按支付宝、微信、银行卡、券商等 source 名称硬编码。
- v0.2.2 Stage 4 task IDs 是 `S4-P1-T1`、`S4-P1-T2`、`S4-P1-T3`、`S4-P2-T1`、`S4-P2-T2`、`S4-P2-T3`。
- v0.2.2 Stage 4 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage4_contract()`；Interconnection 模块是 `src/pfi_v02/stage_v022_interconnection.py`。
- v0.2.2 Stage 4 验收报告是 `docs/pfi_v022/STAGE4_INTERCONNECTION.md`；Interconnection Matrix 是 `docs/pfi_v02/INTERCONNECTION_MATRIX.md`。
- v0.2.2 Stage 4 合同测试是 `tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`。
- v0.2.2 Stage 5 task IDs 是 `S5-P1-T1`、`S5-P1-T2`、`S5-P2-T1`、`S5-P2-T2`、`S5-P2-T3`、`S5-P3-T1`、`S5-P3-T2`、`S5-P3-T3`、`S5-P3-T4`。
- v0.2.2 Stage 5 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage5_contract()`；账本分类模块是 `src/pfi_v02/stage_v022_ledger_taxonomy.py`。
- v0.2.2 Stage 5 验收报告是 `docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md`；合同测试是 `tests/test_v022_stage5_ledger_taxonomy.py`。
- v0.2.2 Stage 5 当前事件类型表覆盖消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换。
- v0.2.2 Stage 5 当前双消费口径：`消费总流出` 包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用并由退款抵消；`生活消费` 只包含普通生活消费并由退款抵消。
- v0.2.2 Stage 5 当前分类约束：`L1 ≤ 12`、每类 `L2 ≤ 5`、总 `L2 ≤ 50`、每笔交易主分类数量为 `1`，每个 L1 有 `future_merge_to` / `merge_candidate`。
- v0.2.2 Stage 5 明确不实现 Stage 6 标签持久化、自定义标签增删改、标签历史或标签筛选视图。
- v0.2.2 Stage 4 当前规则：同一真实事件只有一个 `economic_event_id`；同一资金链路进入一个 `interconnection_group_id`；同一事件可多处展示但同一核心指标只计算一次。
- v0.2.2 Stage 4 消费口径：投资入金、基金申购、黄金申购、投资买入和费用进入消费总流出；投资入金、基金申购、投资买入不进入生活消费；退款抵消原消费；信用卡还款不重复计入生活消费。
- v0.2.2 Stage 4 stop condition：`投资入金未进入消费总流出`、`基金申购未进入消费总流出`、`投资入金错误进入生活消费`、同一 `interconnection_group_id` 重复计入核心金额。
- v0.2.2 Stage 4 Agent 1 复核消费、投资、现金流口径；Agent 2 复核 source -> transaction -> group -> economic event -> ledger -> metric 链路。
- `PFI_v0.2.2_UIUX_Logic_Review_Template.html` 只是后续逻辑审查页参考；Stage 0 不修改 `PFI/web/index.html`、`PFI/web/app/shell.js` 或新增审查页。
- 2026-06-27验收退回纠偏：默认 8501 顶部已新增 PFI 本机数据上传；真实支付宝导出 CSV parser 已支持说明区/中间表头/GB18030/尾随空列；旧支付宝原始账单 4 份已导入 `~/.pfi/runtime/imports/alipay_daily`，覆盖 `2022-06-06` 至 `2026-06-03`，`8815` 条标准化流水，`406` 条待复核；Web Shell 动态英文状态已中文化，8 个一级入口浏览器点击验证通过。
- 2026-06-27二次纠偏：QBVS 已从 `PFI/` 内部分离为顶层 `QBVS/`；PFI 合同改为 `qbvs_independent_system=true`；Web Shell 补回 V0.1 六入口；`MetaDatabase/` 保存支付宝原始 CSV、manifest 和标准化流水，供 GitHub 验收。
- 当前 GitHub 分支 `codex/pfi-stage6-meta-qbvs-sync` 已推送 commit `d0d0a4b8f50231e2c63293396a1fee8e03de7fda`；PFI/QBVS/MetaDatabase 相关工作区在该 commit 后干净。
- 2026-06-27 Stage 1-5 acceptance audit：根 `README.md` 和 `governance/projects.yaml` 已登记 `QBVS` 和 `MetaDatabase`；`MetaDatabase` 补三基和最小治理；PFI Stage 1-5 contracts `Ran 89 tests / OK`；QBVS smoke `Ran 1 test / OK`；PFI/QBVS/MetaDatabase governance `errors 0 / warnings 0`；Web Shell Chrome 点击验收 `14/14`、console errors `0`。
- 2026-06-27 v0.2.1 Stage 1：HTML Web Shell 左侧导航已改为 15 个统一入口；`数据与系统` 映射设置页；策略实验室旧入口和投资管理卡片都打开投资管理下的策略实验室状态；新增 `docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md`；三基文件已明确功能目录、开发日志、参数依据三种定位。
- 2026-06-27 v0.2.1 Stage 2：HTML Web Shell 与动态首页摘要完成中文可读文案清理；`Review lifecycle`、`PFI Context Export`、`Synthetic E2E`、`Rollback plan`、`Follow-up list`、`Top N`、`tradeoff`、`owner gate`、`parser / raw / batch` 等旧英文/机器文案被移出用户可见面；`运行边界`、`查看边界`、`验收边界`、`安全边界` 和英文 `Boundary` 被合同测试禁止；未新增 iframe、手机演示框或预览框。
- 2026-06-27 v0.2.1 Stage 3：`设置` 和 `数据与系统` 深链统一进入设置主工作区；业务页面不常驻反馈控制台；设置页包含运行反馈控制台、多模态反馈、触感、声音、视觉、通知、反馈测试和无障碍反馈；顶部全局搜索支持 15 个入口、V0.1 别名、工作区卡片、功能面板、任务中心、决策行和设置反馈控制项的模糊检索。
- 2026-06-27 v0.2.1 Stage 4：新增 `UNIFIED_TREND_DATA`；账户与资产显示现金/净资产趋势；投资管理显示市值/总收益/现金仓位趋势；消费管理显示支出/预算/现金流趋势；趋势图有中文标题、图例、CNY 基准、终点直接标签和中文空状态。
- 2026-06-27 v0.2.1 Stage 5：`数据源与上传` 页面新增上传中心和导入中心；文件选择、拖拽上传、等待/完成/失败中文状态、失败反馈、已选文件列表、导入批次、导入摘要和 `进入账本复核` 按钮可用；不执行外部真实上传、支付、券商提交或实盘自动下单。
- 2026-06-27 v0.2.1 Stage 6：`投资管理 > 持仓` 新增持仓编辑面板；SQLite operational database 新增 `v021_holding_snapshots` 和 `v021_position_adjustments` 合同；服务覆盖新增、读取、修改、软删除。2026-06-28 复审修复后，生产保存路径必须通过本机 `/api/holdings` 写入 SQLite；浏览器缓存只允许保存明确标注的未提交草稿。
- 2026-06-27 v0.2.1 Stage 7：所有可见按钮进入点击安全清单；按钮点击统一显示 `进行中/成功/失败` 反馈；`hashchange` 同步工作区和左侧高亮；移动端一级入口横向滚动且不竖排；桌面/手机浏览器验收覆盖 15 个一级入口、40 个代表按钮、15 个命令入口和三态反馈。
- 2026-06-28 v0.2.1 Stage 8：新增最终验收合同和审计；`V021-P8-S8-T01` 前端合同测试、`V021-P8-S8-T02` 浏览器验收、`V021-P8-S8-T03` 命令验收统一进入 `PFI-V021-S8-FINAL-ACCEPTANCE-GATE`；Stage 0-8 前端合同、完整 PFI 单测、JS、治理、diff、浏览器、GitHub main、canonical PFI、PFI.app 和缓存清理成为同一 closeout gate。
- 2026-06-28 v0.2.2 Stage 0：读取 v0.2.2 roadmap、Task Pack、参数草案、6 Agent 交叉验证草案、HTML 审查模板和新版 Stage -> Phase -> Task roadmap；生成 `docs/pfi_v022/STAGE0_BASELINE_REPORT.md`，列出现有参数、硬编码阈值、消费/投资/现金流/建议口径、数据源、账户角色、Stage 6 基线和 v0.2.2 冲突清单；合同测试锁定本轮不改 v0.2.1 前端显示。
- 2026-06-28 v0.2.2 Stage 0 补做：按 `S0-P1-T1..S0-P2-T2` 补齐开发记录任务章节、文件定位、非目标清单、`task_name`、`parameter_version` 和 `config/parameter_changelog.md`。
- 2026-06-28 v0.2.2 Stage 0 验证：Stage 0 合同 `Ran 9 tests / OK`；完整 PFI 单测 `Ran 156 tests / OK`；项目治理 `errors 0 / warnings 0`；`node --check PFI/web/app/shell.js` 通过；`git diff --check -- PFI` 通过；`PFI/web` 无 diff。
- 2026-06-28 v0.2.2 Stage 1：新增 `config/pfi_parameters.yaml`、`docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`、`tests/test_pfi_parameters_consistency.py`；`模型参数文件.md` 补中文参数总目录、公式解释、阈值说明和变量别名；`config/parameter_changelog.md` 记录 `S1-P1-T1..S1-P2-T3` 参数变更。
- 2026-06-28 v0.2.2 Stage 2：新增 `src/pfi_v02/stage_v022_fx.py`、`data/fx_snapshots/AUD_CNY/2026-06-28.json`、`docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 和 `tests/test_v022_fx_effective_date.py`；`config/pfi_parameters.yaml`、三基文件、README、HANDOFF、roadmap lock 和 Web Shell 徽标同步为 `AUD/CNY` 当前快照口径。
- 2026-06-28 v0.2.2 Stage 0 补做复核：新增 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，单独复核 `S0-P1-T1..S0-P2-T2`、Milestone 0 acceptance criteria、stop condition、Agent 1/3 自检和验证命令；不回滚 Stage 1/2，不修改 v0.2.1 Web Shell，不提前做 Stage 3。
- 2026-06-28 v0.2.2 Stage 3：新增 `src/pfi_v02/stage_v022_source_profile.py`、`docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 和 `tests/test_v022_stage3_source_account_profiles.py`；`config/pfi_parameters.yaml`、三基文件、README、HANDOFF、roadmap lock 和 governance 同步为 Stage 3 source/account profile 口径。
- 2026-06-28 v0.2.2 Stage 4：新增 `src/pfi_v02/stage_v022_interconnection.py`、`docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage4`；三基文件和参数变更记录同步记录 no-double-count、双消费口径、Metric Dependency Graph、Agent 1/Agent 2 复核和 stop condition。
- 2026-06-28 v0.2.2 Stage 5：新增 `src/pfi_v02/stage_v022_ledger_taxonomy.py`、`docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md` 和 `tests/test_v022_stage5_ledger_taxonomy.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage5`；三基文件、README、roadmap lock 和参数变更记录同步记录统一账本事件、双消费口径、12 大类 / 50 中类 taxonomy、future_merge 字段、Agent 1/Agent 3 复核和 stop condition。
- 2026-06-28 v0.2.1 UIUX 退回整改：`web/styles/tokens.css` 改为深色玻璃工作台风格；`web/index.html` 顶部动作显示“搜索/任务/证据/设置”；`web/app/shell.js` 新增 `restoreOwnerHomeWorkflow()` 并修复视觉波纹反馈条件；`src/pfi_os/app/streamlit_app.py` 移除真实上传面板外层嵌套 expander 并把 Web Shell iframe 高度调整为 `1120`。验证：v0.2.1 前端合同 `49 passed`，`node --check web/app/shell.js` 通过，`git diff --check -- PFI` 通过，真实 8501 console errors `0`，关键点击链上传/搜索/设置/策略实验室通过。
- 2026-06-28 v0.2.1 UIUX 二次退回修复：首屏新增 `视觉回弹/触感回馈/声音提示` 反馈信号条；`bindOwnerFeedbackSignals()` 触发状态条、toast、波纹、触感和声音降级；Streamlit 原生上传控件已本地化为中文 `拖拽 CSV / ZIP 到这里`、`选择文件`、`单文件上限 200MB`；支付宝导入摘要状态 `Ready` 映射为 `就绪`；新增 `tests/test_v021_uiux_multimodal_style_regression.py`。真实 8501 验证：`Drag and drop files here=false`、`Browse files=false`、`Deploy=false`、`Ready=0`、`就绪=4`。
- 2026-06-28 v0.2.1 UIUX 三次退回修复：旧 `视觉回弹/触感回馈/声音提示` 说明按钮条已移除，首屏改为 `data-feedback-hub` 多模态交互反馈中枢；包含 `视觉状态轨道`、`触感强度`、`声音反馈`、强度条和事件日志；`bindFeedbackHub()` / `updateFeedbackHub()` 会在点击后更新 `data-feedback-hub-state`、`data-action-feedback`、toast 和日志；视觉反馈默认开启并修复 `reduce-motion` 反向逻辑；顶栏可见汇率统一为 `AUD/CNY=4.69（20260628--06:00）`。真实 8501 Chrome 验证：`data-feedback-hub=1`、旧 `data-owner-feedback-strip=0`、旧 `.feedback-signal=0`、点击后状态 `视觉状态轨道 · 成功`，截图 `/tmp/pfi-uiux-feedback-hub-clicked.png`。
- 2026-06-28 v0.2.1 复审硬失败修复：`PFI/web` 和注入首页摘要不再出现 `只读/实盘/运行边界/使用限制/隐私边界/交易密码/不下单/不支付/不登录` 等正式 UI 禁词；新增 `src/pfi_v02/stage_v021_runtime_api.py`；`web/app/shell.js` 保存持仓调用 `/api/holdings`，本机 API 调用 `V021HoldingsPersistenceService` 写入 SQLite，`/api/trends` 从 SQLite 运行读模型派生账户、投资和消费趋势；策略实验室一级入口和投资管理内部入口统一到 `/investment/strategy-lab`。
- 2026-06-28 v0.2.1 复审最终本地验收：v0.2.1 合同 `58 passed`；完整 PFI pytest `198 passed, 64 subtests passed`；`node --check PFI/web/app/shell.js` 和 `git diff --check -- PFI` 通过；Chrome/系统浏览器真实点击 15 个入口、设置隔离、正式 UI 禁词扫描、持仓保存到 SQLite、API 查询、趋势读模型、刷新读取和 API 重启后读取均通过，console errors `0`；`macOS app acceptance lite` `29 pass / 0 fail / 2 info`；三处 `PFI.app` 入口均指向 canonical PFI，其中 Desktop 为 `/Applications/PFI.app` 符号链接。
- 2026-06-28 v0.2.2 Stage 5 closeout 运行修复：`src/pfi_os/app/streamlit_app.py` 移除原生上传面板内嵌 `st.expander()`，避免 Streamlit `Expanders may not be nested`；`page_icon` 改为 `None`，避免浏览器请求 `/PFI` 产生 404。`tests/test_v021_stage8_final_acceptance.py` 增加对应回归断言。

## Decisions

- Do not re-embed `QBVS/qbvs` inside `PFI/`.
- Any future QBVS change must happen under `CodexProject/QBVS`.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep PFI strategy backtesting, 盘感训练 and 大数据模拟器 under PFI `投资管理`.
- Keep V0.1 compatibility entries visible as aliases in the same navigation list: 首页、市场、研究、持仓、策略实验室、数据与系统.
- Do not recreate a separate `strategy` product workspace; PFI strategy backtesting, 盘感训练 and simulator stay under `投资管理`.
- Do not recreate visible new/old navigation group titles.
- Keep PFI research-only: no trading password, no automatic real-money orders.
- Non-CSV sources are first-class: 支付宝基金、中国大陆券商、ABC Bullion do not rely on CSV as the primary contract.
- Low-confidence OCR/screenshot/recording input is candidate-only and must enter review before acceptance.
- Stage 3 `sync_all_plan` is a plan/preview only. It does not log in, submit payments, submit broker orders, or mutate real accounts.
- Stage 3 legacy FX values were deterministic local fixtures for UI/test readability. v0.2.2 Stage 2 introduces real local snapshot reading for current `AUD/CNY` display while still prohibiting ordinary-run network refresh.
- Stage 4 attribution values are deterministic local estimates. If evidence is insufficient, PFI must show `estimate/需要复核` rather than precise conclusions.
- Stage 4 consumption analysis excludes transfers and investment records from living consumption.
- Stage 4 cashflow forecast separates life cash from investment cash.
- Stage 5 recommendations are review queue items. They are not orders, payment actions, or automatic real-money decisions.
- Stage 5 Alpha export is only `pfi_context_snapshot_v1`; it does not add Alpha/Ralpha/System first-level entries and does not modify the Alpha repository.
- Stage 5 context constraints keep `trading_password_available=false` and `live_trade_submission_authorized=false`.
- Stage 6 is synthetic/read-only E2E only. It proves local V0.2 can run, verify, and rollback; it does not prove real account production connectivity.
- Stage 6 follow-ups are separate gates: external Alpha context consumer, real account data connection, PDF/ZIP package, CDR/Open Banking, and production release evidence.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha tests.test_stage6_e2e_stabilization -q
cd ../QBVS && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
node --check web/app/shell.js
git diff --check
```

Latest Stage 2 target result: `Ran 22 tests / OK`.
Latest closeout result: Stage 1+2 contracts `Ran 45 tests / OK`; legacy QBVS smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; PFI.app resolves to `CodexProject/PFI`; port 8501 is served by canonical PFI `.venv`; no PFI LaunchAgent found.
Latest Stage 3 closeout result: Stage 1+2+3 contracts `Ran 59 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Python compile `OK`; Web shell syntax `OK`.
Latest Stage 4 closeout result: Stage 1+2+3+4 contracts `Ran 71 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 4 contract `Ran 12 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`.
Latest Stage 5 closeout result: Stage 1+2+3+4+5 contracts `Ran 85 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 5 contract `Ran 14 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; browser validation screenshot `/tmp/pfi-stage5-browser-verified.png`.
Latest Stage 6 closeout result: Stage 1+2+3+4+5+6 contracts `Ran 95 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 6 contract `Ran 10 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; browser validation screenshot `/tmp/pfi-stage6-browser-verified.png`.
Latest验收退回纠偏 result: `tests.test_stage2_alipay_import` `Ran 7 tests / OK`; Stage 1 classification + Stage 2 targeted contracts `Ran 32 tests / OK`; Python compile `OK`; Web shell syntax `OK`; real old Alipay import `4/4 files`, `8815` records, `406` review; browser validation `upload panel true`, `private ledger true`, `file input 1`, `navCount 8`, all primary entry clicks OK, no raw `ready`/`Synthetic E2E`; screenshot `/tmp/pfi-alipay-upload-verified-v2.png`.
Latest v0.2.1 Stage 1 target result: Stage 1 target contracts `Ran 22 tests / OK`; full PFI unittest discover `Ran 112 tests / OK`; `node --check web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop clicked `15/15` entries with screenshot `/tmp/pfi-v021-stage1-nav-verified.png`; Chrome headless mobile 390x844 validated `数据源与上传` and `策略实验室` with screenshot `/tmp/pfi-v021-stage1-mobile-verified.png`.
Latest v0.2.1 Stage 2 target result: Stage 2 contract `Ran 4 tests / OK`; Stage 0/1/2 frontend contracts `Ran 16 tests / OK`; Stage 4/5/6 regression contracts `Ran 36 tests / OK`; full PFI unittest discover `Ran 116 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop clicked `15/15` entries and validated `复盘生命周期`、`PFI 上下文导出`、`策略实验室`, console errors `0`, screenshot `/tmp/pfi-v021-stage2-copy-desktop-verified.png`; Chrome headless mobile 390x844 validated `15` entries and `数据源与上传`, screenshot `/tmp/pfi-v021-stage2-copy-mobile-verified.png`.
Latest v0.2.1 Stage 3 target result: Stage 0/1/2/3 frontend contracts `Ran 21 tests / OK`; full PFI unittest discover `Ran 121 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop verified settings route, legacy data-system deep link, fuzzy searches `xf`、`fk`、`ledger`, keyboard jump and console errors `0`, screenshot `/tmp/pfi-v021-stage3-settings-search-desktop-verified.png`; Chrome headless mobile 390x844 verified fuzzy search `fk` -> `运行反馈控制台`, screenshot `/tmp/pfi-v021-stage3-settings-search-mobile-verified.png`.
Latest v0.2.1 Stage 4 target result: Stage 0/1/2/3/4 frontend contracts `Ran 26 tests / OK`; full PFI unittest discover `Ran 126 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop verified `/accounts`、`/investment`、`/consumption` trend titles, CNY baseline, legends and nonblank canvas with console errors `0`, screenshot `/tmp/pfi-v021-stage4-trends-desktop-verified.png`; Chrome headless mobile 390x844 verified `消费管理` trend panel and nonblank canvas, screenshot `/tmp/pfi-v021-stage4-trends-mobile-verified.png`.
Latest v0.2.1 Stage 5 target result: Stage 0/1/2/3/4/5 frontend contracts `Ran 31 tests / OK`; full PFI unittest discover `Ran 131 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop verified `/sources-upload` upload panel, file picker upload, drag/drop upload, failure feedback, import center summary, review-link jump to `账本流水`, console errors `0`, screenshot `/tmp/pfi-v021-stage5-upload-desktop-verified.png`; Chrome headless mobile 390x844 verified upload/import panel and review entry, screenshot `/tmp/pfi-v021-stage5-upload-mobile-verified.png`.
Latest v0.2.1 Stage 6 target result: Stage 0/1/2/3/4/5/6 frontend contracts `Ran 37 tests / OK`; target Stage 6 contract `Ran 6 tests / OK`; full PFI unittest discover `Ran 137 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; browser desktop verified `/investment?tab=holdings` edit/save/reload/reopen persistence with console errors `0`, screenshot `/tmp/pfi-v021-stage6-holdings-desktop-verified.png`; browser mobile 390x844 verified holdings panel and 3 rows, screenshot `/tmp/pfi-v021-stage6-holdings-mobile-verified.png`.
Latest v0.2.1 Stage 7 target result: Stage 0/1/2/3/4/5/6/7 frontend contracts `Ran 42 tests / OK`; target Stage 7 contract `Ran 5 tests / OK`; full PFI unittest discover `Ran 142 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; browser desktop/mobile verified 15 primary entries, 14 unique route aliases, 40 representative clicks, 15 command entries, `progress/success/failure` feedback states, zero console errors, screenshots `/tmp/pfi-v021-stage7-clicksafe-desktop-verified.png` and `/tmp/pfi-v021-stage7-clicksafe-mobile-verified.png`.
Latest v0.2.1 Stage 8 target result: Stage 0/1/2/3/4/5/6/7/8 frontend contracts `Ran 47 tests / OK`; target Stage 8 contract `Ran 5 tests / OK`; full PFI unittest discover `Ran 147 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; browser desktop/mobile verified 15 primary entries, 14 unique route aliases, AUD/CNY 06:00 badge, global fuzzy search, upload picker/drag/drop/failure feedback, ledger review entry, holdings persistence, settings feedback console, progress/success/failure feedback states, zero console errors, screenshots `/tmp/pfi-v021-stage8-final-desktop-verified.png` and `/tmp/pfi-v021-stage8-final-mobile-verified.png`; GitHub main synced at `f6a53db5`; canonical `PFI/` content matches `origin/main`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; `/Applications/PFI.app`、`~/Downloads/PFI.app`、`~/Desktop/PFI.app` all point to canonical PFI; `http://127.0.0.1:8501/_stcore/health` returned `ok`.
Latest v0.2.2 Stage 2 target result: Stage 2 FX contract `Ran 7 tests / OK`; Stage 0+1+2 targeted governance contracts `Ran 24 tests / OK`; full PFI unittest discover `Ran 171 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; local FX read returned `fx_AUD_CNY_20260628`, `rate=4.6874`, `ordinary_runtime_network_refresh=false`.
Latest v0.2.2 Stage 4 closeout result: Stage 4 interconnection/no-double-count contracts `8 passed`; Stage 0-4 v0.2.2 contracts `40 passed`; full PFI pytest `193 passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; `http://127.0.0.1:8501/_stcore/health` returned `ok`.
Latest v0.2.2 Stage 5 target result: Stage 5 ledger taxonomy contracts `5 passed`; Stage 0-5 v0.2.2 contracts `45 passed`; full PFI pytest `203 passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; Streamlit app compile `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; `/Applications/PFI.app` launched canonical PFI on port `8501`, PID `87045`; browser validation confirmed PFI 首页、数据源上传、投资管理、消费管理、AUD/CNY 徽标和原生上传控件可见，nested expander error `false`, console errors `0`, screenshot `/tmp/pfi-v022-stage5-app-verified.png`.

## Next

1. 下一轮 pursuing goal 应从 v0.2.2 Stage 6 `标签系统与自定义视图` 开始。
2. 不得提前实现 Stage 7-13，不得修改 v0.2.1 Web Shell UIUX 基线，除非用户单独开启前端目标。
