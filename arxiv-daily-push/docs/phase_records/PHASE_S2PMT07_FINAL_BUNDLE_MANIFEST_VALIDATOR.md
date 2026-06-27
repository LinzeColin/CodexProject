# S2PMT07 Final Bundle Manifest Validator

- 时间：2026-06-28 05:18:27 Australia/Sydney
- 任务：`S2PMT07-FINAL-BUNDLE-MANIFEST-VALIDATOR`
- 验收：`ACC-S2PMT07-FINAL-REVIEW`
- 状态：`blocked_manifest_validator_ready_manifest_missing_no_closure_no_production`
- 范围：只新增未来 `FINAL_ACCEPTANCE_BUNDLE/manifest.json` 的严格校验门，不创建最终验收包，不关闭 P0/P1，不完成 S2PLT04，不声明生产验收。

## 当前结论

S2PMT07 final acceptance bundle readiness 现在包含 `FINAL_ACCEPTANCE_BUNDLE/manifest.json` 的 manifest validator。当前真实 manifest 仍不存在，因此 validation state 必须保持 `blocked`：

| 项目 | 当前值 |
|---|---|
| manifest path | `FINAL_ACCEPTANCE_BUNDLE/manifest.json` |
| manifest present | `false` |
| validation status without manifest | `blocked` |
| validation error without manifest | `final_acceptance_bundle_manifest_missing` |
| inherited P0/P1 | `8 / 37` |
| S2PLT04 completed | `false` |
| integrated production accepted | `false` |
| manifest missing state hash | `3b3ecc8417d458a56e2a5dce5764f04eabfa44e7df3113fbbb88808d1115907b` |
| final bundle readiness hash | `13d008aa5e13bd9012032ca645bb03f2cb0152c1c1b826ca4d9842fb89ff3fb8` |

## 未来 manifest 必须满足的校验

| 校验项 | 要求 |
|---|---|
| schema version | `adp.final_acceptance_bundle_manifest.v1` |
| contract | `ADP-PRODUCT-CONTRACT-V7.2` |
| generated_at | 非空字符串 |
| final_bundle_decision | `FINAL_ACCEPTANCE_BUNDLE_READY_NO_PRODUCTION_ACCEPTANCE` |
| bundle_items | 精确等于最终验收包必需文件清单 |
| bundle_item_hashes | 每个必需文件都有 `sha256:` hash |
| artifact_validations | `P0_P1_ZERO_PROOF_ARTIFACT`、`S2PLT04_COMPLETION_REPORT`、`INDEPENDENT_REVIEW_SIGNOFF`、`FINAL_COMMAND_EXECUTION`、`NO_PRODUCTION_SIDE_EFFECT_ATTESTATION`、`NEXT_AGENT_HANDOFF` 全部为 `pass` |
| closure_state | `p0_zero_proven`、`p1_zero_proven`、`s2plt04_completed`、`independent_final_review_passed`、`final_commands_executed` 必须为 true；`production_acceptance_claimed`、`integrated_production_accepted` 必须为 false |
| no_production_side_effects | SMTP、scheduler、Release、production restore、public schema、DB migration、production queue、source adapter、ranking、CURRENT、V7.1、V7.2 等副作用 flag 必须全部为 false |
| manifest_hash | 必须等于去掉 `manifest_hash` 字段后的 canonical payload hash |

## 验证

| 命令 | 结果 |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_final_manifest_red PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_final_gate.py -q` | TDD red：因缺少 `S2PMT07_FINAL_ACCEPTANCE_BUNDLE_MANIFEST_DECISION` 导入失败，符合预期 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/codex_adp_final_manifest_green1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest arxiv-daily-push/tests/test_stage2_final_gate.py -q` | 33 tests OK |

## 禁止误读

- 这不是最终验收包。
- 这不是 P0/P1 归零证明。
- 这不是 S2PLT04 完成证明。
- 这不是 S2PMT07 通过。
- 这不启用真实 SMTP、scheduler、Release、production restore 或 DAILY_OPERATION。
- 这不修改 public schema、DB migration、production queue、source adapter、ranking、CURRENT、V7.1 或 V7.2 合同文件。

## 下一步

继续保持 S2PMT07 blocked，直到真实最终验收包同时包含 valid manifest、P0/P1 zero proof、S2PLT04 completion report、independent signoff、final command execution proof、no-production attestation 和 handoff，并由独立最终复审确认。
