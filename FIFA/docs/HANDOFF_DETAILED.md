# TAB FIFA 盘口研究系统 Handoff

更新时间：2026-06-13 17:15 AEST

## 最新追加更新（2026-06-13 17:15 AEST）

- 已为 `TAB FIFA盘口研究系统.app` 设计并安装新 macOS 图标。
- 图标概念：`Research Compass`，使用足球核心、盘口/概率雷达、数据价值线和金色价值标记；避免博彩筹码、投注单、美元符号等低质博彩视觉。
- 本地源文件：
  - `assets/app_icon/TABFIFAResearch.png`
  - `assets/app_icon/TABFIFAResearch.icns`
  - `assets/app_icon/generate_app_icon.py`
  - `assets/app_icon/design_notes.md`
- 已更新 `scripts/build_downloads_app_entry.py`，每次重建 app 会自动复制 `TABFIFAResearch.icns` 到 `Contents/Resources/`，并写入 `CFBundleIconFile=TABFIFAResearch`。
- 已重建并刷新 `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`；当前 app bundle 已包含 `Contents/Resources/TABFIFAResearch.icns`。
- `generate_app_icon.py` 默认清理 `.iconset` 中间目录；当前源目录只保留正式 PNG、ICNS、脚本和设计说明，无 `__pycache__`/`.iconset` 缓存。
- 已验证：`CFBundleIconFile=TABFIFAResearch`、ICNS 文件有效、`py_compile` 通过、app 入口 contract 单测通过。

## 最新追加更新（2026-06-13 17:05 AEST）

- 已将后续开发主仓库确定为 `https://github.com/LinzeColin/FIFA`；本地工作副本为 `../../github_sync/FIFA`。
- 已完成 GitHub 初始化同步：
  - `a94ec0b Initial TAB FIFA research system sync`
  - `88b7bd0 Add local cleanup audit`
- GitHub 当前包含：
  - `tab-research-pipeline/` 当前主系统源码、测试、脚本、配置、README/RUNBOOK。
  - `legacy/fifa-analysis-system/` 旧版相关系统源码，排除 `.venv`。
  - `artifacts/latest/` 84 个 public-safe latest 交付物。
  - `artifacts/backups/tab_fifa_reports_20260613.sqlite3.gz` 历史 SQLite 压缩备份。
  - `artifacts/backups/public_outputs_without_sqlite_20260613.tar.gz` 非 SQLite public outputs 压缩备份。
  - `artifacts/backups/legacy_fifa_analysis_db_20260613.sqlite3.gz` 旧系统 DB 压缩备份。
  - `AGENTS.md`、`docs/DEVELOPMENT_STATUS.md`、`docs/FILE_RETENTION_POLICY.md`、`docs/HANDOFF*.md`、`ops/local_cleanup_*`。
- 已完成本地瘦身：
  - 删除路径：397
  - 删除文件：2952
  - 释放空间：159.72 MiB
  - 清理后目录体量：总目录约 `70M`，`outputs` 约 `4.9M`，`work` 约 `4.5M`，`github_sync/FIFA` 约 `60M`。
- 本地保留必要文件：
  - `work/tab-research-pipeline/` 当前源码。
  - `outputs/*_latest.*` 当前 public-safe 状态产物。
  - `outputs/13062026_partial_daily_research.*` 当前 research-only 日报。
  - `outputs/04062026.pdf` 最近可信正式报告。
  - `outputs/research_only_raw/` fresh partial raw 研究证据。
  - `outputs/tab_fifa_app_entry_runtime.html` 本地运行入口副本。
  - `work/private/tab_fifa/tab_chrome_profile` 非缓存文件，用于用户授权的 My Bets 只读 bootstrap。
  - 小型私有 bankroll/positions/diagnostics JSON。
  - `github_sync/FIFA` GitHub 工作副本。
- 已删除但不上传的私有/缓存类：
  - Python/pytest/macOS cache、旧 `.venv`、PDF QA/preview cache、Chrome cache。
  - 私有 raw backups、sensitive archive、public output quarantine、旧 app/automation logs、旧 My Bets raw text。
- 最终验证：
  - 远端 `refs/heads/main = 88b7bd0f84825c80e408e968e15419bd6a4d92be`。
  - 本地 `http://127.0.0.1:8767/api/status` 返回 `ok=true`、`raw_status=blocked`、`ai_controlled_access_rejected`、`partial_status=ready_research_only`、`private_status=profile_login_required`。
- 后续 agent 接手应先读 GitHub 仓库内 `AGENTS.md`、`docs/HANDOFF.md`、`docs/DEVELOPMENT_STATUS.md`、`docs/FILE_RETENTION_POLICY.md`。

## 最新追加更新（2026-06-13 16:38 AEST）

- 已修复 raw 访问政策问题：TAB public raw / Live discovery 遇到 Access Denied 或 AI controlled access 拒绝时统一归类为 `ai_controlled_access_rejected`，公开 raw 必须 fail-closed。禁止 headed fallback、CAPTCHA bypass、fingerprint spoofing、stealth browser；允许路径只有官方/授权数据源、用户导出导入快照、或已有 fresh partial raw 的 research-only 诊断。
- 已收紧底层执行：`run_daily_report.py` 的 public raw 子进程强制 `TAB_FIFA_HEADLESS=1`，即使内部误传 `headed_fallback=True` 或 `extra_env TAB_FIFA_HEADLESS=0` 也会被忽略并记录 `headed_fallback_ignored_by_access_policy=true`；`scripts/refresh_tab_readonly.mjs` 与 `scripts/discover_tab_live_boards.mjs` 也不再接受 `TAB_FIFA_HEADLESS=0` 切 headed。
- 已保留必要例外：`TAB_FIFA_HEADLESS=0` 仅用于私有 My Bets 用户授权只读 bootstrap，不用于公开 raw 或 Live discovery。私有链仍禁止下注、赔率点击、Bet Slip 修改，并且不保存密码/OTP。
- 已更新运行态 API：`/api/public-raw-refresh` 返回 `started=false`、`blocked=true`、`mode=public_raw_access_policy_blocked`；`/api/live-board-discovery` 返回 `mode=live_board_discovery_access_policy_blocked`；`/api/status.raw_refresh` 现在强制包含 `access_policy.status=blocked_by_access_policy`、`blocker_code=ai_controlled_access_rejected`、`automated_public_raw_refresh_allowed=false` 和授权/导入 next action，即使旧 raw health artifact 仍带 route mismatch 文案也不会误导用户去重试抓取。
- 已更新 Downloads/Web 文案：按钮从“刷新/重试”改为“检查Raw合规状态”“检查Live合规状态”；Live 区块改为 `TAB Live 访问合规状态`；`active_timeline_report_latest.*` 已重新生成，旧提示“先刷新公开盘口 raw”已替换为“先接入授权 raw 或导入用户导出快照”。
- 已重建真实产物：`/Users/linzezhang/Downloads/FIFA Report/TAB FIFA盘口研究系统.html`、`/Users/linzezhang/Downloads/FIFA Report/app_assets/*`、`/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`、工作区 `outputs/tab_fifa_app_entry_runtime.html`。
- 已重启本地 app server：当前 `http://127.0.0.1:8767/` 监听进程为 PID `75915`，已验证 `/api/status`、`/api/public-raw-refresh`、`/api/live-board-discovery` 均加载新逻辑。
- 验证通过：`python3 -m py_compile ...`；`bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh`；`node --check scripts/refresh_tab_readonly.mjs`；`node --check scripts/discover_tab_live_boards.mjs`；`python3 -m unittest tests.test_pipeline` -> `Ran 152 tests in 95.243s OK`。Downloads HTML/assets 关键文案命中，旧 `Headed fallback`、`重试 Live 板块发现`、`先刷新公开盘口 raw` 等文案未命中。
- 当前仍不能进入完整正式 automation：正式 raw 仍未 5/5 ready，Australia Markets 仍缺失/route mismatch，私有 My Bets 仍需用户本机授权登录。新增可执行下注金额继续为 `AUD 0`。

## 最新追加更新（2026-06-13 15:35 AEST）

- 已把 ChatGPT 足球赛事分析建议继续落到 automation 合约层：正式日报门禁与 research-only 每日诊断日报现在明确分离。`automation_readiness_latest.json` 新增 `research_only_daily_report_ready`、`research_only_recurring_candidate_ready`、`research_only_daily_report`，当前状态为 `research_only_daily_ready_formal_blocked`；`formal_report_publish_ready=false`、`recurring_automation_ready=false`、`partial_daily_research_latest.pdf` ready、`current_executable_new_stake_aud=0`。
- 已更新 scheduler 候选包：`automation_candidate_latest.json` 默认 entrypoint 改为 `scripts/run_tab_fifa_daily_automation.sh --allow-research-only-success`，expected artifacts 新增 `DDMMYYYY_partial_daily_research.pdf`、`partial_daily_research_latest.pdf/json`。该 flag 只允许“正式日报 fail-closed 但 research-only PDF fresh/AUD0”时把 runner 视为研究日报生成成功，不解锁正式日报、不下注、不点击赔率、不修改 Bet Slip。
- 已更新 runner 合约：`scripts/run_tab_fifa_daily_automation.sh` 新增 `--allow-research-only-success` / `TAB_FIFA_ALLOW_RESEARCH_ONLY_SUCCESS=1`，summary 写入 `formal_exit_code`、`effective_exit_code`、`research_only_success_exit_override`、`partial_daily_research`；正式 run 失败仍保留 formal exit code，research-only 成功只影响报告生成层。
- 已修复 readiness 生成性能：`automation_readiness` 不再每次扫描整个 outputs 或 95MB SQLite；改为复扫当前非 SQLite 公开产物，并复用 latest_commit 已验证的 public safety 结论。`safety.public_artifact_hits` 也改为每文件只 lower 一次并先 substring 过滤，再跑边界 regex，避免大文本安全扫描卡住。
- 已更新首页和成熟度矩阵：Downloads 首页“今日决策中心”新增“研究日报 automation”卡片，显示 research-only PDF ready / 候选就绪 / 正式日报 blocked；`automation_maturity_latest.*` 新增 `research_only_daily_report` 与 `report_intelligence_dashboard` 验收项，当前 maturity 为 `7/15 ready`、状态 `blocked`。
- 已重建真实产物：`automation_candidate_latest.*`、`automation_readiness_latest.*`、`automation_maturity_latest.*`、`/Users/linzezhang/Downloads/FIFA Report/TAB FIFA盘口研究系统.html`、`/Users/linzezhang/Downloads/FIFA Report/app_assets/*`、`/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`。
- 验证通过：`python3 -m unittest tests.test_pipeline` -> `Ran 150 tests in 98.731s OK`；`py_compile` 通过；公开产物安全审计覆盖 Downloads HTML、automation readiness/candidate/maturity JSON/MD/PDF，`public_artifact_safety_ready=True`、issue 0；`/api/status` 返回 `ok=true`、`raw_status=blocked`、`partial_status=ready_research_only`、`partial_ready=true`、`partial_stake=0`、`private_status=profile_login_required`。
- 当前仍不能进入完整每日 automation：正式 raw 仍未 5/5 ready，Australia Markets 仍缺失/route mismatch，私有 TAB My Bets 持仓仍需本机授权登录。当前可进入的是“research-only 每4小时候选日报生成能力”，不是正式可执行下注日报，也不是自动下注。

## 当前目标

持续优化 TAB FIFA 盘口研究系统，直到达到“每日自动生成研究报告，不自动下注”的 automation 水平。

核心边界：
- 只做研究、盘口读取、报告、回测、持仓监控。
- 不自动下注、不点击赔率、不加入 Bet Slip、不提交投注单。
- 私有 My Bets 只允许在用户本机授权登录后做只读读取，不保存密码、OTP 或敏感凭据。

## 当前状态

- 本地网页主入口：`http://127.0.0.1:8767/`
- Downloads HTML：`/Users/linzezhang/Downloads/FIFA Report/TAB FIFA盘口研究系统.html`
- Downloads App：`/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`
- 工作区入口副本：`work/tab-research-pipeline/outputs/tab_fifa_app_entry_runtime.html`
- 当前页面首屏优先展示“推荐下注板块”，包含时间、板块、盘口、下注、赔率、金额、分析一致性、盘口价值、EV、Edge、套利率、Risk of ruin、概率赔率编辑、置信度、市场资金倾向分等字段。
- 当前有效研究范围为 `4/5`：Matches、Futures、Group Betting、Team Futures Multi 可进入 research-only 诊断；Australia Markets 仍不可用。
- 新增可执行下注金额保持 `AUD 0`，因为正式 raw 和私有持仓未全部 ready。

## 最新完成

- 优化 Downloads/Web 首页为 EVA OS 风格的决策工作台：
  - 首屏从 6 个等权卡片压缩为 3 列工作台。
  - 新增 `task-list` 当前任务清单。
  - 新增分组导航：决策、自动化、报告。
  - 增加滚动高亮与锚点跳转，覆盖推荐下注、市场资金、主动测试、Raw 刷新、恢复矩阵、持仓监控、报告下载等区域。
- 修复并加速“主动测试与自动补缺”：
  - 点击后先展示最近 `active_timeline_latest.json` 快照。
  - 实时 `/api/active-test` 返回后覆盖结果。
  - API 失败时保留缓存时间线，避免空白失败。
  - 90 秒内重复点击走 `fresh_cached_timeline_fast_path`。
- 当前主动测试实测：
  - 第一次 fresh path：外层约 `4961ms`，内部约 `4554ms`。
  - 重复点击：外层约 `711ms`，内部约 `13ms`，`cache_age_seconds=16`。
  - 当前结果：`ok=true`、`day_count=9`、`missing_analysis_day_count=5`、`missing_report_day_count=8`、`backfill_queue_count=8`。
  - 因 raw blocked，正式补跑仍 `blocked_by_raw_refresh`；只补 research-only 诊断，不发布正式下注日报。
- 已同步 Downloads 入口和 app assets，HTML 已确认包含：
  - `工作台导航`
  - `主动测试与自动补缺`
  - `task-list`
  - `#available-board-strategy`
  - `cached_snapshot_fast_preview`
  - 旧文案 `主动测试并自动补缺` 已不存在。

## 关键文件

- App server：`work/tab-research-pipeline/scripts/tab_fifa_app_server.py`
- Downloads 入口生成：`work/tab-research-pipeline/scripts/build_downloads_app_entry.py`
- 主流程：`work/tab-research-pipeline/run_daily_report.py`
- 推荐/操作报告：`work/tab-research-pipeline/tab_research/recommendation_operations.py`
- 持仓 preflight：`work/tab-research-pipeline/tab_research/my_bets_bootstrap.py`
- 测试：`work/tab-research-pipeline/tests/test_pipeline.py`
- 工作目录 handoff：`work/tab-research-pipeline/HANDOFF.md`

## 关键决策

- 不能用陈旧盘口生成当前下注建议；live discovery 或 staged raw 未通过时必须 fail closed。
- `raw_refresh_research_only_latest.json` 只可支持研究诊断，不能解锁正式日报或新增下注金额。
- 当前 TAB 公开页面不披露真实成交资金、净资金或订单簿深度；“市场资金分析”只能明确标注为公开盘口代理指标。
- automation 分两层：
  - research-only daily PDF 可以作为候选下一阶段。
  - 完整正式 automation 必须等 raw `5/5`、My Bets 只读持仓、preflight 全通过。

## 验证结果

最近通过：
- `python3 -m py_compile scripts/build_downloads_app_entry.py scripts/tab_fifa_app_server.py`
- `python3 -m unittest tests.test_pipeline.PipelineTests.test_local_app_private_position_bootstrap_contract tests.test_pipeline.PipelineTests.test_active_backfill_fails_fast_when_raw_refresh_is_not_ready`
- 结果：`2 tests OK`

最近一次完整 suite 记录：
- `python3 -m unittest tests.test_pipeline`
- 结果：`Ran 149 tests in 66.281s OK`

接口状态：
- `/api/status` 返回 `ok=true`
- `entry=true`
- `partial_daily_research.ready=true`
- `partial_success=4/5`
- `raw_status=blocked`
- `private_status=profile_login_required`

未完成的视觉验证：
- Playwright/Chrome 截图受 macOS Crashpad/沙箱权限阻止，未生成截图；没有绕过权限。

## 未解决风险

- 正式 raw 仍 `blocked`，不能进入完整每日 automation。
- Australia Markets 仍 route mismatch/live nav 缺失。
- 私有 My Bets 持仓仍需用户本机授权登录后只读导入。
- 当前部分概率工程模块仍是 planned/policy 层，不应在报告里伪装成已完成真实 MCMC、完整 xG 事件级建模或完整赛制 Monte Carlo。
- 新增可执行下注金额必须继续保持 `AUD 0`，直到 raw/private/preflight 全部 ready。

## 下一步

推荐顺序：
1. 修 Australia Markets：做 live/deep-link route 变体发现与定期重试；找不到时继续标记 unavailable/no-bet。
2. 完成 My Bets 只读授权导入：用户需在本机 TAB 窗口登录授权；系统只读取持仓快照，不保存凭据。
3. 将主动测试缺口补全为 research-only 日报链路：每天至少 4 次分析检查，每天一份诊断报告；不发布正式下注日报。
4. raw `5/5` 与私有持仓 ready 后，再跑完整 automation readiness。

## 当前进度

- Research-only 报告/工作台成熟度：约 `76%`
- 完整正式 automation 成熟度：约 `60%`
- 预计剩余迭代：`3-5` 轮
- 预计时间：`4-8` 小时有效工程时间，取决于 TAB 当前页面是否重新暴露 Australia Markets、以及 My Bets 授权是否顺利。
- 置信度：中高；主要不确定性来自 TAB 动态页面/登录态，而不是本地工程结构。
