# Source Registry · 迁移遗留例外清单（ADP-S1-P02-T013）

> 从线上真身（`worker_cloud.js` 的 `REGISTRY` 数组，33 源）迁入统一 Registry。**不改抓取行为**：迁移前后 source_id 集合与每板块成员完全一致（benchmarks/before==after）。
> 权威真相 = **worker REGISTRY**（实际运行者）；`config/boards_v0_3.yaml` 与之不一致处按下表登记为例外，不在本任务修复。

## EXC-1 · board3「官方」标签与媒体实体不符（DRIFT-FACT-006 / FACT-003）
- worker board3（中国政策法规）现有 4 源：`people-politics`、`people-finance`（人民网）、`chinanews-scroll`（中国新闻网）、`sina-china-focus`（新浪），platform 标注「官方 RSS」。
- **Registry 裁决**：按 T012 schema 与 DIR-002，这四者是**党媒/商业媒体**，非 A0/A1/A2 政府官方源 → `authority_kind: media`、`official_evidence: false`。
- **缺口**：board3 尚无真正的中国 A0/A1/A2 政府官方源（国务院/部委/省级/重点城市）。补齐属后续来源真相任务（S1-P02 之后 / S2），非本迁移任务。

## EXC-2 · config ↔ worker board3 来源不一致（DRIFT-FACT-006）
- `config/boards_v0_3.yaml` board3 定义的是 Google News 按部委聚合 + RSSHub 路由（均 official:false）；worker 实际跑的是 EXC-1 的四家媒体。
- **Registry 裁决**：以 **worker（线上真身）** 为准迁移；config 的 board3 定义与线上不符，登记为待对齐（后续把 config 对齐到 Registry，或反之，由来源真相任务决定）。

## EXC-3 · 聚合/发现源（非官方证据）
- `gnews-us-tech`（board4，Google News 聚合）→ `authority_kind: aggregator`、`official_evidence: false`（discovery，非官方证据）。

## 非例外（干净迁移）
- board1 预印本 3（arxiv-all/biorxiv/medrxiv）→ `preprint`, official_evidence=true。
- board2 顶级期刊 17（nature… ieee-spectrum）→ `journal`, official_evidence=true。
- board4 美国官方 8（fed-*/sec-*/ftc-press/nist-news/whitehouse-actions）→ `intl_official`, official_evidence=true。

## 汇总
- 迁入 33 源；official_evidence=true 28（预印本3+期刊17+美国官方8），=false 5（board3 媒体4 + gnews聚合1）。
- 每个线上 source_id 在 Registry 唯一；迁移前后 fixture 一致。
