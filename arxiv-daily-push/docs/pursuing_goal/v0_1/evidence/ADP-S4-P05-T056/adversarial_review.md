# 对抗复核记录 · ADP-S4-P05-T056（Coverage Debt + As-of 底座）

用独立 skeptic 对底座做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **(a) as-of leak-check 真非空洞（不同于 T048 原 bug）**：as_of_query 按解析 (y,m,d) 元组取 ≤query 的最大 observed_at;future_leakage 对真 resolver 结构为 0,但被补偿:①独立 oracle(_oracle_as_of,filter-sort-last vs 单遍 max)会抓「不泄漏但错」的 resolver;②broken-resolver 控制在版本间查询确产生未来解析(query 2019-04-01 返回 2026-07-15,detected True);畸形日期 raise ValueError。
- **(b) 693=21 真链×33 查询日**真笛卡尔积,keyed by 真 canonical_id,非凑;含 6 条 2 版链跑未来/过去边界。**caveat（已诚实披露）**:语料无天然跨月修订(同 canonical_id 重复同月被覆盖),故 2 版链为 edge-test 构造(时间顺序真);scoped claim 成立。
- **(c) coverage 网格非平凡且诚实**:180 格,11 covered,169 debt 各带具体 reason(source_not_yet_active 139 + not_backfilled 30)全暴露;0 UNEXPLAINED 结构不可达但 verifier 的 `cells<=covered` 守卫确保真有 debt 需解释且 debt 被 surface 非隐藏。
- **(d) manifest resolver 永不未来**:全 resolution 重推(2015→None,2099→2026-07,余匹配),皆 as_of≤query。
- **(e)** 小健壮性:verifier 原仅 live 重推 coverage_debt,信报告的 as-of/manifest 聚合。skeptic 独立重推全部(693/0/0;manifest 匹配)确认准确,无 false-pass。

**加固（关闭 skeptic 指出的 (e)）**：verifier check5 已扩为**全 live 重推**——as-of 聚合(samples/leakage/disagreements)+每条 manifest resolution 均从 tool 现推并比对报告,手改报告(伪造 0 泄漏)会被抓 FAIL。复跑 PASS(exit 0)。known_gaps 补精确披露 2 版链为 edge-test 构造(非自然跨月改版)。

实现者不自签 PASS —— 交独立复核。
