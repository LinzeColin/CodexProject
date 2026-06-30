# KMFA Development Ledger

product_version: 0.1.0-s10-stage-review

## Current Iteration

- project_id: `KMFA`
- current_stage: `S10`
- current_phase: `S10-GITHUB-UPLOAD｜待开始`
- current_tasks: `KMFA-S10-GITHUB-UPLOAD-20260630`
- status: `s10_stage_review_passed_local_only_pending_github_upload`
- risk_tier: `T3`

## Completed

| Task | Result | Evidence |
|---|---|---|
| `S1PAT01-S1PAT03` | S01-P1 只读计划完成 | `KMFA/stage_artifacts/S01_P1_read_only_plan/` |
| `S1PBT01` | 项目骨架与中文入口创建 | `KMFA/README.md`, `KMFA/功能清单.md`, `KMFA/开发记录.md`, `KMFA/模型参数文件.md` |
| `S1PBT02` | governance/project 配置草案登记 | `governance/projects.yaml`, `KMFA/docs/governance/project.yaml` |
| `S1PBT03` | 时间参考规则与上传规则写入 | `KMFA/AGENTS.md`, `KMFA/HANDOFF.md` |
| `S1PCT01` | 完整需求追溯矩阵导入 | `KMFA/metadata/traceability/requirements.csv` |
| `S1PCT02` | 正式 no_omission 检查脚本导入并通过 | `KMFA/tools/no_omission_check.py` |
| `S1PCT03` | Stage/Phase/Task 状态登记建立 | `KMFA/metadata/stage_status.jsonl` |
| `KMFA-S01-STAGE-REVIEW-20260629` | Stage 1 总复审通过，上传限定为隔离 worktree | `KMFA/stage_artifacts/S01_STAGE_REVIEW/human/stage1_review_report.md` |
| `S2PAT01` | metadata 七类目录和目录 manifest 创建 | `KMFA/metadata/protocol/directory_manifest.json` |
| `S2PAT02` | metadata 核心标识符协议定义 | `KMFA/metadata/protocol/metadata_protocol.yaml` |
| `S2PAT03` | metadata 公开仓库隐私边界和检查器建立 | `KMFA/docs/governance/METADATA_PROTOCOL.md`, `KMFA/tools/metadata_protocol_check.py` |
| `S2PBT01` | raw manifest append-only 登记规范建立 | `KMFA/metadata/imports/raw_manifest_schema.json`, `KMFA/metadata/imports/raw_manifest_policy.yaml` |
| `S2PBT02` | 派生数据版本、失效、重跑、对比协议建立 | `KMFA/metadata/lineage/derived_data_policy.yaml`, `KMFA/metadata/lineage/derived_data_versions.jsonl` |
| `S2PBT03` | 前端/人工 control event raw 写入边界建立 | `KMFA/metadata/approvals/control_event_policy.yaml`, `KMFA/metadata/approvals/control_events.jsonl` |
| `S2PCT01` | Q0-Q5 数据质量等级定义建立 | `KMFA/docs/governance/QUALITY_GATE_POLICY.md`, `KMFA/metadata/quality/quality_grade_policy.yaml` |
| `S2PCT02` | A/B/C/D 报告可信等级定义建立 | `KMFA/metadata/reports/report_grade_policy.yaml`, `KMFA/metadata/reports/report_manifest.jsonl` |
| `S2PCT03` | 质量等级到报告发布权限门禁建立 | `KMFA/metadata/reports/report_release_gate.yaml`, `KMFA/tools/check_report_grade_gate.py` |
| `KMFA-S02-STAGE-REVIEW-20260629` | Stage 2 整体复审通过，上传路径可用 | `KMFA/stage_artifacts/S02_STAGE_REVIEW/human/stage2_review_report.md` |
| `KMFA-S02-GITHUB-UPLOAD-20260629` | Stage 2 整体上传 GitHub main | `834ff75516405ddbc8289f00ba67579691473709` |
| `KMFA-S01-V12-REBASE-20260629` | v1.2 完整任务包承接并重放 Stage 1；45 个 HTML/7 个核心样板进入基线 | `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/human/stage1_v12_replay_report.md` |
| `S3PAT01-S3PAT03` | S03-P1 文件型导入登记、安全解包、hash/size/import_run/source package metadata 和 WPS/OLE 提示完成 | `KMFA/stage_artifacts/S03_P1_file_import/human/s03_p1_completion_record.md` |
| `S3PBT01-S3PBT03` | S03-P2 数据源检查矩阵、五状态枚举和 metadata-only 状态事件完成 | `KMFA/stage_artifacts/S03_P2_source_check_matrix/human/s03_p2_completion_record.md` |
| `S3PCT01-S3PCT03` | S03-P3 源优先级、同源失效重跑事件和跨源差异队列入口完成 | `KMFA/stage_artifacts/S03_P3_source_priority/human/s03_p3_completion_record.md` |
| `KMFA-S03-STAGE-REVIEW-20260629` | Stage 3 整体复审通过，源优先级链路对齐 finding 已修复 | `KMFA/stage_artifacts/S03_STAGE_REVIEW/human/stage3_review_report.md` |
| `KMFA-S03-GITHUB-UPLOAD-20260629` | Stage 3 整体上传 GitHub main | `39b0eef52424a12b6c0c8ad368bd878b46300be4` |
| `S4PAT01-S4PAT03` | S04-P1 金额标准化、no-float 检查和异常输入拒绝策略完成 | `KMFA/stage_artifacts/S04_P1_amount_tools/human/s04_p1_completion_record.md` |
| `S4PBT01-S4PBT03` | S04-P2 字段标准化、字段别名字典和缺字段质量状态完成 | `KMFA/stage_artifacts/S04_P2_field_standardization/human/s04_p2_completion_record.md` |
| `S4PCT01-S4PCT03` | S04-P3 基础工具边界测试和工具函数测试报告完成 | `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/s04_p3_completion_record.md` |
| `KMFA-S04-STAGE-REVIEW-20260629` | Stage 4 整体复审通过，owner-readable 金额工具详情缺口已修复 | `KMFA/stage_artifacts/S04_STAGE_REVIEW/human/stage4_review_report.md` |
| `KMFA-S04-GITHUB-UPLOAD-20260629` | Stage 4 final GitHub upload 已完成 | `KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md` |
| `S5PAT01-S5PAT03` | S05-P1 A0 文件登记、A0 项目候选清单和 Q3/Q4 状态完成本地验证 | `KMFA/stage_artifacts/S05_P1_a0_file_registration/human/s05_p1_completion_record.md` |
| `S5PBT01-S5PBT03` | S05-P2 public-safe 字段合同、45 条 A0 golden fixture 候选、40 条 PDF 字段 hash/source anchor 和 Excel owner/授权降级决策完成本地验证 | `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/owner_decision_record.md` |
| `S5PCT01-S5PCT03` | S05-P3 A0 authority baseline lock 完成本地验证：40 条 PDF 字段锁定为 Q5 calculation baseline，5 条 Excel 字段排除为 cross-source support only | `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/s05_p3_completion_record.md` |
| `KMFA-S05-STAGE-REVIEW-20260630` | Stage 5 整体复审本地通过，GitHub upload 未执行 | `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md` |
| `KMFA-S05-GITHUB-UPLOAD-20260630` | Stage 5 final GitHub upload 已完成 | `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` |
| `S6PAT01-S6PAT03` | S06-P1 零差异校验器完成本地验证：逐字段比较整数分，任意 1 分差异失败并生成 public-safe mismatch report | `KMFA/stage_artifacts/S06_P1_zero_delta_validator/human/s06_p1_completion_record.md` |
| `S6PBT01-S6PBT03` | S06-P2 跨源差异队列完成本地验证：PDF/Excel 同项目冲突进入人工队列，未关闭差异阻断 A 级报告 | `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/human/s06_p2_completion_record.md` |
| `S6PCT01-S6PCT03` | S06-P3 校验证据输出完成本地验证：zero-delta summary、sanitized mismatch index、project validation status 和 metadata/quality records 已生成 | `KMFA/stage_artifacts/S06_P3_validation_evidence_output/human/s06_p3_completion_record.md` |
| `KMFA-S06-STAGE-REVIEW-20260630` | Stage 6 整体复审本地通过，复审步骤未执行 GitHub upload | `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md` |
| `KMFA-S06-GITHUB-UPLOAD-20260630` | Stage 6 final GitHub upload 已完成 | `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` |
| `S7PAT01-S7PAT03` | S07-P1 财务文件适配完成本地验证：9 类财务支撑源登记、45 条 hash-only 字段候选和 9 条只读字段报告已生成 | `KMFA/stage_artifacts/S07_P1_finance_file_adapter/human/s07_p1_completion_record.md` |
| `S7PBT01-S7PBT03` | S07-P2 WPS 文件适配完成本地验证：4 类 WPS 导出、20 条 hash-only 字段映射、4 条转换提示、4 条只读字段报告和 1 个映射规则版本已生成 | `KMFA/stage_artifacts/S07_P2_wps_file_adapter/human/s07_p2_completion_record.md` |
| `S7PCT01-S7PCT03` | S07-P3 红圈导出后置策略完成本地验证：4 类红圈导出模板已预留，D15 自动接口已阻断，后续只读/hash/rollback/manual approval 控制已建立 | `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md` |
| `KMFA-S07-STAGE-REVIEW-20260630` | Stage 7 整体复审本地通过，复审步骤未执行 GitHub upload | `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md` |
| `KMFA-S07-GITHUB-UPLOAD-20260630` | Stage 7 final GitHub upload 已完成 | `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md` |
| `S8PAT01-S8PAT03` | S08-P1 项目组合键完成本地验证：8 个 hash-only 身份组件、整数权重、单字段缺失不全阻断和人工复核队列已生成 | `KMFA/stage_artifacts/S08_P1_project_composite_key/human/s08_p1_completion_record.md` |
| `S8PBT01-S8PBT03` | S08-P2 业务实体模型完成本地验证：8 类实体、14 条关系、32 条生命周期状态和 schema metadata 已生成 | `KMFA/stage_artifacts/S08_P2_business_entity_model/human/s08_p2_completion_record.md` |
| `S8PCT01-S8PCT03` | S08-P3 匹配质量测试完成本地验证：4 类 public-safe 质量场景、4 条 quality cases、3 条人工复核队列和 entity_matching_report 已生成 | `KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/s08_p3_completion_record.md` |
| `KMFA-S08-STAGE-REVIEW-20260630` | Stage 8 整体复审本地通过，复审步骤未执行 GitHub upload | `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/stage8_review_report.md` |
| `KMFA-S08-GITHUB-UPLOAD-20260630` | Stage 8 final GitHub upload 已完成 | `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` |
| `S9PAT01-S9PAT03` | S09-P1 项目成本事实层完成本地验证：6 个 fact metric slots、4 条 project cost fact records、9 条 unallocated project cost pool records；保留 S06/S08 质量阻断，不执行 S09-P2/S09-P3、Stage 9 review 或 GitHub upload | `KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/s09_p1_completion_record.md` |
| `S9PBT01-S9PBT03` | S09-P2 毛利与现金毛利完成本地验证：4 条 project margin records、12 条 scope difference summary records；权威显示值和系统复算值分开保留，不执行 S09-P3、Stage 9 review 或 GitHub upload | `KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/s09_p2_completion_record.md` |
| `S9PCT01-S9PCT03` | S09-P3 口径转换与差异核对完成本地验证：12 条 public-safe reconciliation records、6 条 domain controls；记录原因候选、依据 refs、影响范围、责任角色、reviewer 和 pending 状态，不执行 Stage 9 review 或 GitHub upload | `KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md` |
| `KMFA-S09-STAGE-REVIEW-20260630` | Stage 9 整体复审本地通过；复跑 S09-P1/P2/P3 validators、`check_s09_stage_review.py`、全量 KMFA tests、治理 validator、raw/secret scan 和 parse checks，并修复 secret scan 误报 finding；复审步骤未执行 GitHub upload | `KMFA/stage_artifacts/S09_STAGE_REVIEW/human/stage9_review_report.md` |
| `KMFA-S09-GITHUB-UPLOAD-20260630` | Stage 9 final GitHub upload 已完成；基于最新 origin/main rebase Stage 9 栈，复跑 validators、安全扫描和 parse checks，并留下 dry-run push、push 与 post-push parity 证据 | `KMFA/stage_artifacts/S09_STAGE_REVIEW/human/github_upload_record.md` |
| `S10-P1` | S10-P1 报告模板完成本地验证：2 个 public-safe 报告模板、11 个管理可读章节、HTML 样板引用和 scope gate 均已锁定；不执行 S10-P2/S10-P3、Stage 10 review 或 GitHub upload | `KMFA/stage_artifacts/S10_P1_report_templates/human/s10_p1_completion_record.md` |
| `S10-P2` | S10-P2 报告可信等级完成本地验证：基于质量、差异、人工确认和时效判定锁定 2 条报告等级记录为 D；缺关键 lineage、zero-delta 失败和 12 条 pending reconciliation 阻断完整可信报告、正式报告和经营决策依据；每条记录绑定报告版本、公式版本和字段映射版本；不执行 S10-P3、Stage 10 review 或 GitHub upload | `KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/s10_p2_completion_record.md` |
| `S10-P3` | S10-P3 导出完成本地验证：生成 2 个 public-safe HTML 报告、2 个 public-safe CSV 附表、2 个 Excel 兼容 CSV 下载记录和 PDF private-runtime-only 策略；报告等级保持 D，正式报告和经营决策依据继续阻断；不提交 `.xlsx` 或 `.pdf`，不执行 Stage 10 review 或 GitHub upload | `KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md` |
| `KMFA-S10-STAGE-REVIEW-20260630` | Stage 10 整体复审本地通过；复跑 S10-P1/P2/P3 validators、`check_s10_stage_review.py`、全量 KMFA tests、治理 validator、raw/secret scan 和 parse checks；复审步骤未执行 GitHub upload、S11、UI、lineage full check、正式报告或外部接口 | `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/stage10_review_report.md` |

## In Progress

| Task | Result | Evidence |
|---|---|---|
| `KMFA-S10-GITHUB-UPLOAD-20260630` | Stage 10 final GitHub upload 待开始；下一轮只允许对齐最新 origin/main、复跑 S10 validators/治理 validator/raw/secret scan/parse checks，并留下 push proof，不得进入 S11 | `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/stage10_review_report.md` |

## Not Completed

| Task | Reason | Next |
|---|---|---|
| Stage 10 final GitHub upload | Stage 10 review 本轮只完成本地复审；upload 不在本 phase 范围 | 下一轮只执行 Stage 10 final GitHub upload |
| v1.2 私有源数据 | 只能本地私有使用，禁止提交公开 GitHub | 公开仓库只保存 SHA256 清单和禁止提交规则 |
