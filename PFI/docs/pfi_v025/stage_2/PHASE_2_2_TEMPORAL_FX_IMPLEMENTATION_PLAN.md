# PFI v0.2.5 Stage 2 Phase 2.2 实施计划

- Phase：`V025-S2-P2.2`
- Tasks：`S2-P2-T1` 至 `S2-P2-T4`
- Acceptance：`ACC-PFI-V025-S2-P22-TEMPORAL-FX`
- Risk tier：`T3_FINANCIAL_TEMPORAL_POLICY`
- 基线提交：`bce1b21826a829094481a3ef63c46aa5aa95c99e`

## 目标与范围

建立八类时间字段与 Australia/Sydney 时区合同；实现 06:00 有效 FX 业务日、周末和显式 source closed dates 回退；建立 FX snapshot 的 source/hash/current/stale/blocked 状态；证明普通运行无隐式联网。

## 明确非范围

- 不抓取或加载生产 FX，不写死汇率。
- 不修改、复制、迁移或删除真实数据。
- 不把旧 v0.2.2 snapshot 提升为 v0.2.5 production source。
- 不进入 Phase 2.3，不执行 Stage 2 整阶段验收。
- 不 push，不安装 canonical App。

## 验证

```bash
PFI/.venv/bin/python -B -m pytest PFI/tests/test_v025_stage2_temporal_truth.py -q
PFI/.venv/bin/python -B -m pytest PFI/tests/test_v025_stage2_fx_policy.py -q
PFI/.venv/bin/python -B -m pytest PFI/tests/test_v025_stage2_source_manifest.py -q
python3 -B scripts/lean_governance.py check-render --project PFI
```

## 回滚与停止条件

只回退 Phase 2.2 提交。若需要联网、写生产数据、硬编码汇率，或无法明确 source/effective-date/direction 语义，则保持 blocked 并停止。
