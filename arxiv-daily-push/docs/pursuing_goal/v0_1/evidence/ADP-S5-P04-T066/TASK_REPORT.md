# TASK_REPORT · ADP-S5-P04-T066｜实现 Watchlist 与 Change-only Digest

## 唯一目标（达成）
持续监测主题/机构/地区/实体/文号，**只推送实质变化**：重跑不重复通知、无变化不打扰、每条变化可定位。交付 rules、dedup notifications、daily/weekly digest、source silence signal。release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：Watchlist（5 facet 规则）+ Change-only Digest（实质变化=T026 content_hash）+ dedup（重跑不重复）+ silence signal；无变化不打扰、每条可定位。
2. **允许修改文件**：`tools/watchlist_digest.py`（新）+ `evidence/ADP-S5-P04-T066/*` + 治理同步。**不改 worker/生产/registry/VERSION**。复用 T026 `version_engine.content_hash`。
3. **绝不能改变**：生产 worker/cron/数据/实时；六主题/MVP；NOT_DEPLOYED。库层只读、period 由调用方传入（不读时钟）。
4. **基线**：main `00b3f253`（T065 已合入）；两周期 Golden 场景（含 noise-only 再渲染、真变、新条目、无关条目）。
5. **验收**：重跑不重复（stateful rerun 0；stateless 非平凡 re-emit 负控制）；无变化不打扰（noise-only 同 content_hash→抑制、真变异 hash 不同→触发）；每条变化可定位（locator 解析到真实变更条目）。
6. **回滚**：`git revert <sha>`（只读库，生产未变更）。

## 交付物
- `tools/watchlist_digest.py` —— `make_watch/matches`（facet ∈ {topic,agency,region,entity,doc_number} 精确匹配，entity/topic 支持多值）+ `run_digest`（实质变化由 **T026 content_hash**[body/attachments/status，噪声不敏感] 判；通知键=(watch_id,canonical_id,content_hash)，`state.seen` 去重；**不原地改调用方 state**，返回新 state）+ silence signal（被监测源本周期无变化）+ daily/weekly digest（by_watch 聚合）+ `notification_is_locatable`。
- `evidence/…/build_watchlist_digest.py`（day1 基线 + day2：noise-only 再渲染/真新版本/新条目/无关条目；rerun 场景）+ `watchlist_digest_report.json` + `test-results/{t066_verify.py, watchlist_digest_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/watchlist_digest_tests.txt，ACCEPTANCE = PASS，exit 0）
- **① 重跑不重复通知**：day2 出 4 通知（doc-2 新版本×2 watch + doc-3 新条目×2 watch）；**携 state 重跑 day2 → 0 新通知**。**负控制（判别力）**：**无记忆的 stateless digest 对同 day2 re-emit 6**（含 doc-1）→ 证明去重非平凡真起作用。
- **② 无变化不打扰**：day2 的 doc-1 是**纯 noise-only 再渲染**（正文+页脚/版权噪声）→ **content_hash 与 day1 相等（实测 True）→ 不通知**；而 doc-2 真变异 → **content_hash 不同（实测 True）→ 通知**（判别）；**再喂未变语料（day1 again）→ 0 新通知**。
- **③ 每条变化可定位**：8 条通知全带 `locator{canonical_id,content_hash,matched_facet,matched_value}`，且 `notification_is_locatable` 解析到**真实变更条目且当前 hash 相符**。
- **source silence signal**：W5（entity=国家统计局，无匹配）两周期均**发静默信号**；有变化的 watch 不发。
- **不原地改 state**：run_digest 返回新 state，调用方 state.seen 不被改。
- **实时无回归**：NOT_DEPLOYED，无部署 → live `build_id=b189d3cc0703`（==T040）。

## Data / Performance / Visual
Data = 5 watch 规则 + 两周期 6 条目（noise/真变/新/无关）。Performance = 实时无回归。无 UI 改动；六主题保留（digest 为库层，供通知/Digest 视图消费）。

## Value / Cost（S5 多板块深度）
- **Value**：**只推实质变化的持续监测**——重跑幂等不刷屏、无变化不打扰、每条变化可回溯到源条目与版本、源静默亦成信号；对齐竞品 Watchlist/Change-only Digest 收益，复用 T026 单一"实质变化"定义不另立标准。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = 规则/去重/digest + Golden + 验证编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：实质变化=T026 content_hash（body/attachments/status，含状态与附件变更；**排除纯 facet/日期元数据重分类**，与"只推实质变化"一致，单一事实源不分叉）；state 持久化由部署阶段提供（本任务用内存 state 证明幂等）；daily/weekly 由 period 参数区分（不读时钟）。

## 不适用证据项
`migration.sql/rollback.sql`（无 schema）、`screenshots-or-videos`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，库层）。`data-samples` = watchlist_digest_report.json。`benchmarks` = N/A。

## 完成声明
```text
Task: ADP-S5-P04-T066
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/watchlist_digest.py(新) + T066 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: watchlist_digest_tests.txt —— 重跑0新(stateless re-emit 6判别);noise-only同hash抑制+真变异不同hash触发+未变语料0新;8通知全可定位到真实变更条目;W5静默信号;不原地改state;实时无回归(build_id b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: Watchlist规则 + Change-only Digest(T026实质变化) + dedup + silence signal
Data/Performance/Visual: Data=5规则+两周期6条目；Perf=实时无回归；Visual=六主题保留
Value: 只推实质变化,重跑幂等不刷屏,无变化不打扰,每条可定位,源静默成信号
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（只读库；生产未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
