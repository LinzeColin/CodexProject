# 事务发件箱与消息ID扫描

更新时间：2026-06-27 16:22:55 Australia/Sydney

本页是 P0 `A-003` 的 GitHub 浅层阅读入口。它只说明事务发件箱、消息 ID、发送 claim 和 SMTP accepted-before-commit crash window 的当前本地证据；不关闭 P0，不发送 SMTP，不启用 scheduler，不代表 Stage 2 production accepted。

## 一眼结论

| 指标 | 当前值 |
|---|---:|
| 探针数 | 6 |
| 同 revision 消息 ID 稳定 | 已验证 |
| 内容修订后消息 ID 变化 | 已验证 |
| 同一发件箱记录 100 次 claim | 1 成功 / 99 阻断 |
| SMTP accepted-before-commit 无 provider ref | fail-closed |
| Provider accept ref 后本地 finalize | 已验证 |
| delivery semantics | `at_least_once_with_idempotent_message_id` |
| exactly-once 声明 | `false` |
| 真实 SMTP 发送 | `false` |
| P0 关闭声明 | `false` |

## 探针明细

| 探针 | 要求 | 当前证据 |
|---|---|---|
| `message_identity_same_revision` | 同一 cycle/product/recipient/content revision/body 生成稳定 `message_id` | 已通过 |
| `message_identity_revision_change` | 内容 revision 或 body 变化后 `message_id` 必须变化，避免新内容复用旧 ID | 已通过 |
| `single_outbox_claim_under_contention` | 100 个 sender claim 同一 outbox row 只能有 1 个成功，其余 row_version CAS 阻断 | 已通过 |
| `smtp_accept_pending_commit_fail_closed` | SMTP 已接受但本地未提交且无 provider ref 时，不能安全重发，必须阻断 | 已通过 |
| `provider_accept_finalizes_without_resend` | provider accept ref 存在时只能本地 finalize，不触发真实 SMTP resend | 已通过 |
| `at_least_once_no_exactly_once_claim` | 只声明 at-least-once + idempotent message ID，不声明 exactly-once | 已通过 |

## 证据位置

- [A-003 运行清单](../../governance/run_manifests/ADP-S2PMT03-OUTBOX-DELIVERY-A003-20260627.json)
- [A-003 阶段记录](../docs/phase_records/PHASE_S2PMT03_OUTBOX_DELIVERY_A003.md)
- [P0 复审 receipt](../docs/phase_records/PHASE_S2PMT07_P0_INDEPENDENT_REVIEW_RECEIPT.md)
- [聚焦测试](../tests/test_stage2_lease_fencing.py)

## 仍未完成

P0 `A-003` 仍需独立 reviewer 对证据充分性作出明确判断。本页不启用 SMTP、scheduler、Release，不改队列/Schema/数据源，不关闭 P0/P1，不声明 `INTEGRATED_PRODUCTION_ACCEPTED`。
