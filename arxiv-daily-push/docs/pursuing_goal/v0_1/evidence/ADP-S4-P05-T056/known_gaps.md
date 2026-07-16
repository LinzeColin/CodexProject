# Known gaps · ADP-S4-P05-T056（Coverage Debt 与 As-of 历史查询底座）

目标：展示 2016+ 哪些地域/年份/类型完整，支持截至某日恢复当时已知版本。100 修订样本查不同日期不用未来版本；覆盖空洞可解释。诚实边界：

1. **底座建于当前回填语料**：coverage/as-of 覆盖 A0(T046/T047 waves,18)+A1 省级(T050,9)=27 真实文档 5 源。coverage 网格=各源 2016+ 窗口全月(180 格),covered 11 / 调试 debt 169(source_not_yet_active 139 + not_backfilled 30),**unexplained=0 每空洞可解释**。全域随更多回填批次跨真实时间收敛。
2. **as-of 无未来泄漏（非同义反复）**：693 样本(21 链×33 查询日)0 未来泄漏 + 与独立 oracle 0 分歧;用解析日期(y,m,d)非字符串;负控制:故意 broken resolver 在版本间查询确产生未来解析(被抓)、畸形日期被拒。**修订链构造说明（诚实）**：**当前语料无天然「同文跨月修订」**（同 canonical_id 的重复均同月→覆盖）,故 6 条 2 版链是**为跑未来/过去边界而构造的 edge-test**（时间顺序真实,but 非自然跨月改版）;真自然修订链随文档跨真实时间被多次观测后累计（承 T026/T048）。no-future-leak 性质在构造链上真实验证。
3. **coverage 的「完整」是回填口径**：covered=有回填文档的格;debt 格标 source_not_yet_active(窗口前)/not_backfilled(窗口内未回填)。**「源确实发布但漏掉」仍需地面真值发布索引**(承 T048)——本底座答「我们已知的完整度」,真值完整度是更强命题,随权威发布日历接入增强。
4. **historical manifest resolver=月度快照点时**：按语料月份构造月度 manifest,as-of 查询返回 ≤查询日的最新 manifest,永不未来。真 T027 Parquet 快照 manifest 接线后替换。
5. **NOT_DEPLOYED**：coverage API + as-of + manifest resolver 库,未接 worker/生产。live build 仍 b189d3cc0703(==T040)。
