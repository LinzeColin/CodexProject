# S06-P2 跨源差异队列完成记录

## 范围

- Stage/Phase: `S06-P2`
- Task: `S6PBT01-S6PBT03`
- 目标: 对 PDF 与 Excel 同项目同字段金额冲突建立 public-safe 差异队列和报告等级阻断证据。

## 已完成

- 新增 `KMFA/tools/cross_source_difference_queue.py`。
- 新增 `KMFA/tools/check_s06_p2_difference_queue.py`。
- 新增 `KMFA/tests/test_cross_source_difference_queue.py`。
- 新增 public-safe synthetic PDF/Excel 同项目 1 分差异 fixture、差异队列 JSONL 和报告等级 gate JSON。

## 任务映射

- `S6PBT01`: PDF 与 Excel 同项目同字段冲突通过 `build_pdf_excel_difference_queue_item` 进入 `cross_source_difference_queue_item`。
- `S6PBT02`: 队列项强制 `auto_correction_allowed=false`、`averaging_allowed=false`、`rounding_mask_allowed=false`、`auto_selection_allowed=false`，并拒绝 float 金额。
- `S6PBT03`: 未关闭差异通过 `evaluate_report_grade_gate` 阻断 A 级报告，`report_grade_a_allowed=false`、`maximum_report_grade=B`、`hard_block_reason=unresolved_critical_difference`。

## 边界

- 只使用合成 fixture；不读取 Excel、PDF、zip、私有 CSV 或真实业务源文件。
- 只保存 public-safe source id、source class、synthetic anchor、整数分差异和证据索引；不保存真实字段明文。
- 不写入 `KMFA/metadata/quality/source_difference_queue.jsonl` 的运行时业务差异项；本 phase 只交付队列工具、validator 和 stage evidence。
- 不关闭差异、不自动选择 PDF 或 Excel 任一来源、不平均、不四舍五入掩盖。
- 不实现 S06-P3 metadata/quality 运行时证据输出、不做事实层、UI、正式报告、Stage 6 复审或 GitHub upload。

## 回滚

- 删除 `KMFA/tools/cross_source_difference_queue.py`。
- 删除 `KMFA/tools/check_s06_p2_difference_queue.py`。
- 删除 `KMFA/tests/test_cross_source_difference_queue.py`。
- 删除 `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/`。
- 恢复 S06-P2 governance/status 记录为 planned。
