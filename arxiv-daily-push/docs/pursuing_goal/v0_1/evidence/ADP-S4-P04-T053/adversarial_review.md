# 对抗复核记录 · ADP-S4-P04-T053（首批高价值 A2 pilot）

用独立 skeptic 对 A2 pilot 选择器做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **增量价值真实非退化**：incremental_signals = zone signals ∩ LOCAL_SIGNAL_TYPES，且 LOCAL_SIGNAL_TYPES ∩ BASELINE = ∅（确认空）。baseline 减法非空操作：雄安/横琴/前海各带 policy 信号被真实剔除（inc=3/3/2 非 4/4/3）。仅 policy 的区 → [] → 拒。6 类本地行动信号真区别于 A0/A1 {policy,regulation,statistics}。
- **无价值源不晋级**：policy-repost-zone → inc=[] → 拒（价值门触发,即使身份会验 A1）；zone-media → verify_identity media/未验证 → 拒（非官方）。两者皆走真 select_pilot 路径,无一漏入。
- **官方身份真 T033 路径**：verify_official 走 OI.verify_identity；.gov.cn 域必需,非 gov host → unofficial 拒。10 入选全非中央 .gov.cn 功能区真门户,无凑数。
- **诚实**：3 区 confirmed_signals=recon 可达者(雄安/苏工园/横琴),其余 7 诚实 tls_blocked/fetch-pending 非冒充已抓。10 区全真高价值。manifest 与 live select_pilot() deep-equal。
- **无 gate-pass-while-false**。

**加固（关闭 skeptic 指出的证据完整性小缺口）**：skeptic 指 "9/17/6 信号词" recon 仅在 prose/注释,无 committed 原始 capture。已加 `recon_signals.json`（dev-env 重跑,记 3 区 http_status + signal_term_total + by_term:雄安9/苏工园17/横琴6),使 confirmed_signals 有 committed 证据支撑。此为 reachability metadata,不在验收门内,但补齐更诚实。

实现者不自签任务 PASS —— 交独立复核。
