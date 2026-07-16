# TASK_REPORT · ADP-S4-P02-T048｜完成 A0 历史附件、修订和效力 QA Gate

## 唯一目标（达成）
验证历史**不只是有 URL**，而是**有原文、附件、版本和状态**。交付 A0 acceptance pack、random readback、status/version samples。**100 个附件可读；修订链和 as-of 样本正确；0 个未解释 P0 缺口。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：A0 历史 QA Gate——可读附件≥100、修订链正确、as-of 正确、0 未解释 P0 缺口。
2. **允许修改文件**：`tools/a0_qa_gate.py`（新）+ `docs/pursuing_goal/v0_1/evidence/ADP-S4-P02-T048/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——QA gate 只读校验；附件 readback 走**开发环境**实抓。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `1f1e231d`（T047 Wave 2 已合入）；语料=Wave 1(T046,7)+Wave 2(T047,11)=18 真实 A0 原文；用 T026 版本引擎 + T043 gap detector。
5. **验收**：100 附件可读；修订链和 as-of 样本正确；0 未解释 P0 缺口。
6. **回滚**：`git revert <sha>`（QA gate 只读，生产未变更；无既有生产数据改写）。

## 交付物
- `tools/a0_qa_gate.py` —— 四道确定性 gate（attachment / revision / as-of / gap）。
- `evidence/…/a0_acceptance_pack.json` —— A0 acceptance pack（四 gate 结果 + 成本）。
- `evidence/…/attachment_readback.json` —— **115 真实可读附件**逐条 readback（http_status/bytes/sha256/magic）。
- `evidence/…/{discover_attachments.py, topup_attachments.py}` —— dev-env 实抓驱动（可复现）。
- `evidence/…/test-results/{t048_verify.py, qa_gate_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/qa_gate_tests.txt，ACCEPTANCE = PASS，exit 0）
- **100 个附件可读**：**115 个真实附件可读、115 个 distinct sha256**（≥100）。readable 判定=HTTP 200 + bytes>64 + 识别 magic（PK/PDF/OLE，非 HTML 错误页）+ 真实 64-hex sha256。类型：zip/ooxml 83、ole/msoffice 31、pdf 1。源：stats-gov 113 + gov.cn 2。**走 dev-env 实抓 → 0 云成本**。
- **修订链样本正确**：5/5 正确——①幂等重观测**不产生幻版**（3×→1 版，replay 稳定）②模板/导航噪声**不产生版本**（strip_noise 剥离）③真实正文实质改版→**恰 1 新版**+distinct content_hash+version_no=2 ④效力状态 现行有效→已废止→**恰 1 新版** ⑤附件 sha 变更→**恰 1 新版**。用真实官方正文作 v1 + 受控真实形态编辑作 v2，验证 T026 引擎决策。
- **as-of 样本正确**：15 条链（含乱序插入 / 3–5 版 / 边界日期对抗 fixture）× 33 查询日 = **495 样本，未来版本泄漏 0，与独立 oracle 0 分歧**；**用解析日期比较（非字符串）**；顺序 spot-check 正确。**非同义反复**：故意写错的 resolver **被泄漏检查抓到**（control_catches_broken）、畸形 observed_at **被拒绝**（malformed_rejected）。
- **0 个未解释 P0 缺口**：**全 2016+ 窗口网格 140 格（4 源×35 月）** 经 T043 gap detector 分类。重构为对**已尝试（attempted）单元**判定：attempted=9（产出文档 7 + 真实 T047 尝试失败源 ndrc/cac 2）；**silent_holes=0**（无已尝试单元被静默丢弃）；**真实 ndrc/cac 尝试失败被 surface 为 fetch_failed（2/2，可达真实信号，非不可达 ghost）**；**silent-hole 检测器在真实变异上触发（control_detects_silent_hole=True）**；unexplained=0。**诚实范围**：检测「源确实发布但回填静默漏掉」需地面真值发布索引 → 明确**推迟到 T056 Coverage Debt**，本 gate 不冒充能测。经 4-skeptic 对抗复核两轮 + gap 单独复核，四 gate 全 CONFIRMED_SOUND。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040），today 200。

## Data / Performance / Visual
Data = 115 真实可读附件 + 18 文档语料 + 修订/as-of/gap 样本。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 2016+ Expansion）
- **Value**：**A0 历史质量门**——证明回填历史不是「会 404 的 URL」，而是可读附件 + 正确版本 + 正确 as-of + 0 未解释缺口；为 T056 as-of 底座与 T049–T051 省市扩展提供可信语料基线。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = dev-env 附件 readback + gate 编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：附件类型集中在 stats .xlsx（多样性随 T049–T051 增）；修订/as-of 用真实正文 + 受控多观测（天然「同文多版」待 T056）；gap 网格为当前 A0-central 语料；dev-env 读取生产未触。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，无 schema/UI/部署变更）。`data-samples` = attachment_readback.json + a0_acceptance_pack.json。

## 完成声明
```text
Task: ADP-S4-P02-T048
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/a0_qa_gate.py(新) + T048 证据包 + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: qa_gate_tests.txt —— 四 gate 全过：附件115可读/115 distinct(≥100,magic白名单)；修订链5/5正确；as-of 495样本0未来泄漏/0 oracle分歧/control抓到broken/拒畸形日期;gap 140格 attempted=9 silent_holes=0 fetch_failed_surfaced=2/2(真实ndrc/cac) control_detects_silent_hole=True unexplained=0(真值完整性推迟T056)；实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)。经 4-skeptic 对抗复核两轮+gap单独复核，as-of/gap 两处同义反复/空洞洞已加固并全 CONFIRMED_SOUND；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A0 历史 QA Gate(可读附件+修订链+as-of+0未解释缺口)
Data/Performance/Visual: Data=115可读附件+样本；Perf=实时无回归；Visual=六主题保留
Value: 证明回填历史真实可读可版本可as-of，为T056/T049-T051提供可信基线
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED,dev-env)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（QA gate；生产 worker/cron/数据未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
