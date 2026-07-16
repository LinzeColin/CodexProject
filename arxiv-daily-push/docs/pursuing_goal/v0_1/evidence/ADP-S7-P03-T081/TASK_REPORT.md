# TASK_REPORT · ADP-S7-P03-T081｜接入按主题/路由/设备分段的 RUM 与 CWV

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P03-T081（Stage S7 / S7-P03 RUM、CWV、动效与数据性能，size S）
- **release_mode**: NOT_DEPLOYED（改 worker 源 + 重算 BUILD `40a46aa2baee`→`8c19387c846b`，不部署；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S7-P02-T079；ADP-S7-P02-T080

## 6 个前置问题
1. **测什么？** — Core Web Vitals：LCP（largest-contentful-paint）、CLS（layout-shift，排除 hadRecentInput）、INP（用最大交互 event 时延近似，**如实标注为近似**）。
2. **怎么分段？** — 每个 metric 打标签 theme(data-theme)/route(pathname 归一)/device(视口宽度桶)/network(navigator.connection.effectiveType)，随页面隐藏 sendBeacon 到 /api/rum。
3. **怎么不破坏六主题视觉/动效？** — RUM 客户端在 **router 层**（htmlResp）注入，**不改 PAGE 壳/任何合同哈希**；detect_regression = **0 变化**（整份 asset_hashes 逐字节相同，master_visual 也不变）。
4. **怎么「无数据不声称达标」？** — 离线查询工具每个 segment/overall 评估都**门控于最小样本数（min_samples=30）**；不足即 `insufficient_data`（rating/meets_bar=None）；空/薄数据 `claims_any_compliance=False`。
5. **NOT_DEPLOYED？** — 改源 + 重算 build_id，不部署；live 不变；**无真实 RUM 数据**，故**不声称任何 CWV 达标**（真实 p75 基线需部署+采集真实流量）。
6. **成本/DIR-007？** — 端点写**新表 cn_rum**（不动既有生产数据）；部署后每次页面隐藏最多 3 beacon→3 D1 写；`RUM_SAMPLE` 采样杆可下调以守免费额度；当前 NOT_DEPLOYED 实际成本 0。

## 交付物
- **RUM 客户端**（`RUM_JS`）+ **注入**（htmlResp，`RUM_ENABLED` 门）+ **`rumIngest` 纯验证器** + **`/api/rum` 端点**（验证+采样→CREATE TABLE IF NOT EXISTS cn_rum→bind INSERT）。BUILD 自哈希重算。
- **查询工具** `tools/rum_cwv.py`：p75(nearest-rank)/rate(Google CWV 阈值)/query(单维)/query_multi(全维)/overall_baseline/claims_any_compliance，全部**门控最小样本**。
- **Node 测试** `test-results/rum_ingest_test.js`（真实抽取的 rumIngest）：坏 metric/越界值/非数值/null/薄采样全拒，合法打标签+净化。
- **浏览器证明** `browser_measurements.json`（内置 Chromium）：真实客户端捕获真 LCP(2128ms)+CLS+INP，按 theme/route/device/network 打标签，beacon 到 /api/rum。
- **pre_fix_worker.js/pre_fix_baseline.json**（T080 基线，合同不变性对照）、**rum_harness.html**、**独立对抗复核** adversarial_review.md。

## 验收（PASS，verifier 独立重算，exit 0）
证据：`test-results/rum_cwv_tests.txt`（ACCEPTANCE = PASS）。

1. **LCP/INP/CLS 可按主题/路由/设备/网络查询** — query 按 4 维分段+p75+rating；theme 分段判别（minimal=good/cosmos=poor）；query_multi 全维交叉；p75/阈值正确；**浏览器证真实客户端按 4 维打标签**。
2. **无数据不声称达标** — 空数据集与薄 segment（5<30）`claims_any_compliance=False`、`insufficient_data`；**负控制载重**（去掉门则空数据会假称达标）。
3. **写入安全** — rumIngest Node 测试全绿（坏/越界/超长/采样外全拒，D1 写仅在 ok 后 + bind 参数化）。
4. **现有高级视觉保持** — 整份合同**逐字节相同**（router 注入不碰任何 hashed 元素）。

## 实时未回归
NOT_DEPLOYED：改源+重算 build_id(8c19387c846b)，不部署。live `/build.json`=b189d3cc0703（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 0；R2 0；model 0；cloud 0（NOT_DEPLOYED）。**部署后**：每页隐藏 ≤3 beacon → ≤3 D1 写/页面访问，`RUM_SAMPLE` 可下调守 DIR-007 免费额度（须部署时按真实流量定采样）。只读 GET 1；in-app 渲染 1；Node 测试 1；人工=RUM 客户端+端点+验证器+查询工具+Node/浏览器测试+验证器+复核。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
