# Known gaps · ADP-S5-P02-T060（精确/结构化检索）

目标：先达到专业用户的确定性检索收益。交付 exact index/structured filters/test corpus。**100 条精确标识第一结果命中率 100%；过滤结果与 SQL 基准一致。** 诚实边界：

1. **精确检索=O(1) 哈希索引**：build_index 建 doc_number/doi 唯一标识哈希 + agency/region/status facet 索引。exact_lookup 返回第一(且唯一)结果。**归一化**(trim + 全半角空格 + ASCII case-fold[DOI 不分大小写]),故格式微差不漏。
2. **100% 命中在 120 doc 测试语料**：120 doc 全 distinct docnum + distinct doc_id;100 精确标识第一结果全命中(rate 1.0);24 DOI 亦全命中;归一化(空格/大写 DOI)仍命中。
3. **过滤与 SQL 基准一致**：structured_filter(agency/region/status AND + [date_from,date_to] 区间)对 **in-memory sqlite3 等价 WHERE 基准**跑 30 查询(单 facet/组合/日期区间)**0 mismatch**;list== 有序精确比(ORDER BY doc_id),非 set-equal。日期 YYYY-MM-DD 零填充→字典序==时序,与 sqlite 字符串比一致。
4. **测试语料为确定性生成**：真实形态文号(苏政办函〔YYYY〕N号/鲁科字/京科发/国办发/发改)+ 5 机构/地域 + 2016-2026 日期 + 3 状态;真实全域检索随抓取语料扩。全文与语义重排是 T061(仅精确/结构化不足时才引入),版本/as-of 检索 API 是 T062。
5. **NOT_DEPLOYED**：index+filters+corpus 库,未接 worker/生产。live build 仍 b189d3cc0703(==T040)。
