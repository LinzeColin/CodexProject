# Known gaps · ADP-S7-P03-T081｜接入按主题/路由/设备分段的 RUM 与 CWV

诚实披露**范围**、**近似**、**成本**与 NOT_DEPLOYED 语义。

## 实现与不破坏承诺
- **RUM 客户端在 router 层注入**（htmlResp，`RUM_ENABLED` 门）——**不改 PAGE 壳/主题/动效层的任何合同哈希**。经 T077/T078 验证 `detect_regression` = **0 变化**，整份 `asset_hashes` 逐字节相同（master_visual 也不变）。六主题视觉/动效**完全不受影响**。
- **端点写新表 cn_rum**（CREATE TABLE IF NOT EXISTS + bind 参数化 INSERT）——**不动既有生产数据**；rumIngest 验证/净化/采样后才写。

## 关键近似与如实标注
- **INP 用「最大交互 event 时延」近似**，非规范 INP（规范 INP 取交互时延的高分位、按交互数调整）。这是**刻意的轻量近似**（客户端零依赖、免 web-vitals 库），**如实标注为近似**（worker 注释 + 本文件 + tool 文档），**不冒称为真实 INP**。真实 INP 需引入 web-vitals 库或更复杂的交互聚合（可后续升级）。
- **CLS**：累加 layout-shift 且排除 `hadRecentInput`，**未实现规范的「会话窗口」分组**（规范取 5s 会话窗口内的最大簇）。对单页浏览的粗基线足够；升级同上。
- **LCP**：取 `renderTime||startTime` 最后一个 largest-contentful-paint 条目——标准做法。

## 无数据不声称达标（核心，载重）
- 查询工具每个 segment/overall 评估**门控最小样本数**（`DEFAULT_MIN_SAMPLES=30`）：不足即 `insufficient_data`（rating/meets_bar=None）。空/薄数据 `claims_any_compliance()=False`。**当前 NOT_DEPLOYED 无真实数据 → 不声称任何 CWV 达标**。真实 p75 基线须**部署 + 采集真实字段流量**后才产生（届时 30 样本门是「可报一个 p75」的下限，真实稳定 p75 通常需数百样本，可上调门）。

## 成本 / DIR-007（部署后）
- 部署后每次页面隐藏最多 **3 beacon → 3 D1 写/页面访问**。`RUM_SAMPLE`（[0,1]）采样杆可下调以守免费额度；`RUM_ENABLED=false` 全关（不注入客户端、端点 202 忽略）。**当前 NOT_DEPLOYED 实际成本 0**。部署时须按真实流量设采样，避免超 D1 免费额度（100k 写/日）。
- **无 wrangler 迁移文件**：cn_rum 用端点内 `CREATE TABLE IF NOT EXISTS` 惰性自建（幂等、安全）。若偏好显式迁移，可后续加 schema 文件。

## 边界 / 未做
- **无仪表盘 UI**：交付**离线查询工具 + p75 基线**（deliverable「dashboard」以工具形式交付，非页面）。若需页面级 CWV 仪表盘可后续加（会改 page 函数，非合同哈希）。
- **未部署逐真机 RUM**：客户端在 harness 真实采到 CWV，但线上真实字段数据须部署后累积。
- **NOT_DEPLOYED**：改源 + 重算 build_id(40a46aa2baee→8c19387c846b)，不部署；live 仍 b189d3cc0703。T077 基线不重冻（同 T079/T080）。
