# PFI v0.2.5 Stage 3 Phase 3.3 对账、幂等与差异实施记录

## 唯一执行合同

- Roadmap tasks：`S3-P3-T1..T4`
- Acceptance：`ACC-PFI-V025-S3-P33-RECONCILIATION`
- 输入：`HEAD` 中 8,815 条交易的 immutable Git-object snapshot；只在内存解析。
- 输出：重复导入结果、对账摘要、Interconnection Matrix、read-model 去重合同、脱敏 lineage 与 review queue 汇总。
- 明确不做：Stage 3 whole-stage review、Stage 4、数据库迁移、review queue 持久化、真实源写入、push、App 安装。

## 决策与实现

1. 同一只读 blob 连续解析两次；Ledger `idempotency_key` 进入同一个内存 registry。第一次发布 6,879，第二次发布 0、识别重复 6,879、collision 0。
2. 只接受上游 `ACCEPTED`、非零金额且能由结构化 `event_type + signed direction` 映射的记录。禁止来源名称推断，禁止金额/时间近似挂链。
3. 真实快照没有显式 transfer link/account-role 证据，也没有 refund offset，因此相关记录 fail-closed：转账 1,250、退款 249 进入 review queue，发布数均为 0。
4. 另有上游 `NEEDS_REVIEW` 406 条与零金额 31 条进入 review queue。8,815 条输入精确分区为 6,879 条发布候选和 1,936 条复核项，silent drop 为 0。
5. 来源时间只有日期粒度；标准化为当日 `00:00:00Z` 仅用于稳定 RFC3339 表示，并明确 `exact_transaction_time_claimed=false`。
6. Interconnection Matrix 覆盖自有账户转账、信用卡还款、退款、投资入金、基金/黄金申购、投资买入/卖出 8 条主链路及全部 10 类事件 flags；1,250 条未分类 transfer 作为共享、不可跨 event row 相加的 review pool，避免 UI 重复计数。
7. read model 先按 `economic_event_id` 去重，再按 metric flags 投影；homepage/consumption/investment/cashflow/report 共享同一 `read_model_hash`。

## 风险与停止条件

- 复核队列表示“差异已定位且未错误发布”，不表示账户角色、transfer counterpart 或 refund offset 已人工确认。
- 真实快照没有余额、负债、持仓、价格或生产 FX；本 Phase 不声明净资产、投资市值或现金余额可计算。
- 任何需要修改真实源、按来源名称分类、按金额/时间近似关联、或静默丢弃差异的实现均应停止。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v025_stage3_idempotency.py -q
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v025_stage3_no_double_count.py -q
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B -m pytest -p no:cacheprovider PFI/tests/test_v025_stage3_interconnection.py -q
```

本文件只记录 Phase 3.3 candidate。Stage 3 仍为 `in_progress`，下一轮必须先做整阶段独立 review、整改、复审和显式验收，不能直接进入 Stage 4。
