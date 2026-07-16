# 对抗复核记录 · ADP-S4-P03-T051（重点城市 A1 cohort）

用独立 skeptic 对城市 cohort 选择器做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **明确价值**：value_score 产 8 个不同 admitted 值(0.67…1.0)，tier 真分层(直辖市1.0→关键经济0.64)+role bonus(封顶)；top-tier 饱和于 1.0 是饱和非退化；0.6 stop 真分开 key_economic(入选)与 ordinary(拒)。
- **官方原文无洗白**：18 入选全真城市 .gov.cn 经 T033 判 A1；`official_domain`(endswith .gov.cn)是独立硬门，`gov_directory_listed` 洗不了非 gov 域；探针证 非gov.com→unofficial、gov上媒体→media、中央→A0。
- **不凑数量**：ordinary-city 按 value 拒(0.3<0.6)、city-news-portal 按身份拒(value0.93≥stop 但 media≠A1)——两负控制走真 select_cohort 路径，价值≠入选。
- **2016 游标**：18 入选全 start_month=2016-01。
- **诚实无夸大**：18 全 pending_headless、0 服务器端实抓、经 original_fetch_status+note 披露；**skeptic 独立核验北京 proof 为真**（evidence/ADP-S4-P03-T050/province_backfill_docs.json 含真实 beijing.gov.cn A1 文档）；manifest 称「官方原文发布者」(身份角色)非「已抓原文」。
- 仅 1 处 cosmetic（value_score docstring 写 0.7*tier 而码用 TIER_WEIGHT）——已修，不影响门/宣称。

实现者不自签任务 PASS —— 交独立复核。
