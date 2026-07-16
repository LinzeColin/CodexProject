# Known gaps · ADP-S5-P01-T058（跨来源实体解析）

目标：统一机关/机构/作者/公司/地区/主题/标准。交付 entity schema/aliases/provenance/merge-split audit。**错误合并可撤销；实体来源和置信边界可追溯。** 诚实边界：

1. **合并靠共享 alias（精确）非模糊**：resolve 按共享 alias 聚类;真实机关别名(国家统计局≡统计局≡NBS;国务院办公厅≡国办;发改委≡NDRC)。**无共享 alias 的不同机关保持独立**(防误并)。真实抓取的 alias 由抽取(全称/简称/英文/变体)填 aliases。
2. **错误合并可撤销（精确）**：merge 存 `before` **deepcopy 快照** + audit;split 从快照**逐字节还原**两个 pre-merge 实体(restored[a]==ents[a] and restored[b]==ents[b])。任意误并可撤。
3. **置信边界**：AUTO_MERGE_MIN=0.80;confidence<0.80 的合并**不自动应用→pending_review**(实体不变);≥0.80 才 applied。防弱信号静默过并。
4. **provenance 逐 alias**：每个 alias 记 source_id;provenance_of 覆盖全 aliases,无 unsourced。多源别名(NBS 来自 media-x + stats-gov)可追溯来源边界。
5. **当前 alias 集为 curated 示例**：真实全域实体图随抓取积累;merge 置信度真实计算(名称/上下文相似)后续增强;本任务先立 schema+可撤销 audit+置信边界+provenance。跨板块 Evidence Relation 是 T059。
6. **NOT_DEPLOYED**：resolver 库,未接 worker/生产。live build 仍 b189d3cc0703(==T040)。
