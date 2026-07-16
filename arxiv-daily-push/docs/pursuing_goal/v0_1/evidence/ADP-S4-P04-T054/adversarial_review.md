# 对抗复核记录 · ADP-S4-P04-T054（按边际价值扩展 A2 Registry）

用独立 skeptic 对 A2 registry 扩展做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **门有意义、控制有牙**：裸 rate 比较(new 1.0≥baseline 1.0)孤立看近同义反复(admitted 皆 verified-useful→结构 1.0),但被两点补偿：①verifier 对每个 admitted 独立复检(.gov.cn host/A2/inc 非空/verified_useful/2016 游标)②真数据驱动负控制——`rate_if_all`=8/10=0.8<1.0(实跑确认);若从候选移除负控制,rate_if_all 变 8/8=1.0 且控制断言会 FAIL + "无 baseline-only 拒/无非官方拒" 也 FAIL,故控制有牙、强制真 reject 存在。结构 1.0 藏不住质量退化(误 admit 的非 useful 区会被逐区复检抓)。
- **基线真实**：baseline_from_t053 读真 T053 manifest 10 区(各 inc 非空)→rate 10/10=1.0,未被操纵。
- **边际价值真**：marginal=len(incremental_signals)=第一线信号超 {policy,regulation,statistics};baseline-only-zone→inc=[]→拒。
- **官方身份 T033 强制**：verify_official 走 OI.verify_identity;zone-aggregator(media)→DISCOVERY_ONLY 短路→非官方拒;非 .gov.cn→unofficial 拒(纵深防御)。8 admitted 全 A1(官方非中央)→标 A2。
- **交付+诚实**：cohorts(8)+marginal_value_report(全 10 候选)+health(8 全健康)齐且一致;verifier re-derive R.expand() 匹配。8 区真二波高价值(南沙/舟山/西海岸/合肥高新/东湖高新/滨海/江北/成都高新)真 .gov.cn host,tls_blocked/pending 无伪造抓取,非凑数。
- **无 gate-pass-while-false**。

本轮无需修复（skeptic 判 CONFIRMED_SOUND，近同义反复已被逐区复检 + 有牙负控制补偿）。实现者不自签 PASS —— 交独立复核。
