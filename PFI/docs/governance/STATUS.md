# STATUS

当前状态：PFI v0.2.2 数据库治理已完成 Stage 3 数据源、账户角色与可扩展结构；PFI V0.2 本地 synthetic/read-only MVP 可运行、可验证、可回滚，但不声明生产就绪。

已记录事实：Stage 1 信息架构、Stage 2 多数据源合同、Stage 3 首页/账户/账本/低操作 UX read-model、Stage 4 投资/消费分析 read-model、Stage 5 建议/报告/Alpha 只读 context export、Stage 6 synthetic E2E / 20 gate audit / ACC-* audit / rollback plan、顶层 QBVS lifecycle smoke、本机 PFI.app 入口、实盘和支付提交禁止边界。

v0.2.1 Stage 0 新事实：正式前端目标为 `PFI/web` HTML Web Shell；系统基准货币为 CNY；所有页面顶部右上角必须展示 `CNY/AUD=4.70（YYYYMMDD--HH:MM）`，读取当日 06:00 Australia/Sydney 汇率快照；多模态反馈、触感、声音、视觉、通知和运行反馈控制台后续收敛到设置页。

v0.2.2 Stage 1 新事实：`PFI/config/pfi_parameters.yaml` 是唯一机器可读参数源；`PFI/模型参数文件.md` 是中文解释源；`PFI/tests/test_pfi_parameters_consistency.py` 验证 Markdown/YAML/前端核心参数一致。

v0.2.2 Stage 2 新事实：当前顶部汇率徽标为 `AUD/CNY=4.69（YYYYMMDD--HH:MM）`，真实本地快照为 `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json`，`1 AUD = 4.6874 CNY`；普通运行只读本地快照，不默认联网，缺失快照显示 `汇率数据待更新`。

v0.2.2 Stage 3 新事实：`PFI/src/pfi_v02/stage_v022_source_profile.py` 建立 source profile schema、capabilities、`other_source_template`、账户多角色、`role_effective_from` / `role_effective_to` 和按 role/event type 计算合同；下一轮默认从 Stage 4 `Economic Event 与 Interconnection 逻辑` 开始。
