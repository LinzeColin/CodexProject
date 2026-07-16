# TASK_REPORT · ADP-S1-P03-T019｜实现确定性 QA、单次重试与 Factsheet 回退

## 唯一目标（达成）
生成失败时宁可少讲，也不发布模板垃圾 —— 交付 language/empty/duplicate/unsupported/template checks、quarantine/fallback。

## 六个开始前问题（已回答）
1. 唯一目标：确定性内容 QA + 最多一次重试 + 回退到事实卡/原文，绝不发模板垃圾。
2. 允许修改文件：`docs/pursuing_goal/v0_1/tools/content_qa.py` + 本证据包 + 治理同步。**复用 T018 render payload，不改 worker/D1**。
3. 绝不能改变：抓取行为、六主题、worker、D1（NOT_DEPLOYED）。
4. 基线：main `0a717623`（T018 已合入）；输入 = render_payload_sample.json；L2 provisional。
5. 验收：注入模型超时/重复/缺字段时最多重试一次，之后只发事实卡/原文。
6. 回滚：`git revert <sha>`（纯工具，NOT_DEPLOYED）。

## 交付物
- `tools/content_qa.py` —— 5 类 QA 检查（language 无大段英文 / empty / duplicate / unsupported 无 locator / template 套话）+ `publish()`（≤1 次重试）+ `fallback()`（隔离 L2，只发事实卡 L0/L1 + 原文 L3）。

## 验收结果（实测，见 test-results/qa_tests.txt）
- **timeout**：注入模型超时（每次 raise）→ 最多 2 次尝试（初始+1 重试）→ 回退 `quarantined_fallback`（publish_mode=fact_card_and_raw_only）。**PASS**。
- **template_garbage（缺字段/套话）**：生成「暂无」→ QA template 拦 → 回退只发事实卡/原文。**PASS**。
- **duplicate**：L2 与他项重复 → QA duplicate 拦 → 回退。**PASS**。
- **good_generation**：合法生成 → 全量发布（full_l0_l3），**1 次尝试**、不回退。**PASS**。
- **baseline_qa**：baseline payload（L2 provisional）QA 无 unsupported。**PASS**。
- 总 **RESULT: PASS**（5/5）。

## Data / Performance / Visual
N/A —— 纯 QA/回退逻辑，无数据/性能/UI；未碰 worker/D1。

## Value / Cost（S1 = Truth & Content Stabilization）
- **Value（S1 指标）**：内容质量门到位——生成失败/重复/套话时最多重试一次，然后**宁可少讲**（回退事实卡 L0/L1 + 原文 L3），绝不发模板垃圾；把「英文直出/模板」缺陷在发布路径上封死。
- **Cost（逐项，未知不填 0）**：新增请求 0；D1 0；R2 0；模型调用 = 由 publish() 控制，最多 2 次/条（初始+1 重试），失败不重复烧钱；人工维护 = 接模型时 generate 回调接上。经常性云成本 0。

## Known gaps
见 known_gaps.md（QA 判据 provisional；未接入 worker 发布路径=后续部署任务）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`（无 UI）、`benchmarks`、`data-samples`（复用 T018）、`deployment_manifest.preview.json`(T009覆盖) —— N/A。

## 完成声明
```text
Task: ADP-S1-P03-T019
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: content_qa.py + 证据 + 治理同步（见 changed_files.txt）
Tests: qa_tests.txt —— timeout/template/duplicate/good/baseline 5/5 PASS（超时/重复/缺字段最多重试1次后回退事实卡/原文）；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: content QA + ≤1 retry + factsheet fallback（宁可少讲不发模板垃圾）
Data/Performance/Visual: N/A
Value: 内容质量门（失败回退事实卡/原文，封死模板垃圾）
Cost: 请求0 / D1 0 / R2 0 / 模型≤2次/条(由publish控制)；经常性成本 0
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED
Rollback: git revert <sha>（纯工具）
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
