# S2PMT07 P0/P1 Zero-Proof Readiness

时间：2026-06-28 04:36:58 Australia/Sydney

## 目标

为后续真正关闭 inherited P0/P1 前必须提交的 `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` 建立 fail-closed 机器校验口径。当前只记录 schema/readiness 与缺失阻断，不创建最终包，不关闭 P0/P1。

## 当前状态

| 项目 | 状态 |
|---|---|
| task_id | `S2PMT07-P0-P1-ZERO-PROOF-READINESS` |
| acceptance_id | `ACC-S2PMT07-FINAL-REVIEW` |
| zero proof artifact | `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json` |
| artifact present | `false` |
| status | `blocked` |
| inherited open P0/P1 | `8 / 37` |
| p0_zero_proven / p1_zero_proven | `false / false` |
| independent final closure decision | `false` |
| zero proof state hash | `694d5a601a7421952c86d1e940e05cc04784319c228a1ef211aef3a180c63dc0` |
| final bundle readiness hash | `d7ca0e0e1bf083416e1368b055c51f3d9bbd39df04ce7da34350cd9e693cf695` |

## 必填字段

`p0_p1_zero_proof.json` 未来至少必须包含：

- `schema_version`
- `contract_id`
- `generated_at`
- `reviewer_independence`
- `source_candidate_refs`
- `finding_counts`
- `zero_severity_counts`
- `independent_closure_decision`
- `final_bundle_refs`
- `no_production_side_effects`
- `decision_hash`

## 阻断原因

- `p0_p1_zero_proof_artifact_missing`
- `independent_final_closure_decision_missing`
- `inherited_v7_1_p0_findings_open`
- `inherited_v7_1_p1_findings_open`

## 验证

- TDD RED：`test_stage2_final_gate.py` 在新增 API 前失败，原因是缺少 zero-proof readiness builder/validator。
- GREEN：`PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_zero_proof_refactor PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_final_gate.py -q` -> 28 tests OK。

## 边界

本记录没有启用 SMTP、scheduler、Release、生产恢复、Daily Operation；没有创建 `FINAL_ACCEPTANCE_BUNDLE/`；没有改公共 schema、DB、生产队列、source adapter、ranking、CURRENT、V7.1 或 V7.2 合同；没有关闭 inherited P0/P1；没有声明 `INTEGRATED_PRODUCTION_ACCEPTED`。

## 下一步

继续在 S2PMT07 下补齐 S2PLT04 终局完成、final bundle、独立最终签出、最终命令执行和 inherited P0/P1 归零证明。任何技术候选证据都不能替代 `p0_p1_zero_proof.json`。
