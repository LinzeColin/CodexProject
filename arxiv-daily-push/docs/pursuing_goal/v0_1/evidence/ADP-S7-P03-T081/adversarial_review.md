# 独立对抗复核 · ADP-S7-P03-T081｜接入按主题/路由/设备分段的 RUM 与 CWV

实现者**不自签 PASS**。由独立 skeptic Agent（`general-purpose`，不共享推理）对抗复核，目标**证伪**验收。

## 结论：CONFIRMED_SOUND

复核 Agent 独立重算全部六向量，无法证伪验收：

- **(a) 无数据不声称达标（核心）— SOUND**。`_assess` 门控 `min_samples` 且是 `meets_bar` 的唯一来源；三入口（overall_baseline/query/query_multi）默认 30 且转发。**最激进旁路** `overall_baseline([], min_samples=0)` → 每 metric `meets_bar=False`（空 p75=None→rating None→`None=="good"`=False）：**空数据无条件不声称**，即便门被强设为 0。`claims_any_compliance` 真遍历 list+嵌套 dict，只计 `status=="ok"` 节点，薄/insufficient 段无法泄漏声明。唯一得 True 的方式=调用方显式传 `min_samples=0` 且 ≥1 good 样本——**任何验收路径不可达**（默认 30），是文档化调参杆非旁路。
- **(b) 可查询性 — SOUND**。p75 nearest-rank 正确（p75(1..100)=75）；4 维各自可 query（每次重新分桶）；分段判别（minimal=good/cosmos=poor）；query_multi 交叉可用。
- **(c) RUM 客户端 — SOUND**。外层 try/catch + 每 observer/每 send try/catch；PerformanceObserver 缺失早返回；**不改 DOM/样式（render-inert）**，页面不会被弄白；`sent[m]` 守卫→每页最多 3 beacon（即便 visibilitychange 与 pagehide 都调 flush）；sendBeacon 缺失 try/catch 静默安全。INP=最大交互时延**如实标注为近似**。CLS=累加（排除 hadRecentInput）非规范会话窗最大——**方向是高估（保守）**，故不会假称 good，对本条款安全。
- **(d) 写入安全 — SOUND**。rumIngest：payload 对象→metric 白名单→有限值在量程→采样门→theme/device 白名单或 other→route/network slice+字符白名单。D1 写仅在 `res.ok` 后；INSERT 用 `.bind()` 参数（无注入）；`request.json()` 包裹（坏 JSON→null→422）。422(坏 payload/metric/value) vs 202(采样外/关) 合理。**Node 测试里的 rumIngest 与 worker 逐字节相同**（复核 diff 了函数体）→ 测的是真码。
- **(e) 视觉合同 / NOT_DEPLOYED — SOUND**。pre_fix_worker.js 与 origin/main 逐字节同；worker diff = BUILD 行 + RUM 块 + htmlResp 包裹，别无他物；`detect_regression` = **0 变化**，18 个 hashed 面（page_shell/hero_*/per_theme/theme_js/options/keyframes/fx_*/dom_producers/master_visual…）全同。**证检查非空洞**：改一处 data-theme 即触发 theme:techno/master_visual/hero_css/contract_root。BUILD 自哈希从零重算 = `8c19387c846b`。live `b189d3cc0703` ≠ 新 build → NOT_DEPLOYED 成立。cn_rum 惰性 CREATE TABLE IF NOT EXISTS（幂等安全）。t081_verify（PASS exit 0）+ rum_ingest_test（PASS exit 0）在真文件上过。
- **(f) 成本/DIR-007 — SOUND**。RUM_SAMPLE 杆在码内披露；每页 ≤3 beacon→≤3 INSERT 诚实随设计而来；「无真实基线」准确（NOT_DEPLOYED⇒无字段数据，工具拒绝任何无数据达标声明）。T081 证据中无任何过早「达标」声明。

## 复核的两点精确澄清（非 hole，已采纳）
1. **「逐字节相同」是指合同哈希**：服务出的 HTML **不**逐字节相同（`</body>` 前追加了一个 render-inert `<script>`），但**每个 hashed 视觉/动效面不变**、脚本不改 DOM/样式，故**渲染出的视觉/动效身份保持**。措辞已在 known_gaps/report 中按此理解（"整份 asset_hashes 逐字节相同"，指哈希）。`String.replace('</body>', …)` 注入安全：RUM_JS 不含 `$`/`</script`/`</body`/`${`。
2. **CLS 保守**：累加高估，方向安全（不会假称 good）。规范会话窗升级留待后续（同 INP 近似）。

## 底线
验收（1）LCP/INP/CLS 可按主题/路由/设备/网络查询（2）无数据不声称达标，均由**门控查询工具 + 真实抽取码 Node 测试 + 内置浏览器真 CWV 采集 + 合同不变性(0 变化)独立重算**证明；build 自哈希与 NOT_DEPLOYED 诚实；INP 近似与成本如实披露。

**VERDICT: CONFIRMED_SOUND**（复核原文），实现者据此提交。
