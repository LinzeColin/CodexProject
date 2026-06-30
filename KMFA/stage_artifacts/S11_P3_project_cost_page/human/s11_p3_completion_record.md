# S11-P3｜项目成本页面完成记录

更新时间: 2026-07-01

## 范围

本次只完成 `S11-P3｜项目成本页面`。范围包括 public-safe 项目列表、项目详情、来源证据、待处理事项和报告预览页面；不执行 Stage 11 整体复审、GitHub upload、S12、lineage full check、正式报告或外部接口。

## 输入基线

- `S11-P1｜首页与导航` 已本地验证完成。
- `S11-P2｜数据源检查板` 已本地验证完成。
- `S09-P1｜项目成本事实层` 提供 4 条 public-safe 项目 fact records 和 9 类成本分类。
- `S09-P2｜毛利与现金毛利` 提供 4 条 public-safe margin records。
- `S09-P3｜口径转换与差异核对` 保留 12 条 pending owner/授权复核记录。
- `S10-P2/S10-P3` 保留 D 级报告门禁和 public-safe 报告预览边界。
- 已读取 v1.2 HTML/UIUX 项目成本专题报告预览样板。

## 输出

- `KMFA/tools/project_cost_page_runtime.py`
- `KMFA/tools/check_s11_p3_project_cost_page.py`
- `KMFA/tests/test_project_cost_page_runtime.py`
- `KMFA/metadata/reports/project_cost_page_manifest.json`
- `KMFA/metadata/reports/project_cost_page_projects.jsonl`
- `KMFA/stage_artifacts/S11_P3_project_cost_page/machine/s11_p3_manifest.json`
- `KMFA/stage_artifacts/S11_P3_project_cost_page/exports/html/kmfa_project_cost_page.html`

## 验收映射

| 任务 | 验收状态 | 证据 |
|---|---|---|
| T1 项目列表、毛利、成本结构、回款、差异状态 | `completed_validated_local_only` | `project_cost_page_projects.jsonl`, `kmfa_project_cost_page.html` |
| T2 项目详情展示来源证据和待处理事项 | `completed_validated_local_only` | `project_cost_page_manifest.json`, `kmfa_project_cost_page.html` |
| T3 报告预览可直接查看，但不可绕过质量等级 | `completed_validated_local_only` | `project_cost_page_manifest.json`, `check_s11_p3_project_cost_page.py` |

## 门禁状态

- `report_preview_direct_view_allowed=true`
- `report_grade_visible=D`
- `quality_grade_bypass_allowed=false`
- `report_grade_bypass_allowed=false`
- `formal_report_allowed=false`
- `complete_trusted_report_display_allowed=false`
- `business_decision_basis_allowed=false`
- `stage11_review_allowed=false`
- `github_upload_allowed=false`

## Public-safe 边界

本次新增输出不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、真实金额、真实账号、字段明文、私有来源明文或 credentials。页面和 manifest 只保存 public-safe 项目分组、受控状态、计数、证据引用和质量门禁结果。

## 未完成

Stage 11 整体复审、GitHub upload、S12、lineage full check、正式报告、差异关闭、派生指标重跑和外部接口仍未执行。下一步只能执行 Stage 11 整体复审。
