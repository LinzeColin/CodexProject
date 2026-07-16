# 对抗复核记录 · ADP-S4-P03-T052（A1 Coverage/Quality/Cost Gate）

用独立 skeptic 对 A1 gate 做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量对真实证据全成立，无 false-pass）：
- **官方身份 100%**：每个评分源真为 A1——3 promote 省（江苏/山东/北京）docs 全 authority_level=A1；18 城市来自 T051 身份核验 manifest（媒体被拒）；广东为真省政府门户。**promote 门要求 canonical_ok==docs（仅计 A1 docs）→ 非 A1 省无法晋级**。
- **实际证据**：promote 需 docs≥1+canonical_ok==docs+latest_month；3 省各 3 内容寻址 A1 docs+真实日期/月份（与 T050 coverage 交叉一致）。held 城市 docs=0 诚实非伪造。
- **晋级需赢得**：18 价值城市全 hold（fetch pending_headless 非 confirmed），不凭价值晋级；广东（隔离,docs=0）disable。
- **可回滚**：只读缓存证据、只写 scorecard JSON、NOT_DEPLOYED、rollback 声明——真实。
- **无误分类**：尝试失败(广东)→disable、未尝试(城市)→hold，诚实区分。re-derivation guard 抓 output 手改。

**加固（关闭 skeptic 指出的 robustness gap）**：skeptic 指出省级 `official_identity` 原为硬编码字面量 "A1"（对真实证据无 false-pass，但非 A1 省被注入会误标）。已改 `_province_identity`：**有 docs → 从 docs 的 authority_level 派生（须均 A1，否则暴露并拉低 rate 使门失败）；无 docs（隔离省）→ 域名判定（官方非中央 .gov.cn → A1）**。现身份为**赢得**（documents/domain basis），非 stamped。3 省 basis=documents、广东 basis=domain；rate 仍 1.0，门仍 PASS。

实现者不自签任务 PASS —— 交独立复核。
