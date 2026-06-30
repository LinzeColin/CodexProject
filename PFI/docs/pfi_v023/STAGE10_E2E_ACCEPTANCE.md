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

## Scope Guard

Stage 10 whole-stage review 未执行。

GitHub main upload 未执行。

本轮未创建、填充或替换任何财务数据；所有可见金额和流水状态来自当前本机 PFI 运行态与 MetaDatabase 读取结果。
