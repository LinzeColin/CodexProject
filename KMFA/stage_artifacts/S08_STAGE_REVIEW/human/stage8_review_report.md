# KMFA Stage 8 Review Report

- review_id: `KMFA-S08-STAGE-REVIEW-20260630`
- review_time: `2026-06-30T23:00:00+10:00`
- stage: `S08 - 业务实体与项目身份匹配`
- scope: `S08-P1`, `S08-P2`, `S08-P3`, Stage 8 owner-readable entries, governance status, public-repo safety boundary
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- reviewed_head: `e60b8924b1f3`
- worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`
- branch: `codex/kmfa`
- github_upload_status: `not_pushed`

## 复审结论

Stage 8 三个 Phase 已完成本地实现、验证和整体复审。S08-P1 建立 public-safe 项目组合键，使用合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个 hash-only 身份组件，生成 4 条 profile、3 条匹配记录和 2 条人工复核队列记录。S08-P2 建立 public-safe 业务实体模型，定义 customer、contract、project、cost_record、invoice、collection、receivable、tax_evidence 8 类实体、14 条关系和 32 条生命周期状态。S08-P3 建立匹配质量测试，覆盖同名项目、多主体、多账户、多期间 4 类质量场景，生成 4 条 quality cases、3 条人工复核队列记录和 1 份 entity_matching_report。

复审中发现的主要缺口是 Stage 8 review 证据与治理状态尚未形成闭环；本轮已补齐 `S08_STAGE_REVIEW` 证据包、owner-readable 状态、machine manifest、stage_status 和 governance events。另一个复审 finding 是初始 evidence consistency 临时检查错误假设了 S08 manifest 字段名；已按 S08-P1/P2/P3 各自 schema 改为 schema-aware 检查并通过。当前树具备 Stage 8 GitHub 上传前的本地复审条件，但本轮未执行 push；最终上传仍必须在独立 upload 步骤中对齐最新 `origin/main`、复跑 validators，并留下 upload manifest 和 push proof。

## 覆盖范围

| 范围 | 复审结果 | 证据 |
|---|---|---|
| `S08-P1` 项目组合键 | PASS | `KMFA/tools/project_composite_key.py`, `KMFA/tools/check_s08_p1_project_composite_key.py`, `KMFA/stage_artifacts/S08_P1_project_composite_key/` |
| `S08-P2` 业务实体模型 | PASS | `KMFA/tools/business_entity_model.py`, `KMFA/tools/check_s08_p2_business_entity_model.py`, `KMFA/stage_artifacts/S08_P2_business_entity_model/` |
| `S08-P3` 匹配质量测试 | PASS | `KMFA/tools/entity_matching_quality.py`, `KMFA/tools/check_s08_p3_entity_matching_quality.py`, `KMFA/stage_artifacts/S08_P3_entity_matching_quality/` |
| Stage 8 入口状态 | PASS_AFTER_FIX | `KMFA/功能清单.md`, `KMFA/开发记录.md`, `KMFA/模型参数文件.md`, `KMFA/HANDOFF.md`, `KMFA/docs/governance/` |
| 敏感数据边界 | PASS | raw artifact extension scan, high-signal secret scan |
| v1.2 no-omission / governance | PASS | `KMFA/tools/no_omission_check.py`, `scripts/lean_governance.py`, `scripts/validate_project_governance.py` |

## Finding 与处理

| Finding ID | 严重度 | 状态 | 说明 | 处理 |
|---|---|---|---|---|
| `KMFA-S08-REV-F01` | P2 | fixed | Stage 8 三个 Phase 已完成，但整体复审证据、review manifest 和治理状态仍显示未复审。 | 已新增 `KMFA/stage_artifacts/S08_STAGE_REVIEW/`，同步 owner-readable、stage_status 和 governance events 为 local-only review passed。 |
| `KMFA-S08-REV-F02` | P2 | passed | S08-P1 项目组合键必须只输出 hash/private refs，不得提交真实身份字段、raw values 或越界 S08-P2/P3 scope。 | `check_s08_p1_project_composite_key.py` 通过：components=8、profiles=4、matches=3、manual_review_queue=2、formal_report_allowed=false、github_upload_allowed=false。 |
| `KMFA-S08-REV-F03` | P2 | passed | S08-P2 业务实体模型必须保持 public-safe schema/hash/ref/status/evidence metadata，不得写事实层或报告。 | `check_s08_p2_business_entity_model.py` 通过：entities=8、relationships=14、lifecycle_statuses=32、fact_layer_scope=false、formal_report_allowed=false。 |
| `KMFA-S08-REV-F04` | P2 | passed | S08-P3 匹配质量测试必须保持人工复核边界，中高风险候选不得自动合并。 | `check_s08_p3_entity_matching_quality.py` 通过：scenarios=4、quality_cases=4、manual_review_queue=3、entity_matching_report=1、formal_report_allowed=false。 |
| `KMFA-S08-REV-F05` | P3 | fixed | 初始 evidence consistency 临时检查假设了错误的 S08 manifest key。 | 已按各 phase manifest schema 执行 schema-aware evidence consistency check 并通过。 |
| `KMFA-S08-REV-F06` | P3 | accepted_next_step | Stage 8 复审通过后仍需要独立 GitHub 上传步骤与 push 证据。 | 本轮记录为 `PASS_UPLOAD_READY_LOCAL_ONLY`；未执行 GitHub upload。 |

## 不在本轮范围

- 不执行 GitHub push。
- 不实现 S09 事实层、lineage 完整检查或正式报告生成。
- 不新增 UI、外部系统 connector 或自动接口。
- 不关闭人工复核队列，不自动合并中高风险实体匹配候选。
- 不提交 raw business data、zip、Excel、PDF、私有 CSV、credentials、银行流水、合同、薪资或税务申报。

## 后续门禁

复审后下一门禁为 `KMFA-S08-FINAL-GITHUB-UPLOAD-GATE`。上传门禁必须基于最新 `origin/main` 对齐当前 reviewed Stage 8 tree，复跑 S08-P1/P2/P3 validators、治理 validator、raw/secret scan、parse checks 和 evidence consistency check，并记录 dry-run push、push 和 post-push parity。
