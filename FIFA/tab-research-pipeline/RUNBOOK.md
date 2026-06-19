# TAB FIFA 盘口研究系统 RUNBOOK

更新时间：2026-06-12 18:55 Australia/Sydney

## 运行边界

本系统目标是每日自动生成 TAB FIFA 盘口研究 PDF、dashboard、SQLite 记录和新旧报告对比。当前仍处于 automation-ready 打磨阶段。

明确禁止：

- 不自动下注。
- 不点击赔率价格。
- 不添加选择到 Bet Slip。
- 不提交、确认或修改任何 TAB 账户投注。
- 不在用户未明确授权前创建 recurring automation。

授权配置文件：

```text
config/automation.toml
```

默认状态必须保持：

```toml
authorized = false
allow_recurring = false
allow_auto_betting = false
cadence = "manual"
scope = "report_generation_only"
```

只有用户明确批准进入每日自动生成报告后，才允许把 `authorized` 和 `allow_recurring` 改为 `true`。`allow_auto_betting` 必须始终为 `false`。

## 当前状态矩阵

| 项目 | 当前状态 | 说明 |
|---|---:|---|
| 最新成功指针 | ready | `outputs/latest_commit.json` 仍指向 04062026 technical-good run |
| raw refresh health | blocked | `outputs/raw_refresh_health_latest.json` 当前 0/5 required boards ready；blockers=`refresh_command_failed, route_mismatch, stale_raw` |
| 报告索引 | ready | `outputs/report_index_latest.json` 记录本地报告目录、图表数、新旧对比和 committed latest |
| 报告历史可视化 | ready | `outputs/report_index_latest.md` 记录历史 run 状态、推荐数、图表数、新旧变化和 automation runner history |
| 报告历史 PDF | ready | `outputs/report_index_latest.pdf` 为正式 PDF sidecar |
| 自动化就绪审计 | current run blocked | `outputs/automation_readiness_latest.json` 当前为 `current_run_preflight_blocked` |
| 自动化就绪可视化报告 | ready | `outputs/automation_readiness_latest.md` 包含 4 个 Mermaid gate 图表 |
| 自动化就绪 PDF | ready | `outputs/automation_readiness_latest.pdf` 为正式 PDF sidecar |
| 自动化候选调度包 | review-only ready | `automation_candidate_latest.json/.md/.pdf` 描述4小时report-only候选，不安装调度 |
| 技术 automation ready | 历史成功 | 最新成功 run 技术通过；当前 attempted run 因当日私有持仓快照缺失不能发布 |
| recurring automation entry ready | false | 用户尚未授权 recurring automation |
| 自动下注 | 禁止 | 系统只生成报告和建议，不执行下注 |
| 公共输出安全 | ready | 成功指针引用的公开产物通过 public safety |
| 报告主路径 | ready | `/Users/linzezhang/Downloads/FIFA Report/DDMMYYYY.pdf` |
| PDF QA | 已接入 | 检查页数、文本长度、文件大小、关键中文术语，并用 PyMuPDF 渲染抽样页做视觉 smoke QA |
| latest artifact consistency | 已接入 | verifier 会拒绝 run-scoped key 指向 `*_latest` 文件 |
| 可视化覆盖 | ready | `outputs/report_visual_inventory_latest.json` 当前 13 个报告族均有图表/表格/Dashboard；average_score=0.9904 |
| 目标验收追踪 | in progress | `outputs/goal_traceability_latest.json/.md/.pdf` 已生成并写入 `goal_traceability_snapshots`；当前 5 ready / 3 partial / 3 blocked |
| 主 PDF 模型审计章节 | ready | 下一次 fresh run 的主商业 PDF 会包含模型交叉验证审计、Top分歧比赛和Elo/Dixon-Coles对照表 |
| 模型对比报告可视化 | ready | `tab_fifa_model_comparison_v0_1.md` 包含 Open-source Model Dashboard 和 GitHub Source Audit |
| 模型对比 PDF | ready | `tab_fifa_model_comparison_v0_1.pdf` 包含 5 个图表和 3 个附表 |
| dashboard 历史索引 | ready | 最近运行区包含报告历史趋势 SVG，自动化运行历史区包含 runner 状态 SVG/表格，产物区链接 report index |
| 开源模型参考 | 已复核 | 3 个 GitHub 模型参考已在 2026-06-12 再次访问确认；2 个已转成 implemented proxy，1 个为 design reference |
| raw refresh timeout 诊断 | fixed | 子进程超时会写 public-safe attempt diagnostic，主流程会刷新 blocked health，不保留旧 ready 状态 |
| readiness raw blocker 透传 | fixed | `automation_readiness_latest.*` 会在 raw 未 ready 时透传最近 `refresh_command_failed` |
| matches chunked refresh | fixed | matches 采用 5 场一批抓取、合并 staged raw，并记录 chunk quality diagnostics |

## 最新成功与当前阻塞

唯一最新成功指针：

```text
outputs/latest_commit.json
run_id: 20260604T135753Z-212e8e9a
report_date: 04062026
status: ready_for_manual_report
technical_automation_ready: true
automation_entry_ready: false
ready_required_boards: 5/5
public_artifact_safety_ready: true
```

正式 PDF：

```text
/Users/linzezhang/Downloads/FIFA Report/04062026.pdf
```

报告索引：

```text
outputs/report_index_20260604T135753Z-212e8e9a.json
outputs/report_index_latest.json
outputs/report_index_latest.md
outputs/report_index_latest.pdf
report_index_latest.md Mermaid charts: 3
report_index_latest.pdf charts: 7
report_index_latest.pdf extra tables: 1
report_index_latest.pdf automation detail rows: 9
automation_run_count: 9
```

自动化就绪审计：

```text
outputs/automation_readiness_latest.json
outputs/automation_readiness_latest.md
outputs/automation_readiness_latest.pdf
status: current_run_preflight_blocked
formal_report_publish_ready: false
recurring_automation_ready: false
blockers: current-day private position snapshot missing, recurring_authorization_missing
Mermaid charts: 4
PDF charts: 4
```

自动化候选调度包：

```text
outputs/automation_candidate_latest.json
outputs/automation_candidate_latest.md
outputs/automation_candidate_latest.pdf
status: review_required_not_installed
recommended_cadence: 4h
rrule: FREQ=HOURLY;INTERVAL=4
entrypoint: scripts/run_tab_fifa_daily_automation.sh
installed: false
auto_wagering_allowed: false
public_artifact_safety_ready: true
```

模型对比报告：

```text
outputs/tab_fifa_model_comparison_v0_1.md
outputs/tab_fifa_model_comparison_v0_1.pdf
Visual Summary: true
Mermaid charts: 4
PDF charts: 4
PDF detail rows: 12
match_count: 26
public_artifact_safety_ready: true
```

主 PDF 模型审计已接入代码和 QA：

```text
generate_business_pdf_report.py
section: 模型交叉验证审计
table: Top分歧比赛
required PDF QA terms: 模型交叉验证审计, Top分歧比赛, Elo/Dixon-Coles
status: implemented, waiting for next fresh gated report run
```

05062026 PDF 只可作为历史生成物，不可作为 automation-ready 最新成功：

```text
run_id: 20260604T141232Z-d2eff3e0
status: blocked_by_gate
reason: current-day private position snapshot missing
pdf_qa_ready: true
```

当前 readiness gate 已知阻塞：

```text
current-day private position snapshot missing
latest private capture diagnostic: access_denied via fresh-context
private_position_bootstrap.status: profile_login_required
private_position_bootstrap.next_action: run headed read-only capture with --wait-for-login-ms 600000
raw_refresh_health_latest.json: ready, required boards 5/5
automation_readiness_latest.json: current_run_preflight_blocked
```

最新 06062026 attempted run 状态：

```text
run_id: 20260605T232012Z-bad22171
raw_snapshot_refresh: ok
raw_refresh_gate: ok
pdf_quality_gate: ok
blocked_by_gate: current-day private position snapshot missing
latest_commit.json: unchanged at 04062026
```

这是正确的 fail-closed 行为。不得用 stale raw 生成正式可操作下注建议。

最近验证：

```text
python3 -m py_compile run_daily_report.py tests/test_pipeline.py
OK

python3 -m unittest tests.test_pipeline
Ran 97 tests
OK

scripts/verify_fifa_automation_readiness.sh --hermetic
OK

scripts/verify_fifa_automation_readiness.sh --artifact-chain-only
OK

selected report-index/dashboard/SQLite public safety scan
OK, checked_count: 10, sensitive_artifact_count: 0

并行审查后修复：

```text
My Bets import fail-closed:
  capture exit code must be 0
  raw text mtime must be >= runner started_at
  import uses raw mtime as scraped_at
  preflight rejects snapshot report_date mismatch, missing scraped_at, invalid scraped_at, or scraped_at outside report date in Australia/Sydney

Browser readonly hardening:
  capture_tab_my_bets_readonly.mjs uses serviceWorkers: "block"
  refresh_tab_readonly.mjs uses serviceWorkers: "block"
  My Bets dry-run now validates private output/profile path guards before ready=true

Runner persistence:
  embedded summary/readiness/candidate/SQLite post-run failure exits non-zero after writing sanitized summary when possible
  TAB_FIFA_PRIVATE_DIR is passed to My Bets capture via --output-dir
  default My Bets Chrome profile follows ${PRIVATE_DIR}/tab_chrome_profile unless TAB_FIFA_CHROME_USER_DATA_DIR is explicit
  wrapper now holds ${PRIVATE_DIR}/.tab_fifa_daily_runner.lock from capture through post-run persistence
  stale runner lock with dead pid is cleared; active runner exits fail-closed with code 75

Latest publishing:
  latest_commit.json is now the single atomic success pointer
  run-scoped report index/PDF/manifest/dashboard artifacts are finalized before latest_commit publish
  convenience latest copies, Downloads PDF, dashboard_latest, and report_index_latest are derived after latest_commit and are non-authoritative
```

outputs/tab_fifa_model_comparison_v0_1.pdf
chart_count: 4
detail_row_count: 12
public_artifact_safety_ready: true

PDF fixture QA:
public report text contains 模型交叉验证审计, Top分歧比赛, Elo/Dixon-Coles
PyMuPDF visual smoke QA renders sample pages and blocks near-blank formal PDFs

automation_candidate_latest.pdf
chart_count: 4
status: review_required_not_installed
cadence: 4h
```

报告历史 Markdown 当前覆盖：

```text
Run status mix
Technical readiness by recent run
Recommended new exposure by run
Recommendation volume by run
New-vs-old changed items by run
Automation runner status mix
Automation Runner History table
```

自动化就绪 Markdown 报告当前覆盖：

```text
Gate readiness mix
Gate scorecard
Blocker severity mix
Next action priority
```

## SQLite 证据链

主库：

```text
outputs/tab_fifa_reports.sqlite3
```

核心表：

| 表 | 用途 |
|---|---|
| `report_runs` | 每次日报运行的主记录 |
| `board_runs` | 5 个 TAB FIFA 板块就绪状态 |
| `recommendations` | 各板块推荐和金额 |
| `model_comparisons` | 开源模型对照和分歧 |
| `visual_snapshots` | PDF/dashboard 图表快照 |
| `artifacts` | PDF、dashboard、manifest、report index 等公开产物索引 |
| `automation_runs` | 每次 runner 执行的 public-safe 状态历史，包含 mode/status/exit code/raw gate/publish gate/私有持仓 capture-import 状态 |
| `source_logs` | 官方源、新闻源、开源模型、本地参考文件日志 |
| `audit_logs` | raw refresh、preflight、public safety、portfolio gate 审计 |
| `decision_records` | 下注建议级决策记录 |
| `missing_data_logs` | 真正缺失/阻塞的数据项 |
| `manual_review_queue` | 人工复核项，主要来自高模型分歧 |

用户未授权 recurring automation 不写入 `missing_data_logs`。它只影响 `automation_entry_ready=false`。

## Runner verify-only 语义

`scripts/run_tab_fifa_daily_automation.sh --verify-only` 默认使用：

```bash
TAB_FIFA_VERIFY_MODE=hermetic
```

这个默认值只验证代码、fixture、只读浏览器契约和 dry-run，不要求当前 live preflight 可发布。需要检查历史成功链或当前 live artifact 时，显式设置：

```bash
TAB_FIFA_VERIFY_MODE=artifact-chain-only scripts/run_tab_fifa_daily_automation.sh --verify-only
TAB_FIFA_VERIFY_MODE=live-artifacts scripts/run_tab_fifa_daily_automation.sh --verify-only
TAB_FIFA_VERIFY_MODE=full scripts/run_tab_fifa_daily_automation.sh --verify-only
```

当前 `live-artifacts/full` 仍会因 `06062026` 私有持仓快照缺失而 fail-closed；这不代表 hermetic code readiness 失败。

## 可视化覆盖

当前应保持 10 个图表：

```text
board_readiness
report_compare
recommendation_distribution
stake_allocation
match_value
odds_probability_edge
model_divergence
model_consensus
model_source_coverage
model_capability_coverage
```

这些图表应进入 PDF、dashboard 和 SQLite `visual_snapshots`。

模型对比 Markdown 还应额外包含 4 个 Mermaid 图表：

```text
Model disagreement by match
Consensus confidence mix
Open-source capability coverage
GitHub reference adoption mix
```

## GitHub 开源模型参考

已复核并纳入模型参考元数据，`verified_at = 2026-06-05`。2026-06-05 14:13 AEST 再次访问确认：

```text
https://github.com/Hicruben/world-cup-2026-prediction-model
https://github.com/opisthokonta/goalmodel
https://github.com/RyanSCodes/Dixon-Coles-Football-Predictor
https://github.com/martineastwood/penaltyblog
https://github.com/ML-KULeuven/socceraction
https://github.com/openfootball/worldcup.json
https://github.com/openfootball/help
https://socceraction.readthedocs.io/en/latest/documentation/faq.html
```

采用原则：

- Hicruben：参考 Elo、Dixon-Coles、Monte Carlo、walk-forward backtest 和 48 队赛事路径。
- goalmodel：参考 xG 到 1X2、OU、BTTS、评分规则和市场概率反推 xG。
- RyanSCodes：参考 Dixon-Coles 时间衰减、主场优势、攻防参数和比分矩阵；不复制 Python 2.7 legacy 实现。
- penaltyblog：参考 no-vig/overround removal、Poisson/Bivariate Poisson/Dixon-Coles、Asian handicap、大小球、ratings 和模型不确定性；MIT，可作为本地实现口径对照。
- socceraction：参考 SPADL、xT、VAEP、Atomic-VAEP 和 provider adapters；当前无事件流 raw 时只作为基本面路线和缺口提示。
- openfootball/worldcup.json：参考 2026 World Cup public JSON、source text files、public-domain license 和 SQLite/CSV/JSON export pattern；只做赛程/阶段校验，不替代 TAB 盘口。

## 常用命令

进入项目目录：

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/work/tab-research-pipeline
```

运行完整单测：

```bash
python3 -m unittest tests.test_pipeline
```

运行完整 readiness gate。默认同时跑 hermetic checks 和 live artifact checks；如果 raw stale，会按预期失败：

```bash
scripts/verify_fifa_automation_readiness.sh
```

只跑代码、fixture、dry-run 和只读刷新安全检查，不检查当前 outputs/raw 新鲜度：

```bash
scripts/verify_fifa_automation_readiness.sh --hermetic
```

只检查当前 outputs/latest/raw 是否可作为正式自动化产物：

```bash
scripts/verify_fifa_automation_readiness.sh --live-artifacts
```

复用 4 小时内有效 TAB 快照生成日报：

```bash
TAB_FIFA_REFRESH_RAW=reuse_fresh python3 run_daily_report.py
```

完整日报生成：

```bash
python3 run_daily_report.py
```

公开 raw / Live discovery 如果被 TAB 拒绝，必须保持 fail-closed；不要用 headed Chrome、CAPTCHA 绕过、fingerprint spoofing 或 stealth browser 作为恢复路径。主恢复路径是官方/授权数据源或授权第三方 TAB-labeled odds API；用户导出 raw 快照导入只作为兜底，已有 fresh partial raw 只允许 research-only 诊断。

```bash
python3 run_daily_report.py
```

## 授权 odds provider raw 路径

第三方 provider 只负责批量 raw，不负责绕过 TAB。当前已支持：

| Provider | 用途 | 固定边界 |
|---|---|---|
| The Odds API | AU region + `tab` bookmaker + decimal odds，优先服务 Matches 主盘口 `Result`、`Total O/U`、`Handicap context` | 无 key 时 fail-closed；只写 provider staging；地区盘口默认忽略 |
| OpticOdds | TAB sportsbook odds，适合 alternate markets / futures / limit-liquidity 字段覆盖测试 | endpoint/query 需按账号文档配置；只写 provider staging |

命令：

```bash
cp config/odds_providers.local.env.example config/odds_providers.local.env
# 在本机编辑 config/odds_providers.local.env；真实 key 不提交 GitHub
export TAB_FIFA_THE_ODDS_API_SPORTS="soccer_fifa_world_cup"
export TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY="1"
export TAB_FIFA_PROVIDER_SCOPE="matches"
export TAB_FIFA_THE_ODDS_API_MATCH_MARKETS="h2h,totals,spreads"
export TAB_FIFA_OPTICODDS_ENDPOINT="/fixtures/odds"
export TAB_FIFA_OPTICODDS_QUERY="sport=soccer&sportsbook=TAB"

python3 scripts/build_provider_config_doctor.py
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches

# 小样本补齐 Total/Team Total，不要默认全量扫 68 场。
python3 refresh_odds_provider_raw.py \
  --provider the_odds_api \
  --scope matches \
  --event-market-probe-limit 3 \
  --event-odds-limit 3 \
  --event-odds-markets totals,alternate_totals,team_totals,alternate_team_totals
```

默认忽略 `2026 World Cup Australia Markets` 这类地区盘口。`Team Total Goals Over/Under` 已支持 provider payload 解析，但 The Odds API 是否可请求 `team_totals` 取决于账号、sport 和 bookmaker；未验证前不要默认加入，以免浪费 500 credits/月额度。需要试验时使用 `TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS=team_totals,alternate_team_totals`。

如果本机 Python SSL trust store 缺失，provider 请求会自动尝试 `certifi` CA bundle，但仍保持 TLS 证书校验开启；不要用关闭证书校验的方式修复 provider 访问。

`provider_kpi_latest.json/md/pdf` 汇总 provider 覆盖、credit、盘口缺口和下一步动作；public-safe 副本同步在 `artifacts/latest/provider_kpi_latest.*`。

`refresh_odds_provider_raw.py` 成功后会同步重建 `provider_kpi_latest.*`，因此 KPI refresh id 应与 raw/coverage refresh id 一致；若不一致，先重跑 provider KPI bundle 或检查 refresh 命令是否异常退出。

`provider_alternate_plan_latest.json/md/pdf` 把覆盖缺口转成下一批小样本 probe 队列；会排除已经拉过 event-level odds 的比赛，并给出推荐 batch、预估 credit 区间和停止条件，避免默认全量扫 68 场。`provider_alternate_probe_evidence_latest.json` 会持久保存 event-level evidence；普通主盘口刷新不能抹掉低收益 Team Total 证据。

当 Team Total 小样本 event-market probe 没有返回任何 TAB Team Total market key 时，计划会切到 `fallback_required` 和 `manual_or_official_provider_priority`。此时不要继续默认消耗 The Odds API credits 扫 Team Total，应转 OpticOdds 官方访问/白名单或人工 TT 批次模板。

Team Total fallback 走人工 overlay，不走 TAB 自动抓取，也不把 provider 缺口伪装成已覆盖：

```bash
# 重建 Team Total 人工 CSV 模板、导入状态、hash gate、overlay preview、发布预检。
python3 provider_manual_verification.py

# 先看校验工作台；它会把 68 个候选拆成批次，显示下一批和剩余高优先级。
open "../../outputs/provider_manual_workbench_latest.pdf"

# 人工只读 TAB 后填写 manual_verification/provider_team_total_manual_verification.csv，
# 并保存匹配的 manual_verification/provider_team_total_overlay_approval.json 后，
# 才能显式尝试把 overlay 写入 Matches raw slot。
python3 publish_provider_manual_overlay.py
```

如果 CSV 缺失、签名缺失、hash 不匹配或 raw validation 不通过，该命令只输出 `provider_manual_overlay_publish_latest.json/md/pdf` 的阻断状态，不写正式 raw，不写 5-board batch manifest，不释放新增下注金额。

输出：

| 文件 | 含义 |
|---|---|
| `outputs/provider_raw/<refresh_id>/` | provider staged raw，不直接作为正式 TAB raw |
| `outputs/odds_provider_raw_latest.json` | staged artifact manifest |
| `outputs/odds_provider_coverage_latest.json` | 覆盖率、validation、人工 TAB final check gate |

正式发布必须另有人工 TAB 最终校验文件，且 `refresh_id + board_id + sha256` 匹配 staged raw：

```bash
python3 refresh_odds_provider_raw.py \
  --input-json /path/to/provider_payload.json \
  --refresh-id <refresh_id> \
  --verification-file outputs/provider_tab_final_verification_latest.json \
  --publish-verified
```

`config/odds_providers.example.json` 给出 key 环境变量、provider 参数和 verification schema。未通过人工最终校验前，即使 provider raw 有数据，也不能释放新增下注金额。

`formal_publish_allowed` 只代表当前 scope 的 raw 可发布；`full_automation_allowed` 才代表完整自动日报 gate。Matches-only 发布不会伪造成 5/5 full automation。

## 输出路径

| 类型 | 路径 |
|---|---|
| PDF 报告 | `/Users/linzezhang/Downloads/FIFA Report/DDMMYYYY.pdf` |
| 最新 dashboard | `outputs/tab_fifa_dashboard_latest.html` |
| 最新 SQLite | `outputs/tab_fifa_reports.sqlite3` |
| 最新报告索引 | `outputs/report_index_latest.json` |
| 最新报告历史可视化 | `outputs/report_index_latest.md` |
| 最新报告历史 PDF | `outputs/report_index_latest.pdf` |
| 最新自动化就绪审计 | `outputs/automation_readiness_latest.json` |
| 最新自动化就绪可视化报告 | `outputs/automation_readiness_latest.md` |
| 最新自动化就绪 PDF | `outputs/automation_readiness_latest.pdf` |
| 最新自动化候选配置 | `outputs/automation_candidate_latest.json` |
| 最新自动化候选可视化报告 | `outputs/automation_candidate_latest.md` |
| 最新自动化候选 PDF | `outputs/automation_candidate_latest.pdf` |
| 最新模型对比 PDF | `outputs/tab_fifa_model_comparison_v0_1.pdf` |
| 最新成功指针 | `outputs/latest_commit.json` |
| 最新 manifest | `outputs/daily_report_manifest_latest.json` |
| 最新 runner summary | `outputs/automation_run_latest.json` |
| 私有 runner logs | `work/private/tab_fifa/automation_run_logs/` |
| 私有 My Bets 快照 | `work/private/tab_fifa/` |
| 私有 My Bets capture 诊断 | `work/private/tab_fifa/tab_my_bets_capture_diagnostics_DDMMYYYY.json` |
| 私有 quarantine | `work/private/tab_fifa/public_output_quarantine/` |

## 私有持仓快照导入

当 `automation_readiness_latest.status=current_run_preflight_blocked` 且原因是 `current-day private position snapshot missing` 时，使用私有只读链生成当日快照：

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/work/tab-research-pipeline
TAB_FIFA_HEADLESS=0 \
node scripts/capture_tab_my_bets_readonly.mjs --report-date DDMMYYYY --wait-for-login-ms 600000
python3 import_my_bets_snapshot.py --source ../../work/private/tab_fifa/tab_my_bets_raw_DDMMYYYY.txt --report-date DDMMYYYY
```

如果专用 profile 已建立，也可以让一次性 daily runner 在报告前自动执行只读 capture/import：

```bash
scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY
TAB_FIFA_HEADLESS=0 scripts/run_tab_fifa_daily_automation.sh --capture-my-bets --report-date DDMMYYYY --wait-for-login-ms 600000
```

该入口默认关闭；启用后仍不自动登录、不点击赔率、不添加 Bet Slip、不提交投注。它只会先尝试私有只读 capture，若 raw text 存在则导入私有 snapshot，然后继续走正常日报 fail-closed 门禁。`automation_run_latest.json` 只记录 sanitized capture/import 状态和 private log 文件名。

边界：

- 只读取 `TAB My Bets` 页面正文。
- 默认使用 `work/private/tab_fifa/tab_chrome_profile` 作为专用可复用 Chrome profile。
- 可通过 `TAB_FIFA_CHROME_USER_DATA_DIR` 或 `--chrome-user-data-dir` 覆盖专用 profile；profile 必须位于 private 路径。
- `--wait-for-login-ms` 只用于一次性 headed 登录态 bootstrap；后续自动化复用同一个 private profile。
- 不保存 TAB 账号密码。
- 不点击赔率、不添加 Bet Slip、不提交投注。
- 阻断写请求、Bet Slip/place-bet URL、账户资料/支付类 URL、非 My Bets account 页面；允许渲染持仓所需的 My Bets/bets/history 只读数据。
- 不写入 `outputs/`。
- 成功或登录态失败都会写入私有 `tab_my_bets_capture_diagnostics_DDMMYYYY.json`；该文件只含 `auth_status`、`auth_mode`、正文长度、去 query 的 URL 等安全诊断字段。
- 生成的 `tab_my_bets_positions_DDMMYYYY.json` 必须位于 `work/private/tab_fifa/`，权限为 owner-only。
- `summary.position_statuses_valid=false` 或未知持仓状态时，technical preflight 必须 fail-closed。
- `automation_readiness_latest.json/.md/.pdf` 的 `private_position_bootstrap` 会给出 public-safe 状态：profile 是否存在、raw text 是否已抓取、snapshot 是否已导入、sanitized capture 状态以及下一步应 capture 还是 import；不得输出 raw bet 内容、账户标识或 private 绝对路径。

## 失败处理矩阵

| 失败状态 | 阻塞 automation | 处理方式 |
|---|---:|---|
| `automation unauthorized` | 是 | 不创建 recurring automation；保留手动日报和 verify-only；等待用户明确授权 |
| `raw_refresh_blocked` | 是 | 查看 `outputs/raw_refresh_health_latest.json` 和 diagnostics；如是 TAB 拦截，保持 fail-closed，优先改用官方/授权数据源或授权第三方 TAB-labeled odds API；用户导入只作兜底 |
| `provider_raw_blocked` | 是 | 查看 `outputs/odds_provider_coverage_latest.json`；缺 API key、provider coverage 不足或 TAB final verification 未通过时，不发布正式 raw，新增执行金额保持 AUD 0 |
| `refresh_command_failed` | 是 | 查看 `outputs/raw_refresh_diagnostics_latest.json` 的 attempt/timeout 字段；保持 fail-closed，不沿用旧 ready health |
| `access_denied` | 是 | 归类为 `ai_controlled_access_rejected`；禁止公开 headed fallback，保持上一个 `latest_commit.json` 不变 |
| `raw_stale` | 是 | 重新 live refresh；不能用超过 4 小时的快照生成可操作报告 |
| `mixed_refresh_id` | 是 | 重新完整批量刷新 5 个板块；禁止混用不同时间快照 |
| `event/source failed` | 是 | 等待公开源恢复或修复 fetch/parser；不能用缺失公开源的结果进入 automation |
| `PDF QA failed` | 是 | 不发布 latest；检查必需章节、图表标题、中文理由、PDF 生成质量和 PyMuPDF 视觉 smoke QA 采样页 |
| `technical preflight failed` | 是 | 不发布 latest；检查 raw、私有持仓快照、public safety、portfolio gate |
| `my_bets_login_required` | 是 | 读取私有 capture 诊断；需要建立或刷新可复用 TAB 已登录 profile；不能用旧持仓替代当日快照 |
| `my_bets_access_denied` | 是 | 读取私有 capture 诊断；改用 headed Chrome 或专用已登录 profile 只读抓取，不能把 Access Denied 当成空持仓 |
| `latest_commit artifact consistency failed` | 是 | 修正 run-scoped artifact 指针，不允许指向失败 run 的 `*_latest` |
| `automation_readiness_safety failed` | 是 | 不更新 `latest_commit.json`；修复 readiness 公开脱敏或 artifact 引用后重跑 |
| `public_artifact_safety_failed` | 是 | 不发布 latest；把可疑 public artifact 移入私有 quarantine；修复脱敏后重跑 |
| `private My Bets unknown status` | 是 | 不把未知持仓状态用于资金结论；需要重新读取或人工确认状态映射 |
| `latest_publish_failed` | 是 | 不更新 `latest_commit.json`；检查 PDF/dashboard/SQLite 写入权限和磁盘状态 |
| `test failure` | 是 | 先修测试，不进入 automation |

## 恢复原则

- 读取 `outputs/latest_commit.json` 作为唯一最新成功状态。
- 读取 `outputs/report_index_latest.json` 作为本地报告目录和历史 run 检索入口，但其中的正式最新成功必须与 `latest_commit.json` 一致。
- 读取 `outputs/automation_readiness_latest.json` 判断当前是否能发布正式日报或进入 recurring automation；`formal_report_publish_ready=false` 时不生成可执行下注报告。
- 如果本次运行失败，不手动拼接 `*_latest` 文件作为成功报告。
- run-scoped key 如 `automation_preflight`、`pdf_qa`、`manifest`、`dashboard_run_copy` 必须指向含 run_id 的文件。
- 如果 public safety gate 失败，不把本轮产物给用户作为正式报告。
- 私有 quarantine 不自动删除，除非用户明确要求清理。
- 建议结论必须来自新一轮通过 gate 的报告，不手改 PDF/JSON 下注建议。
