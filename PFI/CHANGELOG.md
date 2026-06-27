# CHANGELOG

## 0.2.0 - 2026-06-27

- PFI 根项目确认为当前注册项目根。
- 三基人类入口统一为 Markdown 文件：`功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- 补齐最小治理文件，记录 Stage 1/2 合同事实和生产未验证边界。
- 完成 PFI V0.2 Stage 2 本地合同验收，覆盖 phases 2A-2H。
- 新增 `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`，记录 phase/task evidence、stop-condition checks、validation results、本地 app-entry evidence 和缓存清理证据。
- 完成 PFI V0.2 Stage 3 本地可读 MVP，覆盖首页总览、账户地图、账本流水、待复核、同步全部、建议和报告入口。
- 新增 `src/pfi_v02/stage3_read_mvp.py` 与 `tests/test_stage3_readable_mvp.py`，将 Stage 3 3A-3D acceptance 固化为本地合同测试。
- Web shell 默认首页接入 Stage 3 read-model，左侧显示 V0.2 8 个一级入口；旧策略回测、盘感训练、大数据模拟器和 QBVS 兼容入口保留。
- 完成 PFI V0.2 Stage 4 投资与消费智能分析 MVP，覆盖投资总览、收益归因、风险分析、行为复盘、消费总览、分类分析、订阅检测、异常消费和现金流预测。
- 新增 `src/pfi_v02/stage4_analysis_mvp.py` 与 `tests/test_stage4_analysis_mvp.py`，将 Stage 4 4A/4B acceptance 固化为本地合同测试。
- Web shell 首页、投资管理和消费管理接入 Stage 4 analysis read-model；旧策略回测、盘感训练、大数据模拟器和 QBVS 独立系统引用继续保留。
- 完成 PFI V0.2 Stage 5 建议、报告、Alpha 只读出口 MVP，覆盖 recommendation model、review lifecycle、投资建议、消费建议、Top N ranking、四类报告、导出中心和 `pfi_context_snapshot_v1`。
- 新增 `src/pfi_v02/stage5_advice_report_alpha.py` 与 `tests/test_stage5_advice_report_alpha.py`，将 Stage 5 5A/5B/5C acceptance 固化为本地合同测试。
- Web shell 首页、建议与复盘、报告与洞察接入 Stage 5；仍保持 8 个一级入口，不新增 Alpha/Ralpha/System/Development 产品入口。
- 生产联通、真实账户凭证、支付提交、券商下单、Alpha repo 修改和实盘交易仍为独立后续 gate，未在 Stage 5 声明就绪。
- 完成 PFI V0.2 Stage 6 端到端验收与稳定化，覆盖 synthetic 多数据源、首页闭环、账本闭环、建议闭环、回归治理、交付回滚和 20 个总验收 gate。
- 新增 `src/pfi_v02/stage6_e2e_stabilization.py` 与 `tests/test_stage6_e2e_stabilization.py`，将 Stage 6 6A/6B/6C acceptance 固化为本地合同测试。
- Web shell 首页和报告与洞察接入 Stage 6；仍保持 8 个一级入口，不新增外部系统产品入口，QBVS 顶层独立且 PFI 不覆盖 QBVS。
- Stage 6 仍只证明本地 synthetic/read-only V0.2 可运行、可验证、可回滚；真实数据连接、外部 context consumer、PDF/ZIP、CDR/Open Banking 和生产发布证据为后续独立 gate。
