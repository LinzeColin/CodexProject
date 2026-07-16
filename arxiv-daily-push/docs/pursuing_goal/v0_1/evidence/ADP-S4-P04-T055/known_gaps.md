# Known gaps · ADP-S4-P04-T055（A2 Production Gate）

目标：把稳定高价值 A2 晋级，其他保持 disabled/低频。0 个仅因数量目标晋级；每个晋级 source 有实际 30 日健康证据。诚实边界：

1. **0 晋级=诚实的证据门结果，非敷衍**：18 个 A2 区（T053 10 + T054 8）**全无 30 日健康证据**（门户 JS/TLS 挡，实际抓取待 headless；confirmed_signals 区仅 1 次 recon=1 日健康,其余 0 日）。晋级须 health_days≥30 → **0 晋级**。3 confirmed 区（雄安/苏工园/横琴）held **low_frequency**（1 日健康），其余 15 区 **disabled**（0 日）。
2. **门非空洞（关键）**：非同义反复——控制证明门真按 30 日阈值判：`decide(health=35)→promote`、`decide(health=5)→low_frequency(不 promote)`，走**同一 decide() 路径**。若控制坏/去掉,verifier 会 FAIL。故「0 晋级」是真实证据门结果。
3. **0 仅因数量晋级**：promoted_for_volume=0（by construction:晋级须 health,永不凭 count/value/coverage）。价值/tier 无法绕过 health 晋级。
4. **health_days 当前是观测天数近似**：confirmed_signals=1 日（单次 recon），tls_blocked=0 日。真 30 日健康随 worker 接线跨真实日历累计（每日健康探针）。本任务先立门 + 证明其强制 30 日。
5. **可回滚且未部署**：NOT_DEPLOYED；决定绑 feature-flag；不改既有生产数据；回滚=git revert/flag off。每 held 区有 days_to_promotion。
6. **★收尾 S4-P04（A2）★**：T053 pilot + T054 扩展 + T055 生产门。A2 全域随 headless fetcher + 真实 30 日健康累计后重评晋级。
