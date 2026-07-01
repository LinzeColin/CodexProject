# KMFA｜经营分析系统

KMFA 是面向 C-level management / board 的经营分析系统。当前优先级是文件型项目成本分析 MVP：先建立项目治理、数据治理、金额精度、零差异、差异队列、人工处理事件、重跑链路和可追溯经营报告基础。

## 当前状态

| 项目 | 内容 |
|---|---|
| project_id | `KMFA` |
| 当前版本 | `0.1.0-s18-github-upload` |
| 当前 Stage | `S18｜回归、压力、稳定验收与后续接入准备` |
| 当前 Phase | `Stage 18 GitHub Upload｜已完成` |
| 当前 Task | `KMFA-S18-GITHUB-UPLOAD-20260701` |
| 风险等级 | `T3`，涉及经营数据、金额、税务、隐私和公开仓库边界 |
| GitHub 目录 | `LinzeColin/CodexProject/KMFA` |
| 当前基线 | `KMFA/taskpack/v1_2`，源包 SHA256 `3bb2ebf16fb4ad8b9d198484e9d80ea2aed3c19c54c483efebe023b772ad0e66` |
| Stage 上传规则 | 中间 Phase 不上传 GitHub；Stage 5、Stage 6、Stage 7、Stage 8、Stage 9、Stage 10、Stage 11、Stage 12、Stage 13、Stage 14、Stage 15、Stage 16、Stage 17 和 Stage 18 均已完成三个 Phase、整体复审和 GitHub upload；Stage 18 review-level Go/No-Go 仍为 `NO_GO`；lineage full check、正式报告和业务执行仍不得跳过门禁 |

## 双平面结构

### 人类可读面

| 文件 | 用途 |
|---|---|
| `README.md` | 项目入口、范围、状态、运行边界 |
| `功能清单.md` | 面向 owner 的功能、限制、证据和下一任务 |
| `开发记录.md` | Stage -> Phase -> Task 开发记录、验收、风险、回滚 |
| `模型参数文件.md` | 模型、公式、参数、质量门禁和验证状态 |
| `HANDOFF.md` | 跨线程交接摘要 |

### 机器可读面

| 文件/目录 | 用途 |
|---|---|
| `docs/governance/project.yaml` | Lean v2 项目事实 |
| `docs/governance/roadmap.yaml` | Lean v2 Roadmap 事实 |
| `docs/governance/events.jsonl` | Lean v2 事件 |
| `docs/governance/*` | v1 兼容治理文件 |
| `metadata/project/project.yaml` | KMFA 内部项目配置草案 |
| `metadata/stage_status.jsonl` | Stage/Phase/Task 状态登记草案 |
| `metadata/model_registry.yaml` | KMFA 内部模型参数机器镜像草案 |
| `metadata/imports/file_import_policy.yaml` | S03-P1 文件型导入登记、安全解包、WPS/OLE 提示和公开仓库禁止项 |
| `metadata/sources/source_check_matrix_policy.yaml` | S03-P2 数据源检查矩阵维度、状态枚举和 metadata-only 状态事件策略 |
| `metadata/sources/source_priority_policy.yaml` | S03-P3 原始/授权/处理后数据优先级、同源失效重跑和跨源差异队列策略 |
| `metadata/schema_maps/field_standardization_policy.yaml` | S04-P2 字段标准化、缺字段质量状态和 no-raw-write 策略 |
| `metadata/schema_maps/field_alias_dictionary.csv` | S04-P2 通用字段别名字典和中文字段映射 |
| `metadata/schema_maps/finance_file_adapter_manifest.json` | S07-P1 财务文件适配 manifest，记录 9 类财务支撑源、45 条字段候选、只读解析状态和公开仓库安全边界 |
| `metadata/schema_maps/finance_field_candidates.jsonl` | S07-P1 财务字段候选映射，只保存 canonical field、source_header_hash、private ref 和质量状态 |
| `metadata/imports/finance_support_source_registry.json` | S07-P1 财务支撑源登记，只保存 source_ref、file_hash、private ref 和只读解析状态 |
| `metadata/schema_maps/wps_file_adapter_manifest.json` | S07-P2 WPS 文件适配 manifest，记录 4 类 WPS 导出、20 条字段映射、转换提示、版本化规则和公开仓库安全边界 |
| `metadata/schema_maps/wps_field_mappings.jsonl` | S07-P2 WPS 字段映射，只保存 canonical field、source_header_hash、private ref、mapping rule version 和质量状态 |
| `metadata/schema_maps/wps_mapping_rule_versions.json` | S07-P2 WPS 映射规则版本登记，当前 active 版本为 `MAP-SRC-kmfa-wps-file-adapter-s07p2-v0.1.0` |
| `metadata/imports/wps_export_source_registry.json` | S07-P2 WPS 导出源登记，只保存 source_ref、converted file hash、private ref 和转换状态 |
| `metadata/schema_maps/redcircle_postponement_manifest.json` | S07-P3 红圈导出后置策略 manifest，记录 4 类预留模板、D15 自动接口禁止、后续只读/hash/rollback 控制和公开仓库安全边界 |
| `metadata/schema_maps/redcircle_reserved_export_templates.jsonl` | S07-P3 红圈经营、合同、回款、财务 4 类预留模板，只保存 template id、source_ref、template contract hash、private ref 和控制状态 |
| `metadata/schema_maps/redcircle_postponement_policy.yaml` | S07-P3 红圈后置策略，固化 D15 文件型 MVP 不接自动接口以及未来接入必须只读、留 hash、可回滚 |
| `metadata/imports/redcircle_export_source_registry.json` | S07-P3 红圈导出源预留登记，不保存红圈原始导出文件或接口凭证 |
| `metadata/schema_maps/project_composite_key_manifest.json` | S08-P1 项目组合键 manifest，记录 8 个 hash-only 身份组件、整数权重、阈值、匹配数量和人工复核边界 |
| `metadata/schema_maps/project_identity_profiles.jsonl` | S08-P1 public-safe 项目身份 profile，只保存组件 hash、private ref、质量状态和组合键 hash |
| `metadata/schema_maps/project_composite_key_matches.jsonl` | S08-P1 项目匹配候选结果，只保存 public-safe profile ref、匹配组件、缺失组件、整数得分和人工复核状态 |
| `metadata/quality/project_identity_review_queue.jsonl` | S08-P1 低于强匹配阈值的人工复核队列，`auto_merge_allowed=false` |
| `metadata/schema_maps/business_entity_model_manifest.json` | S08-P2 业务实体模型 manifest，记录 8 类实体、14 条关系、32 条生命周期状态和公开仓库安全边界 |
| `metadata/schema_maps/business_entity_model_schema.json` | S08-P2 public-safe 业务实体 schema，定义实体字段、上游引用和不写 raw 层约束 |
| `metadata/schema_maps/business_entity_relationships.jsonl` | S08-P2 实体关系图，只保存 controlled relationship metadata |
| `metadata/schema_maps/business_entity_lifecycle_statuses.jsonl` | S08-P2 实体生命周期状态，覆盖 candidate、active、requires_review、closed |
| `docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md` | S08-P2 owner-readable 业务实体模型 schema 文档 |
| `metadata/quality/entity_matching_quality_manifest.json` | S08-P3 匹配质量测试 manifest，记录 4 类 public-safe 质量场景、case 数、人工复核队列数量和 scope boundary |
| `metadata/quality/entity_matching_quality_cases.jsonl` | S08-P3 匹配质量 cases，只保存 public-safe profile/entity/source hash refs、匹配分、风险和证据状态 |
| `metadata/quality/entity_matching_review_queue.jsonl` | S08-P3 中高风险匹配人工复核队列，`auto_merge_allowed=false`、`raw_layer_write_allowed=false` |
| `metadata/quality/field_quality_status.jsonl` | S04-P2 缺字段/无效字段质量状态协议 |
| `metadata/baseline/source_package_v1_2.json` | v1.2 完整任务包机器清单、源包 hash、复制/排除策略 |
| `metadata/baseline/html_acceptance_samples_v1_2.json` | 45 个 HTML 样板与 7 个核心样板的机器清单 |
| `metadata/baseline/a0_authority_baseline_manifest.json` | S05-P3 A0 权威基准锁定 manifest，记录版本、hash、锁定角色、锁定时间和报告/upload gate |
| `metadata/baseline/a0_authority_baseline_records.jsonl` | S05-P3 public-safe field lock/exclusion 记录，不保存字段明文 |
| `metadata/reports/performance_fact_fields_manifest.json` | S15-P1 public-safe 绩效事实字段 manifest，记录 6 个字段、6 条绑定、4 个人工复核字段和工资/奖金/薪资导出阻断 |
| `metadata/reports/performance_fact_field_definitions.jsonl` | S15-P1 绩效事实字段定义，只保存 canonical 字段 ID/标签、事实类型和门禁状态，不保存来源表头明文或真实值 |
| `metadata/reports/performance_fact_field_bindings.jsonl` | S15-P1 绩效字段绑定记录，只保存 upstream artifact refs、hash refs、状态和人工复核引用 |
| `metadata/reports/performance_fact_manual_review_fields.jsonl` | S15-P1 缺失或未锁定字段人工复核标记，不生成 S15-P2 复核清单 |
| `metadata/reports/performance_review_manifest.json` | S15-P2 public-safe 绩效复核清单 manifest，记录 4 条绩效事实行、16 条复核事项和工资/奖金/薪资导出阻断 |
| `metadata/reports/performance_fact_table.jsonl` | S15-P2 绩效事实表，只保存项目 ref、指标状态、evidence refs 和人工复核状态，不保存真实金额或人员明细 |
| `metadata/reports/performance_review_items.jsonl` | S15-P2 异常项目和复核事项清单，覆盖结算速度、回款速度、审计偏差、客情费率四类人工复核字段 |
| `metadata/reports/performance_salary_boundary_manifest.json` | S15-P3 工资项目边界 manifest，记录事实接口预留、未来读取草案、人工审批/发放边界和禁止工资/奖金/薪资导出 |
| `metadata/reports/performance_fact_output_interface_contract.json` | S15-P3 public-safe 绩效事实输出接口契约，只允许 hash/ref/status/evidence 字段，不创建 live API、connector 或导出 |
| `metadata/reports/salary_system_readiness_draft.jsonl` | S15-P3 未来工资系统读取草案，只保存读取准备状态和人工审批/发放边界，不保存薪酬金额或人员明细 |
| `metadata/security/access_security_policy_manifest.json` | S17-P1 权限与安全 manifest，记录 4 类角色、15 类敏感材料禁入策略、5 类审计动作和 scope gate |
| `metadata/security/role_permission_matrix.jsonl` | S17-P1 角色权限矩阵，覆盖 management、finance、reviewer、readonly，所有写入范围限定为 metadata 或只读 |
| `metadata/security/public_repo_sensitive_data_policy.jsonl` | S17-P1 公开仓库敏感材料禁入策略，只允许 private storage 或 hash/ref-only metadata |
| `metadata/security/audit_log_policy.jsonl` | S17-P1 导入、处理、报告、导出、通知五类审计日志策略；通知只记录 policy，不发送完整报告 |
| `metadata/notifications/notification_manifest.json` | S17-P2 通知提醒 manifest，记录 3 类触发器、metadata outbox-only 投递模式和 scope gate |
| `metadata/notifications/notification_rules.jsonl` | S17-P2 通知规则，覆盖报告生成完成、重大风险、数据源缺失三类提醒 |
| `metadata/notifications/notification_events.jsonl` | S17-P2 append-only 通知事件记录，只保存 trigger、role ref、metadata target 和证据引用 |
| `metadata/notifications/notification_dispatch_log.jsonl` | S17-P2 通知 dispatch 日志，记录 `metadata_logged`，不保存收件地址、完整报告正文或附件 |
| `metadata/operations/operations_sop_manifest.json` | S17-P3 运维与 SOP manifest，记录 4 类操作手册、2 条知识索引、2 条演练记录和 scope gate |
| `metadata/operations/operations_runbooks.jsonl` | S17-P3 导入、复核、发布、回滚操作手册，只保存 metadata/manual SOP，不执行生产动作 |
| `metadata/operations/finance_sop_knowledge_index.jsonl` | S17-P3 财务 SOP 与交接材料知识索引，只保存 refs、hashes、roles 和状态 |
| `metadata/operations/error_backup_drill_log.jsonl` | S17-P3 错误处理和备份恢复演练日志，记录 dry-run/manual-only 证据，不做生产恢复 |
| `stage_artifacts/S15_STAGE_REVIEW/` | Stage 15 整体复审证据，复跑 S15-P1/P2/P3 validators、Stage 15 review validator、治理和安全门禁 |
| `stage_artifacts/S15_GITHUB_UPLOAD/` | Stage 15 final GitHub upload 证据，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity |
| `stage_artifacts/S16_STAGE_REVIEW/` | Stage 16 整体复审证据，复跑 S16-P1/P2/P3 validators、Stage 16 review validator、治理和安全门禁；未执行 GitHub upload |
| `stage_artifacts/S16_GITHUB_UPLOAD/` | Stage 16 final GitHub upload 证据，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity |
| `stage_artifacts/S17_P1_access_security/` | S17-P1 权限与安全完成记录、测试结果和 machine manifest；未执行 S17-P2/S17-P3、Stage 17 review 或 GitHub upload |
| `stage_artifacts/S17_P2_notification/` | S17-P2 通知提醒完成记录、测试结果和 machine manifest；未执行外部邮件连接器、S17-P3、Stage 17 review 或 GitHub upload |
| `stage_artifacts/S17_P3_operations_sop/` | S17-P3 运维与 SOP 完成记录、测试结果和 machine manifest；未执行 Stage 17 review、GitHub upload、live connector 或生产恢复 |
| `stage_artifacts/S17_STAGE_REVIEW/` | Stage 17 整体复审证据包，记录 S17-P1/P2/P3 复跑、Stage 17 review validator、治理 validator、raw/secret scan、parse checks 和 local-only upload readiness |
| `stage_artifacts/S18_STAGE_REVIEW/` | Stage 18 整体复审证据包，记录 S18-P1/P2/P3 复跑、Stage 18 review validator、治理 validator、raw/secret scan、parse checks、review-level Go/No-Go 和 local-only upload readiness |
| `stage_artifacts/S17_GITHUB_UPLOAD/` | Stage 17 final GitHub upload 证据，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity |
| `stage_artifacts/S18_GITHUB_UPLOAD/` | Stage 18 final GitHub upload 证据，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity |
| `metadata/traceability/requirements.csv` | 完整需求追溯矩阵，P0/P1 绑定任务、验收、测试、证据 |
| `tools/no_omission_check.py` | 正式防遗漏检查脚本，可在 CI/本地运行 |
| `tools/check_required_html.py` | v1.2 HTML/UIUX/报告样板强制门禁 |
| `tools/file_import_register.py` | S03-P1 文件登记、hash/manifest、私有 storage ref 和 zip 安全解包工具 |
| `tools/source_check_matrix.py` | S03-P2 数据源检查矩阵 row 和状态事件生成工具 |
| `tools/source_priority.py` | S03-P3 源优先级、同源不一致事件和跨源差异队列 metadata 工具 |
| `tools/amount_tools.py` | S04-P1 金额标准化到整数分工具 |
| `tools/check_no_float_money.py` | S04-P1 业务金额 no-float 检查器 |
| `tools/field_standardization.py` | S04-P2 字段别名、日期、期间、主体、项目、客户/对手方和合同编号标准化工具 |
| `tools/generate_tool_test_report.py` | S04-P3 基础工具边界测试报告生成器 |
| `tools/a0_authority_baseline_lock.py` | S05-P3 A0 权威基准锁定生成器 |
| `tools/check_a0_authority_baseline_lock.py` | S05-P3 A0 权威基准锁定 validator |
| `tools/zero_delta_validator.py` | S06-P1 public-safe 整数分零差异校验器 |
| `tools/cross_source_difference_queue.py` | S06-P2 public-safe PDF/Excel 跨源差异队列生成器 |
| `tools/check_s06_p2_difference_queue.py` | S06-P2 跨源差异队列和报告等级阻断 validator |
| `tools/validation_evidence_output.py` | S06-P3 public-safe 校验证据输出和 metadata/quality 写入工具 |
| `tools/check_s06_p3_validation_evidence.py` | S06-P3 stage artifact 与 metadata/quality 证据 validator |
| `tools/access_security_policy.py` | S17-P1 权限、安全和审计策略生成器 |
| `tools/check_s17_p1_access_security.py` | S17-P1 权限、安全和审计策略 validator |
| `tools/notification_reminders.py` | S17-P2 public-safe 通知提醒规则、事件和 metadata dispatch log 生成器 |
| `tools/check_s17_p2_notifications.py` | S17-P2 通知提醒 validator |
| `tools/operations_sop.py` | S17-P3 public-safe 运维手册、知识索引和演练日志生成器 |
| `tools/check_s17_p3_operations_sop.py` | S17-P3 运维与 SOP validator |
| `tools/check_s17_stage_review.py` | Stage 17 review validator，验证 S17-P1/P2/P3 evidence、通知/运维/安全门禁、D 级阻断、no upload/S18/formal/lineage/live connector gate |
| `tools/finance_file_adapter.py` | S07-P1 财务支撑源只读解析、字段候选和 public-safe evidence 生成工具 |
| `tools/check_s07_p1_finance_file_adapter.py` | S07-P1 财务文件适配 validator |
| `stage_artifacts/S07_P1_finance_file_adapter/` | S07-P1 完成记录、测试结果、只读字段报告和 machine manifest |
| `tools/wps_file_adapter.py` | S07-P2 WPS 导出只读结构解析、字段映射、转换提示和版本化规则生成工具 |
| `tools/check_s07_p2_wps_file_adapter.py` | S07-P2 WPS 文件适配 validator |
| `stage_artifacts/S07_P2_wps_file_adapter/` | S07-P2 完成记录、测试结果、WPS 转换提示、只读字段报告和 machine manifest |
| `tools/redcircle_postponement_policy.py` | S07-P3 红圈导出预留模板、自动接口后置策略和 future rollback 控制生成工具 |
| `tools/check_s07_p3_redcircle_postponement.py` | S07-P3 红圈后置策略 validator |
| `stage_artifacts/S07_P3_redcircle_postponement_policy/` | S07-P3 完成记录、测试结果、connector postponement policy、future rollback plan 和 machine manifest |
| `stage_artifacts/S07_STAGE_REVIEW/` | Stage 7 整体复审证据包，记录 S07-P1/P2/P3 复跑、治理 validator、raw/secret scan、parse checks 和 evidence consistency check |
| `tools/project_composite_key.py` | S08-P1 项目组合键生成器和匹配评分工具，使用 hash-only 组件与整数 basis points 权重 |
| `tools/check_s08_p1_project_composite_key.py` | S08-P1 项目组合键 validator，验证组件、权重、阈值、人工复核队列和公开仓库安全边界 |
| `stage_artifacts/S08_P1_project_composite_key/` | S08-P1 完成记录、测试结果和 machine manifest；不包含 Stage 8 review 或 GitHub upload |
| `tools/business_entity_model.py` | S08-P2 业务实体模型生成器，定义实体、关系、生命周期和 public-safe schema |
| `tools/check_s08_p2_business_entity_model.py` | S08-P2 业务实体模型 validator，验证 8 类实体、14 条关系、32 条生命周期状态和 scope boundary |
| `stage_artifacts/S08_P2_business_entity_model/` | S08-P2 完成记录、测试结果和 machine manifest；不包含 S08-P3、Stage 8 review 或 GitHub upload |
| `tools/entity_matching_quality.py` | S08-P3 匹配质量测试生成器，覆盖同名项目、多主体、多账户、多期间质量场景 |
| `tools/check_s08_p3_entity_matching_quality.py` | S08-P3 匹配质量 validator，验证 quality cases、manual review queue、entity_matching_report 和 public-safe 边界 |
| `stage_artifacts/S08_P3_entity_matching_quality/` | S08-P3 完成记录、测试结果、entity_matching_report 和 machine manifest；不包含 Stage 8 review 或 GitHub upload |
| `stage_artifacts/S08_STAGE_REVIEW/` | Stage 8 整体复审证据包，记录 S08-P1/P2/P3 复跑、治理 validator、raw/secret scan、parse checks、evidence consistency check 和 local-only upload readiness |
| `stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` | Stage 8 final GitHub upload 证据，记录 rebase、validators、raw/secret scan、dry-run push、push 和 post-push parity |
| `stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json` | Stage 8 final GitHub upload machine manifest |
| `metadata/reports/report_export_manifest.json` | S10-P3 public-safe 报告导出 manifest，记录 HTML/CSV/Excel-compatible/PDF private-runtime 策略和 scope gate |
| `metadata/reports/report_export_records.jsonl` | S10-P3 报告导出记录，只保存 report id、template id、grade、导出模式和公开安全状态 |
| `metadata/reports/home_navigation_manifest.json` | S11-P1 public-safe 首页导航 manifest，记录 8 个首页模块、KM 标识、蓝色商务风、scope gate 和正式报告阻断 |
| `metadata/reports/home_navigation_modules.jsonl` | S11-P1 首页模块记录，只保存公开安全入口文案、状态标签和导航顺序 |
| `metadata/reports/source_check_board_manifest.json` | S11-P2 public-safe 数据源检查板 manifest，记录固定 11 列、5 种状态、低干扰样式、状态点击详情和 scope gate |
| `metadata/reports/source_check_board_rows.jsonl` | S11-P2 数据源检查板记录，只保存公开安全来源类别、业务板块、包引用、主体分组、账户分组、状态、影响和下一步 |
| `metadata/reports/project_cost_page_manifest.json` | S11-P3 public-safe 项目成本页面 manifest，记录项目列表、项目详情、来源证据、待处理事项、报告预览和质量门禁 |
| `metadata/reports/project_cost_page_projects.jsonl` | S11-P3 项目成本页面记录，只保存公开安全项目分组、毛利/成本/回款/差异状态、证据引用和下一步 |
| `tools/report_export_runtime.py` | S10-P3 public-safe 报告导出 runtime，生成 HTML 预览、CSV 附表和导出 manifest |
| `tools/check_s10_p3_report_export.py` | S10-P3 报告导出 validator，验证 D 级阻断、无 `.xlsx/.pdf` 提交和正式报告阻断 |
| `stage_artifacts/S10_P3_report_export/` | S10-P3 完成记录、测试结果、machine manifest、HTML 预览和 CSV 附表 |
| `stage_artifacts/S10_STAGE_REVIEW/` | Stage 10 整体复审证据包，记录 S10-P1/P2/P3 复跑、全量单测、治理 validator、raw/secret scan、parse checks 和 local-only upload readiness |
| `stage_artifacts/S10_STAGE_REVIEW/human/github_upload_record.md` | Stage 10 final GitHub upload 证据，记录 rebase、validators、raw/secret scan、dry-run push、push 和 post-push parity |
| `stage_artifacts/S10_STAGE_REVIEW/machine/stage10_upload_manifest.json` | Stage 10 final GitHub upload machine manifest |
| `tools/check_s10_stage_review.py` | Stage 10 review validator，验证 S10-P1/P2/P3 evidence、report grade D 阻断、HTML/CSV 导出、no Excel/PDF commit 和 upload/S11 gate |
| `tools/home_navigation_runtime.py` | S11-P1 public-safe 首页导航 runtime，生成 8 个模块、HTML 首页样张、manifest 和 records |
| `tools/check_s11_p1_home_navigation.py` | S11-P1 首页导航 validator，验证 required modules、KM 标识、蓝色商务风、全中文可见入口、public-safe 边界和 scope gate |
| `stage_artifacts/S11_P1_home_navigation/` | S11-P1 完成记录、测试结果、machine manifest 和 public-safe HTML 首页样张 |
| `tools/source_check_board_runtime.py` | S11-P2 public-safe 数据源检查板 runtime，生成 13 行矩阵、HTML 检查板样张、manifest 和 rows |
| `tools/check_s11_p2_source_check_board.py` | S11-P2 数据源检查板 validator，验证固定列、状态枚举、状态详情点击、蓝灰低干扰样式、public-safe 边界和 scope gate |
| `stage_artifacts/S11_P2_source_check_board/` | S11-P2 完成记录、测试结果、machine manifest 和 public-safe HTML 数据源检查板样张 |
| `tools/project_cost_page_runtime.py` | S11-P3 public-safe 项目成本页面 runtime，生成 4 条项目页面记录、HTML 项目成本页面、manifest 和 records |
| `tools/check_s11_p3_project_cost_page.py` | S11-P3 项目成本页面 validator，验证项目列表、项目详情、来源证据、待处理事项、报告预览、D 级不可绕过和 public-safe 边界 |
| `stage_artifacts/S11_P3_project_cost_page/` | S11-P3 完成记录、测试结果、machine manifest 和 public-safe HTML 项目成本页面 |
| `metadata/approvals/manual_resolution_event_manifest.json` | S12-P1 public-safe 人工处理事件 manifest，记录事件合同、scope gate、不可污染边界和反向事件要求 |
| `metadata/approvals/manual_resolution_events.jsonl` | S12-P1 人工处理事件日志，只保存追加式 public-safe metadata，不写 raw 层或字段明文 |
| `metadata/approvals/manual_impact_preview_manifest.json` | S12-P2 public-safe 影响预览 manifest，记录预览数量、影响域、二次确认门禁和 scope boundary |
| `metadata/approvals/manual_impact_previews.jsonl` | S12-P2 影响预览记录，只保存 public-safe affected project/metric/report refs、风险、发布门禁和证据 refs |
| `metadata/lineage/manual_rerun_manifest.json` | S12-P3 public-safe 重跑机制 manifest，记录 cache invalidation、rerun chain、same-source consistency 和 scope gate |
| `metadata/lineage/manual_rerun_cache_invalidations.jsonl` | S12-P3 派生缓存失效记录，只覆盖 preview passed/publish-allowed events |
| `metadata/lineage/manual_rerun_steps.jsonl` | S12-P3 派生重跑步骤，覆盖字段映射、事实层、指标和报告引用 |
| `metadata/lineage/manual_rerun_consistency_checks.jsonl` | S12-P3 同源引用一致性校验记录 |
| `tools/manual_resolution_events.py` | S12-P1 public-safe 人工处理事件 runtime，生成 append-only 事件、manifest 和 HTML 工作台样张 |
| `tools/check_s12_p1_manual_resolution_events.py` | S12-P1 人工处理事件 validator，验证四类动作、必填字段、反向事件、public-safe 边界和 scope gate |
| `stage_artifacts/S12_P1_manual_resolution_events/` | S12-P1 完成记录、测试结果、machine manifest 和 public-safe HTML 人工处理工作台 |
| `tools/manual_impact_preview.py` | S12-P2 public-safe 影响预览 runtime，生成每个人工处理事件的项目、指标、报告影响和高风险二次确认门禁 |
| `tools/check_s12_p2_manual_impact_preview.py` | S12-P2 影响预览 validator，验证预览覆盖、必需影响域、未通过不得发布、高风险 pending 阻断和 scope gate |
| `stage_artifacts/S12_P2_manual_impact_preview/` | S12-P2 完成记录、测试结果、machine manifest 和 public-safe HTML 影响预览 |
| `tools/manual_rerun_mechanism.py` | S12-P3 public-safe 重跑机制 runtime，生成缓存失效、重跑步骤、同源一致性校验和 HTML 样张 |
| `tools/check_s12_p3_manual_rerun_mechanism.py` | S12-P3 重跑机制 validator，验证只有通过预览的事件进入重跑、旧版本保留、新版本追加和 scope gate |
| `stage_artifacts/S12_P3_manual_rerun_mechanism/` | S12-P3 完成记录、测试结果、machine manifest 和 public-safe HTML 重跑机制 |
| `tools/check_s12_stage_review.py` | Stage 12 review validator，验证 S12-P1/P2/P3 evidence、人工处理/影响预览/重跑链路计数、no upload/S13/formal/lineage gate |
| `stage_artifacts/S12_STAGE_REVIEW/` | Stage 12 整体复审证据包，记录 S12-P1/P2/P3 复跑、治理 validator、raw/secret scan、parse checks 和 local-only upload readiness |
| `tools/check_s11_stage_review.py` | Stage 11 review validator，验证 S11-P1/P2/P3 evidence、public-safe HTML、D 级阻断、12 条 pending reconciliation、no upload/S12/formal/lineage gate |
| `stage_artifacts/S11_STAGE_REVIEW/` | Stage 11 整体复审证据包，记录 S11-P1/P2/P3 复跑、全量单测、治理 validator、raw/secret scan、parse checks 和 local-only upload readiness |
| `stage_artifacts/S11_STAGE_REVIEW/human/github_upload_record.md` | Stage 11 final GitHub upload 证据，记录 rebase、validators、raw/secret scan、dry-run push、push 和 post-push parity |
| `stage_artifacts/S11_STAGE_REVIEW/machine/stage11_upload_manifest.json` | Stage 11 final GitHub upload machine manifest |
| `stage_artifacts/S06_STAGE_REVIEW/` | Stage 6 整体复审与 GitHub upload 证据包，记录 S06-P1/P2/P3 复跑、治理 validator、raw/secret scan、evidence consistency check 和 push proof |
| `taskpack/v1_2/` | v1.2 FULL_HTML_NO_OMISSION 可提交基线 |
| `stage_artifacts/` | Stage/Phase 证据包 |

## P0 MVP 边界

P0 是文件型项目成本分析 MVP，目标链路如下：

```text
上传/登记权威项目成本资料
-> 原始文件hash与manifest
-> 字段映射
-> A0黄金基准
-> 金额整数分标准化
-> 零差异校验
-> 差异队列
-> 人工处理事件
-> 重跑派生链路
-> 项目成本报告
-> 经营总览摘要
```

当前 `S04-P1` 已建立金额工具：`normalize_amount_to_cents` 使用 `Decimal` 和整数分输出，支持元、万元、千元、千分位、负数和括号负数；`check_no_float_money.py` 阻断 KMFA Python 代码中的 float literal、`float()` 调用和 float 标注。当前 `S04-P2` 已建立字段标准化工具：日期标准化为 `YYYY-MM-DD`，期间标准化为 `YYYY-MM`，公司主体、项目名称、客户/对手方、合同编号进入 canonical field，缺字段进入 `field_quality_status` metadata 且 `field_skipped_silently=false`。当前 `S04-P3` 已完成基础工具边界测试和工具函数测试报告，覆盖金额小数、负数、万元、异常字符、中文日期、年月和空值。Stage 4 整体复审已通过并修复 owner-readable 金额工具详情缺口，final GitHub upload 证据已生成。

当前 Stage 5 的 S05-P1、S05-P2、S05-P3、整体复审和 GitHub upload 已完成：S05-P1 登记 8 个 PDF + 1 个 Excel 的 public-safe A0 文件清单；S05-P2 生成字段合同和 45 条候选，并通过 active owner/授权降级决策将 Excel candidate 排除为 cross-source support only；S05-P3 将 40 条 PDF 字段 hash/source-anchor 记录锁定为 public-safe Q5 calculation baseline，5 条 Excel 字段不进入正式报告；Stage 5 复审和上传证据位于 `KMFA/stage_artifacts/S05_STAGE_REVIEW/`。

当前 Stage 6、Stage 7、Stage 8、Stage 9、Stage 10、Stage 11、Stage 12、Stage 13、Stage 14、Stage 15、Stage 16、Stage 17 和 Stage 18 均已完成整体复审和 GitHub upload；Stage 18 upload 证据位于 `KMFA/stage_artifacts/S18_GITHUB_UPLOAD/`。S17-P1 已完成 public-safe 权限与安全：4 类角色、15 类敏感材料禁入策略和 5 类审计动作；S17-P2 已完成 metadata outbox-only 通知提醒：3 类提醒规则、事件和 dispatch log；S17-P3 已完成 metadata-only 运维 SOP：4 类操作手册、2 条知识索引和 2 条演练日志。S18-P1 精度与压力测试、S18-P2 全量回归和验收、S18-P3 后续接入准备、Stage 18 整体复审和 Stage 18 final GitHub upload 均已完成验证；Stage 18 review-level Go/No-Go 结论仍为 `NO_GO`，因为 lineage full check、正式报告发布和 12 条 pending reconciliation 仍未完成。当前仍显示 D 级阻断，不能作为正式经营决策、完整报告通知投递、采购执行、付款审批、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收、法律决策、绩效发放、工资计算、奖金审批或薪资导出依据；lineage 完整检查、正式报告和外部接口仍未完成。下一步只能另开独立目标确认 lineage/report gate 范围。

## 禁止事项

- 不提交原始敏感数据到公开 GitHub。
- 不自动付款、报税、开票、发工资或发奖金。
- 不对外发送完整经营报告。
- 不在金额计算中使用 float。
- 不把缺数据报告伪装成完整报告。
- 不自动选择 PDF 或 Excel 冲突的一边。
- 不用工具化、营销化、非真实软件感的前端或报告文案。

## 验证命令

当前 Stage 15 GitHub upload 验证:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_salary_boundary.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p3_salary_boundary.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_review_list.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p2_performance_review_list.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_performance_fact_fields.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_p1_performance_fact_fields.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_s15_stage_review.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s15_stage_review.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
ruby -ryaml -e 'ARGV.each { |p| YAML.load_file(p); puts "yaml_ok #{p}" }' KMFA/docs/governance/ASSURANCE_STATUS.yaml KMFA/docs/governance/VERSION_MATRIX.yaml KMFA/docs/governance/formula_registry.yaml KMFA/docs/governance/project.yaml KMFA/docs/governance/roadmap.yaml KMFA/metadata/model_registry.yaml KMFA/metadata/project/project.yaml
git diff --check -- KMFA scripts
```

当前 S06 upload gate 验证:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_a0_file_register KMFA.tests.test_a0_golden_fixture KMFA.tests.test_s05_p2_excel_owner_decision KMFA.tests.test_s05_p2_owner_decision_intake KMFA.tests.test_s05_p2_owner_decision_templates KMFA.tests.test_s05_p2_owner_decision_application KMFA.tests.test_s05_p2_completion_gate KMFA.tests.test_s05_p3_authority_baseline_lock -q
python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q
python3 KMFA/tools/generate_tool_test_report.py --format json
python3 KMFA/tools/generate_tool_test_report.py --format markdown
python3 -m unittest KMFA.tests.test_field_standardization -q
python3 -m unittest KMFA.tests.test_amount_tools -q
python3 KMFA/tools/check_no_float_money.py
python3 -m unittest KMFA.tests.test_source_priority -q
python3 -m unittest KMFA.tests.test_source_check_matrix -q
python3 -m unittest KMFA.tests.test_file_import_register -q
python3 KMFA/tools/check_required_html.py
python3 KMFA/tools/no_omission_check.py
python3 KMFA/tools/check_report_grade_gate.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- KMFA
```
