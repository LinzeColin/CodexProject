# TASK_REPORT · ADP-S4-P03-T049｜省级政府门户通用 Adapter Family (A1)

## 唯一目标（达成）
**用少量模板族覆盖 A1**，而不是为每省复制一套业务代码。交付 adapter family、site profiles、override hooks、fixtures。**至少 3 种不同省级站点模板通过；特殊逻辑限制在 profile。** release_mode=NOT_DEPLOYED。

## 六个开始前问题（已回答）
1. **唯一目标**：省级门户通用 adapter family——一套类 + 声明式 profile 覆盖 ≥3 省级站点，特殊逻辑只在 profile/hook。
2. **允许修改文件**：`tools/adapter_a1_province.py`（新）+ `evidence/ADP-S4-P03-T049/*` + 治理同步。**不改 worker/生产**。
3. **绝不能改变**：生产 worker/cron/数据/实时——family 只读解析；fixtures 从 dev-env 实抓。六主题/MVP 不变。NOT_DEPLOYED。
4. **基线**：main `06d55e96`（T048 已合入）；复用 T031 OfficialConnector 接口 + T033 verify_identity(A1)。
5. **验收**：≥3 省级站点模板通过；特殊逻辑限制在 profile。
6. **回滚**：`git revert <sha>`（family 只读，生产未变更）。

## 交付物
- `tools/adapter_a1_province.py` —— **一套 A1ProvinceConnector 类**（零省份条件分支）+ 声明式 `SiteProfile` + 命名 override hooks（`TITLE_HOOKS`）+ `PROFILES`（3 省）+ `run_contract`。
- `evidence/…/fixtures/` —— **6 个真实捕获 HTML**（江苏/山东/北京各 list+article）。
- `evidence/…/contract_report.json` —— 三省 contract 结果。
- `evidence/…/test-results/{t049_verify.py, family_tests.txt, realtime_check.txt}`。

## 验收结果（实测，见 test-results/family_tests.txt，ACCEPTANCE = PASS，exit 0）
- **≥3 省级站点模板通过**：**3/3 通过**（江苏 discover 75、山东 45、北京 999），每省 discover≥1 → verify A1 → normalize（标题清洗 + 省份文号 + 日期）。
- **≥2 模板族**（证明是 family 非一次性）：`art-cms`（江苏+山东，URL `/art/Y/M/D/art_col_id.html`，钩子 `strip_leading_labels`）+ `beijing-zhengce`（北京，URL `./YYYYMM/tYYYYMMDD_id.html`，钩子 `before_underscore`）。**江苏+山东共享 art-cms 族正是「少模板族覆盖多省」的要点**。
- **特殊逻辑限制在 profile**：A1ProvinceConnector 类体**省份字面量 = NONE**（江苏/山东/北京/苏政/鲁科/京科/族名皆不在类体）——全部差异在 `PROFILES`（声明式）+ 命名钩子（省份无关、参数化）。
- **A1 身份正确**：verify_identity 要求 官方 .gov.cn 域 + marker + 非中央 → A1；3 省皆 official_domain=True、A1、非中央。
- **真实解析（含 doc_date 正确性三重交叉校验）**：江苏 苏政办函〔2026〕39号/**2026-07-14**；山东 鲁科字〔2023〕143号/**2026-07-09**；北京 京科发〔2026〕10号/**2026-07-14**/3 附件；标题经钩子清洗（去「省 栏目」前缀 / 去「_政策文件_首都之窗」后缀）。**doc_date 取文档发布日期（pubdate meta），非页面渲染时间戳（Maketime meta）**；三重交叉校验：≠Maketime、art-cms 与 URL 路径日期一致、与 pubdate meta 一致。
- **对抗复核（skeptic）发现并修复真实缺陷**：首版 `date_re` 取页面首个日期串 = `<meta Maketime>` 渲染时间戳而非文档日期（山东误报 2026-07-16 应为 2026-07-09、江苏误报 2026-07-15 应为 2026-07-14）。已改 `_extract_date`（剥离 Maketime → 优先 pubdate meta → 回退 发布/成文 label），并加 3 个交叉校验（会捕获该 bug）；复审确认 CONFIRMED_SOUND。见 `adversarial_review.md`。
- **实时无回归**：NOT_DEPLOYED，无部署 → live build 仍 b189d3cc0703（==T040）。

## Data / Performance / Visual
Data = 6 真实省级门户 HTML fixtures + 3 省 contract 结果。Performance = 实时无回归。无 UI 改动；六主题保留。

## Value / Cost（S4 A1 Expansion）
- **Value**：**A1 省级通用适配器族**——一套类 + profile 覆盖多省，新增省 = 加 profile 非加代码；为 T050（分批省级回填）提供可扩展底座。
- **Cost（逐项，未知不填 0）**：生产请求 0；D1 读 0/写 0；R2 字节 0/操作 0；模型 0；人工维护 = dev-env fixture 捕获 + family/profile/hook 编写。经常性云成本 delta = $0/月（NOT_DEPLOYED）。

## Known gaps
见 `known_gaps.md`：3 站点/2 族（共享族是要点）；stdlib server-rendered 范围（JS/TLS 门户需 headless fetcher，未来）；A1 身份靠 profile curated 断言（省域可核）；body_text 正文抽取后续；NOT_DEPLOYED，T050 下游执行。

## 不适用证据项
`migration.sql/rollback.sql`、`screenshots-or-videos`、`benchmarks`、`deployment_manifest.preview.json` —— N/A（NOT_DEPLOYED，无 schema/UI/部署变更）。`data-samples` = fixtures/ + contract_report.json。

## 完成声明
```text
Task: ADP-S4-P03-T049
Commit: <记于提交步骤，见 changed_files.txt / git 历史>
Files changed: tools/adapter_a1_province.py(新) + T049 证据包(6 fixtures + 报告) + 治理同步（见 changed_files.txt）；无 worker/生产改动
Tests: family_tests.txt —— 3/3 省级站点通过(江苏/山东/北京)跨2模板族(art-cms+beijing-zhengce)；全 A1；连接器类体省份字面量=NONE(特殊逻辑限 profile)；真实文号/日期/标题清洗；实时无回归(build b189d3cc0703==T040)，ACCEPTANCE=PASS(exit 0)；治理门 lean_governance ci = SHIP（提交步骤）
Business evidence: A1 省级政府门户通用 adapter family(1类+profile覆盖3省2族)
Data/Performance/Visual: Data=6真实fixtures+3省contract；Perf=实时无回归；Visual=六主题保留
Value: 少模板族覆盖A1多省，新增省=加profile；T050省级回填底座
Cost: 生产请求0 / D1 0 / R2 0 / 模型 0；经常性成本 0(NOT_DEPLOYED,dev-env)
Known gaps: 见 known_gaps.md
Deployment: NOT_DEPLOYED（adapter family；生产 worker/cron/数据未触，实时无回归）
Rollback: git revert <sha>
Verifier: 待独立上下文复核（实现者不自签 PASS）
```

**IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION**
