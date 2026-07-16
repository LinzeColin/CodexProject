# 对抗复核记录 · ADP-S5-P02-T060（精确/结构化检索）

用独立 skeptic 对精确检索做对抗复核，判 **CONFIRMED_SOUND**（5 攻击向量全过，无 hole）：
- **(a) 100%第一结果真实**：100 标识为 100 distinct docnum;全 120 docnum 唯一,by_docnum 零归一化冲突(无静默覆盖);100 查询返回 100 distinct doc_id 各匹配自身。无膨胀。
- **(b) SQL 基准平价**：基准为独立 in-memory sqlite3 oracle(变异测试:注入 OR-region bug→基准抓 6 mismatch);structured_filter 对 4320 查询差分(全 facet/region/status×6 日期锚含等边界)0 mismatch。日期 YYYY-MM-DD 零填充→字典序==时序,共享字符串比在此真正正确非潜在缺陷。
- **(c) 顺序**:两侧 ORDER BY doc_id(零填充 doc-NNN),list== 精确比,dup/missing 会暴露。
- **(d) 语料诚实**:corpus.json 从 build_corpus.py 字节级可重生(非手调);真形态文号 + 5 机构/4 地域/3 状态/2016-2026;DOI 子集 24 doc 全查中。filter 真分区(agency→24/120)。

**加固（关闭 skeptic 指出的两处 test-sensitivity gap,非 hole）**：①DOI case-fold 检查原半真(样本 DOI 无 ASCII 字母,.upper() 空操作)→已改语料 DOI 含 ASCII 字母(10.1016/J.STATS...),verifier 用 swapcase() 大小写翻转 DOI 仍命中 + 不存在 DOI 不误中。②日期区间 battery 原锚(2019/2020)匹配 0 doc 不测边界→已改锚在**真实语料日期**,单日 inclusive 边界查询返回真 boundary docs(非空断言),开区间上/下界亦测。复跑 PASS(exit 0)。

实现者不自签 PASS —— 交独立复核。
