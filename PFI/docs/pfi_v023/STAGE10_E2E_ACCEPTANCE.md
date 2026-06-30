# PFI v0.2.3 Stage 10 E2E Acceptance

## Stage 10 Phase 10.1

Stage 10 Phase 10.1 入口 E2E 已完成候选验收，覆盖：

- app 打开验证：`~/Downloads/PFI.app` dry-run 指向当前 checkout，并通过 app 入口版本参数打开同一 Streamlit UI。
- localhost 打开验证：`http://127.0.0.1:8501` 健康，浏览器截图显示当前 PFI UI。
- build/hash 一致验证：运行时 metadata 的 web bundle hash 与当前 checkout 磁盘 manifest 一致。
- 清缓存验证：仅执行 dry-run，删除 0 项，未触碰报告、持仓、导入、SQLite 或市场 bar cache。

## Evidence

证据包位置：`PFI/reports/pfi_v023/stage_10/phase_10_1/`

已记录：

- `browser_validation.json`
- `build_hash_consistency.json`
- `cache_cleanup_dry_run.json`
- `screenshots/app_entry.png`
- `screenshots/localhost.png`

## Stage 10 Phase 10.2

Stage 10 Phase 10.2 导航和页面 E2E 已完成候选验收，覆盖：

- 10 个入口点击：按 v0.2.3 固定 10 个一级入口逐个点击并截图。
- 二级页点击：每个一级入口至少点击一个主要二级页并截图。
- 前进/后退：浏览器 back 从账本流水回到账户与资产，forward 再回到账本流水。
- 移动端基础验收：390 x 844 视口截图，移动端导航存在 10 个入口。

证据包位置：`PFI/reports/pfi_v023/stage_10/phase_10_2/`

已记录：

- `browser_validation.json`
- `screenshots/entries/*.png`
- `screenshots/secondary/*.png`
- `screenshots/mobile_basic.png`

## Stage 10 Phase 10.3

Stage 10 Phase 10.3 数据和报告 E2E 已完成候选验收，覆盖：

- 核心指标状态：确认首页指标显示真实数据来源、真实非零流水金额和待复核数量；0 值必须有可见解释。
- 数据检查板：打开数据源与上传路径，确认数据源状态和待复核队列可解释。
- 报告中心：打开报告与洞察月报路径，确认报告结论或阻断原因可见。
- 错误状态路径：打开市场与研究市场观察路径，确认空态说明、阻断原因和下一步可见。

证据包位置：`PFI/reports/pfi_v023/stage_10/phase_10_3/`

已记录：

- `browser_validation.json`
- `core_metrics_state.json`
- `data_check_board.json`
- `report_center.json`
- `error_state_paths.json`
- `screenshots/*.png`

## Stage 10 Whole-stage Review

Stage 10 Whole-stage Review 已完成本地整阶段复审，覆盖：

- app 入口：`~/Downloads/PFI.app` dry-run 成功，项目绑定当前 checkout。
- localhost：`http://127.0.0.1:8501` 与 app 入口展示同一正式 PFI UI。
- 10 个一级入口：全部逐项点击通过。
- 二级页面：每个一级入口至少一个二级 tab 点击通过。
- 核心指标：`本月支出 CNY 7,153.98` 和 `待复核交易 406` 来自 MetaDatabase 真实支付宝流水；0 值均有来源或缺口说明。
- 报告中心：可打开，并展示月报阻断原因和数据门禁说明。
- 浏览器历史：back / forward 在账户与资产和账本流水之间通过。
- 证据完整性：整阶段 review 包含 screenshot 和 JSON。

证据包位置：`PFI/reports/pfi_v023/stage_10/whole_stage_review/`

已记录：

- `browser_validation.json`
- `evidence.json`
- `changed_files.txt`
- `terminal.log`
- `screenshots/app_entry_review.png`
- `screenshots/navigation_review.png`
- `screenshots/data_report_review.png`
- `screenshots/mobile_review.png`

## Stage Closeout

Stage 10 自动验收与真实浏览器复审已通过。用户手动验收仍需用户在本轮最终报告后按 checklist 实际点击确认，Codex 不冒充用户确认。

GitHub main upload terminal gate：本文件所在 Stage 10 closeout commit 推送后，通过 `git fetch origin main`、`git rev-parse HEAD`、`git rev-parse origin/main` 和 ahead/behind 结果验证远端一致。由于 commit hash 不能在同一 commit 内自包含，最终 GitHub main commit 以本轮 terminal 验证和最终报告为准。

本轮未创建、填充或替换任何财务数据；所有可见金额和流水状态来自当前本机 PFI 运行态与 MetaDatabase 读取结果。

本轮未进入 Stage 11。
