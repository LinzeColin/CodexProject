# KMFA Stage 9 Review Report

- review_id: `KMFA-S09-STAGE-REVIEW-20260630`
- review_time: `2026-06-30T23:59:00+10:00`
- stage: `S09 - 项目成本计算引擎`
- scope: `S09-P1`, `S09-P2`, `S09-P3`, Stage 9 owner-readable entries, governance status, public-repo safety boundary
- result: `PASS_UPLOAD_READY_LOCAL_ONLY`
- reviewed_head: `db9169464f71`
- worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`
- branch: `codex/kmfa`
- github_upload_status: `not_pushed`

## 复审结论

Stage 9 三个 Phase 已完成本地实现、验证和整体复审。S09-P1 建立 public-safe 项目成本事实层，覆盖收入、合同额、开票、回款、成本合计和成本分类 6 个 fact slots，生成 4 条 project cost fact records 和 9 条 unallocated project cost pool records。S09-P2 建立 public-safe 毛利与现金毛利层，生成 4 条 margin records 和 12 条 scope difference summary records，保持 authority display refs、system recomputed refs 和 cash refs 分离。S09-P3 建立 public-safe 口径转换与差异核对层，生成 12 条 reconciliation records 和 6 条 domain controls。

复审确认 S09-P3 的 12 条 reconciliation records 仍全部为 `pending_owner_or_authorized_review`。因此本轮不关闭差异、不重跑派生指标、不生成正式报告、不进入 S10、不做 UI、不做外部接口、不做 lineage full check，也不执行 GitHub upload。Stage 9 review 仅使当前本地树进入下一独立 `Stage 9 final GitHub upload` 门禁；upload 仍必须先对齐最新 `origin/main`，复跑 validator 和安全检查，并留下 push proof。

复审中发现一个安全扫描 finding：通用 high-signal secret regex 将 `KMFA/tools/a0_golden_fixture.py` 中的局部变量名 `normalized_token` 误判为 token 赋值。经定位，该值只是 normalized value hash 的输入材料，不包含 credential；本轮已将命名改为 `normalized_hash_source`，并复跑 S05 fixture 单测、A0 fixture validator 和 high-signal secret scan，结果通过。

## 覆盖范围

| 范围 | 复审结果 | 证据 |
|---|---|---|
| `S09-P1` 项目成本事实层 | PASS | `KMFA/tools/project_cost_fact_layer.py`, `KMFA/tools/check_s09_p1_project_cost_fact_layer.py`, `KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/` |
| `S09-P2` 毛利与现金毛利 | PASS | `KMFA/tools/project_margin_cash_margin.py`, `KMFA/tools/check_s09_p2_margin_cash_margin.py`, `KMFA/stage_artifacts/S09_P2_margin_cash_margin/` |
| `S09-P3` 口径转换与差异核对 | PASS | `KMFA/tools/project_scope_reconciliation.py`, `KMFA/tools/check_s09_p3_scope_reconciliation.py`, `KMFA/stage_artifacts/S09_P3_scope_reconciliation/` |
| S05 fixture secret-scan finding | PASS_AFTER_FIX | `KMFA/tools/a0_golden_fixture.py`, `KMFA/tests/test_a0_golden_fixture.py`, `KMFA/tools/check_a0_golden_fixture.py` |
| Stage 9 入口状态 | PASS_AFTER_FIX | `KMFA/tools/check_s09_stage_review.py`, `KMFA/功能清单.md`, `KMFA/开发记录.md`, `KMFA/模型参数文件.md`, `KMFA/HANDOFF.md`, `KMFA/docs/governance/` |
| 敏感数据边界 | PASS | raw artifact extension scan, high-signal secret scan |
| v1.2 no-omission / governance | PASS | `KMFA/tools/no_omission_check.py`, `scripts/lean_governance.py`, `scripts/validate_project_governance.py` |

## Finding 与处理

| Finding ID | 严重度 | 状态 | 说明 | 处理 |
|---|---|---|---|---|
| `KMFA-S09-REV-F01` | P2 | fixed | Stage 9 三个 Phase 已完成，但整体复审证据、review manifest 和治理状态仍显示未复审。 | 已新增 `KMFA/stage_artifacts/S09_STAGE_REVIEW/` 和 `KMFA/tools/check_s09_stage_review.py`，同步 owner-readable、stage_status 和 governance events 为 local-only review passed。 |
| `KMFA-S09-REV-F02` | P2 | passed | S09-P1 必须保持 public-safe fact layer，不得提交 raw values、字段明文或直接生成报告。 | `check_s09_p1_project_cost_fact_layer.py` 通过：fact_records=4、cost_categories=9、unallocated_pool=9、formal_report_allowed=false、github_upload_allowed=false。 |
| `KMFA-S09-REV-F03` | P2 | passed | S09-P2 必须保持权威显示值、系统复算值和现金口径分离，不得互相覆盖。 | `check_s09_p2_margin_cash_margin.py` 通过：margin_records=4、difference_summary=12、formal_report_allowed=false、github_upload_allowed=false。 |
| `KMFA-S09-REV-F04` | P2 | passed | S09-P3 必须保持 12 条核对记录 pending，不得关闭差异、重跑派生指标或生成正式报告。 | `check_s09_p3_scope_reconciliation.py` 通过：reconciliation_records=12、domain_controls=6、pending_resolutions=12、formal_report_allowed=false。 |
| `KMFA-S09-REV-F05` | P3 | fixed | high-signal secret scan 将 `normalized_token` 局部变量误判为 credential 风险。 | 已改名为 `normalized_hash_source`，并复跑 S05 fixture 单测、A0 fixture validator 和 secret scan。 |
| `KMFA-S09-REV-F06` | P3 | accepted_next_step | Stage 9 review 通过后仍需要独立 GitHub upload 步骤与 push 证据。 | 本轮记录为 `PASS_UPLOAD_READY_LOCAL_ONLY`；未执行 GitHub upload。 |

## 不在本轮范围

- 不执行 GitHub push。
- 不实现 S10 报告模板、报告等级判定、HTML/CSV 导出或 UI。
- 不实现 lineage full check。
- 不新增外部系统 connector 或自动接口。
- 不关闭 12 条 pending owner/授权核对记录，不重跑派生指标。
- 不提交 raw business data、zip、Excel、PDF、私有 CSV、credentials、银行流水、合同、薪资或税务申报。

## 后续门禁

复审后下一门禁为 `KMFA-S09-FINAL-GITHUB-UPLOAD-GATE`。上传门禁必须基于最新 `origin/main` 对齐当前 reviewed Stage 9 tree，复跑 S09-P1/P2/P3 validators、`check_s09_stage_review.py`、全量 KMFA tests、治理 validator、raw/secret scan、parse checks，并记录 dry-run push、push 和 post-push parity。
