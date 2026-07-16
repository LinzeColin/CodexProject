# Known gaps · ADP-S5-P01-T059（跨板块 Evidence Relation）

目标：连接政策/论文/标准/专利/统计/试点/招采,不建无边界大图谱。交付 relation types/evidence rules/query examples。**每条关系有文档/片段依据；无证据推断明确标记或不保存。** 诚实边界：

1. **有界词表非任意图**：RELATION_TYPES 固定谓词 + 允许的 (subject_kind,object_kind) 对(implements/interprets/cites/references_standard/supported_by_stat/pilot_under/procurement_under/supersedes);**off-vocabulary 谓词/对 + 未知 board kind → refused 不入图**。防无边界大图谱。
2. **只存有证据的边**：_has_evidence 要求 doc_id AND 非空 fragment(引用片段);saved 边全带 {doc_id,fragment,source_id}。**无证据断言→inferred_unsaved 明确标记,不入图**(既不静默丢也不静默存)。graph 恰含 saved 边(无 refused/inferred 泄漏)。
3. **fixture 用真实 backfill 文号 + 现实片段**：苏政办函〔2026〕39号 implements 国办函(片段「根据《国办函...》...制定」)、苏采〔2026〕7号 procurement_under 苏政办函39(片段「为落实...开展采购」)、鲁科字143 references_standard GB/T 12345、某试点 pilot_under 苏政办函39。真实抓取的 fragment 由片段抽取(承 T016 factsheet/T038 resolver)填。
4. **当前断言为 curated 示例**：真实全域关系随抓取 + 抽取积累;关系置信/自动抽取后续增强;本任务先立**有界词表 + 证据强制 + inferred 标记 + query**。
5. **★收尾 S5-P01(事件/实体/关系)★**:T057 事件聚合+T058 实体解析+T059 关系。下一步 S5-P02 检索(T060 精确/T061 全文语义/T062 版本as-of API)。**NOT_DEPLOYED**,live build 仍 b189d3cc0703(==T040)。
