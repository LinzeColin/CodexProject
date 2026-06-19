# 05 - Data Sources, Cadence and Provenance

## 1. Source priority

1. 监管、法律和政府原始数据；
2. 公司或交易对手官方披露；
3. 有许可的商业数据库；
4. 专业新闻/调查报道作为线索；
5. 基于有引用输入的系统推导。

完整 34 类来源见 `data/source_registry_extended.csv` 和 `docs/12_RESEARCH_UNIVERSE_SOURCE_METRICS_SCREENING.md`。

## 2. MVP automated sources

- SEC Submissions/filing metadata；
- SEC Company Facts/XBRL；
- captured official fixtures。

Phase 1.5/2 可接入 USAspending、GLEIF、LDA、USPTO、FTC/DOJ、EIA、IRS、FFIEC/FDIC 等。付费来源不得成为开源 MVP 正确性的硬依赖。

## 3. Supply-chain evidence sources

优先顺序：

- 10-K/10-Q/S-1 中的供应商、客户、采购义务和风险；
- 重大合同附件和官方合作公告；
- 政府采购、补贴、许可、出口/贸易文件；
- 设施、能源、电网、环境和地方政府记录；
- 专利、标准和许可资料；
- 对手方官方披露；
- 高质量二手报道仅进入 research queue，除非交叉核验。

不得用行业常识生成 reported 供应链边。

## 4. SEC connector requirements

- 官方域名 allowlist；
- 描述性 User-Agent；
- 客户端安全上限 <=8 req/s；
- timeout、有限重试、指数退避+jitter、cache、hash；
- 保存 accession、form、filing date、report date、accepted time、document；
- fixture/dry-run/idempotent upsert；
- CI 不依赖 live source。

## 5. Provenance

每个 source document 保存：source、external ID、URL、title、publisher、document date、observed/retrieved、content hash、media type、raw snapshot URI、parser version。

每个 evidence 保存：role、locator、structured fact、support excerpt/hash、review status、derivation metadata。

## 6. Freshness and lag

同时显示：

- connector last attempt/success/failure；
- latest document date；
- latest report period；
- expected cadence；
- typical disclosure lag；
- stale threshold；
- last verified。

“今天抓取成功”不代表事实是今天发生。

## 7. Conflict handling

- 不静默覆盖；
- 建 conflict record；
- amendment 可 supersede 旧值但保留历史；
- evidence drawer 显示分歧；
- 控制权、金额、供应链材料性和关键评分输入冲突进入人工复核。

## 8. Ingestion contract

```text
fetch -> snapshot -> normalize -> validate -> resolve -> upsert -> derive -> score -> diff -> report
```

只有 successful transaction 才发布新事实和分数。失败不 partial publish；相同 snapshot 和 profile 重跑幂等。
