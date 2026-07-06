# KMFA Handoff

更新时间: 2026-07-06

## 当前目标

最近一个完成的 phase 是 `V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION`：基于上一 phase ignored private full source-map input 和 private processed target staging，已将 149 条 processed-value source-map records materialize 到 ignored private runtime。当前确认 `processed_target_slot_count=149`、`full_materialization_source_map_record_count=149`、`full_materialized_record_count=149`、`full_materialization_blocked_record_count=0`、`linked_materialized_record_count=77`、`outside_scope_materialized_record_count=72`、`full_unique_private_value_source_count=84`、`full_processed_value_materialization_complete=true`、`raw_to_processed_value_comparison_ready=true`、Go/No-Go=`NO_GO`。本 phase 不读取、不列出、不 stat、不 fingerprint、不解析、不写入、不删除、不移动、不重命名、不复制或标准化 raw inbox；不改写 source private full source-map 或 private processed staging；private replay、diagnostic 和 materialized records 保留在 ignored runtime 且不会提交。当前只完成 full processed-value materialization replay；尚未执行 raw-to-processed comparison、full reconciliation、lineage full check、formal report、GitHub upload、app reinstall 或 business execution。下一步只能另起单一 phase 做 full raw-to-processed comparison precheck；不得自动执行 full reconciliation、GitHub upload、重装 app、发布正式报告或业务动作。用户要求 raw 原始数据不得修改增删；后续如 full raw-to-processed comparison 和多次交叉验证仍无法保持处理数据与原始数据一致，最终 goal closeout 必须提供 public-safe 差异报告。

## v0.1.4 当前续跑状态

- 当前本地分支: `codex/kmfa`
- 当前版本: `0.1.4-full-materialization-replay-after-outside-scope-application`
- 当前已完成: `V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION`
- 证据目录: `KMFA/stage_artifacts/V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION/`
- validator: `KMFA/tools/check_v014_full_processed_value_materialization_replay_after_outside_scope_application.py --require-private-replay`
- focused test: `KMFA/tests/test_v014_full_processed_value_materialization_replay_after_outside_scope_application.py`
- manifest: `KMFA/stage_artifacts/V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION/machine/full_processed_value_materialization_replay_after_outside_scope_application_manifest.json`
- go_no_go: `KMFA/stage_artifacts/V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION/machine/full_processed_value_materialization_replay_after_outside_scope_application_go_no_go_report.json`
- summary: `KMFA/stage_artifacts/V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION/machine/full_processed_value_materialization_replay_after_outside_scope_application_summary.json`
- metadata copies: `KMFA/metadata/quality/v014_outside_scope_authorized_source_map_extension_application_manifest.json`, `KMFA/metadata/quality/v014_outside_scope_authorized_source_map_extension_application_go_no_go_report.json`, `KMFA/metadata/quality/v014_outside_scope_authorized_source_map_extension_application_summary.json`, `KMFA/metadata/quality/v014_outside_scope_authorized_source_map_extension_application_matrix_public_safe.json`
- current_gate: `NO_GO_FULL_MATERIALIZATION_REPLAY_COMPLETE_RAW_COMPARISON_NEXT_PHASE`
- current_state: processed_target_slot_count=`149`, full_materialization_source_map_record_count=`149`, full_materialized_record_count=`149`, full_materialization_blocked_record_count=`0`, linked_materialized_record_count=`77`, outside_scope_materialized_record_count=`72`, full_unique_private_value_source_count=`84`, full_processed_value_materialization_complete=`true`, raw_to_processed_value_comparison_ready=`true`, raw_to_processed_value_comparison_performed=`false`, full_raw_to_processed_value_comparison_complete=`false`, business_value_consistency_verified=`false`, Go/No-Go=`NO_GO`
- raw boundary: 本 phase 不读取、不列出、不 stat、不 fingerprint、不解析、不写入、不删除、不移动、不重命名、不复制或标准化 raw inbox；不改写 source private full source-map 或 private processed staging；只写入 ignored private full materialization replay/diagnostic/materialized records/blocker records。用户要求原始数据不得修改增删；后续如 full raw-to-processed comparison 和多次交叉验证仍无法保持处理数据与原始数据一致，最终 goal closeout 必须提供差异报告。
- upload policy: v1.4 不按单个 Stage 或补充 gate 上传；GitHub main upload 必须等 owner raw source identity、raw alignment application、lineage full check、formal report release、pending reconciliation 和 final gate 全部通过后才可单独执行。
- 未完成/阻断: full processed-value materialization replay 已执行并完成，但 raw-to-processed comparison 尚未执行；full raw-to-processed comparison complete=false；processed-data reconciliation=false；business value consistency verified=false；lineage full check complete=false；official report release allowed=false；GitHub upload=false；app reinstall=false；formal report=false；business execution=false。
- 下一步: 另起一个单一 follow-up phase 执行 full raw-to-processed comparison precheck after full materialization；不得自动执行 full reconciliation、GitHub upload、重装 app、发布正式报告或执行业务动作。

## v0.1.3 历史状态

v1.2 FULL_HTML_NO_OMISSION 完整任务包已成为 KMFA 后续开发基线。Stage 1-18 均已完成本地实现、验证、整体复审和 GitHub main 上传；Post-S18 Part 1-6 已在 canonical worktree 本地通过并生成 validator/evidence/local-governance 记录。Post-S18 第二阶段全项目本地复审已完成：新增 task pack zero-delta synthetic fixture、lineage completeness 阻断 validator、whole-project final review validator 和当前全项目 Go/No-Go。当前 `STAGE18_GITHUB_UPLOAD_PENDING` 已从最新全项目 Go/No-Go blocker 中移除并记录为 resolved，但项目仍为 `NO_GO`，`delivery_allowed=false`。随后已独立完成 KMFA worktree cleanup：只保留 canonical `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`，确认无遗留 `kmfa-s*` worktree，删除空旧目录 `/Users/linzezhang/Documents/KMFA v0.1`。Lineage / Report Gate 已独立锁定：0 条 actual lineage rows、2 条 D 级 report runtime、12 条 pending reconciliation 继续阻断正式报告、经营决策依据、release claim 和 delivery claim。Final GitHub backup evidence 已按 `NO_GO governance backup only` 生成并基于最新 `origin/main` rebase；本轮仍未执行 lineage full check completion、正式报告、live connector、OpMe 深度耦合、生产恢复或业务动作。

## v0.1.3 当前续跑状态

- 当前本地分支: `codex/kmfa`
- 当前版本: `0.1.3-stage1-10-github-upload`
- 当前已完成: `v0.1.3 Stage 1-10 GitHub upload gate local validation`
- 证据目录: `KMFA/stage_artifacts/V013_STAGE1_10_GITHUB_UPLOAD/`
- Stage 7 复审结论: S07-P1/S07-P2/S07-P3 replay validators 全部 PASS；legacy S07-P1 finance adapter validator/unit、legacy S07-P2 WPS adapter validator/unit、legacy S07-P3 Redcircle postponement validator/unit 均 PASS；Stage 7 review validator 和 focused unit test PASS。复审确认 phase_results=`S07-P1=PASS, S07-P2=PASS, S07-P3=PASS`、open findings=`0`、Q5 allowed count=`0`、formal report allowed count=`0`、Redcircle automatic connector allowed=`false`、data quality=`Q4`、report grade=`D`、release permission=`blocked`、`s08_p1_performed=false`、`github_upload_performed=false`。
- upload policy: v1.3 不按单个 Stage 做 GitHub upload gate；Stage 1-10 已全部完成并完成 batch overall review，当前只允许执行一次性 Stage 1-10 GitHub upload gate。不得把 Stage 4、Stage 5、Stage 6、Stage 7、Stage 8、Stage 9 或 Stage 10 单独 upload 作为 active next step。
- S08-P1 结论: 已重放既有 public-safe 项目组合键能力，锁定 8 个 hash-only 组件、4 个 profiles、3 个 match results、2 条人工复核队列、1 条 strong auto match、10000 bps 权重总和、8500/7000/5000 bps 阈值。
- S08-P2 结论: 已重放既有 public-safe 业务实体模型能力，锁定 8 类实体、14 条关系、32 条 lifecycle statuses、每类实体 4 个状态；实体值保持 hash/ref only，关系保持 schema-only，生命周期保持 status-only；S08-P3 已由后续 phase 完成，GitHub upload 未执行。
- S08-P3 结论: 已重放既有 public-safe 匹配质量能力，锁定 4 类质量场景、4 条 quality cases、3 条 manual review queue、1 份 entity_matching_report 和 high=2/medium=1/low=1 风险汇总；人工复核队列 `auto_merge_allowed=false`，Stage 8 review 已由本轮完成，GitHub upload 未执行。
- Stage 8 review 结论: S08-P1/S08-P2/S08-P3 replay validators 全部 PASS；focused unit test 和 Stage 8 review validator PASS；phase_results=`S08-P1=PASS, S08-P2=PASS, S08-P3=PASS`、open findings=`0`、fixed findings=`1`、Q5 allowed count=`0`、formal report allowed count=`0`、legacy Stage 8 upload artifacts current gate=`false`、data quality=`Q4`、report grade=`D`、release permission=`blocked`、`s09_p1_performed=false`、`github_upload_performed=false`。
- S09-P1 结论: 已重放既有 public-safe 项目成本事实层能力并验证 v0.1.3 Stage 8 review dependency；锁定 required metrics=`6`、cost categories=`9`、fact records=`4`、unallocated pool=`9`、authority locked fields=`40`、excluded fields=`5`、business entity types=`8`、project identity profiles=`4`、manual review queue=`3`、unresolved differences=`1`、blocked quality results=`2`；metric/cost category value 均保持 hash/private-ref only，formal calculation allowed=`0`，report grade=`D`，release permission=`blocked`，`s09_p2_performed=false`、`s09_p3_performed=false`、`stage9_review_performed=false`、`github_upload_performed=false`。
- S09-P2 结论: 已重放既有 public-safe 毛利与现金毛利层能力并验证 v0.1.3 S09-P1 dependency；锁定 required margin metrics=`4`、project cost fact records=`4`、margin records=`4`、scope difference summary records=`12`、authority field groups=`8`、manual review queue=`3`、unresolved differences=`1`、zero-delta fail count=`1`、blocked quality results=`2`；authority/system/cash value 均保持 hash/private-ref only，authority/system overwrite allowed=`0`，public amount values committed=`0`，formal report allowed=`false`，`s09_p3_performed=false`、`stage9_review_performed=false`、`github_upload_performed=false`。
- S09-P3 结论: 已重放既有 public-safe 口径转换与差异核对层能力并验证 v0.1.3 S09-P2 dependency；锁定 reconciliation records=`12`、domain controls=`6`、required reconciliation domains=`6`、required human fields=`8`、confirmed resolutions=`0`、pending resolutions=`12`、authority/system recomputed domain records=`8`、bank/receivable aging domain records=`4`；derived metric rerun allowed=`false`、formal report rerun allowed=`false`、formal report allowed=`false`、stage9_review_performed=`false`、github_upload_performed=`false`。
- Stage 9 review 结论: 已本地完成 v0.1.3 Stage 9 overall review；S09-P1/S09-P2/S09-P3 replay validators、legacy S09 validators、Stage 9 review validator 和 focused unit test 均 PASS；phase_results=`S09-P1=PASS, S09-P2=PASS, S09-P3=PASS`、open findings=`0`、fixed findings=`1`、pending resolutions=`12`、confirmed resolutions=`0`、legacy Stage 9 upload artifacts current gate=`false`、data quality=`Q4`、report grade=`D`、release permission=`blocked`、`s10_p1_performed=false`、`github_upload_performed=false`。
- S10-P1 结论: 已本地完成 v0.1.3 report templates replay；验证 v0.1.3 Stage 9 review dependency 并复用 legacy S10-P1 public-safe artifacts，锁定 template_count=`2`、section_count=`11`、project_cost_section_count=`4`、business_overview_section_count=`7`、pending_reconciliation_count=`12`、formal_report_count=`0`、export_artifact_count=`0`；`trusted_grade_assignment_allowed=false`、`report_runtime_scope_count=0`、`s10_p2_performed=false`、`s10_p3_performed=false`、`stage10_review_performed=false`、`github_upload_performed=false`。
- S10-P2 结论: 已本地完成 v0.1.3 report grade runtime replay；验证 v0.1.3 S10-P1 dependency 并复用 legacy S10-P2 public-safe report grade artifacts，锁定 report_grade_record_count=`2`、grade_distribution=`D:2`、pending_reconciliation_count=`12`、confirmed_resolution_count=`0`、source_quality_grade=`Q4`、zero_delta_passed=`false`、full_trusted_report_allowed_count=`0`、formal_report_count=`0`、export_artifact_count=`0`；record/template/formula/mapping/field mapping/grade policy/release gate versions 已绑定；`s10_p3_performed=false`、`stage10_review_performed=false`、`github_upload_performed=false`。
- S10-P3 结论: 已本地完成 v0.1.3 report export replay；验证 v0.1.3 S10-P2 dependency 并复用 legacy S10-P3 public-safe report export artifacts，锁定 report_export_record_count=`2`、html_export_count=`2`、csv_appendix_count=`2`、excel_compatible_download_count=`2`、committed_pdf_file_count=`0`、committed_excel_file_count=`0`、formal_report_count=`0`、business_decision_basis_count=`0`、pending_reconciliation_count=`12`、grade_distribution=`D:2`；HTML 继承蓝色商务样板，Excel 下载保持 compatible CSV，PDF 仅 private-runtime-only policy；`stage10_review_performed=false`、`github_upload_performed=false`。
- Stage 10 review 结论: 已本地完成 v0.1.3 Stage 10 overall review；复跑 S10-P1/S10-P2/S10-P3 replay validators、legacy S10 validators、legacy Stage 10 review validator、v0.1.3 Stage 10 review validator 和 focused unit test，phase_results=`S10-P1=PASS, S10-P2=PASS, S10-P3=PASS`，open findings=`0`，fixed findings=`2`，report_template_count=`2`，report_grade_record_count=`2`，report_export_record_count=`2`，html_export_count=`2`，csv_appendix_count=`2`，excel_compatible_download_count=`2`，pending_reconciliation_count=`12`，confirmed_resolution_count=`0`，formal_report_count=`0`，business_decision_basis_count=`0`，legacy Stage 10 upload artifacts current gate=`false`，GitHub upload status=`not_uploaded_deferred_until_stage1_10_batch`。
- Stage 1-10 batch review 结论: 已本地完成 v0.1.3 Stage 1-10 batch overall review；复核 S01-S10 共 10 个 v0.1.3 stage review manifest，stage_results 全部 `PASS`，open_stage_review_finding_count=`0`，open_batch_finding_count=`0`，fixed_batch_finding_count=`1`，legacy_individual_stage_upload_artifacts_current_gate=`false`，github_upload_ready_next_gate=`true`，github_upload_performed=`false`，github_upload_status=`not_uploaded_ready_for_separate_stage1_10_github_upload_gate`。
- Stage 1-10 GitHub upload gate 结论: 已完成 local validation；已 unshallow/fetch/rebase 到 latest `origin/main`，upload base=`387f2bdd1e4cb06d3fced781417f057f854c2901`，reviewed batch commit=`494a166779fa8fdc1a282d1ebbdca293e3e78886`；upload validator、focused upload unit、focused batch unit、full KMFA tests 326、S01-S10 validators、no-float、no-omission、governance validators、raw/private path scan、strict secret scan、public-safe semantic scan 和 diff check 均 PASS。本 gate 仍保持 `delivery_allowed=false`、`formal_report_allowed=false`、`business_execution_allowed=false`、report grade=`D`、data quality=`Q4`、pending reconciliation=`12`。
- raw boundary: 本轮 GitHub upload gate 未读取、列出、修改、删除、移动、重命名、覆盖或写入 `/Users/linzezhang/Downloads/KMFA_MetaData`；只处理 public-safe governance、validator、test 和 evidence。公开证据不包含 raw 文件名、raw hash、字段/表头明文、sheet 名、ZIP member 名、row values、真实业务值、PDF/Excel 原值、connector secret 或 Redcircle native file；未新增 private diagnostic。
- 未执行: raw value matching、lineage full check、formal report、live connector、Redcircle automatic connector、OpMe deep coupling、business execution。
- 下一步: 若 push 和 post-push parity 完成，则 v0.1.3 Stage 1-10 GitHub upload gate 关闭；后续只能由用户指定下一个单一 phase，不得自动推进 raw value matching、正式报告、lineage full check、live connector 或业务动作。

## 持久本机 raw boundary

- 用户确认 KMFA 后续本机财务原始数据统一放在 `/Users/linzezhang/Downloads/KMFA_MetaData`。
- 该目录属于 raw/private business data；Codex 只能在当前 phase 明确需要时只读读取，不得修改、删除、移动、重命名、覆盖或写入生成文件。
- Codex 生成的私有 inventory、schema/header diagnostic、mapping diagnostic、scratch files 或本地报告只能写入项目受控且 Git 忽略的位置，例如 `KMFA/.codex_private_runtime/`，或另一个明确加入 `.gitignore` 的额外工作目录。
- 公开 GitHub 只能保存 public-safe 结构、聚合计数、状态、hash/ref、证据索引、validator 结果和治理记录；不得提交 raw 文件、raw 文件名、字段/表头明文、sheet 名、row values、业务金额、credentials、银行流水、合同、薪资或税务材料。

## 当前状态

- Post-S18 Part 1 Review 已本地通过：新增 `KMFA/tools/check_part1_stages_01_03_review.py`、`KMFA/tests/test_part1_stages_01_03_review.py` 和 `KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/`；当轮全量 KMFA unittest 为 269 tests。
- Post-S18 Part 2 Review 已本地通过：新增 `KMFA/tools/check_part2_stages_04_06_review.py`、`KMFA/tests/test_part2_stages_04_06_review.py` 和 `KMFA/stage_artifacts/PART2_STAGES_04_06_REVIEW/`；全量 KMFA unittest 当前为 270 tests。
- Post-S18 Part 3 Review 已本地通过：新增 `KMFA/tools/check_part3_stages_07_09_review.py`、`KMFA/tests/test_part3_stages_07_09_review.py` 和 `KMFA/stage_artifacts/PART3_STAGES_07_09_REVIEW/`；全量 KMFA unittest 当前为 271 tests。
- Post-S18 Part 4 Review 已本地通过：新增 `KMFA/tools/check_part4_stages_10_12_review.py`、`KMFA/tests/test_part4_stages_10_12_review.py` 和 `KMFA/stage_artifacts/PART4_STAGES_10_12_REVIEW/`；全量 KMFA unittest 当前为 272 tests。
- Post-S18 Part 5 Review 已本地通过：新增 `KMFA/tools/check_part5_stages_13_15_review.py`、`KMFA/tests/test_part5_stages_13_15_review.py` 和 `KMFA/stage_artifacts/PART5_STAGES_13_15_REVIEW/`；全量 KMFA unittest 当前为 273 tests。
- Post-S18 Part 6 Review 已本地通过：新增 `KMFA/tools/check_part6_stages_16_18_review.py`、`KMFA/tests/test_part6_stages_16_18_review.py` 和 `KMFA/stage_artifacts/PART6_STAGES_16_18_REVIEW/`；全量 KMFA unittest 当前为 274 tests。
- Post-S18 Whole Project Final Review 已本地通过且 delivery 仍为 `NO_GO`：新增 `KMFA/tools/check_lineage_completeness.py`、`KMFA/tools/check_whole_project_final_review.py`、`KMFA/tests/test_lineage_completeness.py`、`KMFA/tests/test_whole_project_final_review.py` 和 `KMFA/stage_artifacts/WHOLE_PROJECT_FINAL_REVIEW/`；全量 KMFA unittest 当前为 276 tests。
- KMFA worktree cleanup 已本地完成：新增 `KMFA/tools/check_worktree_cleanup.py` 和 `KMFA/stage_artifacts/WORKTREE_CLEANUP/`；只保留 canonical KMFA sparse worktree；旧 `/Users/linzezhang/Documents/KMFA v0.1` 为空目录骨架，已用 `rmdir` 删除；没有可迁移 KMFA 变更，也没有 raw/private 数据迁入公开仓库。
- Lineage / Report Gate 已本地锁定为 `blocked_no_go_owner_scope_required`：新增 `KMFA/tools/check_lineage_report_gate.py`、`KMFA/tests/test_lineage_report_gate.py`、`KMFA/metadata/quality/lineage_report_release_gate_review.json` 和 `KMFA/stage_artifacts/LINEAGE_REPORT_GATE/`；validator 复算 0 条 actual lineage rows、2 条 D 级 report runtime、12 条 pending reconciliation 和 `delivery_allowed=false`。
- Final GitHub Backup 证据已生成：新增 `KMFA/tools/check_final_no_go_backup_upload.py`、`KMFA/tests/test_final_no_go_backup_upload.py` 和 `KMFA/stage_artifacts/FINAL_GITHUB_BACKUP/`；只允许 `NO_GO governance backup only`，不允许 release、delivery、正式报告或业务执行。
- 已修复复审 findings：`TASKPACK_ZERO_DELTA_FIXTURE_MISSING`、`LINEAGE_COMPLETENESS_VALIDATOR_MISSING`、`CURRENT_GO_NO_GO_STALE_STAGE18_UPLOAD_BLOCKER`。
- `S01-P1` 已在前序工作目录完成，只读计划证据已迁移到 `KMFA/stage_artifacts/S01_P1_read_only_plan/`。
- `S01-P2` 已创建项目根、三中文入口、模型参数文件、Lean v2 与 v1 兼容治理文件、metadata 草案。
- `S01-P3` 已导入完整需求追溯矩阵、新增正式 `KMFA/tools/no_omission_check.py`、建立 18 Stage / 54 Phase / 162 Task 状态登记。
- Stage 1 总复审已通过，复审产物在 `KMFA/stage_artifacts/S01_STAGE_REVIEW/`。
- Stage 1 已上传到 GitHub main: `ff834578e640dc360e764ab18f9da2003c735e3e`。
- `S02-P1` 已建立 metadata 七类目录、标识符协议、公开仓库隐私边界和 `KMFA/tools/metadata_protocol_check.py`。
- `S02-P2` 已建立 raw manifest append-only 规范、派生版本协议、前端 raw 写入边界和 `KMFA/tools/immutability_policy_check.py`。
- `S02-P3` 已建立 Q0-Q5 数据质量等级、A/B/C/D 报告可信等级、发布门禁和 `KMFA/tools/check_report_grade_gate.py`。
- Stage 2 复审已通过，复审产物在 `KMFA/stage_artifacts/S02_STAGE_REVIEW/`。
- Stage 2 已上传 GitHub main: final remote commit `6178b5215f92f12d6facad9a990e8659b3a70ba4`，reviewed content commit `834ff75516405ddbc8289f00ba67579691473709`。
- v1.2 完整任务包已同步到 `KMFA/taskpack/v1_2/`，源 zip SHA256 为 `3bb2ebf16fb4ad8b9d198484e9d80ea2aed3c19c54c483efebe023b772ad0e66`。
- HTML/UIUX/报告验收样板已同步：45 个 HTML，7 个核心验收样板。
- `90_用户原始上传数据` 未进入公开仓库，只保存 SHA256 登记和禁止提交规则。
- Stage 1 v1.2 重放证据在 `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/`。
- `S03-P1` 已完成本地实现与验证：新增 `KMFA/tools/file_import_register.py`、`KMFA/tests/test_file_import_register.py` 和 `KMFA/stage_artifacts/S03_P1_file_import/`。
- S03-P1 只生成文件登记 metadata、hash、size、import_run、source package、私有 storage ref 和 WPS/OLE 提示；未导入真实原始文件，未解析业务字段。
- `S03-P2` 已完成本地实现与验证：新增 `KMFA/tools/source_check_matrix.py`、`KMFA/tests/test_source_check_matrix.py` 和 `KMFA/stage_artifacts/S03_P2_source_check_matrix/`。
- S03-P2 只生成数据源检查矩阵 metadata 和 append-only 状态事件；未提交真实源行，未做源优先级。
- `S03-P3` 已完成本地实现与验证：新增 `KMFA/tools/source_priority.py`、`KMFA/tests/test_source_priority.py` 和 `KMFA/stage_artifacts/S03_P3_source_priority/`。
- S03-P3 只生成源优先级、同源失效重跑事件和跨源差异队列 metadata；未解析真实业务源值，未自动选边，未上传 GitHub。
- Stage 3 复审已通过，发现的源优先级链路对齐问题已修复，并已上传 GitHub main，reviewed content commit `39b0eef52424a12b6c0c8ad368bd878b46300be4`。
- `S04-P1` 已完成本地实现与验证：新增 `KMFA/tools/amount_tools.py`、`KMFA/tools/check_no_float_money.py`、`KMFA/tests/test_amount_tools.py` 和 `KMFA/stage_artifacts/S04_P1_amount_tools/`。
- S04-P1 只提供金额标准化与 no-float 检查；未做字段标准化、zero-delta、A0 基准、事实层、报告或 UI。
- `S04-P2` 已完成本地实现与验证：新增 `KMFA/tools/field_standardization.py`、`KMFA/tests/test_field_standardization.py`、`KMFA/metadata/schema_maps/field_alias_dictionary.csv`、`KMFA/metadata/schema_maps/field_standardization_policy.yaml`、`KMFA/metadata/quality/field_quality_status.jsonl` 和 `KMFA/stage_artifacts/S04_P2_field_standardization/`。
- S04-P2 只提供字段别名、日期、期间、主体、项目、客户/对手方、合同编号标准化和缺字段质量状态；未做 S04-P3 工具测试报告、zero-delta、A0 基准、事实层、报告或 UI。
- `S04-P3` 已完成本地实现与验证：新增 `KMFA/tests/test_basic_tool_boundaries.py`、`KMFA/tools/generate_tool_test_report.py` 和 `KMFA/stage_artifacts/S04_P3_basic_tool_tests/`，并修复中文完整日期转期间边界。
- S04-P3 只提供基础工具合成边界测试和工具函数测试报告；未做 zero-delta、A0 基准、事实层、报告或 UI。
- Stage 4 整体复审已通过：新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/`，复跑 S04-P1/P2/P3 工具测试、治理 validator、no-float 检查和敏感文件扫描。
- Stage 4 复审修复了 `功能清单.md` 中 `FEAT-KMFA-016` 金额工具详情缺口。
- Stage 4 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_upload_manifest.json`。
- `S05-P1` 已完成本地实现与验证：新增 `KMFA/tools/a0_file_register.py`、`KMFA/tools/check_a0_file_registration.py`、`KMFA/tests/test_a0_file_register.py`、`KMFA/metadata/baseline/a0_file_manifest.json`、`KMFA/metadata/baseline/a0_project_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P1_a0_file_registration/`。
- S05-P1 只登记 A0 private source package 的公开安全 source package SHA256、8 个 PDF + 1 个 Excel inventory 记录、legacy 指纹、Q3 机器候选和 Q4 未锁定状态；未抽取字段值、未生成 A0 字段级黄金基准、未做 zero-delta、事实层、报告或 UI。
- S05-P1 执行时未提供可验证私有 A0 source package，所以成员级 `member_sha256` 仍为 `pending_private_zip_unavailable`；S05-P2 后续私有审计发现本机 zip 整包 hash/size 与登记 source package 不匹配，因此不能回填 S05-P1 member SHA256，也没有把 legacy CRC/指纹伪装成 SHA256。
- `S05-P2` 已生成 public-safe 字段合同和候选结构：新增 `KMFA/tools/a0_golden_fixture.py`、`KMFA/tools/check_a0_golden_fixture.py`、`KMFA/tests/test_a0_golden_fixture.py`、`KMFA/metadata/baseline/a0_golden_fixture_manifest.json`、`KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl` 和 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/`。
- S05-P2 当前生成 5 个字段合同和 45 条字段候选：合同额、支出合计、毛利、毛利率、成本分类；每条候选都有 private raw/normalized value ref、source anchor 状态和 Q3/Q4/Q5 门禁。
- 本机提供的 A0 private source package 整包 hash/size 与登记 source package 不匹配；过滤 macOS 隐藏文件后 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配。当前只据此和 Ring4 前序提取包执行 hash-only 部分回填，不把整包标记为 source package 匹配。
- S05-P2 已将 8 个 PDF 候选的 40 条字段记录为 hash/source anchor recorded；1 个 Excel 候选的 5 条字段仍为 `pending_private_source_unavailable`；未提交 raw/normalized 字段值、私有 CSV、zip、PDF 或 Excel。
- S05-P2 已新增 Excel 候选机器复核记录：Excel workbook 更像交叉来源汇总/支持材料，不得机器合成为单一 A0 项目基准，不得生成占位 hash，不得进入 Q4/Q5；证据在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md`。
- S05-P2 已新增 Excel owner 决策包：允许 `provide_private_field_mapping`、`downgrade_to_cross_source_support` 或 `keep_pending` 三类决策；证据在 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`。
- S05-P2 已新增 owner 决策包 validator：`KMFA/tools/check_s05_p2_excel_owner_decision.py` 验证决策包、fixture pending 状态、approval/control events 和 Q4/Q5 禁止状态一致。
- S05-P2 已新增 owner 决策 intake contract 和 validator：`KMFA/tools/check_s05_p2_owner_decision_intake.py` 验证 owner/授权决策记录的 public-safe schema、actor role、禁止明文键和 Q4/Q5 边界；active downgrade decision 已通过 intake validator。
- S05-P2 已新增 owner 决策模板和 validator：`KMFA/tools/check_s05_p2_owner_decision_templates.py` 验证三种模板覆盖 allowed decisions，且模板不是 active owner 决策记录。
- S05-P2 已新增 owner decision application preview：`KMFA/tools/preview_s05_p2_owner_decision_application.py` 验证 public-safe 决策如何预览为 private hash backfill、cross-source support downgrade 或继续 pending；active downgrade decision 已输出 ready preview。
- S05-P2 已新增 completion gate validator：`KMFA/tools/check_s05_p2_completion_gate.py` 默认在无 resolving owner/授权决策时返回 `BLOCKED`；使用 active downgrade decision 时返回 `ready`，防止误入 Q4/Q5 但允许本地关闭 S05-P2。
- `S05-P3` 已完成本地实现与验证：新增 `KMFA/tools/a0_authority_baseline_lock.py`、`KMFA/tools/check_a0_authority_baseline_lock.py`、`KMFA/tests/test_s05_p3_authority_baseline_lock.py`、`KMFA/metadata/baseline/a0_authority_baseline_manifest.json`、`KMFA/metadata/baseline/a0_authority_baseline_records.jsonl` 和 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/`。
- S05-P3 已锁定 baseline version `KMFA-A0-Q5-20260630-S05P3-PUBLIC-SAFE-HASH-LOCK` 和 content hash `sha256:dbb55ffb4e3608e49dbcf91e97fc0f19395a8269ff7c8f4d5c3f8ca398c03670`；40 条字段为 `q5_locked_public_safe_hash_baseline`，5 条字段为 `excluded_cross_source_support_only`。
- S05-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV 或字段明文；`formal_report_allowed=false`。
- Stage 5 整体复审已本地通过：新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/stage5_review_report.md`、`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_review_manifest.json`；后续 upload gate 已完成。
- Stage 5 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`；upload base `495bcd977a587b7fd8b1923bfd74f5138f12263e`，reviewed content commit `ca6788949c444188b4b93f7db42c94094d90209f`。
- `S06-P1` 已完成本地实现与验证：新增 `KMFA/tools/zero_delta_validator.py`、`KMFA/tests/test_zero_delta_validator.py` 和 `KMFA/stage_artifacts/S06_P1_zero_delta_validator/`。
- S06-P1 只比较 public-safe 已结构化整数分字段；任意 1 分差异失败并输出包含来源、字段、权威值、系统值和差额的 mismatch report。
- S06-P1 不读取真实 Excel、PDF、zip 或私有 CSV，不写 `KMFA/metadata/quality/zero_delta_results.jsonl` 或 `KMFA/metadata/quality/mismatch_report.csv`，不创建 S06-P2 队列，不做 Stage 6 复审或 GitHub upload。
- `S06-P2` 已完成本地实现与验证：新增 `KMFA/tools/cross_source_difference_queue.py`、`KMFA/tools/check_s06_p2_difference_queue.py`、`KMFA/tests/test_cross_source_difference_queue.py` 和 `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/`。
- S06-P2 只使用 public-safe synthetic PDF/Excel 同项目同字段 1 分差异 fixture；差异进入人工队列，`auto_correction_allowed=false`、`averaging_allowed=false`、`rounding_mask_allowed=false`、`auto_selection_allowed=false`。
- S06-P2 未关闭差异阻断 A 级报告：`report_grade_a_allowed=false`、`maximum_report_grade=B`、`hard_block_reason=unresolved_critical_difference`；不写 metadata/quality 运行时业务差异项，不关闭差异，不做 Stage 6 复审或 GitHub upload。
- `S06-P3` 已完成本地实现与验证：新增 `KMFA/tools/validation_evidence_output.py`、`KMFA/tools/check_s06_p3_validation_evidence.py`、`KMFA/tests/test_validation_evidence_output.py` 和 `KMFA/stage_artifacts/S06_P3_validation_evidence_output/`。
- S06-P3 将 S06-P1/S06-P2 public-safe 结果输出为 `zero_delta_result.json`、sanitized `mismatch_report.csv`、`project_validation_status.jsonl`，并写入 `KMFA/metadata/quality/{zero_delta_results.jsonl,data_quality_results.jsonl,source_difference_queue.jsonl,mismatch_report.csv}`。
- S06-P3 metadata/quality 只保存 hash/ref/status/evidence 和质量门禁状态，不新增字段明文、权威原值、系统原值、PDF 原值或 Excel 原值；不关闭差异，不做 Stage 6 复审或 GitHub upload。
- Stage 6 整体复审已本地通过：新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/stage6_review_report.md`、`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_review_manifest.json`。
- Stage 6 复审复跑 S06-P1/S06-P2/S06-P3 validators、全量 KMFA tests、S05-P3 authority baseline dependency、治理 validator、raw/secret scan、JSON/JSONL parse、parameter CSV shape、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 6 final GitHub upload 已生成证据：`KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json`；upload base `fd14057e7427d7f275fdb62a33619936618d0d35`，reviewed content commit `5cd284e500fec5ff215741b0e8ee164912f50268`，reviewed S06-P3 commit `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`。
- `S07-P1` 已完成本地实现与验证：新增 `KMFA/tools/finance_file_adapter.py`、`KMFA/tools/check_s07_p1_finance_file_adapter.py`、`KMFA/tests/test_finance_file_adapter.py`、`KMFA/metadata/imports/finance_support_source_registry.json`、`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/finance_field_candidates.jsonl` 和 `KMFA/stage_artifacts/S07_P1_finance_file_adapter/`。
- S07-P1 覆盖经营分析、日记账、客户账龄、现金、纳税、开票、账户、贷款、研发费用 9 类财务支撑源；生成 45 条 hash-only 字段候选和 9 条只读字段报告。
- S07-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`wps_scope_included=false`、`redcircle_scope_included=false`。
- `S07-P2` 已完成本地实现与验证：新增 `KMFA/tools/wps_file_adapter.py`、`KMFA/tools/check_s07_p2_wps_file_adapter.py`、`KMFA/tests/test_wps_file_adapter.py`、`KMFA/metadata/imports/wps_export_source_registry.json`、`KMFA/metadata/schema_maps/wps_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/wps_field_mappings.jsonl`、`KMFA/metadata/schema_maps/wps_mapping_rule_versions.json`、`KMFA/metadata/schema_maps/wps_file_mapping_policy.yaml` 和 `KMFA/stage_artifacts/S07_P2_wps_file_adapter/`。
- S07-P2 覆盖 WPS 回款、应收账龄、生产项目状态、保证金 4 类导出；生成 20 条 hash-only 字段映射、4 条转换提示、4 条只读字段报告和 1 个映射规则版本。
- S07-P2 不提交 raw business data、WPS 原始文件、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`finance_scope_included=false`、`redcircle_scope_included=false`。
- `S07-P3` 已完成本地实现与验证：新增 `KMFA/tools/redcircle_postponement_policy.py`、`KMFA/tools/check_s07_p3_redcircle_postponement.py`、`KMFA/tests/test_redcircle_postponement_policy.py`、`KMFA/metadata/imports/redcircle_export_source_registry.json`、`KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`、`KMFA/metadata/schema_maps/redcircle_reserved_export_templates.jsonl`、`KMFA/metadata/schema_maps/redcircle_postponement_policy.yaml` 和 `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/`。
- S07-P3 只预留红圈经营、合同、回款、财务 4 类导出模板；D15 文件型 MVP 明确不接自动接口；后续接入必须只读、留 hash、可回滚并需人工授权。
- S07-P3 不提交 raw business data、红圈原始导出文件、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文、接口凭证或真实业务值；`formal_report_allowed=false`、`q5_calculation_baseline_allowed=false`、`external_connector_included=false`。
- Stage 7 整体复审已本地通过：新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/stage7_review_report.md`、`KMFA/stage_artifacts/S07_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_review_manifest.json`。
- Stage 7 复审复跑 S07-P1/S07-P2/S07-P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 7 final GitHub upload 已生成证据：新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json`。
- `S08-P1` 已完成本地实现与验证：新增 `KMFA/tools/project_composite_key.py`、`KMFA/tools/check_s08_p1_project_composite_key.py`、`KMFA/tests/test_project_composite_key.py`、`KMFA/metadata/schema_maps/project_composite_key_manifest.json`、`KMFA/metadata/schema_maps/project_identity_profiles.jsonl`、`KMFA/metadata/schema_maps/project_composite_key_matches.jsonl`、`KMFA/metadata/quality/project_identity_review_queue.jsonl` 和 `KMFA/stage_artifacts/S08_P1_project_composite_key/`。
- S08-P1 使用合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个 public-safe 组件和整数 basis points 权重；单字段缺失不全阻断，低于强匹配阈值进入人工复核队列，`auto_merge_allowed=false`。
- S08-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；S08-P2 已由业务实体模型覆盖，但 S08-P1 自身不做 S08-P3、Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。
- `S08-P2` 已完成本地实现与验证：新增 `KMFA/tools/business_entity_model.py`、`KMFA/tools/check_s08_p2_business_entity_model.py`、`KMFA/tests/test_business_entity_model.py`、`KMFA/metadata/schema_maps/business_entity_model_manifest.json`、`KMFA/metadata/schema_maps/business_entity_model_schema.json`、`KMFA/metadata/schema_maps/business_entity_relationships.jsonl`、`KMFA/metadata/schema_maps/business_entity_lifecycle_statuses.jsonl`、`KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md` 和 `KMFA/stage_artifacts/S08_P2_business_entity_model/`。
- S08-P2 定义 customer、contract、project、cost_record、invoice、collection、receivable、tax_evidence 8 类业务实体，建立 14 条实体关系和 32 条生命周期状态；只保存 schema/hash/ref/status/evidence metadata。
- S08-P2 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；不做 S08-P3、Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。
- `S08-P3` 已完成本地实现与验证：新增 `KMFA/tools/entity_matching_quality.py`、`KMFA/tools/check_s08_p3_entity_matching_quality.py`、`KMFA/tests/test_entity_matching_quality.py`、`KMFA/metadata/quality/entity_matching_quality_manifest.json`、`KMFA/metadata/quality/entity_matching_quality_cases.jsonl`、`KMFA/metadata/quality/entity_matching_review_queue.jsonl` 和 `KMFA/stage_artifacts/S08_P3_entity_matching_quality/`。
- S08-P3 覆盖同名项目、多主体、多账户、多期间 4 类 public-safe 质量场景，生成 4 条 quality cases、3 条 manual review queue records 和 1 份 `entity_matching_report`；中高风险候选 `auto_merge_allowed=false`。
- S08-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、来源表头明文或真实业务值；不做 Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。
- Stage 8 整体复审已本地通过：新增 `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/stage8_review_report.md`、`KMFA/stage_artifacts/S08_STAGE_REVIEW/human/test_results.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_review_manifest.json`。
- Stage 8 复审复跑 S08-P1/S08-P2/S08-P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse、diff check 和 evidence consistency check；复审步骤本身未执行 GitHub upload。
- Stage 8 final GitHub upload 为历史 legacy 证据：`KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json` 记录旧基线上传；该证据非当前 v0.1.3 active upload gate，当前 GitHub main 未上传。
- Stage 8 upload 基于最新 `origin/main` commit `ce2881204c49a56da463893db5314ff180c7812d` rebase Stage 8 栈，复跑 validators、治理 validator、raw/secret scan、parse checks、dry-run push、push 和 post-push parity。
- `S10-P1` 已完成本地实现与验证：新增 `KMFA/tools/report_templates.py`、`KMFA/tools/check_s10_p1_report_templates.py`、`KMFA/tests/test_report_templates.py`、`KMFA/metadata/reports/report_template_manifest.json`、`KMFA/metadata/reports/report_templates.jsonl`、`KMFA/metadata/reports/report_template_sections.jsonl` 和 `KMFA/stage_artifacts/S10_P1_report_templates/`。
- S10-P1 覆盖 2 个模板和 11 个章节：项目成本专题报告含经营摘要、项目毛利、成本结构、风险事项；经营总览报告含经营总览、收入、开票、回款、现金、项目、税务。
- S10-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；`formal_report_allowed=false`、`trusted_grade_assignment_allowed=false`、`s10_p2_scope_included=false`、`s10_p3_scope_included=false`、`ui_scope_included=false`。
- `S12-P1` 已完成本地实现与验证：新增 `KMFA/tools/manual_resolution_events.py`、`KMFA/tools/check_s12_p1_manual_resolution_events.py`、`KMFA/tests/test_manual_resolution_events.py`、`KMFA/metadata/approvals/manual_resolution_event_manifest.json`、`KMFA/metadata/approvals/manual_resolution_events.jsonl` 和 `KMFA/stage_artifacts/S12_P1_manual_resolution_events/`。
- S12-P1 只建立 public-safe append-only 人工处理事件，覆盖字段映射、项目匹配、差异处理、备注；每个事件记录处理人、时间、原因、影响范围和版本；approved 事件不可静默改写，只能追加反向事件。
- S12-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；不发布 S12-P2 影响预览，不执行 S12-P3 派生重跑，不做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。
- `S12-P2` 已完成本地实现与验证：新增 `KMFA/tools/manual_impact_preview.py`、`KMFA/tools/check_s12_p2_manual_impact_preview.py`、`KMFA/tests/test_manual_impact_preview.py`、`KMFA/metadata/approvals/manual_impact_preview_manifest.json`、`KMFA/metadata/approvals/manual_impact_previews.jsonl` 和 `KMFA/stage_artifacts/S12_P2_manual_impact_preview/`。
- S12-P2 只建立 public-safe 影响预览，基于 5 条 S12-P1 人工处理事件生成 5 条 impact previews；提交前展示受影响项目、指标、报告；3 条高风险预览需要二次确认，pending 时阻断发布。
- S12-P2 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；不执行 S12-P3 派生重跑，不做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。
- `S12-P3` 已完成本地实现与验证：新增 `KMFA/tools/manual_rerun_mechanism.py`、`KMFA/tools/check_s12_p3_manual_rerun_mechanism.py`、`KMFA/tests/test_manual_rerun_mechanism.py`、`KMFA/metadata/lineage/manual_rerun_manifest.json`、`KMFA/metadata/lineage/manual_rerun_cache_invalidations.jsonl`、`KMFA/metadata/lineage/manual_rerun_steps.jsonl`、`KMFA/metadata/lineage/manual_rerun_consistency_checks.jsonl` 和 `KMFA/stage_artifacts/S12_P3_manual_rerun_mechanism/`。
- S12-P3 只对 2 条 preview passed/publish-allowed 事件失效派生缓存并重跑字段映射、事实层、指标和报告引用；3 条高风险 pending preview 不进入重跑。
- S12-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文或真实业务值；不生成正式报告，不做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。
- Stage 12 整体复审已完成本地验证：新增 `KMFA/tools/check_s12_stage_review.py`、`KMFA/tests/test_s12_stage_review.py` 和 `KMFA/stage_artifacts/S12_STAGE_REVIEW/`。
- Stage 12 review 复跑 S12-P1/P2/P3 validators、Stage 12 review validator、全量 152 个 KMFA tests、治理 validator、raw/secret scan 和 parse checks；修复 HANDOFF stale next-step finding。
- Stage 12 review 不执行 GitHub upload、S13、lineage full check、正式报告、差异关闭或外部接口。
- Stage 12 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/machine/stage12_upload_manifest.json`，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity。
- `S13-P1` 已完成本地实现与验证：新增 `KMFA/tools/financial_operating_report.py`、`KMFA/tools/check_s13_p1_financial_operating_report.py`、`KMFA/tests/test_financial_operating_report.py`、`KMFA/metadata/reports/financial_operating_report_manifest.json`、`KMFA/metadata/reports/financial_operating_report_source_lanes.jsonl`、`KMFA/metadata/reports/financial_operating_report_drafts.jsonl` 和 `KMFA/stage_artifacts/S13_P1_financial_operating_report/`。
- S13-P1 覆盖经营情况、费用税金资产、现金情况、贷款明细 4 条 public-safe 数据接入 lane，生成经营周报初稿和经营月报初稿；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告和经营决策依据。
- S13-P1 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实账号或 credentials；不执行 S13-P2、S13-P3、Stage 13 review、GitHub upload、lineage full check、正式报告、外部接口、付款、贷款管理或税务申报。
- `S13-P2` 已完成本地实现与验证：新增 `KMFA/tools/collection_receivable_aging.py`、`KMFA/tools/check_s13_p2_collection_receivable_aging.py`、`KMFA/tests/test_collection_receivable_aging.py`、`KMFA/metadata/reports/collection_receivable_aging_manifest.json`、`KMFA/metadata/reports/collection_receivable_aging_source_lanes.jsonl`、`KMFA/metadata/reports/collection_receivable_aging_priority_items.jsonl`、`KMFA/metadata/reports/collection_receivable_aging_responsibility_items.jsonl` 和 `KMFA/stage_artifacts/S13_P2_collection_receivable_aging/`。
- S13-P2 覆盖回款表、应收账龄、客户账龄、日记账、开票计划 5 条 public-safe source lane，识别已开票未回款、完工未结算、结算未开票、超期应收 4 类问题，生成 4 条回款优先级、4 条责任事项和 1 个 HTML evidence；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、催收/付款/法务动作和经营决策依据。
- S13-P2 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实客户/项目明细、真实账号或 credentials；不执行 S13-P3、Stage 13 review、GitHub upload、lineage full check、正式报告、外部接口、开票、付款、银行、税务或法务催收动作。
- `S13-P3` 已完成本地实现与验证：新增 `KMFA/tools/cross_table_review.py`、`KMFA/tools/check_s13_p3_cross_table_review.py`、`KMFA/tests/test_cross_table_review.py`、`KMFA/metadata/reports/cross_table_review_manifest.json`、`KMFA/metadata/reports/cross_table_review_checks.jsonl`、`KMFA/metadata/reports/cross_table_difference_queue.jsonl`、`KMFA/metadata/reports/operating_report_quality_report.json` 和 `KMFA/stage_artifacts/S13_P3_cross_table_review/`。
- S13-P3 覆盖项目、客户、金额、时间 4 个 public-safe 跨表复核维度，将全部不一致放入 4 条人工差异队列事项，并输出 1 份经营报表质量报告和 1 个 HTML evidence；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据和自动差异处理。
- `S14-P1` 已完成本地实现与验证：新增 `KMFA/tools/fund_cash_loan_plan.py`、`KMFA/tools/check_s14_p1_fund_cash_loan_plan.py`、`KMFA/tests/test_fund_cash_loan_plan.py`、`KMFA/metadata/reports/fund_cash_loan_plan_manifest.json`、`KMFA/metadata/reports/fund_cash_loan_source_lanes.jsonl`、`KMFA/metadata/reports/fund_cash_pressure_signals.jsonl`、`KMFA/metadata/reports/loan_due_alerts.jsonl`、`KMFA/metadata/reports/account_balance_summaries.jsonl` 和 `KMFA/stage_artifacts/S14_P1_fund_cash_loan_plan/`。
- S14-P1 覆盖账户清单、月度现金、资金计划、贷款明细 4 条 public-safe source lane，输出 4 条现金压力信号、3 条贷款到期提示、3 条账户余额汇总和 1 个 HTML overview；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、付款审批、银行操作、贷款管理、开票和税务动作。
- `S14-P2` 已完成本地实现与验证：新增 `KMFA/tools/invoice_tax_plan.py`、`KMFA/tools/check_s14_p2_invoice_tax_plan.py`、`KMFA/tests/test_invoice_tax_plan.py`、`KMFA/metadata/reports/invoice_tax_plan_manifest.json`、`KMFA/metadata/reports/invoice_tax_source_lanes.jsonl`、`KMFA/metadata/reports/invoice_tax_issue_candidates.jsonl`、`KMFA/metadata/reports/invoice_tax_cash_summaries.jsonl` 和 `KMFA/stage_artifacts/S14_P2_invoice_tax_plan/`。
- S14-P2 覆盖开票计划、纳税明细、开票纳税资金汇总 3 条 public-safe source lane，输出待开票、已开票未回款、税率异常候选 3 类事项、3 条现金汇总和 1 个 HTML overview；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、纳税申报、发票开具、付款审批、银行操作和贷款管理动作。
- `S14-P3` 已完成本地实现与验证：新增 `KMFA/tools/policy_evidence_plan.py`、`KMFA/tools/check_s14_p3_policy_evidence_plan.py`、`KMFA/tests/test_policy_evidence_plan.py`、`KMFA/metadata/reports/policy_evidence_plan_manifest.json`、`KMFA/metadata/reports/policy_evidence_directories.jsonl`、`KMFA/metadata/reports/policy_evidence_gaps.jsonl`、`KMFA/metadata/reports/policy_risk_tips.jsonl` 和 `KMFA/stage_artifacts/S14_P3_policy_evidence_plan/`。
- S14-P3 覆盖科小、高新、专精特新、小巨人、研发费用 5 类 public-safe 政策证据目录，只输出 5 条证据缺口和 5 条风险提示；报告等级显示 D，12 条 pending reconciliation 继续阻断正式政策资格结论、政策申报、补贴申请、正式报告、经营决策依据、纳税申报、发票开具、付款、银行、贷款管理和外部接口动作。
- Stage 14 整体复审已完成本地验证：新增 `KMFA/tools/check_s14_stage_review.py`、`KMFA/tests/test_s14_stage_review.py` 和 `KMFA/stage_artifacts/S14_STAGE_REVIEW/`。
- Stage 14 review 复跑 S14-P1/P2/P3 validators、Stage 14 review validator、全量 191 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 evidence consistency；复审未执行 GitHub upload、S15、lineage full check、正式报告、差异关闭、付款、银行、贷款管理、开票、纳税申报、政策申报、补贴申请或外部接口。
- S13-P3 不提交 raw business data、zip、Excel、PDF、私有 CSV、字段明文、真实金额、真实客户/项目明细、真实账号或 credentials；不执行 Stage 13 review、GitHub upload、lineage full check、正式报告、差异关闭、外部接口、开票、付款、银行、税务或法务催收动作。
- Stage 13 整体复审已完成本地验证：新增 `KMFA/tools/check_s13_stage_review.py`、`KMFA/tests/test_s13_stage_review.py` 和 `KMFA/stage_artifacts/S13_STAGE_REVIEW/`。
- Stage 13 review 复跑 S13-P1/P2/P3 validators、Stage 13 review validator、全量 172 个 KMFA tests、治理 validator、raw/secret scan、parse checks 和 evidence consistency；复审未执行 GitHub upload、S14、lineage full check、正式报告、差异关闭或外部接口。
- Stage 13 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/machine/stage13_upload_manifest.json`，记录复跑 validators、治理验证、安全扫描、dry-run push、push 和 post-push parity。
- Stage 14 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/machine/stage14_upload_manifest.json`，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity。
- `S15-P1` 已完成本地实现与验证：新增 `KMFA/tools/performance_fact_fields.py`、`KMFA/tools/check_s15_p1_performance_fact_fields.py`、`KMFA/tests/test_performance_fact_fields.py`、`KMFA/metadata/reports/performance_fact_fields_manifest.json`、`KMFA/metadata/reports/performance_fact_field_definitions.jsonl`、`KMFA/metadata/reports/performance_fact_field_bindings.jsonl`、`KMFA/metadata/reports/performance_fact_manual_review_fields.jsonl` 和 `KMFA/stage_artifacts/S15_P1_performance_fact_fields/`。
- S15-P1 只接入开票金额、毛利率、结算速度、回款速度、审计偏差、客情费率 6 个绩效事实字段，绑定项目成本事实、开票纳税、回款应收账龄和跨表复核 evidence；结算速度、回款速度、审计偏差和客情费率缺少完整权威窗口时标记人工复核。
- S15-P1 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、工资、奖金、薪资、合同或税务申报资料；不输出 S15-P2 绩效事实表/复核清单，不做 S15-P3 工资项目边界接口、Stage 15 review 或 GitHub upload。
- `S15-P2` 已完成本地实现与验证：新增 `KMFA/tools/performance_review_list.py`、`KMFA/tools/check_s15_p2_performance_review_list.py`、`KMFA/tests/test_performance_review_list.py`、`KMFA/metadata/reports/performance_review_manifest.json`、`KMFA/metadata/reports/performance_fact_table.jsonl`、`KMFA/metadata/reports/performance_review_items.jsonl` 和 `KMFA/stage_artifacts/S15_P2_performance_review_list/`。
- S15-P2 只输出 4 条 public-safe 绩效事实行和 16 条异常/人工复核事项，覆盖结算速度、回款速度、审计偏差、客情费率；不计算最终工资、不审批奖金、不导出薪资、不生成最终发放建议。
- S15-P2 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、工资、奖金、薪资、合同或税务申报资料；不做 S15-P3 工资项目边界接口、Stage 15 review 或 GitHub upload。
- `S15-P3` 已完成本地实现与验证：新增 `KMFA/tools/performance_salary_boundary.py`、`KMFA/tools/check_s15_p3_salary_boundary.py`、`KMFA/tests/test_performance_salary_boundary.py`、`KMFA/metadata/reports/performance_salary_boundary_manifest.json`、`KMFA/metadata/reports/performance_fact_output_interface_contract.json`、`KMFA/metadata/reports/salary_system_readiness_draft.jsonl` 和 `KMFA/stage_artifacts/S15_P3_salary_boundary/`。
- S15-P3 只预留 1 个 public-safe 绩效事实输出接口契约和 4 条未来工资系统读取草案；最终审批和发放必须人工处理。
- S15-P3 不提交 raw business data、zip、Excel、PDF、sqlite/db、private CSV、字段明文、真实金额、工资、奖金、薪资、合同或税务申报资料；不创建 live integration、API endpoint、connector、文件导出、工资计算、奖金审批、薪资导出、最终发放、Stage 15 review 或 GitHub upload。
- Stage 15 整体复审已本地通过：新增 `KMFA/tools/check_s15_stage_review.py`、`KMFA/tests/test_s15_stage_review.py` 和 `KMFA/stage_artifacts/S15_STAGE_REVIEW/`；复跑 S15-P1/P2/P3 validators、全量 207 个 KMFA tests、治理 validator、raw/secret scan 和 parse checks；未执行 GitHub upload、S16、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终发放或外部接口。
- Stage 15 final GitHub upload 已完成：新增 `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/machine/stage15_upload_manifest.json`，记录 rebase、validators、安全扫描、dry-run push、push 和 post-push parity；未执行 S16、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终发放或外部接口。

## 关键决策

- canonical GitHub 目录为 `LinzeColin/CodexProject/KMFA`。
- 本地主仓库 root 为 `/Users/linzezhang/Documents/Codex/CodexProject`；普通开发优先使用项目级长期 worktree，例如 KMFA 使用 `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`。
- 只有并行冲突开发、风险隔离、长期实验或用户明确要求时才创建临时 task worktree；新 worktree 优先 sparse checkout，只展开当前项目和必要根文件。
- 公开仓库不保存原始敏感经营数据，只保存 hash、manifest、状态、证据索引和治理记录。
- 后续所有开发工作以 `KMFA/taskpack/v1_2/` 为任务包基线。
- 涉及 UI、报告、前端或验收的 Stage 必须读取 `KMFA/taskpack/v1_2/20_HTML_UIUX_报告预览/`。
- 每次 run work 最多解决一个 Phase；中间 Phase 不上传 GitHub。
- Stage 完成后先整体复审，修复复审问题后再整体上传 GitHub。
- KMFA 后续以 `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa` 作为唯一 canonical 开发入口；除非用户明确要求并行隔离，不再创建新的 `kmfa-s*` 工作树。
- S03-P1 新增的文件登记工具不得保存原始文件 bytes 或明文原始文件名到公开仓库；zip 只能安全解包到私有目录。
- S03-P2 新增的状态事件只能写 metadata，`raw_layer_write_allowed=false`。
- S03-P3 新增的跨源差异队列必须 `auto_selection_allowed=false`，同源不一致只能追加 metadata event。
- S04-P1 金额标准化必须输出整数分；业务金额不得使用 float；空白、横杠、井号、异常文本不得静默转 0。
- S04-P2 字段缺失或异常不得静默跳过；只能进入 metadata 质量状态，且不得写 raw 层或提交真实业务字段值。
- S04-P3 工具测试报告只能使用合成边界值，不得引入真实业务源数据。
- S05-P1 只能登记公开安全 metadata；成员 SHA256 未能从私有 zip 复算时必须显式 pending，不能用 legacy CRC/指纹替代 SHA256。
- S05-P2 公开仓库只能保存字段合同、hash/ref/status 和 private refs；不得保存真实 `raw_value`、`normalized_value`、PDF/Excel/zip、私有 CSV 或业务明文。
- S05-P2 Excel 候选只能通过 owner 或授权私有映射明确角色；机器复核记录不能替代 Q4 人工确认，也不能解除 5 条字段 pending。
- S05-P2 owner decision intake validator 只验证未来决策记录的公开安全边界；它不代表 owner 已作出决策，也不允许进入 Q4/Q5。
- S05-P2 owner decision templates 只帮助生成未来决策记录；模板本身不代表 owner 已决策。
- S05-P2 owner decision application preview 只预演决策的 public-safe 应用路径；active downgrade decision 不代表 Q4/Q5 完成。
- S05-P2 completion gate 的 active downgrade ready 结果只代表 S05-P2 可本地关闭，不代表 Stage 5 完成。
- S05-P3 权威基准锁定只允许 hash/source-anchor 完整且 public-safe 的 40 条 PDF 字段进入 Q5 calculation baseline；Excel candidate 依据 active owner/授权降级决策排除，不得用于正式报告。
- v0.1.4 S05-P3 lock 已完成；Stage 5 review 和 GitHub upload 均未在本轮执行。S05-P3 不代表 zero-delta、lineage、事实层或报告发布完成。
- S06-P1 zero-delta validator、S06-P2 cross-source difference queue、S06-P3 validation evidence output、Stage 6 review/upload、S07-P1 finance adapter、S07-P2 WPS adapter、S07-P3 redcircle postponement policy、Stage 7 review/upload、S08-P1 project composite key、S08-P2 business entity model、S08-P3 entity matching quality、Stage 8 review/upload、S09-P1 public-safe fact layer、S09-P2 margin/cash margin layer、S09-P3 scope reconciliation、Stage 9 review/upload、S10-P1 report templates、S10-P2 report grade runtime、S10-P3 report export、Stage 10 review/upload、S11-P1 home navigation、S11-P2 source check board、S11-P3 project cost page、Stage 11 review/upload、S12-P1 manual resolution events、S12-P2 impact preview、S12-P3 rerun mechanism、Stage 12 review/upload、S13-P1 financial operating report、S13-P2 collection receivable aging、S13-P3 cross table review、Stage 13 review/upload、S14-P1 fund cash loan plan、S14-P2 invoice tax plan、S14-P3 policy evidence plan、Stage 14 review/upload、S15-P1 performance fact fields、S15-P2 performance review list、S15-P3 salary boundary、Stage 15 review 和 Stage 15 upload 已完成；lineage 和报告发布门禁仍未完成。

## 已改/需看文件

- `KMFA/README.md`
- `KMFA/功能清单.md`
- `KMFA/开发记录.md`
- `KMFA/模型参数文件.md`
- `KMFA/docs/governance/*`
- `KMFA/metadata/*`
- `KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/*`
- `KMFA/stage_artifacts/S01_P1_read_only_plan/*`
- `KMFA/stage_artifacts/S01_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S02_P1_metadata_protocol/*`
- `KMFA/stage_artifacts/S02_P2_immutability_policy/*`
- `KMFA/stage_artifacts/S02_P3_quality_gate/*`
- `KMFA/stage_artifacts/S02_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/*`
- `KMFA/stage_artifacts/S03_P1_file_import/*`
- `KMFA/stage_artifacts/S03_P2_source_check_matrix/*`
- `KMFA/stage_artifacts/S03_P3_source_priority/*`
- `KMFA/stage_artifacts/S04_P1_amount_tools/*`
- `KMFA/stage_artifacts/S04_P2_field_standardization/*`
- `KMFA/stage_artifacts/S04_P3_basic_tool_tests/*`
- `KMFA/stage_artifacts/S04_STAGE_REVIEW/*`
- `KMFA/tools/file_import_register.py`
- `KMFA/tools/source_check_matrix.py`
- `KMFA/tools/source_priority.py`
- `KMFA/tools/amount_tools.py`
- `KMFA/tools/check_no_float_money.py`
- `KMFA/tools/field_standardization.py`
- `KMFA/tools/generate_tool_test_report.py`
- `KMFA/tools/a0_file_register.py`
- `KMFA/tools/check_a0_file_registration.py`
- `KMFA/tools/a0_golden_fixture.py`
- `KMFA/tools/check_a0_golden_fixture.py`
- `KMFA/tools/check_s05_p2_excel_owner_decision.py`
- `KMFA/tools/check_s05_p2_owner_decision_intake.py`
- `KMFA/tools/check_s05_p2_owner_decision_templates.py`
- `KMFA/tools/preview_s05_p2_owner_decision_application.py`
- `KMFA/tools/check_s05_p2_completion_gate.py`
- `KMFA/tools/a0_authority_baseline_lock.py`
- `KMFA/tools/check_a0_authority_baseline_lock.py`
- `KMFA/tools/check_part1_stages_01_03_review.py`
- `KMFA/tools/zero_delta_validator.py`
- `KMFA/tests/test_file_import_register.py`
- `KMFA/tests/test_source_check_matrix.py`
- `KMFA/tests/test_source_priority.py`
- `KMFA/tests/test_amount_tools.py`
- `KMFA/tests/test_field_standardization.py`
- `KMFA/tests/test_basic_tool_boundaries.py`
- `KMFA/tests/test_a0_file_register.py`
- `KMFA/tests/test_a0_golden_fixture.py`
- `KMFA/tests/test_s05_p2_excel_owner_decision.py`
- `KMFA/tests/test_s05_p2_owner_decision_intake.py`
- `KMFA/tests/test_s05_p2_owner_decision_templates.py`
- `KMFA/tests/test_s05_p2_owner_decision_application.py`
- `KMFA/tests/test_s05_p2_completion_gate.py`
- `KMFA/tests/test_s05_p3_authority_baseline_lock.py`
- `KMFA/tests/test_part1_stages_01_03_review.py`
- `KMFA/tests/test_zero_delta_validator.py`
- `KMFA/tests/test_cross_source_difference_queue.py`
- `KMFA/tests/test_validation_evidence_output.py`
- `KMFA/tools/cross_source_difference_queue.py`
- `KMFA/tools/check_s06_p2_difference_queue.py`
- `KMFA/tools/validation_evidence_output.py`
- `KMFA/tools/check_s06_p3_validation_evidence.py`
- `KMFA/tools/home_navigation_runtime.py`
- `KMFA/tools/check_s11_p1_home_navigation.py`
- `KMFA/tools/source_check_board_runtime.py`
- `KMFA/tools/check_s11_p2_source_check_board.py`
- `KMFA/tools/project_cost_page_runtime.py`
- `KMFA/tools/check_s11_p3_project_cost_page.py`
- `KMFA/tools/check_s11_stage_review.py`
- `KMFA/tests/test_home_navigation_runtime.py`
- `KMFA/tests/test_source_check_board_runtime.py`
- `KMFA/tests/test_project_cost_page_runtime.py`
- `KMFA/tests/test_s11_stage_review.py`
- `KMFA/metadata/imports/file_import_policy.yaml`
- `KMFA/metadata/sources/source_check_matrix_schema.json`
- `KMFA/metadata/sources/source_check_matrix_policy.yaml`
- `KMFA/metadata/sources/source_check_matrix.jsonl`
- `KMFA/metadata/sources/source_status_events.jsonl`
- `KMFA/metadata/sources/source_priority_policy.yaml`
- `KMFA/metadata/sources/source_priority_events.jsonl`
- `KMFA/metadata/quality/source_difference_queue.jsonl`
- `KMFA/metadata/schema_maps/field_alias_dictionary.csv`
- `KMFA/metadata/schema_maps/field_standardization_policy.yaml`
- `KMFA/metadata/quality/field_quality_status.jsonl`
- `KMFA/metadata/baseline/a0_file_manifest.json`
- `KMFA/metadata/baseline/a0_project_candidates.jsonl`
- `KMFA/metadata/baseline/a0_golden_fixture_manifest.json`
- `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`
- `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`
- `KMFA/metadata/baseline/a0_authority_baseline_records.jsonl`
- `KMFA/metadata/reports/home_navigation_manifest.json`
- `KMFA/metadata/reports/home_navigation_modules.jsonl`
- `KMFA/metadata/reports/source_check_board_manifest.json`
- `KMFA/metadata/reports/source_check_board_rows.jsonl`
- `KMFA/metadata/reports/project_cost_page_manifest.json`
- `KMFA/metadata/reports/project_cost_page_projects.jsonl`
- `KMFA/stage_artifacts/S05_P1_a0_file_registration/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/*`
- `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/*`
- `KMFA/stage_artifacts/S06_P1_zero_delta_validator/*`
- `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/*`
- `KMFA/stage_artifacts/S06_P3_validation_evidence_output/*`
- `KMFA/stage_artifacts/S06_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S11_P1_home_navigation/*`
- `KMFA/stage_artifacts/S11_P2_source_check_board/*`
- `KMFA/stage_artifacts/S11_P3_project_cost_page/*`
- `KMFA/stage_artifacts/S11_STAGE_REVIEW/*`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_resolution_manifest.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_packet.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json`
- `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_templates/*`
- `KMFA/metadata/approvals/resolution_events.jsonl`
- `KMFA/metadata/approvals/control_events.jsonl`
- `KMFA/taskpack/v1_2/*`
- `KMFA/metadata/baseline/*`
- `KMFA/metadata/protocol/*`
- `KMFA/metadata/{sources,imports,schema_maps,quality,lineage,reports,approvals}/*`
- `governance/projects.yaml`
- `README.md`

## 验证命令

```bash
python3 -m unittest KMFA.tests.test_basic_tool_boundaries -q
python3 -m unittest KMFA.tests.test_a0_file_register -q
python3 KMFA/tools/check_a0_file_registration.py
python3 -m unittest KMFA.tests.test_a0_golden_fixture -q
python3 KMFA/tools/check_a0_golden_fixture.py
python3 -m unittest KMFA.tests.test_s05_p2_excel_owner_decision -q
python3 KMFA/tools/check_s05_p2_excel_owner_decision.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_intake -q
python3 KMFA/tools/check_s05_p2_owner_decision_intake.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_templates -q
python3 KMFA/tools/check_s05_p2_owner_decision_templates.py
python3 -m unittest KMFA.tests.test_s05_p2_owner_decision_application -q
python3 -m unittest KMFA.tests.test_s05_p2_completion_gate -q
python3 KMFA/tools/check_s05_p2_completion_gate.py --expect-blocked
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_s05_p3_authority_baseline_lock -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/a0_authority_baseline_lock.py --locked-at 2026-06-30T12:00:00+10:00 --locked-by-ref codex_delegate_s05p3_public_safe_lock_20260630 --check-only
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_a0_authority_baseline_lock.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_zero_delta_validator -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/zero_delta_validator.py --fixture KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_fixture.json --result-json KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_cross_source_difference_queue -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/cross_source_difference_queue.py --fixture KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_pdf_excel_conflict_fixture.json --queue-jsonl KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --gate-json KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p2_difference_queue.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_validation_evidence_output -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/validation_evidence_output.py --zero-delta-result KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_zero_delta_result.json --source-mismatch-report KMFA/stage_artifacts/S06_P1_zero_delta_validator/machine/s06_p1_synthetic_mismatch_report.csv --difference-queue KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_synthetic_difference_queue.jsonl --report-gate KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/machine/s06_p2_report_grade_gate.json --output-dir KMFA/stage_artifacts/S06_P3_validation_evidence_output/machine --metadata-quality-dir KMFA/metadata/quality --evidence-time 2026-06-30T14:30:00+10:00
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s06_p3_validation_evidence.py
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
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest KMFA.tests.test_project_cost_page_runtime -q
PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_s11_p3_project_cost_page.py
python3 KMFA/tools/immutability_policy_check.py
python3 KMFA/tools/metadata_protocol_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
python3 KMFA/tools/check_report_grade_gate.py
git diff --check -- README.md governance/projects.yaml KMFA
```

## 未解决风险

- Stage 5 已完成 S05-P1、S05-P2、S05-P3、整体复审和 GitHub upload；S05-P3 已锁定 40 条 public-safe hash/source-anchor 字段并排除 5 条 Excel 字段；S06-P1、S06-P2、S06-P3、Stage 6 review 和 Stage 6 upload 已完成。
- S05-P1 成员级 SHA256 仍未补算；S05-P2 后续私有审计只确认本机 zip 的 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配，但整包 hash/size 与登记 source package 不匹配。公开仓库不得提交 zip、PDF、Excel 或解包文件。
- S05-P3、Stage 5 review/upload、S06-P1、S06-P2、S06-P3、Stage 6 review/upload、Stage 7 review/upload、Stage 8 review/upload、S09-P1 和 S09-P2 只完成 A0 authority baseline lock、校验/差异/适配/匹配、结构化 fact layer、margin/cash margin 计算合同、整体复审和上传；不能把它扩展解释为差异关闭、lineage 或报告发布。
- S10-P3 public-safe 报告导出、Stage 10 整体复审、final GitHub upload、S11-P1 首页导航、S11-P2 数据源检查板、S11-P3 项目成本页面、Stage 11 review/upload、S12-P1/P2/P3、Stage 12 review/upload、S13-P1 财务经营报表初稿、S13-P2 回款应收账龄草案、S13-P3 跨表复核、Stage 13 review/upload、S14-P1 资金计划现金贷款、S14-P2 开票纳税、S14-P3 政策证据、Stage 14 review/upload、S15-P1 绩效事实字段、S15-P2 绩效复核清单、S15-P3 工资项目边界、Stage 15 review/upload、S16-P1 外协采购归集、S16-P2 项目状态生命周期、S16-P3 客户经营分析、Stage 16 整体复审、Stage 16 upload、S17-P1 权限与安全、S17-P2 通知提醒、S17-P3 运维与 SOP、Stage 17 整体复审、Stage 17 upload、S18-P1 精度与压力测试、S18-P2 全量回归验收、S18-P3 后续接入准备、Stage 18 整体复审和 Stage 18 upload 已完成；lineage 完整检查和运行时正式报告生成尚未实现。
- S02-P3 只实现 report grade gate 协议；正式报告生成和 lineage 完整检查仍属后续 Stage。
- Stage 3 已上传 GitHub main；业务导入解析、A0、zero-delta、lineage 和报告生成仍是后续 Stage。
- v1.2 中私有源数据只能本地使用，不能提交公开 GitHub。

## 下一步

下一步只能另起 run work 执行 `v0.1.3 S10-P3 report export replay` 或用户明确指定的单一 phase；GitHub main upload 必须等 v1.3 Stage 1-10 全部完成、整体复审通过并修复 findings 后一次性执行。本轮 S10-P2 未上传 GitHub；不得把旧 Stage 4/5/6/7/8/9/10 upload gate 作为 active next step，也不得推进 Stage 10 review、raw value matching、lineage full check、正式报告、live connector、Redcircle automatic connector、OpMe 深度耦合或业务执行。
## 2026-07-05 Latest Handoff - V014 Owner Authorized Fill Application

Current phase completed locally: `V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION`.

Current state:
- `active_authorized_fill_record_found=false`
- `fill_application_performed=false`
- `source_map_records_applied_count=0`
- `new_authorized_fingerprint_count=0`
- `source_map_gap_resolution_complete=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw data remains immutable for Codex; this phase did not read, list, fingerprint, write, delete, move, rename, overwrite, normalize or copy raw sources.

Evidence:
- `KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_APPLICATION/machine/private_processed_value_source_map_owner_authorized_fill_application_manifest.json`
- `KMFA/tools/check_v014_private_processed_value_source_map_owner_authorized_fill_application.py`
- `KMFA/tests/test_v014_private_processed_value_source_map_owner_authorized_fill_application.py`

Next allowed step:
- Only run one follow-up phase after an active owner/authorized fill record is supplied, or another explicitly named single phase.
- Do not run materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Auto Candidate Draft

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_AUTO_CANDIDATE_DRAFT`.

Current state:
- `candidate_draft_item_count=113`
- `auto_unique_candidate_item_count=0`
- `auto_ambiguous_candidate_item_count=101`
- `auto_unmatched_item_count=4`
- `non_numeric_or_calculation_context_item_count=8`
- `unresolved_question_item_count=113`
- `raw_numeric_candidate_count=351453`
- `raw_unique_numeric_fingerprint_count=22453`
- `raw_root_stat_unchanged_after_auto_candidate_draft=true`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was read/list/stat/fingerprinted only under owner authorization; raw source mutation, copying into Git, overwrite, move, rename, delete and normalization were not performed.

Private outputs:
- Private raw source index, candidate completion template draft, auto match diagnostic and Chinese question list are under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_auto_candidate_draft/`.
- These private outputs contain raw filenames, source context, table/header/value diagnostics and must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_AUTO_CANDIDATE_DRAFT/machine/processed_value_source_map_completion_auto_candidate_draft_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_auto_candidate_draft.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_auto_candidate_draft.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 KMFA/tools/check_v014_processed_value_source_map_completion_auto_candidate_draft.py --require-private-draft`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_auto_candidate_draft -q`
- governance validators passed; strict credential scan returned no hits; tracked raw/private suffix scan returned no hits.

Next allowed step:
- Owner/authorized delegate must review the private candidate draft and answer/confirm the Chinese question list before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Review Intake Prep

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_REVIEW_INTAKE_PREP`.

Current state:
- `review_group_count=22`
- `response_template_row_count=113`
- `candidate_catalog_record_count=304`
- `source_auto_ambiguous_candidate_item_count=101`
- `source_auto_unmatched_item_count=4`
- `source_non_numeric_or_calculation_context_item_count=8`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed the prior ignored private candidate draft.

Private outputs:
- Grouped private review intake, response template, candidate catalog and grouped Chinese question list are under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_review_intake_prep/`.
- These private outputs may contain raw-derived candidate detail and must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_REVIEW_INTAKE_PREP/machine/processed_value_source_map_completion_owner_review_intake_prep_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_review_intake_prep.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_review_intake_prep.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_review_intake_prep.py --require-private-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_review_intake_prep -q`

Next allowed step:
- Owner/authorized delegate must fill the private owner-review response template before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Response Readiness Recheck

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_READINESS_RECHECK`.

Current state:
- `response_row_count=113`
- `pending_owner_decision_count=113`
- `valid_owner_decision_count=0`
- `invalid_owner_decision_count=0`
- `active_owner_authorized_fill_record_ready=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed the ignored private owner-review response template.

Private output:
- Private readiness diagnostic is under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_response_readiness_recheck/`.
- It must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_READINESS_RECHECK/machine/processed_value_source_map_completion_owner_response_readiness_recheck_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_readiness_recheck.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_response_readiness_recheck.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_readiness_recheck.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_response_readiness_recheck -q`

Next allowed step:
- Owner/authorized delegate must fill the private owner-review response template before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Response Decision Options

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_DECISION_OPTIONS`.

Current state:
- `source_response_row_count=113`
- `source_pending_owner_decision_count=113`
- `decision_option_count=3`
- `non_active_draft_row_count=113`
- `active_owner_authorized_fill_record_ready=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed ignored private response/intake/readiness artifacts.

Private outputs:
- Private decision options, confirmation codes, non-active draft and diagnostic are under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_response_decision_options/`.
- These private outputs are not authorization records and must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_RESPONSE_DECISION_OPTIONS/machine/processed_value_source_map_completion_owner_response_decision_options_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_decision_options.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_response_decision_options.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_response_decision_options.py --require-private-options`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_response_decision_options -q`

Next allowed step:
- Owner/authorized delegate must confirm one private decision option or fill the private owner-review response template before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Group Decision Application

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_APPLICATION`.

Current state:
- `review_group_count=22`
- `response_row_count=113`
- `pending_group_decision_row_count=113`
- `valid_group_decision_row_count=0`
- `invalid_group_decision_row_count=0`
- `owner_group_decision_applied=false`
- `active_owner_authorized_fill_record_ready=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed ignored private owner review-groups path artifacts.

Private output:
- Private owner group decision application diagnostic and pending queue are under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_application/`.
- These private outputs must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_APPLICATION/machine/processed_value_source_map_completion_owner_group_decision_application_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_application.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_application.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_group_decision_application.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_application.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_application.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_application.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_group_decision_application -q`

Next allowed step:
- Owner/authorized delegate must supply group-level decisions before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Group Decision Input Kit

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_INPUT_KIT`.

Current state:
- `review_group_count=22`
- `response_row_count=113`
- `pending_group_template_count=22`
- `allowed_owner_group_decision_code_count=5`
- `owner_group_decisions_supplied=false`
- `owner_group_decision_applied=false`
- `active_owner_authorized_fill_record_ready=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed ignored private pending queue, application diagnostic and review-groups packet artifacts.

Private output:
- Private owner group decision response template, codebook and diagnostic are under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_input_kit/`.
- These private outputs must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_INPUT_KIT/machine/processed_value_source_map_completion_owner_group_decision_input_kit_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_group_decision_input_kit.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_input_kit.py --require-private-kit`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_group_decision_input_kit -q`

Next allowed step:
- Owner/authorized delegate must fill the private group decision response template before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Group Decision Response Intake

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_RESPONSE_INTAKE`.

Current state:
- `review_group_count=22`
- `response_row_count=113`
- `pending_group_decision_count=22`
- `valid_group_decision_count=0`
- `invalid_group_decision_count=0`
- `owner_group_decisions_supplied=false`
- `owner_group_decision_applied=false`
- `active_owner_authorized_fill_record_ready=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed ignored private owner group decision response template and input-kit diagnostic artifacts.

Private output:
- Private owner group decision response intake diagnostic and pending group queue are under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_response_intake/`.
- These private outputs must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_group_decision_response_intake_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_group_decision_response_intake.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_response_intake.py --require-private-intake`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_group_decision_response_intake -q`

Next allowed step:
- Owner/authorized delegate must replace pending group decision codes before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.

## 2026-07-06 Latest Handoff - V014 Processed Value Source-map Completion Owner Group Decision Blocker Audit

Current phase completed locally: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_BLOCKER_AUDIT`.

Current state:
- `consecutive_goal_turn_blocker_count=4`
- `blocked_audit_threshold_met=true`
- `goal_status_recommendation=blocked`
- `review_group_count=22`
- `response_row_count=113`
- `pending_group_decision_count=22`
- `valid_group_decision_count=0`
- `owner_group_decisions_supplied=false`
- `owner_group_decision_applied=false`
- `active_owner_authorized_fill_record_ready=false`
- `go_no_go=NO_GO`
- `github_upload_performed=false`
- `app_reinstall_performed=false`
- raw inbox was not read by this phase; it only consumed public-safe summaries and ignored private owner group decision response template artifacts.

Private output:
- Private owner group decision blocker audit diagnostic is under `KMFA/.codex_private_runtime/v014_processed_value_source_map_completion_owner_group_decision_blocker_audit/`.
- This private output must not be committed to GitHub.

Evidence:
- `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_GROUP_DECISION_BLOCKER_AUDIT/machine/processed_value_source_map_completion_owner_group_decision_blocker_audit_manifest.json`
- `KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py`
- `KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py`

Verified:
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile KMFA/tools/v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py KMFA/tests/test_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit.py --require-private-diagnostic`
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -m unittest KMFA.tests.test_v014_processed_value_source_map_completion_owner_group_decision_blocker_audit -q`

Next allowed step:
- Owner/authorized delegate must replace pending group decision codes before any active completion template or source-map application phase.
- Do not run source-map reapplication, materialization replay, raw-to-processed comparison, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall, live connector or business execution from this state.
- Later cross-validation must reconcile processed outputs to raw source truth; if repeated verification still diverges, final goal closeout must include a discrepancy report.
