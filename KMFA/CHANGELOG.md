# Changelog

## 0.1.3-raw-data-boundary-policy - 2026-07-02

- 登记项目级 raw data inbox：`/Users/linzezhang/Downloads/KMFA_MetaData` 是用户本机 KMFA 财务原始数据目录。
- 明确该目录对 Codex 只读；不得修改、删除、移动、重命名、覆盖或写入生成文件。
- 新增 `KMFA/docs/governance/RAW_DATA_BOUNDARY.md`，并同步 `KMFA/AGENTS.md`、`KMFA/HANDOFF.md` 和 `KMFA/docs/governance/STATUS.md`。
- Codex 私有 inventory、schema/header diagnostic、mapping diagnostic、scratch files 或本地报告只能写入 `KMFA/.codex_private_runtime/` 或明确 Git 忽略的项目受控目录。
- 本次仅更新项目级治理记忆和 GitHub 备份策略，不执行 S02-P3、Stage 2 review、raw value matching、lineage full check、正式报告、外部接口或业务动作。

## 0.1.3-s02p2-raw-mapping-readiness - 2026-07-02

- 完成 `v0.1.3 S02-P2｜raw mapping/value matching readiness` 本地验证：只读解析 `/Users/linzezhang/Downloads/KMFA_MetaData` 的 ZIP/XLSX 容器和表结构，公开证据仅记录 raw_files=5、zip_openable=3、zip_member_count=95、workbooks_seen=48、workbooks_parseable=25、sheets_seen=4198 等聚合计数。
- 新增 `KMFA/tools/v013_s02_p2_raw_mapping_readiness.py`、`KMFA/tools/check_v013_s02_p2_raw_mapping_readiness.py`、`KMFA/tests/test_v013_s02_p2_raw_mapping_readiness.py` 和 `KMFA/stage_artifacts/V013_S02_P2_RAW_MAPPING_READINESS/`。
- 私有 schema/header/mapping diagnostic 只写入 `KMFA/.codex_private_runtime/v013_s02_p2_raw_mapping_readiness/`；公开仓库不包含 raw 文件名、ZIP member 名、sheet 名、field/header 明文、row values、raw hash 或业务值。
- 本 phase 将 raw value matching 锁定为 `blocked_authorized_mapping_required`：S02-P2 只建立私有 schema/header readiness，不抽取 row value；值级对账仍需后续 owner/授权语义映射和专用 parser phase。
- 本轮不执行 S02-P3、Stage 2 整体复审、GitHub upload、rebase、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行。

## 0.1.3-s02p1-raw-readiness - 2026-07-02

- 完成 `v0.1.3 S02-P1｜raw 数据只读清单与准备度` 本地验证：只读扫描 `/Users/linzezhang/Downloads/KMFA_MetaData`，确认 raw 目录存在且可读，当前公开汇总为 5 个文件、总大小 62788056 bytes、扩展名计数 `.xlsx=2` 和 `.zip=3`。
- 新增 `KMFA/tools/v013_s02_p1_raw_readiness.py`、`KMFA/tools/check_v013_s02_p1_raw_readiness.py`、`KMFA/tests/test_v013_s02_p1_raw_readiness.py` 和 `KMFA/stage_artifacts/V013_S02_P1_RAW_READINESS/` 证据包。
- 私有清单和本地诊断只写入 `KMFA/.codex_private_runtime/v013_s02_p1_raw_inventory/`，该目录已被 `KMFA/.gitignore` 忽略；公开证据不包含 raw 文件名、raw 文件哈希、字段明文、表头、行值或业务金额。
- 本 phase 不执行 raw value matching；原因是 S02-P1 只做 inventory/readiness，值级对账需要后续授权 parser/mapping phase。
- 本轮不执行 Stage 2 整体复审、GitHub upload、rebase、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行；后续 GitHub upload 统一延后到整体完成 gate。

## 0.1.3-s01-stage-review - 2026-07-02

- 完成 `v0.1.3 Stage 1｜整体复审` 本地验证：复跑 S01-P1 当前状态复核、S01-P2 范围冻结、S01-P3 防遗漏门禁和 Stage 1 review validator，确认三个 phase 均为 PASS。
- 新增 `KMFA/tools/check_v013_s01_stage_review.py`、`KMFA/tests/test_v013_s01_stage_review.py` 和 `KMFA/stage_artifacts/V013_S01_STAGE_REVIEW/` 证据包，锁定 findings_open=0、findings_fixed=0、github_upload=false、delivery_allowed=false、formal_report_allowed=false、business_execution_allowed=false。
- 继承当前 `NO_GO` blockers：0 条 actual lineage rows、12 条 pending reconciliation 和 2 条 D 级 report runtime 继续阻断正式报告、经营决策依据、release claim 和 delivery claim。
- 本轮只执行 Stage 1 整体复审，不执行 GitHub upload、rebase、S02、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行。
- `/Users/linzezhang/Downloads/KMFA_MetaData` 仍为只读 raw boundary；本轮不读取该目录内容，不修改、删除、移动或提交其中任何文件。

## 0.1.3-s01p3-no-omission-gate - 2026-07-02

- 完成 `v0.1.3 S01-P3｜防遗漏门禁复跑` 本地验证：复跑正式 `KMFA/tools/no_omission_check.py`，确认 requirements=20、P0=9、P1=8、stage_status_records=549、task_records=162。
- 新增 `KMFA/tools/check_v013_s01_p3_no_omission_gate.py`、`KMFA/tests/test_v013_s01_p3_no_omission_gate.py` 和 `KMFA/stage_artifacts/V013_S01_NO_OMISSION_GATE/` 证据包，绑定旧 S01-P3 baseline、v1.2 FULL_HTML_NO_OMISSION 基线和 v0.1.3 S01-P2 范围冻结边界。
- 继续记录外部 v0.1.3 roadmap 原路径当前不可读，未从缺失文件推断新需求；repo 内 v1.2 taskpack/roadmap 仍为可读基线。
- 本轮只执行一个 phase，不执行 Stage 1 整体复审、GitHub upload、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行。
- `/Users/linzezhang/Downloads/KMFA_MetaData` 仍为只读 raw boundary；本 phase 不读取该目录内容，不修改、删除、移动或提交其中任何文件。

## 0.1.3-s01p2-scope-freeze - 2026-07-02

- 完成 `v0.1.3 S01-P2｜范围冻结` 本地验证：锁定本修补包当前只做 public-safe scope freeze，不解决 lineage/reconciliation/report blockers。
- 新增 `KMFA/tools/check_v013_s01_p2_scope_freeze.py`、`KMFA/tests/test_v013_s01_p2_scope_freeze.py` 和 `KMFA/stage_artifacts/V013_S01_SCOPE_FREEZE/` 证据包，继承 S01-P1 的 0 条 actual lineage rows、12 条 pending reconciliation 和 2 条 D 级报告。
- 记录外部 v0.1.3 roadmap 原路径当前不可读，未从缺失文件推断新需求；repo 内 v1.2 taskpack/roadmap 仍为可读基线。
- 登记本机 KMFA 财务原始数据目录 `/Users/linzezhang/Downloads/KMFA_MetaData` 为只读 raw boundary；Codex 不得修改、删除、移动或提交其中任何文件，临时处理只能进入 `KMFA/.codex_private_runtime/`。
- 本轮只执行一个 phase，不执行 S01-P3、Stage 1 整体复审、GitHub upload、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行。

## 0.1.3-s01p1-current-state-preflight - 2026-07-02

- 完成 `v0.1.3 S01-P1｜当前状态复核` 本地验证：读取 S18、LINEAGE_REPORT_GATE、S09 evidence 和治理状态，锁定当前仍为 `NO_GO`。
- 新增 `KMFA/tools/check_v013_s01_p1_preflight.py`、`KMFA/tests/test_v013_s01_p1_preflight.py` 和 `KMFA/stage_artifacts/V013_S01_PRECHECK/` 证据包，复算 0 条 actual lineage rows、12 条 pending reconciliation 和 2 条 D 级报告。
- 本轮只执行一个 phase，不执行 S01-P2、Stage 1 整体复审、GitHub upload、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行。
- 公开仓库未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、credentials、银行流水、合同、薪资或税务申报材料；`NO_GO` 和 `delivery_allowed=false` 保持不变。

## 0.1.3-s00p1-app-entry - 2026-07-02

- 完成 `v0.1.3 S00-P1｜Downloads App Entry` 本地验证：已在 `/Users/linzezhang/Downloads/KMFA.app` 建立 KMFA app 入口，并更新 KMFA 专用 `.icns` 图标。
- 新增 `KMFA/tools/check_v013_s00_app_entry.py`、`KMFA/tests/test_v013_s00_app_entry.py` 和 `KMFA/stage_artifacts/V013_S00_APP_ENTRY/` 证据包，锁定 app bundle、canonical worktree、public-safe 首页 HTML 和图标 hash。
- 本轮只执行一个 phase，不执行 Stage 0 整体复审、GitHub upload、lineage full check、reconciliation closure、正式报告、live connector、OpMe 深度耦合或业务执行。
- 公开仓库未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、credentials、银行流水、合同、薪资或税务申报材料；`NO_GO` 和 `delivery_allowed=false` 保持不变。

## 0.1.0-post-s18-final-no-go-backup-upload - 2026-07-02

- 新增 `KMFA-FINAL-GITHUB-BACKUP-NO-GO-20260702` final backup/upload 证据，明确本次上传仅为 `NO_GO governance backup only`。
- 新增 `KMFA/tools/check_final_no_go_backup_upload.py`、`KMFA/tests/test_final_no_go_backup_upload.py` 和 `KMFA/stage_artifacts/FINAL_GITHUB_BACKUP/`。
- 基于 `origin/main` `54219915c038e645327f6f4d57787227c205a142` 完成 rebase；当前仍保持 0 条 actual lineage rows、12 条 pending reconciliation 和 2 条 D 级报告阻断。
- 本轮不执行正式报告、release、delivery、live connector、OpMe 深度耦合、生产恢复或业务动作。

## 0.1.0-post-s18-lineage-report-gate-local - 2026-07-02

- 新增 `KMFA-LINEAGE-REPORT-GATE-PENDING_OWNER_SCOPE-20260702` 本地 gate 证据，明确当前只能保持 `NO_GO`。
- 新增 `KMFA/tools/check_lineage_report_gate.py`、`KMFA/tests/test_lineage_report_gate.py`、`KMFA/metadata/quality/lineage_report_release_gate_review.json` 和 `KMFA/stage_artifacts/LINEAGE_REPORT_GATE/`。
- validator 复算 0 条 actual lineage rows、2 条 D 级报告 runtime、12 条 pending reconciliation、0 个 formal report allowed/export decision basis allowed。
- 后续若上传 GitHub，只能标记为 `NO_GO governance backup only`；本轮未执行 GitHub upload、backup、lineage full check completion、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-post-s18-whole-project-review-local - 2026-07-02

- 完成 Post-S18 第二阶段全项目本地复审和 findings 修复。
- 修复 task pack 指定命令缺口：新增 public-safe synthetic `KMFA/metadata/fixtures/a0_project_cost_fixture.json`，`zero_delta_validator.py --fixture` 现在可直接通过。
- 新增 `KMFA/tools/check_lineage_completeness.py`、`KMFA/tests/test_lineage_completeness.py`、`KMFA/tools/check_whole_project_final_review.py`、`KMFA/tests/test_whole_project_final_review.py` 和 `KMFA/stage_artifacts/WHOLE_PROJECT_FINAL_REVIEW/`。
- 新增当前全项目 Go/No-Go `KMFA/metadata/quality/whole_project_go_no_go_review.json`，把历史 `STAGE18_GITHUB_UPLOAD_PENDING` 记录为 resolved，但保持 `NO_GO`、`delivery_allowed=false`。
- 本轮未执行 GitHub upload、backup、local cleanup、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-post-s18-part6-review-local - 2026-07-02

- 完成 Post-S18 第一阶段 Part 6 本地复审，范围仅为 Stage 16、Stage 17、Stage 18。
- 新增 `KMFA/tools/check_part6_stages_16_18_review.py`、`KMFA/tests/test_part6_stages_16_18_review.py` 和 `KMFA/stage_artifacts/PART6_STAGES_16_18_REVIEW/`。
- 复跑 S16 subcontract/project/customer、S17 access/notification/operations、S18 precision/regression/integration validators、Part 6 review validator、全量 274 个 KMFA tests、治理 validators、parse checks、raw/private scan、secret scan 和 diff check。
- 本轮未执行 GitHub upload、整体项目复审、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行；Stage 18 review-level Go/No-Go 仍为 `NO_GO`。

## 0.1.0-post-s18-part5-review-local - 2026-07-02

- 完成 Post-S18 第一阶段 Part 5 本地复审，范围仅为 Stage 13、Stage 14、Stage 15。
- 新增 `KMFA/tools/check_part5_stages_13_15_review.py`、`KMFA/tests/test_part5_stages_13_15_review.py` 和 `KMFA/stage_artifacts/PART5_STAGES_13_15_REVIEW/`。
- 复跑 S13 financial operating/collection/cross-table、S14 fund/invoice/policy、S15 performance/salary-boundary validators、Part 5 review validator、全量 273 个 KMFA tests、治理 validators、parse checks、raw/private scan、secret scan 和 diff check。
- 本轮未执行 GitHub upload、Stage 16-18 复审、整体项目复审、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-post-s18-part4-review-local - 2026-07-02

- 完成 Post-S18 第一阶段 Part 4 本地复审，范围仅为 Stage 10、Stage 11、Stage 12。
- 新增 `KMFA/tools/check_part4_stages_10_12_review.py`、`KMFA/tests/test_part4_stages_10_12_review.py` 和 `KMFA/stage_artifacts/PART4_STAGES_10_12_REVIEW/`。
- 复跑 S10 report templates/grade/export、S11 home/source board/project cost page、S12 manual resolution/impact preview/rerun validators、Part 4 review validator、全量 272 个 KMFA tests、治理 validators、parse checks、raw/private scan、secret scan 和 diff check。
- 本轮未执行 GitHub upload、Stage 13-18 复审、整体项目复审、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-post-s18-part3-review-local - 2026-07-02

- 完成 Post-S18 第一阶段 Part 3 本地复审，范围仅为 Stage 7、Stage 8、Stage 9。
- 新增 `KMFA/tools/check_part3_stages_07_09_review.py`、`KMFA/tests/test_part3_stages_07_09_review.py` 和 `KMFA/stage_artifacts/PART3_STAGES_07_09_REVIEW/`。
- 复跑 S07 finance/WPS/Redcircle adapters、S08 project/entity matching、S09 project cost fact/margin/scope reconciliation validators、Part 3 review validator、全量 271 个 KMFA tests、治理 validators、parse checks、raw/private scan、secret scan 和 diff check。
- 本轮未执行 GitHub upload、Stage 10-18 复审、整体项目复审、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-post-s18-part2-review-local - 2026-07-02

- 完成 Post-S18 第一阶段 Part 2 本地复审，范围仅为 Stage 4、Stage 5、Stage 6。
- 新增 `KMFA/tools/check_part2_stages_04_06_review.py`、`KMFA/tests/test_part2_stages_04_06_review.py` 和 `KMFA/stage_artifacts/PART2_STAGES_04_06_REVIEW/`。
- 复跑 S04 金额/字段/工具边界、S05 A0 authority baseline、S06 zero-delta/difference queue validators、Part 2 review validator、全量 270 个 KMFA tests、治理 validators、parse checks、raw/private scan、secret scan 和 diff check。
- 本轮未执行 GitHub upload、Stage 7-18 复审、整体项目复审、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-post-s18-part1-review-local - 2026-07-02

- 完成 Post-S18 第一阶段 Part 1 本地复审，范围仅为 Stage 1、Stage 2、Stage 3。
- 新增 `KMFA/tools/check_part1_stages_01_03_review.py`、`KMFA/tests/test_part1_stages_01_03_review.py` 和 `KMFA/stage_artifacts/PART1_STAGES_01_03_REVIEW/`。
- 复跑 S01-S03 相关 no-omission、required HTML、metadata protocol、immutability、report grade gate、S03 unit tests、全量 269 个 KMFA tests、治理 validators、parse checks、raw/private scan、secret scan 和 diff check。
- 本轮未执行 GitHub upload、Stage 4-18 复审、整体项目复审、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-s18-github-upload - 2026-07-01

- 完成 Stage 18 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `acddc0d36150c072606afad9f91846967cbb4de3` rebase Stage 18 栈，并复跑 S18-P1/P2/P3 validators、Stage 18 review validator、全量 268 个 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S18_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S18_GITHUB_UPLOAD/machine/stage18_upload_manifest.json`。
- 上传范围只包含 public-safe 精度压力、全量回归验收、后续接入准备、Stage 18 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或接口凭证。
- Stage 18 upload 不实现 lineage full check、正式报告、完整报告邮件、live connector、OpMe 深度耦合、生产恢复、外部服务调用或业务 release。
- 后续只能另开独立目标确认 lineage/report gate 范围，不得跳过 `NO_GO`、D 级报告和 pending reconciliation 阻断进入业务执行。

## 0.1.0-s18-stage-review - 2026-07-01

- 完成 `Stage 18 整体复审` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/check_s18_stage_review.py`、`KMFA/tests/test_s18_stage_review.py`、`KMFA/metadata/quality/stage18_go_no_go_review.json` 和 `KMFA/stage_artifacts/S18_STAGE_REVIEW/`。
- 复跑并锁定 S18-P1 精度压力、S18-P2 全量回归验收、S18-P3 后续接入准备证据；复审级 Go/No-Go 清除 `S18_P3_PENDING`，但仍保持 `NO_GO`。
- 复审后下一 gate 为 `KMFA-S18-GITHUB-UPLOAD-GATE`；仍未执行 GitHub upload、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。

## 0.1.0-s18p3-integration-preparation - 2026-07-01

- 完成 `S18-P3｜后续接入准备` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/integration_preparation.py` 和 `KMFA/tools/check_s18_p3_integration_preparation.py`，生成并验证 public-safe 后续接入准备 artifacts。
- 新增 `KMFA/tests/test_integration_preparation.py`，覆盖红圈/金蝶/WPS 只读 future connector、OpMe 轻入口、下一阶段 backlog、scope gate、public-safe 禁止词和 CLI validator。
- 新增 `KMFA/metadata/integration/integration_preparation_manifest.json`、`read_only_connector_plan.jsonl`、`opme_entry_integration_plan.json`、`next_stage_backlog.jsonl` 和 `KMFA/stage_artifacts/S18_P3_integration_preparation/` 证据包。
- 红圈、金蝶、WPS 仅整理为后续只读 future connector 方案；OpMe 仅整理为轻入口、报告索引、运行状态和 handoff 指针方案，不深度耦合。
- 未执行 Stage 18 整体复审、GitHub upload、lineage full check、正式报告、live connector、OpMe 深度耦合、生产恢复或业务执行。
- 下一轮只能执行 `Stage 18 整体复审`。

## 0.1.0-s18p2-full-regression - 2026-07-01

- 完成 `S18-P2｜全量回归和验收` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/full_regression_acceptance.py` 和 `KMFA/tools/check_s18_p2_full_regression_acceptance.py`，生成并验证 public-safe 全量回归验收 artifacts。
- 新增 `KMFA/tests/test_full_regression_acceptance.py`，覆盖五类检查、18 个 Stage evidence、Go/No-Go、scope gate、public-safe 禁止词和 CLI validator。
- 新增 `KMFA/metadata/quality/full_regression_acceptance_manifest.json`、`full_regression_check_results.jsonl`、`stage_acceptance_evidence_index.jsonl`、`go_no_go_report.json` 和 `KMFA/stage_artifacts/S18_P2_full_regression_acceptance/` 证据包。
- S18-P2 Go/No-Go 结论为 `NO_GO`，`delivery_allowed=false`、`github_upload_allowed=false`，因为 lineage full check、正式报告发布、S18-P3 和 Stage 18 review 仍未完成。
- S18-P2 只使用 public-safe metadata/evidence；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或接口凭证。
- 未执行 S18-P3 后续接入准备、Stage 18 整体复审、GitHub upload、lineage full check、正式报告、OpMe 集成、live connector、生产恢复或业务执行。
- 下一轮只能执行 `S18-P3｜后续接入准备`。

## 0.1.0-s18p1-precision-stress - 2026-07-01

- 完成 `S18-P1｜精度与压力测试` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/precision_stress_validation.py` 和 `KMFA/tools/check_s18_p1_precision_stress.py`，生成并验证 public-safe synthetic 精度/压力测试 artifacts。
- 新增 `KMFA/tests/test_precision_stress_validation.py`，覆盖金额精度、zero-delta、重复导入、坏文件、缺字段、连续三次一致性、大批量性能预算、错误报告、HTML 样板读取和 scope gate。
- 新增 `KMFA/metadata/quality/precision_stress_manifest.json`、`precision_stress_scenarios.jsonl`、`precision_stress_import_runs.jsonl`、`precision_stress_error_reports.jsonl` 和 `KMFA/stage_artifacts/S18_P1_precision_stress/` 证据包。
- S18-P1 只使用 public-safe synthetic metadata；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或接口凭证。
- 未执行 S18-P2 全量回归验收、S18-P3 后续接入准备、Stage 18 整体复审、GitHub upload、lineage full check、正式报告、OpMe 集成、live connector、生产恢复或业务执行。
- 下一轮只能执行 `S18-P2｜全量回归和验收`。

## 0.1.0-s17-github-upload - 2026-07-01

- 完成 Stage 17 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `52c15e845c8d3b02d935bd5a234a213b43cd1d9f` rebase Stage 17 栈，并复跑 S17-P1/P2/P3 validators、Stage 17 review validator、全量 246 个 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S17_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S17_GITHUB_UPLOAD/machine/stage17_upload_manifest.json`。
- 上传范围只包含 public-safe 权限安全、通知提醒、运维 SOP、Stage 17 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或接口凭证。
- Stage 17 upload 不实现 S18、lineage full check、正式报告、完整报告邮件、live connector、生产恢复、外部服务调用或业务 release。
- 下一轮只能作为新 run work 从 `S18-P1｜精度与压力测试` 开始，且必须读取 v1.2 task pack、roadmap 和 HTML/UIUX/报告样板。

## 0.1.0-s17-stage-review - 2026-07-01

- 完成 `Stage 17 整体复审` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/check_s17_stage_review.py`、`KMFA/tests/test_s17_stage_review.py` 和 `KMFA/stage_artifacts/S17_STAGE_REVIEW/`。
- 复跑 S17-P1 权限与安全、S17-P2 通知提醒、S17-P3 运维与 SOP validators，确认 4 类角色、15 类敏感材料禁入策略、5 类审计动作、3 类提醒、metadata-only 通知日志、4 类 runbook、2 条知识索引和 2 条演练日志仍为 public-safe evidence。
- 复审将下一 gate 推进到 `KMFA-S17-GITHUB-UPLOAD-GATE`；仍未执行 GitHub upload、S18、lineage full check、正式报告、完整报告邮件、外部邮件连接器、live connector、生产恢复或业务执行。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或 credentials。
- 下一轮只能执行 `Stage 17 GitHub upload`。

## 0.1.0-s17p3-operations-sop - 2026-07-01

- 完成 `S17-P3｜运维与 SOP` 本地验证。
- 新增 `KMFA/tools/operations_sop.py` 和 `KMFA/tools/check_s17_p3_operations_sop.py`，生成并验证导入、复核、发布、回滚四类操作手册。
- 新增 `KMFA/tests/test_operations_sop.py`，覆盖 metadata-only runbook、财务 SOP/交接材料知识索引、错误处理/备份恢复演练、live connector/生产恢复/业务动作阻断和 scope gate。
- 新增 `KMFA/metadata/operations/` 下 S17-P3 manifest、operations runbooks、finance SOP knowledge index、error/backup drill log，以及 `KMFA/stage_artifacts/S17_P3_operations_sop/` 证据包。
- 保持中间 Phase 不上传 GitHub；未执行 Stage 17 review、lineage full check、正式报告、live connector、生产恢复、外部服务调用或业务执行。
- 下一轮只能执行 `Stage 17 整体复审`。

## 0.1.0-s17p2-notification - 2026-07-01

- 完成 `S17-P2｜通知` 本地验证。
- 新增 `KMFA/tools/notification_reminders.py` 和 `KMFA/tools/check_s17_p2_notifications.py`，生成并验证报告生成完成、重大风险、数据源缺失三类通知提醒。
- 新增 `KMFA/tests/test_notification_reminders.py`，覆盖 email reminder only、metadata outbox/log、完整报告正文/附件/真实收件地址/外部连接器阻断和 scope gate。
- 新增 `KMFA/metadata/notifications/` 下 S17-P2 manifest、rules、events、dispatch log，以及 `KMFA/stage_artifacts/S17_P2_notification/` 证据包。
- 保持中间 Phase 不上传 GitHub；未执行 S17-P3 运维 SOP、Stage 17 review、lineage full check、正式报告、外部邮件连接器、完整报告邮件正文、报告附件或业务执行。
- 下一轮只能执行 `S17-P3｜运维与SOP`。

## 0.1.0-s17p1-access-security - 2026-07-01

- 完成 `S17-P1｜权限与安全` 本地验证。
- 新增 `KMFA/tools/access_security_policy.py` 和 `KMFA/tools/check_s17_p1_access_security.py`，生成并验证角色权限矩阵、公开仓库敏感材料禁入策略和审计日志策略。
- 新增 `KMFA/tests/test_access_security_policy.py`，覆盖 management、finance、reviewer、readonly 角色、15 类敏感材料禁入、import/processing/report/export/notification 五类审计动作和 scope gate。
- 新增 `KMFA/metadata/security/` 下 S17-P1 public-safe manifest、role matrix、sensitive policy、audit policy，以及 `KMFA/stage_artifacts/S17_P1_access_security/` 证据包。
- 保持中间 Phase 不上传 GitHub；未执行 S17-P2 通知投递、S17-P3 运维 SOP、Stage 17 review、lineage full check、正式报告或外部接口。
- 下一轮只能执行 `S17-P2｜通知`。

## 0.1.0-s16-github-upload - 2026-07-01

- 完成 Stage 16 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `25698b30517e07e0655ff842f588d008516bc1d9` rebase Stage 16 栈，并复跑 S16-P1/P2/P3 validators、Stage 16 review validator、全量 227 个 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S16_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S16_GITHUB_UPLOAD/machine/stage16_upload_manifest.json`。
- 上传范围只包含 public-safe 外协采购归集、项目状态生命周期、客户经营分析、Stage 16 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或接口凭证。
- Stage 16 upload 不实现 S17、lineage full check、正式报告、经营决策依据、采购执行、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收、法律决策、外部 connector 或业务 release。
- 下一轮只能作为新 run work 从 `S17-P1｜权限与安全` 开始，且必须重新执行 git/root/status 检查并读取 v1.2 task pack / roadmap。

## 0.1.0-s16-stage-review - 2026-07-01

- 完成 `Stage 16 整体复审` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/check_s16_stage_review.py`、`KMFA/tests/test_s16_stage_review.py` 和 `KMFA/stage_artifacts/S16_STAGE_REVIEW/`。
- 复跑 S16-P1 外协采购归集、S16-P2 项目状态生命周期、S16-P3 客户经营分析 validators，确认 4 条外协来源线、5 条项目匹配、2 条未归集成本池、4 条外协异常候选、6 条项目状态来源线、4 条生命周期记录、3 条项目异常、3 条 handoff guard、5 条客户来源线、4 条客户经营摘要和 4 条客户异常事项仍为 public-safe 证据。
- 复审将下一 gate 推进到 `KMFA-S16-GITHUB-UPLOAD-GATE`；仍未执行 GitHub upload、S17、lineage full check、正式报告、经营决策依据发布、采购执行、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收、法律决策或外部 connector。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或 credentials。
- 下一轮只能执行 `Stage 16 GitHub upload`，且 upload 前必须基于最新 origin/main 复跑 validators、治理校验、安全扫描、parse checks 和 diff check。

## 0.1.0-s16-p3-local - 2026-07-01

- 完成 `S16-P3｜客户经营分析` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/customer_business_analysis.py`、`KMFA/tools/check_s16_p3_customer_business_analysis.py` 和 `KMFA/tests/test_customer_business_analysis.py`。
- 生成 `customer_business_analysis_manifest.json`、`customer_analysis_source_lanes.jsonl`、`customer_operating_summaries.jsonl`、`customer_analysis_exception_items.jsonl` 和 `S16_P3_customer_business_analysis/` 证据。
- 覆盖客户价值、项目毛利、回款质量、账龄风险 4 个维度，生成 5 条来源线、4 条客户经营摘要和 4 条异常复核事项。
- 客户经营摘要和异常事项均保持 review-only，不触发自动催收、客户联系、法律决策、开票、付款、银行、税务或外部接口动作。
- 报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、催收/法律/付款/银行动作和业务 release。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实客户/项目名称、银行流水、合同、薪资、税务申报材料或 credentials。
- S16-P3 不执行 Stage 16 review、GitHub upload、lineage full check、正式报告、外部 connector 或任何业务执行动作。
- 下一轮只能执行 `Stage 16 整体复审`。

## 0.1.0-s16-p2-local - 2026-07-01

- 完成 `S16-P2｜项目状态生命周期` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/project_status_lifecycle.py`、`KMFA/tools/check_s16_p2_project_status_lifecycle.py` 和 `KMFA/tests/test_project_status_lifecycle.py`。
- 生成 `project_status_lifecycle_manifest.json`、`project_status_source_lanes.jsonl`、`project_lifecycle_records.jsonl`、`project_lifecycle_exception_items.jsonl`、`project_lifecycle_handoff_guards.jsonl` 和 `S16_P2_project_status_lifecycle/` 证据。
- 覆盖生产项目状态、开工、完工、结算、开票、回款 6 条状态来源线，生成 4 条生命周期记录、3 条异常事项和 3 条人工 handoff guard。
- 完工未结算、结算未开票、开票未回款均保持 review-only，不触发开票、催收、付款、银行、现场施工、安全签字或技术签字动作。
- 报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、现场/签字/结算/开票/催收/付款/银行动作和业务 release。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实项目/客户名称、银行流水、合同、薪资、税务申报材料或 credentials。
- S16-P2 不执行 S16-P3、Stage 16 review、GitHub upload、lineage full check、正式报告、外部 connector 或任何业务执行动作。
- 下一轮只能执行 `S16-P3｜客户经营分析`。

## 0.1.0-s16-p1-local - 2026-07-01

- 完成 `S16-P1｜外协采购归集` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/subcontract_procurement_aggregation.py`、`KMFA/tools/check_s16_p1_subcontract_procurement.py` 和 `KMFA/tests/test_subcontract_procurement_aggregation.py`。
- 生成 `subcontract_procurement_aggregation_manifest.json`、`subcontract_procurement_source_lanes.jsonl`、`subcontract_project_matches.jsonl`、`subcontract_unallocated_cost_pool.jsonl`、`subcontract_anomaly_candidates.jsonl` 和 `S16_P1_subcontract_procurement_aggregation/` 证据。
- 覆盖外协费用、采购、付款按项目匹配；未匹配进入 2 条未归集成本池；识别 2 条重复付款候选和 2 条跨项目费用候选。
- 报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、采购执行、付款执行、银行操作、供应商结算和业务 release。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、银行流水、合同、薪资、税务申报材料或 credentials。
- S16-P1 不执行 S16-P2、S16-P3、Stage 16 review、GitHub upload、lineage full check、正式报告、外部 connector 或任何采购/付款/银行执行动作。
- 下一轮只能执行 `S16-P2｜项目状态生命周期`。

## 0.1.0-s15-github-upload - 2026-07-01

- 完成 Stage 15 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `7aff82efe2dd83fce940a97868868c13e65a6f1c` rebase Stage 15 栈，并复跑 S15-P1/P2/P3 validators、Stage 15 review validator、全量 207 个 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S15_GITHUB_UPLOAD/machine/stage15_upload_manifest.json`。
- 上传范围只包含 public-safe 绩效事实字段、绩效事实表、异常/人工复核事项、工资项目边界契约/读取草案、Stage 15 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实人员明细、薪资材料、合同、税务申报材料或接口凭证。
- Stage 15 upload 不实现 S16、lineage full check、正式报告、外部 connector、工资计算、奖金审批、薪资导出、最终发放、付款执行或业务 release。
- 下一轮只能作为新 run work 从 `S16-P1｜外协采购归集` 开始，且必须重新执行 git/root/status 检查并读取 v1.2 task pack / roadmap。

## 0.1.0-s15-stage-review - 2026-07-01

- 完成 `Stage 15 整体复审` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/check_s15_stage_review.py`、`KMFA/tests/test_s15_stage_review.py` 和 `KMFA/stage_artifacts/S15_STAGE_REVIEW/`。
- 复跑 S15-P1 绩效事实字段、S15-P2 绩效复核清单、S15-P3 工资项目边界 validators，确认 6 个绩效事实字段、4 条绩效事实行、16 条复核事项、1 个事实输出接口契约和 4 条未来读取草案仍为 public-safe 证据。
- 复审将下一 gate 推进到 `KMFA-S15-GITHUB-UPLOAD-GATE`；仍未执行 GitHub upload、S16、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终薪酬结论、付款发放或外部 connector。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、人员薪资材料、合同、税务申报材料或 credentials。
- 下一轮只能执行 `Stage 15 GitHub upload`，且 upload 前必须基于最新 origin/main 复跑 validators、治理校验和安全扫描。

## 0.1.0-s15p3-salary-boundary - 2026-07-01

- 完成 `S15-P3｜与工资项目边界` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/performance_salary_boundary.py`、`KMFA/tools/check_s15_p3_salary_boundary.py` 和 `KMFA/tests/test_performance_salary_boundary.py`。
- 生成 `performance_salary_boundary_manifest.json`、`performance_fact_output_interface_contract.json`、`salary_system_readiness_draft.jsonl` 和 `S15_P3_salary_boundary/` 证据。
- 仅预留 public-safe 绩效事实输出接口契约和未来工资系统读取草案；不创建 live integration、API endpoint、connector、文件导出或外部写入。
- 明确最终审批和发放必须人工处理；不计算工资、不审批奖金、不导出薪资、不产生最终薪酬或发放结论。
- 下一轮只能执行 Stage 15 整体复审；不得直接 GitHub upload。

## 0.1.0-s15p2-performance-review-list - 2026-07-01

- 完成 `S15-P2｜绩效复核清单` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/performance_review_list.py`、`KMFA/tools/check_s15_p2_performance_review_list.py` 和 `KMFA/tests/test_performance_review_list.py`。
- 生成 `performance_review_manifest.json`、`performance_fact_table.jsonl`、`performance_review_items.jsonl` 和 `S15_P2_performance_review_list/` 证据。
- 输出 4 条 public-safe 绩效事实行和 16 条异常/人工复核事项，覆盖结算速度、回款速度、审计偏差、客情费率四类人工复核字段。
- 明确不计算最终工资、不审批奖金、不导出薪资、不产生最终发放结论，不执行 S15-P3、Stage 15 review 或 GitHub upload。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、来源表头明文、真实金额、真实人员/客户/项目明细、薪资税务材料或 credentials。
- 下一轮只能执行 `S15-P3｜与工资项目边界`。

## 0.1.0-s15p1-performance-fact-fields - 2026-07-01

- 完成 `S15-P1｜绩效事实字段` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/performance_fact_fields.py`、`KMFA/tools/check_s15_p1_performance_fact_fields.py` 和 `KMFA/tests/test_performance_fact_fields.py`。
- 建立 6 个 public-safe 绩效事实字段定义和 6 条 source binding：开票金额、毛利率、结算速度、回款速度、审计偏差、客情费率。
- 对结算速度、回款速度、审计偏差、客情费率标记人工复核；本 phase 不输出绩效事实表或异常项目复核清单。
- 报告等级继续显示 D；正式报告、经营决策依据、工资计算、奖金审批、薪资导出、付款执行、Stage 15 review 和 GitHub upload 均保持阻断。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、来源表头明文、真实金额、真实人员/客户/项目明细、薪资税务材料或 credentials。
- 下一轮只能执行 `S15-P2｜绩效复核清单`。

## 0.1.0-s14-github-upload - 2026-07-01

- 完成 Stage 14 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `76782d14bd324a3c44f4e7fc843b6e7cad8843a2` rebase Stage 14 栈，并复跑 S14-P1/P2/P3 validators、Stage 14 review validator、全量 191 个 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S14_GITHUB_UPLOAD/machine/stage14_upload_manifest.json`。
- 上传范围只包含 public-safe 资金/现金/贷款 planning signals、开票纳税 planning signals、政策证据目录/缺口/风险提示、Stage 14 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额、税务申报材料、政策申报材料、政策评分、正式资格结论或 credentials。
- Stage 14 upload 不实现 S15、lineage full check、正式报告、外部 connector、差异关闭、付款、银行、贷款管理、发票开具、纳税申报、政策申报、补贴申请或业务 release。
- 下一轮只能作为新 run work 从 `S15-P1｜销售绩效事实与复核清单` 开始，且必须重新执行 git/root/status 检查并读取 v1.2 task pack / roadmap。

## 0.1.0-s14-stage-review - 2026-07-01

- 完成 `Stage 14 整体复审` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/check_s14_stage_review.py`、`KMFA/tests/test_s14_stage_review.py` 和 `KMFA/stage_artifacts/S14_STAGE_REVIEW/`。
- 复跑 S14-P1 资金计划现金贷款、S14-P2 开票纳税、S14-P3 政策证据 validators，确认三个 phase 仍为 public-safe D 级 planning/evidence signals。
- 复审将下一 gate 推进到 `KMFA-S14-GITHUB-UPLOAD-GATE`；仍未执行 GitHub upload、S15、lineage full check、正式报告、差异关闭、付款、银行、贷款管理、开票、纳税申报、政策资格正式结论、政策申报、补贴申请或外部 connector。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、发票号、税务申报材料、政策申报材料、政策评分、正式资格结论或 credentials。
- 下一轮只能执行 `Stage 14 GitHub upload`，且 upload 前必须基于最新 origin/main 复跑 validators、治理校验和安全扫描。

## 0.1.0-s14p3-policy-evidence-plan - 2026-07-01

- 完成 `S14-P3｜政策证据` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/policy_evidence_plan.py`、`KMFA/tools/check_s14_p3_policy_evidence_plan.py` 和 `KMFA/tests/test_policy_evidence_plan.py`。
- 登记 5 类 public-safe 政策证据目录：科小、高新、专精特新、小巨人、研发费用；输出 5 条证据缺口、5 条风险提示和 1 个蓝色商务风 HTML overview。
- 报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、政策资格正式结论、申报提交、纳税申报、发票开具、付款、银行、贷款管理和业务 release。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、发票号、税务申报材料、政策申报材料、政策评分、正式资格结论或 credentials。
- S14-P3 不执行 Stage 14 整体复审、GitHub upload、lineage full check、正式报告、外部 connector 或任何资金/银行/贷款/开票/税务/政策申报执行动作。
- Stage 14 三个 phase 已本地完成；下一轮只能执行 `Stage 14 整体复审`。

## 0.1.0-s14p2-invoice-tax-plan - 2026-07-01

- 完成 `S14-P2｜开票纳税` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/invoice_tax_plan.py`、`KMFA/tools/check_s14_p2_invoice_tax_plan.py` 和 `KMFA/tests/test_invoice_tax_plan.py`。
- 生成 3 条 public-safe source lane：开票计划、纳税明细、开票纳税资金汇总；共 6 个 source refs、30 个字段映射 refs。
- 输出待开票、已开票未回款、税率异常候选 3 类事项、3 条现金汇总和 1 个蓝色商务风 HTML overview。
- 报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、纳税申报、发票开具、付款审批、银行操作、贷款管理和业务 release。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、发票号、税务申报材料或 credentials。
- S14-P2 不执行 S14-P3 政策证据、Stage 14 整体复审、GitHub upload、lineage full check、正式报告、外部 connector 或任何资金/银行/贷款/开票/税务执行动作。
- 下一轮只能执行 `S14-P3｜政策证据`。

## 0.1.0-s14p1-fund-cash-loan-plan - 2026-07-01

- 完成 `S14-P1｜资金计划现金贷款` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/fund_cash_loan_plan.py`、`KMFA/tools/check_s14_p1_fund_cash_loan_plan.py` 和 `KMFA/tests/test_fund_cash_loan_plan.py`。
- 生成 4 条 public-safe source lane：账户清单、月度现金、资金计划、贷款明细；共 5 个 source refs、25 个字段映射 refs。
- 输出 4 条现金压力信号、3 条贷款到期提示、3 条账户余额汇总和 1 个蓝色商务风 HTML overview。
- 报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据、付款审批、银行操作、贷款管理、开票、税务和业务 release。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实金额、真实账号、银行流水、合同、薪资、税务申报或 credentials。
- S14-P1 不执行 S14-P2 开票纳税、S14-P3 政策证据、Stage 14 整体复审、GitHub upload、lineage full check、正式报告、外部 connector 或任何资金/银行/贷款/开票/税务执行动作。
- 下一轮只能执行 `S14-P2｜开票纳税`。

## 0.1.0-s13-github-upload - 2026-07-01

- 完成 Stage 13 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `dfdf16c98656c4272fa105027dcbf46ba15d37dd` 复跑 S13-P1/P2/P3 validators、Stage 13 review validator、全量 172 个 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S13_GITHUB_UPLOAD/machine/stage13_upload_manifest.json`。
- 上传范围只包含 public-safe S13 财务经营报表初稿、回款应收账龄草案、跨表复核证据、Stage 13 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- Stage 13 upload 不实现 S14、lineage full check、正式报告、外部 connector、差异关闭、开票、付款、银行、税务、法务催收或业务 release。
- 下一轮只能作为新 run work 从 `S14-P1｜资金计划现金贷款` 开始，且必须重新执行 git/root/status 检查并读取 v1.2 task pack / roadmap。

## 0.1.0-s13-stage-review - 2026-07-01

- 完成 Stage 13 整体复审，本地状态为 `review_passed_upload_ready_local_only`，尚未 push GitHub。
- 新增 `KMFA/tools/check_s13_stage_review.py`、`KMFA/tests/test_s13_stage_review.py` 和 `KMFA/stage_artifacts/S13_STAGE_REVIEW/` 复审证据包。
- 复跑并锁定 S13-P1/P2/P3 证据：4 条财务经营 source lane、2 条经营报告初稿、5 条回款应收 source lane、4 条回款优先级、4 条责任事项、4 个跨表复核维度、4 条人工差异队列和 1 份经营报表质量报告。
- 复审确认报告等级仍为 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据和自动差异处理。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额、真实客户/项目明细或 credentials。
- Stage 13 review 不执行 GitHub upload、S14、lineage full check、正式报告、差异关闭、外部 connector、开票、付款、银行、税务或法务催收动作。
- 下一轮只能执行 Stage 13 GitHub upload gate：先对齐最新 `origin/main`，复跑 validators、治理校验、raw/secret scan、parse checks 和 dry-run/push proof。

## 0.1.0-s13p3-cross-table-review - 2026-07-01

- 完成 `S13-P3｜跨表复核` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/cross_table_review.py`、`KMFA/tools/check_s13_p3_cross_table_review.py` 和 `KMFA/tests/test_cross_table_review.py`。
- 生成 4 个 public-safe 跨表复核维度：项目、客户、金额、时间；全部不一致进入 4 条人工差异队列事项。
- 输出 1 份经营报表质量报告和 1 个蓝色商务风 HTML evidence；报告等级显示 D，12 条 pending reconciliation 继续阻断正式报告、经营决策依据和自动差异处理。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、字段明文、真实金额、真实账号、真实客户/项目明细或 credentials。
- S13-P3 不执行 Stage 13 整体复审、GitHub upload、lineage full check、正式报告、差异关闭、外部 connector、开票、付款、银行、税务或法务催收动作。
- 下一轮只能执行 `Stage 13 整体复审`。

## 0.1.0-s13p2-collection-receivable-aging - 2026-07-01

- 完成 `S13-P2｜回款应收账龄` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/collection_receivable_aging.py`、`KMFA/tools/check_s13_p2_collection_receivable_aging.py` 和 `KMFA/tests/test_collection_receivable_aging.py`。
- 生成 5 条 public-safe source lane：回款表、应收账龄、客户账龄、日记账、开票计划；共 5 个 source refs、25 个字段映射 refs。
- 生成 4 类问题草案：已开票未回款、完工未结算、结算未开票、超期应收；输出 4 条回款优先级和 4 条责任事项，并生成 1 个蓝色商务风 HTML evidence。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、字段明文、真实金额、真实账号、真实客户/项目明细或 credentials。
- S13-P2 不执行 S13-P3 跨表复核、Stage 13 整体复审、GitHub upload、lineage full check、正式报告、外部 connector、开票、付款、银行、税务或法务催收动作。
- 下一轮只能执行 `S13-P3｜跨表复核`。

## 0.1.0-s13p1-financial-operating-report - 2026-07-01

- 完成 `S13-P1｜财务经营报表` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/financial_operating_report.py`、`KMFA/tools/check_s13_p1_financial_operating_report.py` 和 `KMFA/tests/test_financial_operating_report.py`。
- 生成 4 条 public-safe 财务经营 source lane：经营情况、费用税金资产、现金情况、贷款明细；共 8 个 source refs、39 个字段映射 refs。
- 生成经营周报初稿和经营月报初稿，并输出 2 个蓝色商务风 HTML draft；初稿展示数据状态、报告等级 D、12 条 pending reconciliation 和使用限制。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、字段明文、真实金额、真实账号或 credentials。
- S13-P1 不执行 S13-P2 回款应收账龄、S13-P3 跨表复核、Stage 13 整体复审、GitHub upload、lineage full check、正式报告、外部 connector、付款、贷款管理或税务申报。
- 下一轮只能执行 `S13-P2｜回款应收账龄`。

## 0.1.0-s12-github-upload - 2026-07-01

- 完成 Stage 12 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `5f6ff2792c8a879998ac90262b0f0a259107cad0` rebase Stage 12 栈，并复跑 S12-P1/P2/P3 validators、Stage 12 review validator、全量 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S12_GITHUB_UPLOAD/machine/stage12_upload_manifest.json`。
- 上传范围只包含 public-safe S12 人工处理事件、影响预览、重跑机制、Stage 12 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- Stage 12 upload 不实现 S13、lineage full check、正式报告、外部 connector、差异关闭或业务 release。
- 下一轮只能作为新 run work 从 `S13-P1｜财务经营报表` 开始，且必须重新执行 git/root/status 检查并读取 v1.2 task pack / roadmap。

## 0.1.0-s12-stage-review - 2026-07-01

- 完成 Stage 12 整体复审，本地状态为 `review_passed_upload_ready_local_only`，尚未 push GitHub。
- 新增 `KMFA/tools/check_s12_stage_review.py`、`KMFA/tests/test_s12_stage_review.py` 和 `KMFA/stage_artifacts/S12_STAGE_REVIEW/` 复审证据包。
- 复跑并锁定 S12-P1/P2/P3 validator 证据：5 条人工处理事件、5 条影响预览、3 条高风险 pending 阻断、2 条 cache invalidation、8 条 rerun step、2 条 same-source consistency check 和 3 个 public-safe HTML 样张。
- 复审修复 `KMFA/HANDOFF.md` 末尾仍指向 S12-P3 的治理 finding，下一 gate 改为 `KMFA-S12-GITHUB-UPLOAD-GATE`。
- 复审确认 GitHub upload、S13、lineage full check、正式报告、差异关闭、外部接口和业务决策依据输出均未执行。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- 下一轮只能执行 Stage 12 final GitHub upload gate：先对齐最新 `origin/main`，复跑 validators、治理校验、raw/secret scan、parse checks 和 dry-run/push proof。

## 0.1.0-s12p3-rerun-mechanism - 2026-07-01

- 完成 `S12-P3｜重跑机制` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/manual_rerun_mechanism.py`、`KMFA/tools/check_s12_p3_manual_rerun_mechanism.py` 和 `KMFA/tests/test_manual_rerun_mechanism.py`。
- 基于 S12-P1 人工处理事件与 S12-P2 影响预览，只有 2 条 preview passed/publish-allowed 事件进入派生缓存失效与重跑；3 条高风险 pending preview 继续阻断。
- 生成 2 条 cache invalidation、8 条 rerun step、2 条 same-source consistency check、stage manifest 和 1 个 public-safe HTML 重跑机制样张。
- 锁定旧派生版本保留、新版本追加，重跑链路覆盖字段映射、事实层、指标、报告引用，并保持 `formal_report=false`、`stage12_review=false`、`github_upload=false`。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- 下一轮只能执行 Stage 12 整体复审；不得直接 upload、进入 S13、执行 lineage full check、正式报告或外部接口。

## 0.1.0-s12p2-impact-preview - 2026-07-01

- 完成 `S12-P2｜影响预览` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/manual_impact_preview.py`、`KMFA/tools/check_s12_p2_manual_impact_preview.py` 和 `KMFA/tests/test_manual_impact_preview.py`。
- 基于 S12-P1 5 条人工处理事件生成 5 条 public-safe impact preview records、manifest、stage manifest 和 1 个蓝色商务风 HTML 影响预览样张。
- 预览提交前展示受影响项目、指标、报告；高风险预览需要二次确认，二次确认 pending 时控制事件发布被阻断。
- 锁定 `未通过影响预览不得发布`，并保持 `derived_rerun_allowed=false`、`formal_report_allowed=false`、`stage12_review_scope_included=false`、`github_upload_scope_included=false`。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- 下一轮只能执行 `S12-P3｜重跑机制`；不得做 Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。

## 0.1.0-s12p1-manual-resolution-events - 2026-07-01

- 完成 `S12-P1｜人工处理事件` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/manual_resolution_events.py`、`KMFA/tools/check_s12_p1_manual_resolution_events.py` 和 `KMFA/tests/test_manual_resolution_events.py`。
- 生成 public-safe manual resolution event manifest、5 条 append-only manual event records 和 1 个蓝色商务风 HTML 人工处理工作台样张。
- 覆盖字段映射、项目匹配、差异处理、备注四类人工动作；每个事件都有处理人、时间、原因、影响范围和版本。
- 已批准事件不可静默改写；变更只能追加反向事件。
- 保持 `raw_layer_write_allowed=false`、`impact_preview_publish_allowed=false`、`derived_rerun_allowed=false`、`formal_report_allowed=false`、`stage12_review_scope_included=false`、`github_upload_scope_included=false`。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- 下一轮只能执行 `S12-P2｜影响预览`；不得做 S12-P3、Stage 12 整体复审、GitHub upload、lineage full check、正式报告或外部接口。

## 0.1.0-s11-github-upload - 2026-07-01

- 完成 Stage 11 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `e694e0ba54b0a36393b42f3fae2d2d9499c3aa42` rebase Stage 11 栈，并复跑 S11-P1/P2/P3 validators、Stage 11 review validator、全量 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S11_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S11_STAGE_REVIEW/machine/stage11_upload_manifest.json`。
- 上传范围只包含 public-safe S11 首页与导航、数据源检查板、项目成本页面、Stage 11 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- Stage 11 upload 不实现 S12、lineage full check、正式报告、外部 connector、差异关闭或派生指标重跑。
- 下一轮只能执行 `S12-P1｜人工处理工作台与重跑机制`，作为独立 phase。

## 0.1.0-s11-stage-review - 2026-07-01

- 完成 Stage 11 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/tools/check_s11_stage_review.py`、`KMFA/tests/test_s11_stage_review.py` 和 `KMFA/stage_artifacts/S11_STAGE_REVIEW/` 复审证据包。
- 复跑并锁定 S11-P1/P2/P3 validator 证据：8 个首页模块、13 行数据源检查板、4 条项目成本页面记录、3 个 public-safe HTML 页面、9 类成本结构和 12 条 pending reconciliation 均保持 public-safe。
- 复审确认正式报告、完整可信报告、经营决策依据、S12、lineage full check、外部 connector 和 GitHub upload 仍未执行。
- 全量 KMFA 单测当前为 132 tests；公开仓库未提交 raw business data、zip、Excel workbook、PDF、sqlite/db、private CSV、字段明文、真实账号、真实金额或 credentials。
- 当前分支在 fetch 后相对 `origin/main` behind 1；下一步只能执行 Stage 11 final GitHub upload gate，先对齐最新 `origin/main`，复跑 validators 和安全检查，并留下 push proof。

## 0.1.0-s11p3-project-cost-page - 2026-07-01

- 完成 `S11-P3｜项目成本页面` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/project_cost_page_runtime.py`、`KMFA/tools/check_s11_p3_project_cost_page.py` 和 `KMFA/tests/test_project_cost_page_runtime.py`。
- 生成 public-safe 项目成本页面 manifest、4 条项目页面记录和 1 个蓝色商务风 HTML 项目成本页面，覆盖项目列表、毛利状态、成本结构、回款状态、差异状态、项目详情、来源证据、待处理事项和报告预览。
- 报告预览允许直接查看，但继续显示 `D` 级；`quality_grade_bypass_allowed=false`、`formal_report_allowed=false`、`complete_trusted_report_display_allowed=false`、`business_decision_basis_allowed=false`。
- 保持 `stage11_review_allowed=false`、`github_upload_allowed=false`、S09-P3 12 条 pending reconciliation 未关闭。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实金额或 credentials。
- S11 三个 phase 已本地验证完成；下一轮只能执行 Stage 11 整体复审，不得做 GitHub upload、S12、lineage full check、正式报告或外部接口。

## 0.1.0-s11p2-source-check-board - 2026-07-01

- 完成 `S11-P2｜数据源检查板` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/source_check_board_runtime.py`、`KMFA/tools/check_s11_p2_source_check_board.py` 和 `KMFA/tests/test_source_check_board_runtime.py`。
- 生成 public-safe 数据源检查板 manifest、13 条检查板记录和 1 个蓝灰商务风 HTML 样张，覆盖固定 11 列和 5 种状态。
- 状态点击可查看影响报告、处理规则和下一步；异常只用小型徽标提示，`large_yellow_surface_count=0`。
- 保持 `formal_report_allowed=false`、`business_decision_basis_allowed=false`、`s11_p3_project_cost_detail_scope_included=false`、`stage11_review_scope_included=false`、`github_upload_allowed=false`。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实账号、真实业务值或 credentials。
- 下一轮只能执行 `S11-P3｜项目成本页面`；不得做 Stage 11 整体复审、GitHub upload、S12、lineage full check、正式报告或外部接口。

## 0.1.0-s11p1-home-navigation - 2026-07-01

- 完成 `S11-P1｜首页与导航` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/home_navigation_runtime.py`、`KMFA/tools/check_s11_p1_home_navigation.py` 和 `KMFA/tests/test_home_navigation_runtime.py`。
- 生成 public-safe 首页导航 manifest、8 条首页模块记录和 1 个蓝色商务风 HTML 首页样张，覆盖经营总览、项目成本、回款应收、财务资金、开票纳税、数据源检查、待处理事项、报告中心。
- 保持 `formal_report_allowed=false`、`business_decision_basis_allowed=false`、`s11_p2_source_matrix_scope_included=false`、`s11_p3_project_cost_detail_scope_included=false`、`stage11_review_scope_included=false`、`github_upload_allowed=false`。
- 不提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文、真实业务值或 credentials。
- 下一轮只能执行 `S11-P2｜数据源检查板`；不得做 Stage 11 整体复审、GitHub upload、S11-P3、S12、lineage full check、正式报告或外部接口。

## 0.1.0-s10-github-upload - 2026-06-30

- 完成 Stage 10 final GitHub upload gate 证据准备：基于最新 `origin/main` rebase S10 stack，并复跑 S10-P1/P2/P3 validators、Stage 10 review validator、全量 KMFA tests、治理 validator、required HTML/no-omission、raw/secret scan、parse checks 和 diff check。
- 新增 `KMFA/stage_artifacts/S10_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S10_STAGE_REVIEW/machine/stage10_upload_manifest.json`。
- 上传范围只包含 public-safe S10 报告模板、D 级报告可信等级运行时、HTML/CSV preview/export、Stage 10 review 和 upload proof；未提交 raw business data、zip、Excel workbook、PDF、private CSV、sqlite/db、字段明文或 credentials。
- Stage 10 上传不实现 S11、UI、lineage full check、正式报告、外部 connector、差异关闭或派生指标重跑。
- 下一轮只能执行 `S11-P1｜首页与导航`，且必须先读取 v1.2 HTML/UIUX 样板和 S11 roadmap；不得跳到 S11-P2/S11-P3、S12 或正式报告。

## 0.1.0-s10-stage-review - 2026-06-30

- 完成 Stage 10 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/tools/check_s10_stage_review.py`、`KMFA/tests/test_s10_stage_review.py` 和 `KMFA/stage_artifacts/S10_STAGE_REVIEW/` 复审证据包。
- 复跑并锁定 S10-P1/P2/P3 validator 证据：2 个报告模板、11 个章节、2 条 D 级报告等级记录、2 个 HTML 导出和 2 个 CSV appendix 均保持 public-safe。
- 复审确认完整可信报告、正式报告、经营决策依据、S11、UI、lineage full check、外部 connector 和 GitHub upload 仍未执行。
- 全量 KMFA 单测当前为 116 tests；公开仓库未提交 raw business data、zip、Excel workbook、PDF、sqlite/db、private CSV、字段明文或 credentials。
- 下一步只能执行 Stage 10 final GitHub upload gate：对齐最新 `origin/main`，复跑 validators 和安全检查，并留下 push proof。

## 0.1.0-s10p3-report-export - 2026-06-30

- 完成 `S10-P3｜导出` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/report_export_runtime.py`、`KMFA/tools/check_s10_p3_report_export.py` 和 `KMFA/tests/test_report_export_runtime.py`。
- 生成 2 个 public-safe HTML 报告、2 个 public-safe CSV 附表、2 个 Excel 兼容 CSV 下载记录，以及 PDF private-runtime-only 策略。
- 保持 2 条报告导出记录均为 `D` 级，`formal_report_allowed=false`、`business_decision_basis_allowed=false`、`stage10_review_allowed=false`、`github_upload_allowed=false`。
- 公开仓库未提交 `.xlsx`、`.pdf`、zip、sqlite/db、raw business data、字段明文或私有 CSV。
- S10 三个 phase 已完成本地实现；下一步只能执行 Stage 10 整体复审，修复复审问题后才允许整体上传 GitHub。

## 0.1.0-s10p2-report-grade-runtime - 2026-06-30

- 完成 `S10-P2｜报告可信等级` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/report_grade_runtime.py`、`KMFA/tools/check_s10_p2_report_grade_runtime.py` 和 `KMFA/tests/test_report_grade_runtime.py`。
- 生成 2 条 public-safe 报告可信等级记录，均因 zero-delta 失败、12 条 pending reconciliation、缺少完整 lineage 和缺少人工确认而锁定为 `D`。
- 每条报告等级记录绑定 report record version、template version/content hash、formula version、mapping version、field mapping version、grade policy version 和 release gate version。
- 保持 `complete_trusted_report_display_allowed=false`、`formal_report_allowed=false`、`business_decision_basis_allowed=false`、`s10_p3_scope=false`、`export_artifact_count=0`。
- 后续只能执行 `S10-P3｜导出`，作为独立 phase；不得执行 Stage 10 整体复审或 GitHub upload。

## 0.1.0-s10p1-report-templates - 2026-06-30

- 完成 `S10-P1｜报告模板` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/report_templates.py`、`KMFA/tools/check_s10_p1_report_templates.py` 和 `KMFA/tests/test_report_templates.py`。
- 生成 public-safe 报告模板 manifest、2 个模板和 11 个管理可读章节：项目成本专题报告覆盖经营摘要、项目毛利、成本结构、风险事项；经营总览报告覆盖经营总览、收入、开票、回款、现金、项目、税务。
- 模板继承 v1.2 HTML/报告验收样板引用，但本阶段不生成 HTML、CSV、Excel 或 PDF 导出文件。
- 保持 `formal_report_allowed=false`、`trusted_grade_assignment_allowed=false`、`s10_p2_scope_included=false`、`s10_p3_scope_included=false`、`ui_scope_included=false`；S09-P3 12 条 pending reconciliation 仍阻断正式报告。
- 不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；本次不执行 Stage 10 整体复审、GitHub upload、lineage full check、UI 或外部接口。

## 0.1.0-s09-github-upload - 2026-06-30

- 完成 Stage 9 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `70ee64c3e0995c68dceffa24ded1950e692c42cf` rebase 完整 Stage 9 栈，并复跑 S09-P1/P2/P3 validators、`check_s09_stage_review.py`、全量 KMFA tests、治理 validator、raw/secret scan 和 parse checks。
- 新增 `KMFA/stage_artifacts/S09_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S09_STAGE_REVIEW/machine/stage9_upload_manifest.json`。
- 保持 12 条 reconciliation records 为 `pending_owner_or_authorized_review`；不关闭差异、不重跑派生指标、不生成正式报告、不执行 S10、lineage full check、UI 或外部接口。
- 后续只能执行 `S10-P1｜报告模板`，作为独立 phase。

## 0.1.0-s09-stage-review - 2026-06-30

- 完成 Stage 9 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S09_STAGE_REVIEW/` 复审证据包，覆盖 S09-P1/P2/P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse checks 和 evidence consistency check。
- 复审确认 S09-P1 项目成本事实层、S09-P2 毛利与现金毛利、S09-P3 口径转换与差异核对均保持 public-safe 边界，不提交 raw business data、字段明文、zip、Excel、PDF 或私有 CSV。
- 修复 review finding：`KMFA/tools/a0_golden_fixture.py` 中 high-signal secret scan 的 `normalized_token` 误报已通过行为不变命名修复为 `normalized_hash_source`，并复跑相关 S05 fixture 测试和 validator。
- 保持 12 条 reconciliation records 为 `pending_owner_or_authorized_review`；不关闭差异、不重跑派生指标、不生成正式报告、不执行 S10、lineage full check、UI、外部接口或 GitHub upload。
- 后续只能执行 Stage 9 final GitHub upload gate：对齐最新 `origin/main`，复跑 validators 和安全检查，并留下 push proof。

## 0.1.0-s09p3-scope-reconciliation - 2026-06-30

- 完成 `S09-P3｜口径转换与差异核对` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/project_scope_reconciliation.py`、`KMFA/tools/check_s09_p3_scope_reconciliation.py` 和 `KMFA/tests/test_project_scope_reconciliation.py`。
- 生成 public-safe scope reconciliation manifest、12 条 reconciliation records 和 6 条 domain controls，覆盖合同/项目收入、项目成本/财务费用、银行回款/应收账龄、开票/合同结算/税务、研发费用/项目人员证据、权威 PDF/Excel 与系统复算。
- 每条记录只保存 refs/hash/status/evidence metadata、原因候选、依据 refs、影响范围、责任角色和 reviewer；不保存真实金额、字段明文或原始文件。
- 当前 12 条 records 均为 `pending_owner_or_authorized_review`；派生指标重跑、正式报告、Stage 9 review 和 GitHub upload 仍为禁止状态。
- 不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；本次不执行 Stage 9 整体复审、lineage 完整检查、正式报告、UI、外部接口或 GitHub upload。

## 0.1.0-s09p2-margin-cash-margin - 2026-06-30

- 完成 `S09-P2｜毛利与现金毛利` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/project_margin_cash_margin.py`、`KMFA/tools/check_s09_p2_margin_cash_margin.py` 和 `KMFA/tests/test_project_margin_cash_margin.py`。
- 生成 public-safe margin/cash margin manifest、4 条 project margin records 和 12 条 scope difference summary records，覆盖 authority gross profit、system recomputed gross profit、cash gross profit 和 gross margin rate。
- 保留 A0 authority display value refs/hash 与 S09-P2 system recomputed refs/hash，不互相覆盖；差异只进入口径差异摘要，S09-P3 尚未执行。
- 公开仓库不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；S09-P3、Stage 9 review、lineage、正式报告、UI、外部接口和 GitHub upload 均未执行。

## 0.1.0-s09p1-project-cost-fact-layer - 2026-06-30

- 完成 `S09-P1｜项目成本事实层` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/project_cost_fact_layer.py`、`KMFA/tools/check_s09_p1_project_cost_fact_layer.py` 和 `KMFA/tests/test_project_cost_fact_layer.py`。
- 生成 public-safe fact layer manifest、4 条 project cost fact records 和 9 条 unallocated project cost pool records，覆盖 revenue、contract_amount、invoice_amount、collection_amount、cost_total、cost_category。
- 成本分类覆盖 labor、material、machinery、subcontract、transport、travel、tax、management_fee、interest；S06/S08 未关闭质量阻断保留为 formal calculation blocker。
- 公开仓库不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；S09-P2、S09-P3、Stage 9 review、lineage、正式报告、UI、外部接口和 GitHub upload 均未执行。

## 0.1.0-s08-github-upload - 2026-06-30

- 完成 Stage 8 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `ce2881204c49a56da463893db5314ff180c7812d` rebase 完整 Stage 8 栈，并复跑 S08-P1/P2/P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、parse checks 和 evidence consistency check。
- 新增 `KMFA/stage_artifacts/S08_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S08_STAGE_REVIEW/machine/stage8_upload_manifest.json`。
- 修复 upload gate finding：rebase 后 Stage 8 review evidence 的 `reviewed_head` 已更新为当前 rebased S08-P3 commit `15e4782e063a4c53b0549ecc674a9c321ec69913`。
- 保持 S09 事实层、lineage 完整检查、正式报告、UI 和外部接口为未完成。

## 0.1.0-s08-stage-review - 2026-06-30

- 完成 Stage 8 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S08_STAGE_REVIEW/` 复审证据包，覆盖 S08-P1/P2/P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、YAML/JSON/JSONL/CSV parse checks 和 evidence consistency check。
- 复审确认 S08-P1 项目组合键、S08-P2 业务实体模型和 S08-P3 匹配质量测试均保持 public-safe 边界，不提交 raw business data、字段明文、zip、Excel、PDF 或私有 CSV。
- 修复 Stage 8 review 证据和治理状态缺口，并将 initial evidence consistency 临时检查改为按 S08-P1/P2/P3 manifest schema 执行。
- 保持 S09 事实层、lineage 完整检查、正式报告、UI、外部接口和 GitHub upload 为未完成。

## 0.1.0-s08p3-entity-matching-quality - 2026-06-30

- 完成 `S08-P3｜匹配质量测试` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/entity_matching_quality.py`、`KMFA/tools/check_s08_p3_entity_matching_quality.py` 和 `KMFA/tests/test_entity_matching_quality.py`。
- 覆盖同名项目、多主体、多账户、多期间 4 类 public-safe 匹配质量场景，生成 4 条 quality cases、3 条人工复核队列记录和 1 份 `entity_matching_report`。
- 中高风险匹配候选进入人工复核，`auto_merge_allowed=false`，公开证据只保存 `profile_ref`、`entity_ref`、`source_hash`、status、risk、evidence metadata。
- 公开仓库不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；Stage 8 review、事实层、lineage、正式报告、UI、外部接口和 GitHub upload 仍未执行。

## 0.1.0-s08p2-business-entity-model - 2026-06-30

- 完成 `S08-P2｜业务实体模型` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/business_entity_model.py`、`KMFA/tools/check_s08_p2_business_entity_model.py` 和 `KMFA/tests/test_business_entity_model.py`。
- 定义 customer、contract、project、cost_record、invoice、collection、receivable、tax_evidence 8 类 public-safe 业务实体。
- 建立 14 条实体关系和 32 条生命周期状态，将 schema 文档写入 `KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md`，并输出 metadata/schema_maps 机器文件。
- 公开仓库不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；S08-P3、Stage 8 review、事实层、lineage、正式报告、UI、外部接口和 GitHub upload 仍未完成。

## 0.1.0-s08p1-project-composite-key - 2026-06-30

- 完成 `S08-P1｜项目组合键` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/project_composite_key.py`、`KMFA/tools/check_s08_p1_project_composite_key.py` 和 `KMFA/tests/test_project_composite_key.py`。
- 建立 public-safe 项目身份组合键：合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个组件全部只保存 hash/private refs。
- 使用整数 basis points 锁定权重和阈值，支持单字段缺失不全阻断；低于强匹配阈值进入人工复核队列，`auto_merge_allowed=false`。
- 新增 `KMFA/metadata/schema_maps/project_composite_key_manifest.json`、`KMFA/metadata/schema_maps/project_identity_profiles.jsonl`、`KMFA/metadata/schema_maps/project_composite_key_matches.jsonl`、`KMFA/metadata/quality/project_identity_review_queue.jsonl` 和 `KMFA/stage_artifacts/S08_P1_project_composite_key/`。
- 公开仓库不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务值；S08-P2、S08-P3、Stage 8 review、事实层、lineage、正式报告、UI、外部接口和 GitHub upload 仍未完成。

## 0.1.0-s07-github-upload - 2026-06-30

- 完成 Stage 7 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `a734729629efc07d49d95732b400144d39dc343c` rebase 完整 Stage 7 栈，并复跑 S07-P1/P2/P3 validators、全量 KMFA tests、治理 validator、raw/secret scan、parse checks 和 evidence consistency check。
- 新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S07_STAGE_REVIEW/machine/stage7_upload_manifest.json`。
- 保持 S08 项目组合键、事实层、lineage 完整检查、正式报告、UI 和外部接口为未完成。

## 0.1.0-s07-stage-review - 2026-06-30

- 完成 Stage 7 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S07_STAGE_REVIEW/` 复审证据包，覆盖 S07-P1/P2/P3 validators、治理 validator、raw/secret scan、JSON/JSONL/CSV/YAML parse checks 和 evidence consistency check。
- 复审确认 S07-P1 财务文件适配、S07-P2 WPS 文件适配和 S07-P3 红圈导出后置策略均保持 public-safe 边界。
- 修复 Stage 7 review 证据和治理状态缺口，同步 owner-readable、stage_status、events 和 project governance。
- 保持 S08、lineage 完整检查、事实层、正式报告、UI、外部接口和 GitHub upload 为未完成。

## 0.1.0-s07p3-redcircle-postponement - 2026-06-30

- 完成 `S07-P3｜红圈导出后置策略` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/redcircle_postponement_policy.py`、`KMFA/tools/check_s07_p3_redcircle_postponement.py` 和 `KMFA/tests/test_redcircle_postponement_policy.py`。
- 预留红圈经营、合同、回款、财务 4 类导出模板，明确 D15 文件型 MVP 不接自动接口。
- 新增后续红圈接入必须只读、留 hash、可回滚、需人工授权的策略与 rollback plan。
- 公开仓库不提交 raw Excel/PDF/zip/private CSV、红圈原始导出文件、接口凭证、字段明文、来源表头明文或真实业务值；Stage 7 review、事实层、lineage、正式报告、UI 和外部接口仍未完成。

## 0.1.0-s07p2-wps-file-adapter - 2026-06-30

- 完成 `S07-P2｜WPS 文件适配` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/wps_file_adapter.py`、`KMFA/tools/check_s07_p2_wps_file_adapter.py` 和 `KMFA/tests/test_wps_file_adapter.py`。
- 覆盖 WPS 回款、应收账龄、生产项目状态、保证金 4 类导出，生成 20 条 hash-only 字段映射、4 条转换提示、4 条只读字段报告和 1 个映射规则版本。
- 新增 `KMFA/metadata/imports/wps_export_source_registry.json`、`KMFA/metadata/schema_maps/wps_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/wps_field_mappings.jsonl`、`KMFA/metadata/schema_maps/wps_mapping_rule_versions.json`、`KMFA/metadata/schema_maps/wps_file_mapping_policy.yaml` 和 `KMFA/stage_artifacts/S07_P2_wps_file_adapter/`。
- 公开仓库不提交 raw Excel/PDF/zip/private CSV、WPS 原始文件、字段明文、来源表头明文或真实业务值；红圈、事实层、lineage、正式报告、UI 和外部接口仍未完成。

## 0.1.0-s07p1-finance-file-adapter - 2026-06-30

- 完成 `S07-P1｜财务文件适配` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/finance_file_adapter.py`、`KMFA/tools/check_s07_p1_finance_file_adapter.py` 和 `KMFA/tests/test_finance_file_adapter.py`。
- 生成 9 类财务支撑源登记、45 条 hash-only 字段候选和 9 条只读字段报告，覆盖经营分析、日记账、客户账龄、现金、纳税、开票、账户、贷款、研发费用。
- 新增 `KMFA/metadata/imports/finance_support_source_registry.json`、`KMFA/metadata/schema_maps/finance_file_adapter_manifest.json`、`KMFA/metadata/schema_maps/finance_field_candidates.jsonl`、`KMFA/metadata/schema_maps/finance_file_mapping_policy.yaml` 和 `KMFA/stage_artifacts/S07_P1_finance_file_adapter/`。
- 公开仓库不提交 raw Excel/PDF/zip/private CSV、字段明文、来源表头明文或真实业务值；WPS、红圈、事实层、lineage、正式报告、UI 和外部接口仍未完成。

## 0.1.0-s06-github-upload - 2026-06-30

- 完成 Stage 6 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `fd14057e7427d7f275fdb62a33619936618d0d35` rebase 完整 Stage 6 栈，并复跑 S06-P1/P2/P3 validators、治理 validator、raw/secret scan、JSON/JSONL parse check 和 evidence consistency check。
- 修复 upload gate finding：rebase 后 Stage 6 review evidence 的 `reviewed_head` 已更新为当前 rebased S06-P3 commit `c66c8b44c17ae760a5a6da4b98ab5892d90d73d0`。
- 修复 upload gate finding：`KMFA/metadata/project/project.yaml` 中重复且过期的 Stage 6 upload policy 已归一。
- 新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S06_STAGE_REVIEW/machine/stage6_upload_manifest.json`。
- 保持 S07 文件适配、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s06-stage-review - 2026-06-30

- 完成 Stage 6 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S06_STAGE_REVIEW/` 复审证据包，覆盖 S06-P1/P2/P3 validators、治理 validator、raw/secret scan、JSON/JSONL parse checks 和 evidence consistency check。
- 复审确认 S06-P1 对 1 分差异保持 expected failure，S06-P2 未关闭差异继续阻断 A 级报告，S06-P3 metadata/quality 输出保持 public-safe hash/ref/status/evidence。
- 修复 Stage 6 review 证据和治理状态缺口，同步 owner-readable、stage_status、events 和 project governance。
- 保持 lineage 完整检查、事实层、正式报告、UI、外部接口和 GitHub upload 为未完成。

## 0.1.0-s06-p3-validation-evidence-output - 2026-06-30

- 完成 `S06-P3｜校验证据输出` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/validation_evidence_output.py`、`KMFA/tools/check_s06_p3_validation_evidence.py` 和 `KMFA/tests/test_validation_evidence_output.py`。
- 输出 S06-P3 `zero_delta_result.json`、sanitized `mismatch_report.csv` 和 per-project validation status JSONL。
- 将 public-safe zero-delta summary、data quality status、source difference queue status 和 mismatch index 写入 `KMFA/metadata/quality`。
- metadata/quality 只保存 hash/ref/status/evidence，不新增字段明文、权威原值、系统原值、PDF 原值或 Excel 原值。
- 保持事实层、lineage 完整检查、正式报告、UI、外部接口、Stage 6 复审和 GitHub upload 为未完成。

## 0.1.0-s06-p2-cross-source-difference-queue - 2026-06-30

- 完成 `S06-P2｜跨源差异队列` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/cross_source_difference_queue.py`、`KMFA/tools/check_s06_p2_difference_queue.py` 和 `KMFA/tests/test_cross_source_difference_queue.py`。
- PDF 与 Excel 同项目同字段金额冲突进入人工差异队列；禁止自动修正、平均、四舍五入掩盖和自动选边。
- 未关闭差异阻断 A 级报告：`report_grade_a_allowed=false`、`maximum_report_grade=B`、`hard_block_reason=unresolved_critical_difference`。
- 新增 `KMFA/stage_artifacts/S06_P2_cross_source_difference_queue/` 证据包，使用 synthetic fixture，不读取或提交真实业务文件。
- 保持 S06-P3 metadata/quality 运行时证据输出、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s06-p1-zero-delta-validator - 2026-06-30

- 完成 `S06-P1｜零差异校验器` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/zero_delta_validator.py` 和 `KMFA/tests/test_zero_delta_validator.py`，逐字段比较 public-safe 已结构化整数分。
- 任意 1 分差异返回失败，并输出包含来源、字段、权威值、系统值和差额的 mismatch report。
- 新增 `KMFA/stage_artifacts/S06_P1_zero_delta_validator/` 证据包，使用 synthetic fixture，不读取或提交真实业务文件。
- 保持 S06-P2 差异队列、S06-P3 metadata/quality 运行时证据输出、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s05-github-upload - 2026-06-30

- 完成 Stage 5 final GitHub upload gate，目标为 `LinzeColin/CodexProject main`。
- 基于最新 `origin/main` commit `495bcd977a587b7fd8b1923bfd74f5138f12263e` rebase 完整 Stage 5 栈，并复跑 S05-P1/P2/P3 validators、治理 validator、raw/secret scan 和 JSONL parse check。
- 修复 upload gate finding：rebase 后 Stage 5 review evidence 的 `reviewed_head` 已更新为当前 rebased S05-P3 commit `c3314e47ce11cfb8bf56e44d4a38a77904584495`。
- 新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S05_STAGE_REVIEW/machine/stage5_upload_manifest.json`。
- 保持 S06 zero-delta、lineage、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s05-stage-review - 2026-06-30

- 完成 Stage 5 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S05_STAGE_REVIEW/` 复审证据包，覆盖 S05-P1/P2/P3 validators、治理 validator、raw/secret scan 和 JSON/JSONL parse checks。
- 复审确认 40 条 PDF 字段保持 public-safe Q5 calculation baseline，5 条 Excel 字段保持 cross-source support only，不进入正式报告。
- 修复 Stage 5 review 证据和治理状态缺口，同步 owner-readable、stage_status、events 和 project governance。
- 保持 zero-delta、lineage、事实层、报告、UI、外部接口和 GitHub upload 为未完成。

## 0.1.0-s05p3-authority-baseline-lock - 2026-06-30

- 完成 `S05-P3｜权威基准锁定` 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/a0_authority_baseline_lock.py` 和 `KMFA/tools/check_a0_authority_baseline_lock.py`，生成并验证 public-safe A0 authority baseline manifest/records。
- 新增 `KMFA/tests/test_s05_p3_authority_baseline_lock.py`，覆盖 40 条 Q5 hash/source-anchor lock、5 条 Excel exclusion、禁止明文字段键和文件输出。
- 新增 `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`、`KMFA/metadata/baseline/a0_authority_baseline_records.jsonl` 和 `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/` 证据。
- 保持 Stage 5 整体复审、zero-delta、lineage、事实层、报告、UI 和 GitHub upload 为未完成。

## 0.1.0-s05p2-private-backfill-partial - 2026-06-30

- 对 `S05-P2｜字段级黄金基准` 执行本地私有 hash-only 部分回填，不上传 GitHub。
- 使用仓库外私有 CSV 回填 8 个 PDF A0 候选的 40 条字段候选 hash/source anchor；1 个 Excel 候选的 5 条字段候选继续 pending。
- 记录审计结论：本机提供的 `销售绩效考核.zip` 整包 hash/size 与登记 source package 不匹配，但 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配；Ring4 前序包 hash 匹配登记值。
- 新增 S05-P2 private backfill public-safe 证据；公开仓库仍不提交 raw PDF/Excel/zip、私有 CSV、真实字段 raw value 或 normalized value。
- 保持 S05-P2 未完成、S05-P3 权威锁定未开始、Stage 5 复审和 GitHub upload 不允许。

## 0.1.0-s05p2-contract - 2026-06-30

- 生成 `S05-P2｜字段级黄金基准` 的 public-safe 字段合同和 A0 golden fixture 候选结构，保持本阶段本地验证，不上传 GitHub。
- 新增 `KMFA/tools/a0_golden_fixture.py` 和 `KMFA/tools/check_a0_golden_fixture.py`，为合同额、支出合计、毛利、毛利率、成本分类生成 private refs、source anchor 状态和 hash-only 输出能力。
- 新增 `KMFA/tests/test_a0_golden_fixture.py`，覆盖无私有源 pending 输出、合成私有 CSV hash-only 输出、公开 metadata 禁止 raw/normalized 明文键。
- 新增 `KMFA/metadata/baseline/a0_golden_fixture_manifest.json` 和 `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`，当前 45 条字段候选均为 private values pending。
- 保持 S05-P2 真实字段值、S05-P3 权威锁定、zero-delta、事实层、报告、UI 和 GitHub upload 为未完成。

## 0.1.0-s05p1 - 2026-06-30

- 完成 `S05-P1｜A0 文件登记` 的 public-safe 登记和本地验证，不上传 GitHub。
- 新增 `KMFA/tools/a0_file_register.py` 和 `KMFA/tools/check_a0_file_registration.py`，登记 `销售绩效考核.zip` source package SHA256、8 个 PDF、1 个 Excel、legacy inventory 指纹和 Q3/Q4 状态。
- 新增 `KMFA/tests/test_a0_file_register.py`、`KMFA/metadata/baseline/a0_file_manifest.json`、`KMFA/metadata/baseline/a0_project_candidates.jsonl` 和 S05-P1 证据包。
- 私有 `销售绩效考核.zip` 未找到，成员级 SHA256 显式记录为 pending，不用 legacy CRC/指纹冒充 SHA256。
- 保持字段级黄金基准、S05-P3 权威锁定、zero-delta、事实层、报告、UI 和 GitHub upload 为未完成。

## Stage 4 Review - 2026-06-29

- 完成 Stage 4 整体复审，结果为 `PASS_UPLOAD_READY_LOCAL_ONLY`，尚未 push GitHub。
- 新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/` 复审证据包。
- 修复 `功能清单.md` 中 `FEAT-KMFA-016` 金额标准化与 no-float 检查详情缺口。
- 复跑 S04-P1/S04-P2/S04-P3 工具测试、治理 validator、no-float 检查和敏感文件扫描。
- 保持 A0 基准、zero-delta、事实层、报告、UI 和外部接口为未完成。

## Stage 4 GitHub Upload - 2026-06-29

- 完成 Stage 4 final GitHub upload 证据记录，目标为 `LinzeColin/CodexProject main`。
- 基于 `origin/main` commit `e6e69d387fc842102931090ffbffe18e54b63c0c` 纳入完整 Stage 4 提交栈。
- reviewed content commit 为 `25c85dcee55679d0789f8462a7c7875188d0aa9f`。
- 新增 `KMFA/stage_artifacts/S04_STAGE_REVIEW/human/github_upload_record.md` 和 `KMFA/stage_artifacts/S04_STAGE_REVIEW/machine/stage4_upload_manifest.json`。

## 0.1.0-s04p3 - 2026-06-29

- 完成 `S04-P3｜基础工具测试`，保持本 Phase 本地验证，不上传 GitHub。
- 新增 `KMFA/tests/test_basic_tool_boundaries.py`，覆盖金额小数、负数、万元、异常字符，以及日期/期间中文日期、年月、空值边界。
- 新增 `KMFA/tools/generate_tool_test_report.py`，生成 S04-P3 工具函数测试报告，支持 JSON 和 Markdown 输出。
- 修复 `KMFA/tools/field_standardization.py` 的中文完整日期转期间边界。
- 新增 `KMFA/stage_artifacts/S04_P3_basic_tool_tests/` 证据包。
- Stage 4 三个 Phase 已全部本地验证；Stage 4 整体复审、复审问题修复和 GitHub 上传尚未完成。

## 0.1.0-s04p2 - 2026-06-29

- 完成 `S04-P2｜字段标准化`，保持本 Phase 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/field_standardization.py`，支持日期、期间、公司主体、项目名称、客户/对手方、合同编号标准化。
- 新增 `KMFA/tests/test_field_standardization.py`，覆盖中文字段映射、缺字段质量状态、异常字段质量状态和 CLI。
- 新增 `KMFA/metadata/schema_maps/field_alias_dictionary.csv`、`field_standardization_policy.yaml` 和 `KMFA/metadata/quality/field_quality_status.jsonl`。
- 更新 mapping version 登记、字段字典、目录 manifest 和 S04-P2 证据包。
- 保持 S04-P3 基础工具测试报告、A0 基准、zero-delta、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s04p1 - 2026-06-29

- 完成 `S04-P1｜金额工具`，保持本 Phase 本地验证，不上传 GitHub。
- 新增 `KMFA/tools/amount_tools.py`，提供 `normalize_amount_to_cents`，支持元、万元、千元、千分位、负数和括号负数，输出整数分。
- 新增 `KMFA/tools/check_no_float_money.py`，检查 KMFA Python 文件中的 float literal、`float()` 调用和 float 标注。
- 新增 `KMFA/tests/test_amount_tools.py`，覆盖金额标准化、float 禁止、异常输入不默认为 0、CLI 和 no-float 检查。
- 新增 `KMFA/stage_artifacts/S04_P1_amount_tools/` 证据包。
- 保持 S04-P2 字段标准化、S04-P3 工具测试报告、A0 基准、zero-delta、事实层、报告、UI 和外部接口为未完成。

## 0.1.0-s03p3 - 2026-06-29

- 完成 `S03-P3｜源优先级`。
- 新增 `KMFA/tools/source_priority.py`，支持源类别优先级排序、同源不一致失效重跑事件和跨源差异队列 metadata。
- 新增 `KMFA/tests/test_source_priority.py`，覆盖原始上传/授权导出优先于处理后数据、同源失效重跑、跨源冲突不自动选边和 direct CLI。
- 新增 `KMFA/metadata/sources/source_priority_policy.yaml`、`source_priority_events.jsonl` 和 `KMFA/metadata/quality/source_difference_queue.jsonl`。
- Stage 3 三个 Phase 已本地完成；Stage 3 复审已通过，并已整体上传 GitHub main。
- 保持业务字段解析、金额、事实层、报告和外部接口为未完成；中间 Phase 不上传 GitHub。

## 0.1.0-s03p2 - 2026-06-29

- 完成 `S03-P2｜数据源检查矩阵`。
- 新增 `KMFA/tools/source_check_matrix.py`，支持来源系统、业务板块、文件包、主体、账户、频率矩阵行生成。
- 新增 `KMFA/tests/test_source_check_matrix.py`，覆盖矩阵维度、五个中文状态枚举和 metadata-only 状态事件。
- 新增 `KMFA/metadata/sources/source_check_matrix_schema.json`、`source_check_matrix_policy.yaml`、`source_check_matrix.jsonl`、`source_status_events.jsonl`。
- 保持 S03-P3 源优先级、业务字段解析、金额、事实层、报告和外部接口为未完成；中间 Phase 不上传 GitHub。

## 0.1.0-s03p1 - 2026-06-29

- 完成 `S03-P1｜文件型导入`。
- 新增 `KMFA/tools/file_import_register.py`，支持 `zip/xlsx/xls/csv/pdf` 文件登记、hash/size/import_run/source package metadata、私有 storage ref 和 zip 安全解包。
- 新增 `KMFA/tests/test_file_import_register.py`，覆盖登记隐私边界、WPS/OLE 操作提示和 zip traversal 防护。
- 新增 `KMFA/metadata/imports/file_import_policy.yaml`，扩展 raw manifest schema/policy、import runs、raw file manifest 和 source registry 的 S03-P1 能力记录。
- 新增 `KMFA/stage_artifacts/S03_P1_file_import/` 证据包。
- 保持 S03-P2 数据源检查矩阵、S03-P3 源优先级、业务字段解析、金额、事实层、报告和外部接口为未完成；中间 Phase 不上传 GitHub。

## 0.1.0-s02p3-v12baseline - 2026-06-29

- 承接 `KMFA_ChatGPT_Stage3_Codex_Delivery_Pack_v1_2_FULL_HTML_NO_OMISSION.zip` 为后续正式开发基线。
- 新增 `KMFA/taskpack/v1_2/`，保存可提交的 v1.2 TaskPack、Roadmap、HTML/UIUX/报告样板、前序散件、工具和机器清单。
- 完整纳入 HTML 验收面：45 个 HTML 文件，7 个核心 HTML 验收样板。
- 新增 `KMFA/tools/check_required_html.py`，并强化 `KMFA/tools/no_omission_check.py` 检查 v1.2 基线与私有源数据禁提交边界。
- 只保存 `90_用户原始上传数据` 的 SHA256 登记和禁止提交规则，未提交原始 zip、mov、Excel、PDF 或数据库类文件。
- 按 v1.2 重新走完 Stage 1，新增证据目录 `KMFA/stage_artifacts/S01_REBASE_V12_FULL_TASKPACK/`。

## 0.1.0-s02p3 - 2026-06-29

- 完成 `S02-P3｜数据质量等级`。
- 新增 `Q0-Q5` 数据质量等级协议，定义预览、内部复核和正式内部报告的质量边界。
- 新增 `A/B/C/D` 报告可信等级协议，要求 A 级报告必须满足 `Q5`、zero-delta、关键差异关闭和人工确认。
- 新增报告发布门禁，缺少门禁证据时默认阻断发布或降级。
- 新增 `KMFA/tools/check_report_grade_gate.py`，验证质量等级、报告等级和发布权限映射。
- S02 三个 Phase 已完成；Stage 2 整体复审已通过，并已上传 GitHub main。

## 0.1.0-s02p2 - 2026-06-29

- 完成 `S02-P2｜不可污染原则`。
- 新增 raw manifest append-only schema 和 policy，禁止修改原始文件、原始抽取值和不可变 manifest 字段。
- 新增派生数据版本协议，支持失效、重跑、对比，禁止覆盖旧版本。
- 新增前端/人工控制事件写入边界，禁止直接写 raw 层。
- 新增 `KMFA/tools/immutability_policy_check.py`，验证不可污染原则。
- 保持中间 Phase 不上传 GitHub；S02-P3 与 Stage 2 复审尚未完成。

## 0.1.0-s02p1 - 2026-06-29

- 完成 `S02-P1｜metadata目录协议`。
- 创建 metadata 七类目录：sources、imports、schema_maps、quality、lineage、reports、approvals。
- 定义 `import_run_id`、`source_id`、`file_hash`、`formula_version`、`mapping_version` 标识符协议。
- 新增 `KMFA/tools/metadata_protocol_check.py`，验证目录、协议文件、标识符和公开仓库隐私边界。
- 保持中间 Phase 不上传 GitHub；S02-P2/S02-P3 与 Stage 2 复审尚未完成。

## 0.1.0-s01p3 - 2026-06-29

- 完成 `S01-P3｜防遗漏基线`。
- 导入完整需求追溯矩阵：20 条需求，P0=9，P1=8。
- 新增正式 `KMFA/tools/no_omission_check.py`，可本地/CI 运行。
- 建立完整 Stage/Phase/Task 状态登记：18 Stage、54 Phase、162 Task、234 JSONL 记录。
- 同步 `docs/governance/TRACEABILITY_MATRIX.csv` 到 20 条治理追溯记录。
- Stage 1 整体复审通过；上传限定为基于 `origin/main` 的隔离 worktree，避免混入非 KMFA 变更。

## 0.1.0-s01p2 - 2026-06-29

- 创建 KMFA 项目骨架与中文入口。
- 建立人类可读面: `README.md`, `功能清单.md`, `开发记录.md`, `模型参数文件.md`, `HANDOFF.md`。
- 建立机器可读面: `docs/governance/*`, `metadata/*`, `stage_artifacts/S01_P1_read_only_plan`。
- 注册 root `governance/projects.yaml` 与 root `README.md` 项目表。
- 明确 Stage 完成复审修复后再上传 GitHub，中间 Phase 不上传。
- 明确时间只是参考，质量门禁通过可提前交付，未通过不得交付。
- 未实现业务导入、金额工具、zero-delta 正式脚本、UI、报告或外部接口。
