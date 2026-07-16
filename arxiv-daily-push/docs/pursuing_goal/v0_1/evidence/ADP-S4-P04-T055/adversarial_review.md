# 对抗复核记录 · ADP-S4-P04-T055（A2 Production Gate）

用独立 skeptic 对 A2 生产门做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **非空洞控制有牙且承重**：decide(health=35)→promote、decide(health=5)→low_frequency(不promote);变异测试证控制抓 breakage——always-promote 门挂 health=5 控制、never-promote 门挂 health=35 控制,任一变异翻 verifier FAIL。控制走**同一 hd≥30 阈值分支**(仅 _health_days 绕过,而其最多算 1)。
- **无 30 日健康不可晋级**：decide 仅 hd≥30 promote;真区 hd=_health_days=1(confirmed)或0,全 18 区最大 1→0 区可达门;value/tier 记录但不入决策分支,无 value/volume 泄漏。
- **ledger 诚实**：18 区=10 pilot+8 扩展,无丢;3 confirmed(苏工园/雄安/横琴)held low_frequency(1日),15 disabled(0日),每 held 有 days_to_promotion;re-derive 匹配。
- **交付+可回滚**：ledger+cost/quality evidence+rollback(git revert/flag off)+NOT_DEPLOYED+每条 reversible+re-derivation guard。
- **无 gate-pass-while-false**;0 晋级是正确证据门结果非空洞(控制独立证 promote 路径可用)。

**加固（关闭 skeptic 指出的理论手改缺口）**：skeptic 指 check5 仅比聚合计数,理论上手改伪造 promoted 条目(health=35)可漏。已改 verifier check5 为**逐条深比对**(每 source_id 的 decision+health_days 须匹配 tool 重推),伪造条目会被抓 → FAIL。复跑 PASS(exit 0)。

实现者不自签 PASS —— 交独立复核。
