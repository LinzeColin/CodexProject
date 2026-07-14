# KMFA v0.1.4 S10-P3 Risk Register

| Risk | Control | Status |
|---|---|---|
| D 级报告被误用为正式经营报告 | manifest/validator 保持 formal_report_allowed=false 与 business_decision_basis_allowed=false | controlled |
| CSV/HTML 导出泄露 raw/private 值 | validator 扫描 evidence 文本并复用 public-safe legacy exports | controlled |
| PDF/Excel workbook 误提交 | policy 与 validator 要求 committed_pdf_file_count=0、committed_excel_file_count=0 | controlled |
| 单 phase 越界进入 Stage 10 review 或 GitHub upload | phase boundaries 与 validator 均要求 false | controlled |
