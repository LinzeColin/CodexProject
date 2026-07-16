# TASK_REPORT · ADP-S1-P03-T018｜实现 L0–L3 分层人话内容与 Evidence Locator

## 唯一目标（达成）
输出 15 秒、2 分钟、深度和原始证据四层，并区分事实/解释/推断 —— 交付 content contract、board prompts、claim locators、render payload。

## 六个开始前问题（已回答）
1. 唯一目标：实现 L0-L3 人话版契约 + 证据定位；中文 UI 无未解释大段英文；关键数字/日期/结果 100% 可定位证据。
2. 允许修改文件：`docs/pursuing_goal/v0_1/{schemas/content_contract.schema.json, tools/build_render_payload.py, BOARD_PROMPTS.md, render_payload_sample.json}` + 本证据包 + 治理同步。**复用 T016/T017 样本，不改 worker/D1**。
3. 绝不能改变：抓取行为、六主题、worker、D1（NOT_DEPLOYED，只读）。
4. 基线：main `80d9e11c`（T017 已合入）；样本 200 条 + factsheet；build_id `bd67a78020a3`。
5. 验收：中文 UI 无未解释大段英文；关键数字/日期/结果 100% 可定位证据。
6. 回滚：`git revert <sha>`（纯 schema/工具/样本，NOT_DEPLOYED）。

## Owner 决策
L2 深度层需模型生成，按 Owner 2026-07-16 指令**暂 provisional_pending_model**（未接模型不生成、不捧造）；L0/L1 为确定性事实层。

## 交付物
- `schemas/content_contract.schema.json` —— L0 15秒/L1 2分钟/L2 深度/L3 原始证据 四层 + claim(fact/interpretation/inference) + locator。
- `tools/build_render_payload.py` —— 确定性 render payload 生成器：L0/L1 中文事实层（每条挂 locator），英文原文只进 L3（显式标 原始证据），L2 provisional_pending_model。
- `BOARD_PROMPTS.md` —— 五板块 L2 深度层 prompt（区分事实/解释/推断，引用 locator，禁英文直出）。
- `render_payload_sample.json` —— 200 条 render payload 样例。

## 验收结果（实测，见 test-results/content_tests.txt）
- **中文 UI 无未解释大段英文**：L0/L1 大段英文块（除标题）= **0**；**英文摘要 leaking 进 L0/L1 = 0**（英文原文全部路由到显式标注的 L3 原始证据层）。（另有 1 例 title==summary 为**中文** board3 项，非英文，不违反。）
- **关键数字/日期/结果 100% 可定位证据**：L0/L1 全部 claim 有 locator（**1479/1479**）；关键事实（日期/DOI/关键数字/文号）**479/479 全部可定位**（True）。
- **四层 + 三类**：schema validate(200)=PASS；L0/L1 事实层、L2 深度 provisional、L3 原始证据；claim_type 区分 fact/interpretation/inference。
- **确定性**：重建字节一致（True）。

## Data / Performance / Visual
- Data：复用 T016/T017 样本（0 新 D1 读），产出 200 render payload。
- Performance/Visual：N/A（未碰 worker/UI；render payload 是给 UI 的数据契约，未接入渲染）。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：把 T017 的英文直出缺陷（113/200）在契约上根治——L0/L1 中文事实层、英文只进显式标注的 L3；关键数字/日期/结果 100% 挂证据 locator，事实/解释/推断分层；直接回应 FACT-002 与 v1.1「区分事实/解释/推断」。
- **Cost（逐项，未知不填 0）**：新增请求 0（复用样本）；D1 读写 0；R2 0；模型调用 0（L2 未生成，provisional）；人工维护 = 接模型生成 L2 时按 board prompts + Owner 复核。经常性云成本 0。

## Known gaps
见 known_gaps.md（L2 深度需模型、provisional 未生成；render payload 未接入 worker 渲染=后续部署任务；标题若英文仍显示为标题）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（未接入渲染）、`benchmarks`（before=T017 defect baseline）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。`data-samples`=render_payload_sample.json。

## 完成声明
```text
Task: ADP-S1-P03-T018
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: content_contract.schema.json + build_render_payload.py + BOARD_PROMPTS.md + render_payload_sample.json + 证据 + 治理同步（见 changed_files.txt）
Tests: content_tests.txt —— schema(200) PASS + L0/L1 英文摘要 leak=0 + 关键事实 479/479 定位 + 1479 claim 全有 locator + 确定性 True；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: L0-L3 content contract + render payload（中文事实层+英文只进标注 L3+100% locator）
Data/Performance/Visual: 复用样本（0 新 D1 读；render payload 未接渲染）
Value: 英文直出契约根治 + 事实 100% 可定位（FACT-002 / v1.1 事实-解释-推断）
Cost: 请求0 / D1 0 / R2 0 / 模型 0(L2 provisional)；经常性成本 0
Known gaps: 见 known_gaps.md（L2 需模型 provisional；未接渲染）
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯 schema/工具/样本）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
