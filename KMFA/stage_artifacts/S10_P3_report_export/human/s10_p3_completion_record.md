# S10-P3｜导出完成记录

更新时间: 2026-06-30

## 范围

本 phase 只实现 `S10-P3｜导出`：

- HTML 报告优先稳定。
- CSV/Excel 附表可下载。
- PDF 导出在模板稳定后启用。

本 phase 不执行 Stage 10 整体复审、GitHub upload、UI、lineage full check、外部接口或差异关闭。

## 输出

| 类型 | 文件 | 说明 |
|---|---|---|
| runtime | `KMFA/tools/report_export_runtime.py` | 读取 S10-P1 模板和 S10-P2 等级记录，生成 public-safe 导出 metadata、HTML 和 CSV |
| validator | `KMFA/tools/check_s10_p3_report_export.py` | 验证导出数量、格式策略、D 级阻断、公开仓库安全边界和 scope gate |
| unit test | `KMFA/tests/test_report_export_runtime.py` | 覆盖 HTML、CSV、Excel 兼容下载、PDF 私有运行时策略和禁止提交 `.xlsx/.pdf` |
| metadata | `KMFA/metadata/reports/report_export_manifest.json` | S10-P3 导出 manifest |
| metadata | `KMFA/metadata/reports/report_export_records.jsonl` | 2 条 report export records |
| machine evidence | `KMFA/stage_artifacts/S10_P3_report_export/machine/s10_p3_manifest.json` | S10-P3 machine manifest |
| HTML export | `KMFA/stage_artifacts/S10_P3_report_export/exports/html/project_cost_special_report.html` | 项目成本专题报告 public-safe HTML |
| HTML export | `KMFA/stage_artifacts/S10_P3_report_export/exports/html/business_overview_report.html` | 经营总览报告 public-safe HTML |
| CSV appendix | `KMFA/stage_artifacts/S10_P3_report_export/exports/csv/project_cost_special_report_appendix.csv` | 项目成本专题报告 public-safe 附表 |
| CSV appendix | `KMFA/stage_artifacts/S10_P3_report_export/exports/csv/business_overview_report_appendix.csv` | 经营总览报告 public-safe 附表 |

## 结果

- `report_export_record_count=2`
- `html_export_count=2`
- `csv_appendix_count=2`
- `excel_compatible_download_count=2`
- `pdf_export_enabled_after_template_stable=true`
- `committed_excel_file_count=0`
- `committed_pdf_file_count=0`
- `grade_distribution={"D": 2}`
- `formal_report_allowed=false`
- `business_decision_basis_allowed=false`
- `stage10_review_allowed=false`
- `github_upload_allowed=false`

## HTML 样板继承

已读取并继承 v1.2 HTML / UIUX / 报告样板约束：

- `KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/HTML文件索引_v1_2.csv`
- `KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_经营分析报告预览_v3_blue.html`
- `KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/01_核心HTML验收样板/KMFA_项目成本专题报告预览_v0_6_blue_zero_delta.html`
- `KMFA/taskpack/v1_2/00_总索引与补漏复核/KMFA_HTML_UIUX_报告样板强制继承规范_v1_2.md`

本 phase 输出的 HTML 保留蓝色商务风、报告等级可见、限制说明可见、先结论后证据的结构；不展示内部 source refs、validator、manifest 或 metadata 字段。

## 边界

- 不提交 raw business data。
- 不提交 zip、Excel workbook、PDF、sqlite/db、私有 CSV。
- 不提交字段明文、真实金额、账号凭证、token 或 API key。
- Excel 附表下载通过 public-safe CSV 兼容格式实现，不提交 `.xlsx`。
- PDF 导出只作为模板稳定后的私有运行时策略启用，不提交 `.pdf`。
- S09-P3 仍有 12 条 pending owner/授权复核记录；报告等级保持 D，完整可信报告、正式报告和经营决策依据继续阻断。

## 下一步

S10 三个 phase 已完成本地实现。下一步只能执行 Stage 10 整体复审，复审并修复 findings 后才允许整体上传 GitHub。
