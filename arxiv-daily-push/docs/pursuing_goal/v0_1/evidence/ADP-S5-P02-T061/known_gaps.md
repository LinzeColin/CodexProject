# Known gaps · ADP-S5-P02-T061（全文与语义重排基准）

目标：只精确/结构化不足才引语义层,避免过早向量。交付 FTS benchmark/semantic experiment/cost-latency-quality ADR。**语义层必须提升固定查询集且不绕过结构化过滤;否则不采用。** 诚实边界：

1. **ADR 规则=(提升) AND (不绕过过滤)**：decide_adopt 采用当且仅当 语义提升固定查询集 metric(MRR/recall@5) **且** 结果为结构化过滤候选集子集。**identity(不提升)拒 / bypass(绕过过滤)拒 / improver-but-bypass 拒**(AND 非 OR)。
2. **提升真实可测**：FTS baseline recall@5=0.875(真有一漏:低温雨雪 query 漏掉用同义词「冰冻灾害」的相关文档);synonym 语义层同义扩展找回该文档→recall@5=0.9167(真提升)。metric(mrr/recall_at_k)标准实现。
3. **respects_filters 真计算**：good 候选在 region 过滤子集内检索,结果 ⊆ 过滤集→True;bypass 候选返回全局结果越出过滤集→False(建模一个绕过过滤的层)。
4. **semantic 为确定性代理实验**：无真 embedding;synonym rerank=同义词表扩展(确定性,建模「语义层能找同义命中」)。**真生产语义/向量层由本 ADR 门控**:仅当在真实固定查询集上提升 FTS 且不绕过结构化过滤才采用。当前证明**决策纪律**(不过早引向量)+ FTS 基准 + 提升可测机制。
5. **NOT_DEPLOYED**：benchmark+ADR 库,未接 worker/生产。live build 仍 b189d3cc0703(==T040)。版本/as-of/新旧对照 API 是 T062。
