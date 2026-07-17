# ADP V0.2 生产集成 · P01 — 关键事实 Factsheet 芯片（PRODUCTION DEPLOY）

## 背景（诚实）
ADP V0.1 任务包（T009–T090）把认知系统的绝大多数能力建成了独立工具 + 证据包，**全部 NOT_DEPLOYED**——0 个接进线上 worker。线上产品 ≈ T040 时代 MVP + S7 视觉打磨。Owner 观察到"网页没有明显变化"完全正确。V0.2 集成程序把这些已建能力**分批集成进线上 worker 并真实部署**，每批可见、可验证、可回滚，绝不弄坏线上 MVP。本任务是 V0.2 第 1 个可见增量。

## 做了什么
把 S1-P03-T016 的 `extract_factsheet.py`（确定性事实抽取）**忠实移植进 `deploy/cloudflare/worker_cloud.js`**：新增 `factsheet(item)` + `factsheetHTML(item)`，从条目已有字段（title/url/summary/categories/authors/published_at）确定性抽取 **DOI / 文号 / 关键数字 / 作者数**，渲染成六主题自适应的 `.badge` 芯片；铺在**今天卡（首屏）、板块列表、搜索、雷达、条目详情**（复用共享的 `itemListHTML` 一处覆盖 board/search/radar）。

- **纯展示层**：只读现有 `cn_items` 字段，不新增表、不改每日流水线、不改 hero/动效/主题（T077/T078 视觉动效契约明确「page body 不在冻结范围」）。
- **不臆造**：抽不到的字段不显示（`缺失即空`，忠实于 extract_factsheet.py 的 `null` 语义）。
- 日期在各卡片元信息行已展示，展示层去重（`factsheet()` 仍保留 date 以忠实 schema）。

## 独立对抗复核抓到的真实缺陷（已修）
复核者 BLOCK：`FS_UNIT_RE = /\d[\d,.]*\s*(?:unit)/g` 是 **O(n²) ReDoS**——长数字/逗号串无尾随单位时二次回溯，40KB 恶意输入实测 **2295ms**，跑在请求路径上会打爆 Cloudflare Worker CPU（board4 金融内容天然有逗号分组长数字）。
**修复（双重）**：(1) 有界量词 `\d[\d,.]{0,39}`（数字 token 永不超 40 字符）→ 全扫描线性时间，与输入/条目数无关；(2) `factsheet()` 内 `title.slice(0,500)/summary.slice(0,2000)` 输入兜底。复核者复验：40KB→4.8ms、400KB→48.8ms（正好 10× = 线性证明）、加 slice 后 0.24ms；真实数字/单位抽取不受影响。终判 **CONFIRMED_SOUND**。

## 部署与验证（真实上线）
- BUILD 自排除哈希：`452f7c5de919 -> 0864030f7dc8`（build_id == source_sha256[:12]）。
- 部署 `adp-cloud` version `f26dc86a-446f-445b-b1ab-d2c132b1cf46`；DB(adp-mirror)/R2(adp-raw-artifacts) 绑定与 cron `30 20 * * *` 均保留。
- 实时验证（test-results/deploy_verify.txt，PASS）：build.json == 0864030f7dc8；7 路由全 200；**六主题 6/6**；factsheet 芯片实时可见 board1=60 / board2=4 / board3=7 / board4=1（真实数据渲染）。
- **回滚目标**：`wrangler versions deploy 5a7c0fbe-8299-4eaa-8b60-940286a67ebc`（即 452f7c5de919）。

## 验收
- test-results/factsheet_tests.txt：ACCEPTANCE = PASS —— 忠实移植 + 4 个 load-bearing 负控制（不臆造）+ ReDoS-safe。
- 未自签；独立复核 CONFIRMED_SOUND（adversarial_review.md）。

release_mode: **PRODUCTION**（live 0864030f7dc8）。Ends IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION.
