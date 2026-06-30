# S09-P3 口径转换与差异核对完成记录

- project_id: `KMFA`
- stage_phase: `S09-P3`
- task_ids: `S9PCT01-S9PCT03`
- completed_at: `2026-06-30T23:55:00+10:00`
- status: `completed_validated_local_only`
- github_upload_performed: `false`

## 完成范围

- 建立 public-safe 口径转换与差异核对层。
- 将 S09-P2 的 12 条 scope difference summary 转换为 12 条 reconciliation records。
- 建立 6 类内部核对域：合同/项目收入、项目成本/财务费用、银行回款/应收账龄、开票/合同结算/税务、研发费用/项目人员证据、权威 PDF/Excel 与系统复算。
- 每条差异记录具备 reason candidate、依据 refs、impact scope、resolution status、责任角色、reviewer、created_at 和 closed_at。
- 当前无 owner/授权确认，`confirmed_resolution_count=0`；派生指标重跑、正式报告重跑和 Stage 9 review 均保持阻断。

## 输出

- `KMFA/tools/project_scope_reconciliation.py`
- `KMFA/tools/check_s09_p3_scope_reconciliation.py`
- `KMFA/tests/test_project_scope_reconciliation.py`
- `KMFA/metadata/reports/project_scope_reconciliation_manifest.json`
- `KMFA/metadata/quality/scope_reconciliation_records.jsonl`
- `KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl`
- `KMFA/stage_artifacts/S09_P3_scope_reconciliation/machine/s09_p3_manifest.json`

## 边界

- 不提交 raw business data、zip、Excel、PDF、private CSV、字段明文或真实业务金额。
- 不写 raw 层，不关闭差异，不把 pending review 伪装为已确认。
- 不实际重跑派生指标或正式报告；只记录确认后才能重跑的 gate。
- 不执行 Stage 9 整体复审。
- 不执行 lineage full check、正式报告、UI、外部接口或 GitHub upload。

## 风险与剩余问题

- 12 条 reconciliation records 仍为 `pending_owner_or_authorized_review`。
- Stage 9 整体复审尚未执行；需要下一轮只做 Stage 9 review，复跑 S09-P1/P2/P3 validators、治理 validator、raw/secret scan 和 evidence consistency check。
- 正式报告、lineage full check、UI 和外部接口仍未实现，不能宣称业务系统已上线可用。

## 回滚

- 删除 S09-P3 新增工具、测试、metadata 输出和 `KMFA/stage_artifacts/S09_P3_scope_reconciliation/`。
- 从 governance registry、stage_status 和事件日志中移除本次 S09-P3 append-only 草案记录。
