# Known gaps · ADP-S4-P03-T052（A1 Coverage/Quality/Cost Gate）

目标：决定哪些省市进入持续生产、哪些降频或隔离。官方身份 100%；质量/及时/成本均有实际证据；决定可回滚。诚实边界：

1. **决定基于当前 SHADOW 证据**：promote/hold/disable 依据 T050（省级实抓 9 真实文档）+ T051（城市 cohort，pending_headless）。3 promote=江苏/山东/北京（真实内容寻址文档+日期+月份证据）；18 hold=城市（验证 A1 但原文未抓，**不凭价值晋级**）；1 disable=广东（T050 隔离/被挡）。
2. **及时性证据窗口小**：本 SHADOW 批各省仅 3 文档（2026-06/07），latest_month 证据真但样本小；全量及时性随 cron 跨真实时间累计。held 城市及时性=空（诚实，无 UNKNOWN 冒充）。
3. **成本=dev-env 0 云**：所有评分源走 dev-env（非 worker）→ 生产请求 0；未测项标 UNKNOWN 不填 0。
4. **决定可回滚且未部署**：NOT_DEPLOYED；决定是 recommendation 绑 feature-flag；不改既有生产数据；回滚=git revert / flag off。城市晋级待 T053+ 与 headless fetcher 后重评。
5. **A2 未涉**：本 gate 仅 A1（省/市）；A2（重要区/功能区）是 T053-T055。
