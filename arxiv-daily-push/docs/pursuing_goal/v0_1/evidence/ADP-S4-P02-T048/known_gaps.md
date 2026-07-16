# Known gaps · ADP-S4-P02-T048（A0 历史附件/修订/效力 QA Gate）

本任务是 **QA Gate**（size S, NOT_DEPLOYED）：验证已回填的 2016+ A0 历史**不只是 URL**，而是**有原文、可读附件、正确修订链、正确 as-of、0 未解释 P0 缺口**。以下是诚实的边界。

1. **附件来源集中在 stats.gov.cn**：本轮 100+ 可读附件绝大多数是国家统计局月度发布的 `.xlsx/.xls` 数据表（真实二进制，magic-byte + sha256 校验）。gov.cn 政策「content」页多为**全文内嵌**、下载型附件稀疏（8 页仅 2 个）。→ 附件可读性 gate 已达标，但**附件类型多样性**（PDF 通知、Word 公告、图片）随 T049–T051 省级/城市级 A1（通知型公文附件密度更高）扩展后自然增加。链接 [[adp-s4-expansion]]。

2. **修订链/as-of 样本用真实官方正文 + 受控多观测构造**：真实回填语料是**单次观测快照**，尚无天然的「同文两版」修订对。修订链 gate 用**真实官方正文作 v1**，再以受控编辑（真实修订句 / 状态 现行有效→已废止 / 附件 sha 变更）作 v2，证明 T026 版本引擎在**幂等不产生幻版、模板噪声不产生版本、实质变更恰产生一版**。真实「同一公文历史多版」需 T056 as-of 历史查询底座接线后跨真实时间累计。

3. **as-of 无未来泄漏在构造链上验证（含对抗 fixture + 独立 oracle + negative control）**：as-of gate 对 15 条链（含乱序/3–5 版/边界）× 33 查询日验证「解析日期 observed_at ≤ 查询日」，495 样本 0 泄漏、与独立 oracle 0 分歧；并以「故意写错的 resolver 必被抓到」「畸形日期必被拒」两个 negative control 排除同义反复。**注**：本 gate 验证的是 T048 自带的 chronological resolver；生产级 as-of 查询路径（真实版本流）随 T056 as-of 底座上线——T026 版本引擎当前只有 build_chains/replay，无 as-of 函数。

4. **gap gate 范围：可测「已尝试单元不被静默丢弃」，不冒充测「真值完整性」**。0 未解释 P0 缺口重构为对**已尝试（attempted）单元**判定（attempted=产出文档单元 ∪ 真实 T047 尝试失败源 ndrc/cac）：①每个已尝试单元显式归类为 covered/fetch_failed/no_publications，silent_holes=0；②真实尝试失败被 surface 为 fetch_failed（2/2，可达真实信号）；③silent-hole 检测器在真实变异上触发（可判别，非不可达 ghost）。**明确不测**：某月源确实发布但回填静默漏掉——需地面真值发布索引，**推迟到 T056 Coverage Debt**（其目标即「展示 2016+ 哪些地域/年份/类型完整」）。窗口内未尝试月标 `not_backfilled`（诚实：跟踪中的未来回填工作，非 covered），随 T050/T051 收敛。**此设计经对抗复核（2 轮 workflow + gap 单独复核）确认前版 as-of/gap 的同义反复/空洞已闭合，四 gate 全 CONFIRMED_SOUND。**

5. **dev-env 读取，生产未触**：附件 readback 从**开发环境**实抓（非 worker）→ 0 云成本、DIR-007 不受影响、live build 仍 b189d3cc0703（==T040）、六主题/MVP 不变。NOT_DEPLOYED。
