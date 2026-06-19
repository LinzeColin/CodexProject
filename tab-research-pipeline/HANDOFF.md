# TAB FIFA 盘口研究系统 Handoff

更新时间：2026-06-15 20:45 AEST

## 最新追加更新（2026-06-15 20:45 AEST）

- 完成本地数据资料备份与存储瘦身：
  - 新增 GitHub 备份目录：`artifacts/backups/20260615/`
  - 备份 `outputs/` 当前快照：`runtime_outputs_snapshot_20260615.tar.gz`，覆盖 280 个 runtime/output 条目。
  - 备份 Excel 资料：`2026_FIFA_ledger_20260615.xlsx`、`fifa_world_cup_team_tables_1930_2022.xlsx`。
  - 记录旧交付 zip checksum：`deleted_review_packages_20260615.sha256`（22 个旧 report zip）、`deleted_download_root_packages_20260615.sha256`（2 个 Downloads 根目录 zip）。
  - 清理审计：`ops/local_slim_audit_20260615.md`。
- 已推送 GitHub：
  - `d925300 Back up FIFA runtime data snapshots`
  - 本轮清理审计提交包含 `deleted_download_root_packages_20260615.sha256` 与 audit/handoff。
- 本地已删除：
  - 22 个旧 `FIFA_agent_review_package_*.zip`，约 614MB。
  - 2 个 Downloads 根目录交付 zip，约 59MB。
  - `~$2026 FIFA.xlsx` 临时锁文件。
  - `.pytest_cache` 与 4 个 `__pycache__` cache 目录，约 4.8MB。
  - 合计释放约 678MB。
- 本地保留：
  - Git 工作区、源码、docs、artifacts 备份。
  - `outputs/` 约 31MB，供本地网页 runtime API 使用。
  - `/Users/linzezhang/Downloads/FIFA Report` 约 29MB，保留 HTML 入口和 `app_assets`。
  - `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`。
  - `/Users/linzezhang/Downloads/2026 FIFA.xlsx` 和 `fifa_world_cup_team_tables_1930_2022.xlsx`。
  - ignored 本地 env：`tab-research-pipeline/config/odds_providers.local.env`，不进入 Git。
- 验证：
  - 旧 report zip 剩余 `0`。
  - 两个 Downloads 根目录 zip 已删除。
  - Excel 临时锁已删除。
  - Python cache 已删除。
  - tracked secret scan 未命中真实 The Odds API key。
- 边界：
  - 未删除 TAB 登录状态、浏览器状态、Keychain、个人文档、源码、Git 历史或 ignored provider env。
  - 未运行 odds provider refresh，未消耗 credits，未触碰 Bet Slip。

## 最新追加更新（2026-06-15 19:52 AEST）

- 完成网页平台首屏操作流程提纯：
  - 新增首页 section：`#operation-panel`
  - 导航新增：`操作总览`
  - 新增 runtime API：`/api/status.operation_panel`
  - 首页首屏现在先显示“当前不要新增下注 / 可执行金额 AUD 0 / 下一步最短路径 / 关键阻塞 / 四步操作流”，再进入技术工作台。
- 用户侧信息层级调整：
  - 重要结论显眼：`当前不要新增下注`、`填写 TT-001`、`新增可执行金额 AUD 0`、`Automation 28.00%`。
  - 操作更短：看推荐 -> 填写 TT-001/工作队列 -> 主动测试与自动补缺 -> 最终执行清单。
  - 页面刷新状态时复用 `/api/status` 的 `operation_panel`，自动更新首屏主结论、主按钮和下一步。
  - 仍保留 `#automation-scorecard`：8 个 weighted gates，当前 `28/100`，2/8 通过，6/8 阻塞，P0=2。
- 当前真实 runtime 状态（2026-06-15 19:39 AEST smoke）：
  - `/api/status.operation_panel`：`headline=当前不要新增下注`，`primary_label=填写 TT-001`，`primary_href=#team-total-manual-entry`。
  - `current_executable_new_stake_aud=0`。
  - `raw=blocked` / `freshness_status=stale_research_only`。
  - provider events `64`，The Odds API remaining `201`，credit reserve floor `200`，不继续 batch。
  - blockers：Value-support paused、Team Total manual_required、Credit runway paused、My Bets login_required。
- 验证：
  - `python3 -m py_compile tab-research-pipeline/scripts/tab_fifa_app_server.py tab-research-pipeline/scripts/build_downloads_app_entry.py tab-research-pipeline/tests/test_pipeline.py` OK。
  - Focused tests：`test_local_app_status_section_payload_returns_single_status_block` OK；`test_local_app_private_position_bootstrap_contract` OK。
  - `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py` OK，Downloads HTML、runtime HTML、`.app` 已重建。
  - LaunchAgent `com.linzezhang.tab-fifa-research` 已 `kickstart -k` 重启。
  - API smoke：`/api/health`、`/api/status.operation_panel`、`/api/status.automation_scorecard` OK。
  - Browser smoke：`#operation-panel` 可见，`当前不要新增下注`、`TT-001`、`AUD 0`、导航入口存在，desktop overflow `0`。
  - Full suite：`Ran 206 tests in 357.434s OK`。
  - `git diff --check` OK；tracked secret scan 未命中真实 The Odds API key。
- 安全边界不变：
  - 本轮未运行 provider refresh，未消耗 The Odds API credits。
  - 未访问 TAB 下注页动作、未点击赔率、未修改 Bet Slip、未自动下注。
  - 真实 API key 只能放 ignored local env 或 shell env，不进入 Git。
- 下一步：
  - 继续 `TT-001` Team Total O/U 人工只读录入或解决 OpticOdds 官方访问/白名单。
  - 完成 My Bets 只读持仓快照，才能同步已下注、余额和累计收益率。
  - credit runway 恢复安全前，不继续 The Odds API batch。
  - formal publish/full automation 仍为 `false`，新增可执行下注金额继续为 `AUD 0`。

## 最新追加更新（2026-06-14 06:55 AEST）

- 新增 Alternate Markets / 盘口覆盖工作台：
  - 首页 section：`#alternate-market-workbench`
  - 导航新增：`盘口覆盖`
  - API：`/api/status.provider_alternate_workbench`
  - 首页 `Provider 采集控制台` 和 `Provider KPI` 现在优先读取完整 `provider_alternate_plan_latest.json`，不再只依赖压缩 KPI summary。
- 当前真实 runtime 状态：
  - refresh：`20260613T194716Z-provider-2fec0bef`
  - event_count：`64`
  - market_family_count：`6`
  - 已达阈值：`2`（Handicap、Total O/U）
  - Team Total：`manual_or_official_required`，继续 `TT-001 / OpticOdds`
  - Value-support 缺口：BTTS、Double Chance、Draw No Bet 因 credit runway 暂停 API batch。
  - credit runway：`next_batch_would_cross_reserve`，剩余 `201`，下一批预计 `4-7` credits，会跌破 `200` reserve floor。
  - `current_executable_new_stake_aud=0`，formal publish/full automation 仍为 `false`。
- 验证：
  - `python3 -m py_compile scripts/tab_fifa_app_server.py scripts/build_downloads_app_entry.py tests/test_pipeline.py` OK。
  - Focused tests：`test_local_app_status_section_payload_returns_single_status_block` OK；`test_provider_command_center_blocks_api_batch_when_next_batch_crosses_credit_reserve` OK；`test_local_app_private_position_bootstrap_contract` OK。
  - Full suite：`Ran 206 tests in 17.856s OK`。
  - `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py` OK，Downloads app/html/assets 已重建。
  - LaunchAgent `com.linzezhang.tab-fifa-research` 已 `kickstart -k` 重启。
  - API smoke：`/api/status.provider_alternate_workbench`、`/api/status.provider_command_center`、`/api/health` 均 OK。
  - Browser smoke desktop/mobile：新增工作台可见，包含 `暂停 API 补齐`、`TT-001 / OpticOdds`、`Double Chance`，console error `0`，全页横向溢出 `0`。
  - `git diff --check` OK；tracked secret scan 未命中真实 The Odds API key。
- 安全边界不变：
  - 本轮未运行 provider refresh，未消耗 The Odds API credits。
  - 未点击 TAB、未修改 Bet Slip、未自动下注。
  - 推荐命令只作为人工终端命令展示；credit 不安全时不执行。
- 下一步：
  - 继续 `TT-001` 人工只读填写 Team Total Over/Under，或解决 OpticOdds 官方访问/白名单。
  - 如 The Odds API 额度恢复到 reserve floor 以上，才允许重新评估小批量 non-Team-Total value-support probe。
  - My Bets 仍需只读 profile 登录快照，formal publish/full automation 解锁前 stake 继续为 `AUD 0`。

## 最新追加更新（2026-06-14 06:41 AEST）

- 新增 TT-001 Team Total 网页录入工作台：
  - 首页 section：`#team-total-manual-entry`
  - 导航新增：`TT-001录入`
  - API：`GET /api/manual-team-total-entry`
  - API：`POST /api/manual-team-total-entry`
- 录入模式从 16 行 CSV 改为 8 场比赛表单：
  - 每场填写 `tab_match_name`、`team_scope`、`tab_market_name`、`line`、`Over odds`、`Under odds`、`observed_at_aest`、`operator_initials`、`evidence`、`verification_status`。
  - 保存时后端固定展开成 `outputs/manual_verification/provider_team_total_manual_verification.csv` 的 Over/Under 两行。
  - 未填完整的比赛保持 `pending` 空行，不写入半成品 invalid row，避免污染 hash gate。
- 服务端安全边界：
  - POST 继续使用本地 action token、Origin/Referer/Host 检查。
  - JSON body 限制 128KB。
  - 不接受用户传入路径，只写固定 `DEFAULT_IMPORT_RELATIVE_PATH`。
  - 保存后复用现有 `write_provider_manual_verification_bundle()`，不新增另一套校验模型。
  - 不触发 provider refresh、不消耗 The Odds API credits、不点击 TAB、不修改 Bet Slip、不自动下注。
- 当前真实 API smoke：
  - `/api/manual-team-total-entry` 返回 `ready=true`、`event_count=8`、`row_count=16`、`current_executable_new_stake_aud=0`。
  - `/api/status.automation_work_queue` 返回 `next_task_id=TT-001`、`credit_runway_status=next_batch_would_cross_reserve`、Team Total missing `64`、下一批 `16` 行。
  - 生产 import 文件仍不存在：`outputs/manual_verification/provider_team_total_manual_verification.csv` 未被 smoke 写入。
- Browser smoke：
  - Desktop 1280px：TT-001 录入区块可见，8 行，保存按钮和 AEST 时间按钮可见，body overflow `0`，section overflow `0`，console error `0`。
  - Mobile 390px：TT-001 录入区块可见，8 行，body/document overflow `0`；宽表只在内部 table-scroll 横向滚动，console error `0`。
- 验证：
  - `python3 -m py_compile scripts/tab_fifa_app_server.py scripts/build_downloads_app_entry.py` OK。
  - Focused tests：`5 tests OK`。
  - Full suite：`Ran 206 tests in 21.334s OK`。
  - `git diff --check` OK。
  - tracked secret scan 未命中真实 The Odds API key；只命中 example/test 的 `replace_with...` 占位值。
- 剩余 gate 不变：
  - TT-001 仍需用户/操作员按 TAB 页面只读填写真实 Team Total Over/Under。
  - The Odds API credit runway 当前不允许继续 batch。
  - OpticOdds 仍需官方访问/白名单。
  - My Bets 仍需只读 profile 登录快照。
  - formal publish/full automation 仍为 `false`，新增可执行下注金额保持 `AUD 0`。

## 最新追加更新（2026-06-14 06:25 AEST）

- 新增 runtime `position_monitor` status endpoint：
  - `/api/status.position_monitor`
  - 来源：`outputs/position_monitor_latest.json` + current private bootstrap fallback
  - 目的：让 app/agent 通过同一 status API 读取持仓监控 gate，而不是只读静态 PDF/HTML。
- 当前真实 HTTP 返回：
  - `ready=false`
  - `artifact_ready=true`
  - `status=blocked`
  - `report_date=14062026`
  - `snapshot_ready=false`
  - `profile_exists=true`
  - `raw_text_exists=false`
  - `snapshot_exists=false`
  - `public_visible_balance=account-update-pending`
  - `current_executable_new_stake_aud=0`
- `automation_work_queue_payload` 现在用 `position_monitor_status` 判断 `MY-BETS-READONLY`：
  - blocker 来自 position monitor preflight
  - evidence 为 `profile_exists=True; snapshot_exists=False`
  - 保持只读持仓边界，不自动下注、不点击赔率、不改 Bet Slip。
- 已重启 LaunchAgent：
  - label：`com.linzezhang.tab-fifa-research`
  - endpoint：`http://127.0.0.1:8767/`
  - HTTP smoke 已确认 `/api/status.position_monitor` 和 `/api/status.automation_work_queue` 均返回 200。
- 验证：
  - `python3 -m py_compile tab-research-pipeline/scripts/tab_fifa_app_server.py` OK。
  - Focused tests：`2 passed, 203 deselected`。
  - Full suite：`205 passed, 5 warnings in 14.61s`。
- 边界不变：automation 未解锁，formal publish 未解锁，stake `AUD 0`；The Odds API batch 仍因 reserve guard 暂停。

## 最新追加更新（2026-06-14 06:18 AEST）

- 新增平台级 `Automation 工作队列`，作为后续 agent/网页用户的主任务入口：
  - API endpoint：`/api/status.automation_work_queue`
  - 首页 section：`#automation-work-queue`
  - 导航新增：`工作队列`
  - 只读边界：不运行 provider refresh、不消耗 credits、不点击 TAB、不修改 Bet Slip、不自动下注。
- 当前队列状态：
  - `automation_ready=false`
  - `current_executable_new_stake_aud=0`
  - `task_count=6`
  - `blocked_count=6`
  - `p0_count=2`
  - `next_task_id=TT-001`
  - `team_total_missing_event_count=64`
  - `team_total_next_batch_pair_rows=16`
  - `credit_runway_status=next_batch_would_cross_reserve`
- 当前任务顺序：
  1. `TT-001:manual_required` - 填写 16 行 Team Total O/U，只读核验 TAB。
  2. `CREDIT-RESERVE:credit_or_yield_blocked` - 暂停 The Odds API batch，避免跌破 200 credits reserve。
  3. `OPTICODDS-ACCESS:provider_access_required` - 解决官方访问/白名单。
  4. `MY-BETS-READONLY:login_required` - 登录 profile 后只读同步持仓。
  5. `FORMAL-PUBLISH-GATE:blocked_until_manual_signature` - 等 hash/overlay/preflight/user signature。
  6. `AUTOMATION-READINESS:not_ready` - 等 P0/P1 gate 关闭后再跑最终 readiness。
- 首页复制按钮 fallback 已改进：浏览器未授权 clipboard 时直接显示完整命令，例如 `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`。
- 验证：
  - `python3 -m py_compile tab-research-pipeline/scripts/tab_fifa_app_server.py` OK。
  - `python3 -m py_compile tab-research-pipeline/scripts/build_downloads_app_entry.py` OK。
  - Focused tests：`2 passed, 203 deselected`。
  - Full suite：`205 passed, 5 warnings in 14.34s`。
  - API smoke `/api/status.automation_work_queue` OK。
  - Browser smoke desktop/mobile OK，console error `0`，mobile `390px` 无全页横向溢出。
- 下一步仍是 `TT-001`：人工只读填写 `outputs/manual_verification/provider_team_total_manual_verification.csv` 的 16 行 Team Total Over/Under，再运行 rebuild command；不继续 The Odds API batch，除非 credit runway 重新变为 safe。

## 最新追加更新（2026-06-14 06:04 AEST）

- Team Total `TT-001` 工作台新增 `manual_intake_contract`，并已进入 JSON/MD/PDF/API/首页：
  - template：`provider_manual_next_batch_pair_template_latest.csv`
  - import target：`outputs/manual_verification/provider_team_total_manual_verification.csv`
  - rebuild command：`TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`
  - current state：missing `64`、partial `0`、invalid `0`、complete `0`、next batch pair rows `16`、stake `0`
  - acceptance criteria：下一批无 missing/invalid、manual import 无 invalid、hash/overlay/preflight 逐步通过、formal publish 在签名前保持 false、stake 保持 0
  - forbidden：自动下注、点击赔率、加入 Bet Slip、提交或修改 wagering ticket、绕过 TAB 访问控制
- `/api/status.provider_manual_workbench` 与 `/api/status.provider_command_center` 均暴露同一 `manual_intake_contract`，后续 agent 不需要从 PDF 里读步骤。
- 首页 `人工校验导入状态` 新增 `TT-001 Intake Contract`、导入步骤、验收条件、复制导入目标、复制重建命令；复制反馈已支持通用 label。
- 已重建 Downloads app，并同步 24 个 manual latest artifacts 到 `artifacts/latest/`。
- 验证：`py_compile` OK；focused tests `3 OK`；full suite `Ran 205 tests in 13.329s OK`；API smoke OK；Browser desktop/mobile overflow `0`、console error `0`。
- 下一步：人工只读填写 `TT-001` 的 16 行 Team Total Over/Under，保存到 import target 后运行 rebuild command；不继续消耗 The Odds API credits。

## 最新追加更新（2026-06-14 05:55 AEST）

- 真实 API key 放置方式已确认：只放 ignored `config/odds_providers.local.env` 或 shell env；tracked `config/odds_providers.local.env.example` 保持固定文件名和占位值，不放真实 key、不改名。
- 本机 ignored env 已同步当前非敏感 provider 参数：`TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup`，`TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY=1`，event odds markets 为 `alternate_totals,alternate_spreads,btts,double_chance,draw_no_bet`。
- 已继续完成 3 轮 The Odds API value-support 小批量补齐，最新 refresh `20260613T194716Z-provider-2fec0bef`：
  - non-Team Total queue `53 -> 50`。
  - usage `used=299`、`remaining=201`、latest cost `7`。
  - Result `64/64`，Handicap `46/64`，Total O/U `51/64`，BTTS `14/64`，Double Chance `11/64`，Draw No Bet `12/64`，Team Total `0/64`。
- 新增 credit runway guard：
  - reserve floor `200` credits。
  - 下一批预计 `4-7` credits；当前 remaining `201`，下一批后最低 `194`。
  - `/api/status.provider_command_center.can_run_provider_batch=false`，`credit_runway.status=next_batch_would_cross_reserve`。
  - 首页 Provider 采集控制台显示 `下一批会破保底` 和 `暂停 API`；推荐转 `TT-001` 或 OpticOdds。
- 已重建 Downloads app、重启 LaunchAgent，并同步 25 个 public-safe latest artifacts 到 `artifacts/latest/`。
- 验证：`py_compile` OK；focused tests `2 OK`；完整 suite `Ran 205 tests in 13.210s OK`；API smoke OK；Browser desktop/mobile overflow `0`、console error `0`；`git diff --check` OK；tracked secret scan 无命中。
- 下一步：暂停 The Odds API 新增 batch，先做 Team Total `TT-001` 人工只读校验或解决 OpticOdds 官方访问/白名单；formal publish/full automation 仍为 `false`，stake `AUD 0`。

## 最新追加更新（2026-06-14 05:40 AEST）

- The Odds API credit-safe batch `1` 已继续推进到 refresh `20260613T193148Z-provider-0bf93159`，cost `7`，non-Team Total probe queue `58 -> 53`。
- 当前 provider state：event count `64`；Result `64/64`，Handicap `46/64`，Total O/U `51/64`，BTTS `11/64`，Double Chance `8/64`，Draw No Bet `9/64`，Team Total `0/64`。
- Usage：used `278`，remaining `222`，remaining ratio `44.40%`；recommended next batch 仍为 `1`，estimated total credit `4-7`，command `double_chance,draw_no_bet,btts`。
- 新增首页 `Provider 采集控制台` 和 API `/api/status.provider_command_center`：显示 API batch、Team Total TT-001、credit、gate、推荐命令、停止条件、覆盖进度条和下一批队列。
- 复制推荐命令按钮已做剪贴板失败降级：自动复制失败时提示手动复制下方命令，不误报成功。
- LaunchAgent `/Users/linzezhang/Library/LaunchAgents/com.linzezhang.tab-fifa-research.plist` 已改为 `KeepAlive=true` 并重新加载；`http://127.0.0.1:8767/api/health` 返回 OK。
- 已重建 Downloads app 并同步 latest artifacts 到 GitHub `artifacts/latest/`。
- 验证：`py_compile` OK；focused app status test `1 OK`；full suite `204 tests in 12.816s OK`；API smoke provider command center OK；Browser smoke desktop/mobile overflow `0`、console error `0`。
- Gate 不变：formal publish `false`，full automation `false`，stake `AUD 0`；Team Total 仍走 OpticOdds 官方访问/白名单或 TT-001 人工只读校验。

## 最新追加更新（2026-06-14 05:20 AEST）

- 修正 provider alternate plan 的 credit 估算：下一批 `estimated_next_batch_credit` 现在包含 primary odds refresh 基础成本。当前 batch `1` 的真实估算从旧 `1-4` 改为 `4-7` credits，与最新实际 cost `7` 对齐。
- 修正 value-support 队列优先级：`recommended_markets` 现在按覆盖缺口排序为 `double_chance,draw_no_bet,btts`，优先补更稀缺的 Double Chance / Draw No Bet。
- 加固 event selector：无 plan queue 时也会跳过已做过 event-market probe 的事件，避免只 probe 过但未返回目标 odds 的事件被重复消耗。
- 执行一轮修正后的 batch：`20260613T191940Z-provider-371af48a`，cost `7`，queue `59 -> 58`；BTTS `9/68 -> 10/68`，Double Chance `6/68 -> 7/68`，Draw No Bet `7/68 -> 8/68`。
- 当前 usage：used `271`，remaining `229`，remaining ratio `45.80%`。继续 batch `1` 仍可行，但如连续低增量应暂停 The Odds API，转 OpticOdds 或 TAB 人工。
- 已重建 Downloads app 并同步 latest artifacts 到 `artifacts/latest/`。
- 本轮最终验证：`py_compile` OK；focused credit/selector tests `5 tests OK`；完整 suite `Ran 204 tests in 13.061s OK`；API smoke `/api/status` 返回 refresh `20260613T191940Z-provider-371af48a`、queue `58`、batch `1`、credit `4-7`、command `double_chance,draw_no_bet,btts`、stake `0`，`/api/status.provider_kpi` equivalent field `overall_progress_pct=0.615`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示 latest refresh、`4-7`、命令顺序、BTTS `10/68`、Double Chance `7/68`、Draw No Bet `8/68`、Team Total `0/68`、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露。
- 不变 gate：formal publish `false`，full automation `false`，current executable new stake `AUD 0`；Team Total 仍为 `0/68`。

## 最新追加更新（2026-06-14 05:10 AEST）

- 已继续执行 The Odds API credit-conservation batch `1`，并发现/修复一个会浪费 credits 的事件选择问题：
  - `20260613T190633Z-provider-b35cbe30`：cost `5`，queue 仍为 `60`，覆盖无新增；根因是 refresh 脚本没有优先使用 `provider_alternate_plan_latest.json.next_probe_queue`，可能重复抓取已做过 event_odds 的部分覆盖事件。
  - 已修复：`refresh_odds_provider_raw.py` 现在优先按 plan queue 选择 event；没有 plan queue 时跳过已有 `event_odds_event_ids`，避免同一事件反复消耗。
  - `20260613T190906Z-provider-404dcf06`：cost `5`，queue `60 -> 59`，BTTS `8/68 -> 9/68`。
- 最新 coverage：Result `68/68`，Handicap `50/68`，Total O/U `55/68`，BTTS `9/68`，Double Chance `6/68`，Draw No Bet `7/68`，Team Total `0/68`。
- The Odds API usage：used `264`，remaining `236`，last cost `5`，remaining ratio `47.20%`。继续 batch `1`，但若连续低增量应暂停 API 并转 OpticOdds/TAB 人工。
- 首页 Provider KPI 新增 `额度效率` 和 `Value-support 覆盖` 卡片；Downloads app 和 latest artifacts 已重建/同步。
- 本轮最终验证：`py_compile` OK；focused provider selector/alternate tests `4 tests OK`；完整 suite `Ran 202 tests in 13.876s OK`；API smoke `/api/status.provider_kpi` 返回 refresh `20260613T190906Z-provider-404dcf06`、`overall_progress_pct=0.615`、stake `0`；API smoke `/api/status` 返回 provider alternate `in_progress`、queue `59`、batch `1`、credit `1-4`、stake `0`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示 latest refresh、`额度效率`、`Value-support 覆盖`、batch `1`、BTTS `9/68`、Double Chance `6/68`、Draw No Bet `7/68`、Team Total `0/68`、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露；`git diff --check` OK；tracked secret scan 无命中。
- 不变 gate：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-14 04:55 AEST）

- 已连续执行 3 轮 The Odds API credit-safe alternate/value-support 小批量补齐：
  - `20260613T185314Z-provider-083b0da8`，cost `18`，queue `68 -> 65`。
  - `20260613T185358Z-provider-c45e751e`，cost `13`，queue `65 -> 62`。
  - `20260613T185434Z-provider-ee1955d8`，cost `12`，queue `62 -> 60`。
- 最新 coverage：Result `68/68`，Handicap `50/68`，Total O/U `55/68`，BTTS `8/68`，Double Chance `6/68`，Draw No Bet `7/68`，Team Total `0/68`。
- Handicap 与 Total O/U 已达到当前 `70.00%` 可用阈值；value-support markets 进入真实覆盖阶段但仍未达到 `35.00%` 阈值。
- The Odds API usage：used `254`，remaining `246`，last cost `12`，remaining ratio `49.20%`。系统已自动从 batch `3` 降速到 batch `1`，下一批预计 `1-4` credits。
- KPI 当前 `61.50%`；覆盖增加但 credit reserve 降至 `<50%` 后 KPI 风控分回落，这是预期的 credit policy 行为。
- 推荐下一步命令：

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 1 --event-odds-limit 1 --event-odds-markets btts,double_chance,draw_no_bet
```

- 已重建 Downloads app 并同步 public-safe latest artifacts 到 GitHub worktree。
- 本轮最终验证：`py_compile` OK；focused provider/status tests `4 tests OK`；完整 suite `Ran 200 tests in 13.259s OK`；API smoke `/api/status` 返回 refresh `20260613T185434Z-provider-ee1955d8`、`probe_queue_count=60`、batch `1`、credit `1-4`、KPI progress `0.615`、stake `0`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示 latest refresh、batch `1`、KPI `61.50%`、BTTS/Double Chance/Draw No Bet coverage、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露；`git diff --check` OK；tracked secret scan 无命中。
- 不变 gate：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。Team Total 仍需 OpticOdds 官方访问/白名单或 TAB 人工最终校验；不自动下注，不点击 TAB 赔率。

## 最新追加更新（2026-06-14 04:38 AEST）

- 已把 alternate markets 从“Team Total 低收益后完全 fallback”升级为“非 Team Total 可小批量补齐，Team Total 继续人工/官方路径”：
  - `provider_alternate_plan_latest.json.status=in_progress`
  - `operational_decision.status=alternate_probe_plus_team_total_manual`
  - `probe_queue_count=68`
  - `fallback_queue_count=68`
  - `recommended_batch_size=3`
  - estimated credit range `3-18`
- The Odds API 当前 event-market 样本显示这些非 Team Total market 可见：`spreads`、`totals`、`btts`、`double_chance`、`draw_no_bet`、`h2h` 均为 `3/3`；Team Total 仍为 `0/3`。
- 默认 event odds markets 已改为 credit-safe value-support 队列：`alternate_totals,alternate_spreads,btts,double_chance,draw_no_bet`；不再把 `team_totals` 放进默认 probe，避免 500 credits/月额度被低收益盲扫消耗。
- 推荐下一步命令：

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 3 --event-odds-limit 3 --event-odds-markets spreads,alternate_spreads,btts,double_chance,draw_no_bet
```

- Provider KPI 已更新为 `60.00%`，primary gap 仍是 `Team Total Score O/U 覆盖: 0/68 (0.00%)`；formal publish `false`、full automation `false`、current executable new stake `AUD 0`。
- Provider config doctor 仍为 `ready`；The Odds API key present 为 `true`，OpticOdds key present 当前为 `false`；真实 key 只允许放在 ignored local env，不允许提交 GitHub。
- 已重建 Downloads 入口与 app bundle，并同步最新 public-safe artifacts 到 `artifacts/latest/`：provider alternate plan/evidence、provider KPI、provider config doctor、dashboard PDF。
- 本轮验证：目标 py_compile + provider/alternate/status 回归测试 OK；完整 suite `python3 -m unittest tab-research-pipeline.tests.test_pipeline` -> `Ran 200 tests in 13.162s OK`；API smoke `/api/status` 返回 `in_progress / alternate_probe_plus_team_total_manual / probe_queue_count=68 / batch=3 / credit=3-18 / stake=0`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示新决策、BTTS/Double Chance/Draw No Bet、batch 3、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露。
- 剩余 gate 不变：Team Total 仍需 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验；My Bets 私有持仓和完整 formal automation gate 未通过前，不发布正式下注日报、不产生新增下注金额。

## 最新追加更新（2026-06-14 04:24 AEST）

- 已修复用户反馈的 raw 命令问题：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches` 当前成功返回 `provider_raw_staged`，active refresh id `20260613T181704Z-provider-1d88f0e3`。
- The Odds API 当前 `/v4/sports` discovery 显示 `soccer_fifa_world_cup` active；最小 h2h 请求成功，随后主盘口 `h2h,totals,spreads` refresh 成功。reported usage 当前 used `208`，remaining `292`，latest request cost `3`。
- 已支持“不改文件名”的本机 env fallback：`refresh_odds_provider_raw.py` 会在 `config/odds_providers.local.env`、`.env` 后读取 `config/odds_providers.local.env.example`，但会跳过 `replace_with...` 占位值；提交前仍必须 secret scan，不能把真实 key 推上 GitHub。
- Provider config doctor 已同步同一 fallback 规则：如果只存在 `.local.env.example` 会显示 `provider_example_env_fallback_in_use` warning；当前本机仍使用 ignored `.local.env`，doctor status `ready`。
- Unknown Sport blocked 输出已增强：`odds_provider_adapter` 的 HTTP 错误会附带 `provider_request_context(...)`，`write_blocked_provider_payload` 会输出 discovery/credit-safe 诊断，明确不要在 Unknown Sport 状态下开启 Team Total/event probe。
- Team Total 人工导入质量诊断已完成：`provider_manual_verification_status_latest.json.import_quality`、`provider_manual_workbench_latest.json.import_quality`、`next_batch_quality`、`quality_gate_summary` 已生成。当前状态 `waiting_for_manual_rows`，missing events `68`，TT-001 下一批 `8` 场均为 `missing_rows`，缺字段/缺 Over-Under 方向已逐场列出。
- 首页 `人工校验导入状态` 已新增 `质量 Gate` 与 `质量诊断` 表格，字段检查完整显示 11 项；`/api/status.provider_manual_workbench` 暴露 `import_quality`、`next_batch_quality`、`quality_gate_summary`。
- 已重建 Downloads 入口与 app assets：`/Users/linzezhang/Downloads/FIFA Report/TAB FIFA盘口研究系统.html`、`/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`。
- 已同步 public-safe artifacts 到 `artifacts/latest/`：provider raw/coverage/KPI/config doctor/alternate plan/manual workbench/manual hash/overlay/publish-preflight 等 latest 产物。
- 验证：
  - `python3 -m unittest tab-research-pipeline.tests.test_pipeline` -> `Ran 200 tests in 13.494s OK`。
  - `py_compile` 覆盖 provider raw、adapter、config doctor、manual verification、app builder、server。
  - API smoke：config doctor `ready`，manual workbench `waiting_for_first_batch`，quality gate `waiting_for_manual_rows`，next batch missing rows `8`，stake `AUD 0`。
  - Browser smoke：desktop `1280px` 与 mobile `390px` 均显示 `质量 Gate`、`质量诊断`、`missing_rows`、`TT-001`；document/body/manual section overflow `0`，console error `0`。
- 剩余 gate 不变：Team Total 仍无真实官方/API/manual 完整数据；formal publish `false`、full automation `false`、current executable new stake `AUD 0`。

## 最新追加更新（2026-06-14 04:08 AEST）

- Team Total 人工补齐工作台已升级为操作台闭环：
  - `provider_manual_workbench_latest.json.operator_cockpit`
  - `next_batch_summary`
  - `field_checklist`
  - `workflow_steps`
  - `action_contract`
- 当前操作台状态：
  - current batch `TT-001`
  - next batch event count `8`
  - required pair rows `16`
  - field checklist `8`
  - workflow steps `5`
  - publish status `blocked_until_manual_import_and_signature`
  - current executable new stake `AUD 0`
- 首页 `人工校验导入状态` 已新增 `TT-001 操作台`、`操作台流程`、`字段检查` 和下一批摘要；移动端长文件名已增加强制换行，避免横向溢出。
- `/api/status.provider_manual_workbench` 已暴露 `operator_cockpit`、`next_batch_summary`、`field_checklist`、`workflow_steps`、`action_contract`、`publish_status`、`can_publish_now`。
- 已同步 public-safe manual artifacts 到 `artifacts/latest/`，包括 workbench JSON/MD/PDF、manual import/hash/overlay/publish-preflight 产物和 CSV 模板。
- 验证：
  - 目标测试：manual workbench missing import、full queue no truncation、status API，`3 tests OK`。
  - 完整 suite：`python3 -m unittest tab-research-pipeline.tests.test_pipeline` -> `Ran 197 tests in 13.198s OK`。
  - `py_compile` OK；`git diff --check` OK；tracked secret scan `0`。
  - API smoke：`/api/status.provider_manual_workbench` 返回 `TT-001`、publish status `blocked_until_manual_import_and_signature`、field count `8`、workflow count `5`、stake `0`。
  - Browser smoke：desktop `1280px` 与 mobile `390px` 均显示 `TT-001 操作台`、`字段检查`、`操作台流程`、publish blocked 状态；document overflow `0`，section overflow `0`，console error `0`。
- 剩余 gate 不变：Team Total 仍需人工 CSV/OpticOdds 官方允许访问后才能进入签名发布；未通过 gate 前 formal publish `false`、full automation `false`、stake `AUD 0`。

## 最新追加更新（2026-06-14 03:56 AEST）

- 用户反馈直接运行 `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches` 曾返回 The Odds API `UNKNOWN_SPORT`。当前本机复测已成功，active refresh id 为 `20260613T175342Z-provider-9141af88`。
- 根因边界：`config/odds_providers.local.env.example` 不需要、也不应该改名成入库 secret 文件；真实 key 保持在 ignored `config/odds_providers.local.env`。旧错误通常来自 shell/旧配置里的 `soccer_world_cup` 或关闭 sports discovery。
- 本轮已加请求级保护：`tab_research/odds_provider_adapter.py` 新增 `normalize_the_odds_api_sports_config()`，即使 discovery 关闭或 shell 注入旧 `soccer_world_cup`，请求构造前也会收敛到当前 scope 的有效 key：
  - matches -> `soccer_fifa_world_cup`
  - futures -> `soccer_fifa_world_cup_winner`
  - all -> matches + futures 默认 key
- `refresh_odds_provider_raw.py` 已使用同一规范化结果传给 event-level probe，避免主刷新成功但补盘口 probe 因旧 sport key 跳过。
- 最新 provider 状态：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `55/68`
  - Team Total O/U `0/68`
  - KPI `53.50%`
  - reported used `207` / remaining `293` / last cost `3`
  - current executable new stake `AUD 0`
- 已同步 public-safe artifacts 到 `artifacts/latest/`：`odds_provider_raw_latest.json`、`odds_provider_coverage_latest.json`、`provider_kpi_latest.*`、`provider_config_doctor_latest.*`、`provider_alternate_plan_latest.*`、`provider_alternate_probe_evidence_latest.json`。
- 验证：
  - `python3 scripts/build_provider_config_doctor.py` -> `status=ready`，issue count `0`，legacy sport count `0`。
  - `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --timeout-seconds 30` -> `ok=true`，`provider_raw_staged`。
  - 目标测试：legacy sport 映射、sports catalog filter、config doctor redaction/blocking，`4 tests OK`。
  - `py_compile` OK；`git diff --check` OK。
- 当前边界不变：The Odds API 主盘口可 staging；formal publish `false`，full automation `false`，Team Total 仍需 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验，不解锁新增下注金额。

## 最新追加更新（2026-06-14 03:46 AEST）

- The Odds API Matches 主盘口 refresh 已成功，active refresh id 为 `20260613T173737Z-provider-e531900e`；当前未复现 `UNKNOWN_SPORT`。
- `refresh_odds_provider_raw.py` 成功后会同步重建 `provider_kpi_latest.*`；CLI 输出新增 `provider_kpi_refresh_id`、`provider_kpi_status`、`provider_kpi_primary_gap`，防止 raw/coverage 与 KPI refresh id 漂移。
- `provider_alternate_probe_evidence_latest.json` 已新增并写入 outputs/app_assets/artifacts/latest，用于持久保存 event-market evidence。普通 `h2h,totals,spreads` refresh 不再抹掉 Team Total 低收益证据。
- 当前 provider 状态：
  - refresh `20260613T173737Z-provider-e531900e`
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `55/68`
  - Team Total O/U `0/68`
  - KPI `53.50%`
  - used `204` / remaining `296` / last cost `3`
  - current executable new stake `AUD 0`
- 当前 alternate plan：
  - status `fallback_required`
  - event-market sample `3`
  - Team Total available sample `0`
  - Total O/U available sample `3`
  - probe queue `0`
  - fallback queue `68`
  - operational decision `manual_or_official_provider_priority`
- UI/API 更新：
  - Provider KPI 卡片显示 `历史失败`，并明确“不代表当前 refresh 失败”。
  - stale blocked attempt 在 KPI 中标记 `stale_history_only=true`。
  - `/api/status.provider_alternate_plan` 输出 event_probe_evidence counts。
  - Downloads app assets 包含 `provider_alternate_probe_evidence_latest.json`。
- 验证：
  - `python3 -m unittest tab-research-pipeline.tests.test_pipeline` -> `Ran 197 tests in 15.130s OK`
  - 目标测试覆盖 KPI 同步、历史 blocked 标识、跨 refresh 持久低收益证据、status API。
  - API smoke `/api/status` OK；browser desktop `1280px` 与 mobile `390px` 无 overflow，console error `0`。
- 下一步：不要继续 The Odds API Team Total 盲扫；Team Total 走 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验。人工路径从 `provider_manual_next_batch_pair_template_latest.csv` 的 `TT-001` 开始。

## 最新追加更新（2026-06-14 03:27 AEST）

- Provider alternate plan 已新增运营决策层：
  - `operational_decision.status=manual_or_official_provider_priority`
  - title：`Team Total 转人工/官方访问优先`
  - primary action：先处理 `TT-001` 人工校验或 OpticOdds 官方访问，不再默认扩大 The Odds API Team Total probe。
- Team Total low-yield 判定已落地：
  - The Odds API 3 个 TAB event-market 样本均未暴露 Team Total market key。
  - `team_total_ou.status=fallback_required`
  - `provider_status=low_yield_in_current_the_odds_api_tab_sample`
  - `probe_queue_count=0`
  - `fallback_queue_count=68`
- 首页 `Provider 覆盖与缺口` 新增 `运营决策` banner；`今日决策中心` 的 Provider 行显示运营动作。
- `/api/status.provider_alternate_plan` 现在对 `fallback_required` 返回 `ready=true`，并输出 `operational_decision`。
- 当前验证：目标测试 `2 tests OK`；完整 suite `193 tests OK`；API smoke for provider alternate/KPI OK；Browser desktop `1280px` 与 mobile `390px` 均显示运营决策且无横向 overflow，console error `0`；`py_compile`、`git diff --check`、secret scan OK。
- 当前边界不变：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-14 03:13 AEST）

- Provider live path 已继续推进：
  - `soccer_world_cup` 旧 sport key 已由配置医生收敛到 `soccer_fifa_world_cup`。
  - 本机 Python 缺 CA bundle 导致的 The Odds API `CERTIFICATE_VERIFY_FAILED` 已修复为 certifi TLS fallback；不禁用 TLS。
  - `refresh_odds_provider_raw.py` 的历史 merge keys 已修复，Team Total 小批量 probe 不再让历史 Total O/U 覆盖倒退。
- 最新 live refresh：
  - 主盘口：`20260613T170821Z-provider-2f478c14`。
  - Team Total 小批量 event-market probe：`20260613T170935Z-provider-1b4980a2`。
  - provider payload count `4`；request kinds：`odds=1,event_markets=3`。
  - reported used `201`，remaining `299`，last cost `6`。
- 最新覆盖：
  - Matches `68`
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `55/68`
  - Team Total O/U `0/68`
  - Provider KPI `66.5%`
- 最新状态：
  - `provider_config_doctor_latest.*` status `ready`
  - `provider_kpi_latest.*` status `in_progress`
  - `provider_alternate_plan_latest.*` status `in_progress`
  - formal publish `false`
  - full automation `false`
  - current executable new stake `AUD 0`
- 当前验证：完整 suite `python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 192 tests`，`OK`；`git diff --check` OK；`py_compile` OK；secret scan 无真实 key 命中；API smoke for provider config/KPI/workbench OK；Browser desktop `1280px` 与 mobile `390px` 无横向 overflow，console error `0`。
- 新增 artifact：`artifacts/latest/odds_provider_raw_latest.json`，用于交接 refresh id、request usage、staging manifest；不包含真实 key。
- 当前下一步：不要全扫 68 场；Team Total 走 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验。人工路径从 `provider_manual_next_batch_pair_template_latest.csv` 的 `TT-001` 开始。

## 最新追加更新（2026-06-14 02:54 AEST）

- 新增 Provider 配置医生：
  - `tab_research/provider_config_doctor.py`
  - `scripts/build_provider_config_doctor.py`
  - `provider_config_doctor_latest.json/md/pdf`
  - 首页 `Provider 配置医生`
  - `/api/status.provider_config_doctor`
- 当前本机状态：`ready`；The Odds API / OpticOdds key 均存在但不会写入 artifact；sports discovery 开启；本机 ignored env 已移除旧 sport `soccer_world_cup`；`TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup`；event probe limit `0`；stake `AUD 0`。
- 目的：阻止后续 agent 因旧 sport key 或关闭 discovery 再次触发 The Odds API `Unknown sport`，同时避免日常 automation 误开 event-level probe 浪费 500 credits/月额度。
- 当前验证：完整 suite `189 tests OK`；API smoke OK；Browser desktop/mobile smoke 显示配置医生、推荐 sport、Event Probe `0`、`AUD 0`，无横向 overflow，console error `0`；secret scan 无真实 key 命中。
- 安全边界：该模块只读取本机 ignored env 的存在性和非敏感参数，不请求 odds、不输出 key、不发布 raw、不下注。

## 最新追加更新（2026-06-14 02:39 AEST）

- Team Total 人工校验工作台新增成对录入模板：
  - `provider_manual_pair_template_latest.csv`：68 个候选 x Over/Under，共 136 行。
  - `provider_manual_next_batch_pair_template_latest.csv`：下一批 `TT-001` 的 8 场 x Over/Under，共 16 行。
- 首页人工导入区新增 `下一批成对模板`、`全量成对模板`、成对模板统计卡，并把下一批模板加入顶部快捷动作和文件清单。
- `/api/status.provider_manual_workbench` 新增成对模板字段：`all_pair_template_csv`、`next_batch_pair_template_csv`、`all_candidate_pair_rows`、`next_batch_pair_rows`。
- 当前验证：完整 suite `187 tests OK`；API smoke 返回 pair rows `136/16`；Browser desktop/mobile smoke 显示成对模板入口、`TT-001`、`16/136`、`AUD 0`，无横向 overflow，console error `0`。
- 安全边界：成对模板只减少人工填写错误，不代表已经取得 TAB 盘口；未填写人工 CSV 与签名前仍不发布 raw、不下注、stake `AUD 0`。

## 最新追加更新（2026-06-14 02:26 AEST）

- 修复 Team Total 人工 CSV 模板只覆盖 50/68 候选的截断问题；当前模板覆盖完整 68 行。
- 新增 Team Total 人工校验工作台：
  - `provider_manual_workbench_latest.json`
  - `provider_manual_workbench_latest.md`
  - `provider_manual_workbench_latest.pdf`
  - `/api/status.provider_manual_workbench`
  - 首页人工校验区显示 workbench 状态、批次数、下一批、剩余候选、下一批比赛表格。
- 当前 workbench 状态：`waiting_for_first_batch`；batch count `9`；next batch `TT-001`；next batch event count `8`；remaining `68`；high priority remaining `55`；stake `AUD 0`。
- 当前验证：完整 suite `187 tests OK`；API smoke OK；Browser desktop/mobile smoke OK。
- 安全边界：该 workbench 只组织人工只读校验，不自动登录 TAB、不点击 odds、不修改 Bet Slip、不发布正式 raw、不生成新增下注金额。

## 最新追加更新（2026-06-14 02:13 AEST）

- Team Total 人工 overlay 显式 publish 已完成本轮验证：
  - 完整测试：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 186 tests`，`OK`。
  - API smoke：`/api/status.provider_manual_overlay_publish` 返回 `blocked_overlay_publish_preflight`、stake `AUD 0`、未写正式 raw、未写 batch manifest。
  - Browser smoke：桌面 `1280px` 与移动 `390px` 都能看到 Overlay 发布链接、阻断状态、stake `AUD 0` 和安全提示；横向溢出 `0`，console error `0`。
- 新增通用只读子状态路由 `/api/status.<status_key>`；新增测试覆盖有效 key、未知 key 和非法 key。
- `README.md` / `RUNBOOK.md` 已补 Team Total manual overlay 命令和 fail-closed 边界。
- 未完成不变：真实 Team Total CSV、匹配 approval、My Bets 私有持仓、Australia Markets、5-board raw batch、正式日报 automation。

## 最新追加更新（2026-06-14 02:05 AEST）

- Team Total 人工 overlay 新增显式 publish 命令：
  - `publish_provider_manual_overlay.py`
  - `publish_provider_manual_overlay(output_dir)`
  - `provider_manual_overlay_publish_latest.json`
  - `provider_manual_overlay_publish_latest.md`
  - `provider_manual_overlay_publish_latest.pdf`
- `/api/status.provider_manual_overlay_publish` 已返回 ok、status、refresh_id、provider_refresh_id、manual hash、overlay raw hash、published raw、batch manifest、raw gate、issue_count 和 stake。
- 首页 `人工校验导入状态` 区块已显示 Overlay 发布状态、发布文件、batch manifest 状态和发布 Gate，动作链接新增 `Overlay发布` PDF。
- 当前状态：已运行一次 CLI，因未导入人工 CSV 且未签名，结果为 `blocked_overlay_publish_preflight`；`formal_raw_publish_performed=false`，`raw_batch_manifest_written=false`，stake `AUD 0`。
- 安全边界：即使 publish 成功，也只发布 Matches raw slot；不写 5-board batch manifest，不解锁 full automation，不自动下注，不点击 TAB。
- 当前验证：provider manual overlay publish 目标测试 2 个 OK；provider manual overlay 全目标测试 5 个 OK；完整 suite 186 个 OK；API 子状态 smoke OK；Browser 桌面/移动 smoke OK；`py_compile` OK；Downloads app build OK。

## 最新追加更新（2026-06-14 01:56 AEST）

- Public Raw Snapshot 导入器新增显式 raw publish 命令：
  - `publish_public_snapshot_raw.py`
  - `publish_public_snapshot_raw(output_dir)`
  - `public_snapshot_raw_publish_latest.json`
  - `public_snapshot_raw_publish_latest.md`
  - `public_snapshot_raw_publish_latest.pdf`
- `/api/status.public_snapshot_raw_publish` 已返回 ok、status、refresh_id、approval hash、published raw、raw batch manifest、raw gate、issue_count 和 stake。
- 首页 `Public Raw Snapshot 导入` 区块已显示 Raw 发布状态、发布文件、batch manifest 状态和 Raw Gate 状态，动作链接新增 `Raw发布` PDF。
- 当前状态：已运行一次 CLI，因未导入有效 snapshot 且未签名，结果为 `blocked_publish_preflight`；`formal_raw_publish_performed=false`，`raw_batch_manifest_written=false`，stake `AUD 0`。
- 安全边界：即使 publish 成功，也只发布 Matches raw slot；不写 5-board batch manifest，不解锁 full automation，不自动下注，不点击 TAB。
- 当前验证：public snapshot 6 个目标测试 OK；`py_compile` OK；Downloads app build OK。

## 最新追加更新（2026-06-14 01:36 AEST）

- Public Raw Snapshot 导入器新增签名发布预检：
  - `public_snapshot_import_approval_template_latest.json`
  - `public_snapshot_import_publish_preflight_latest.json`
  - `public_snapshot_import_publish_preflight_latest.md`
  - `public_snapshot_import_publish_preflight_latest.pdf`
- `/api/status.public_snapshot_publish_preflight` 已返回 approval path、snapshot hash、preview raw hash、passed、issue_count、formal publish boundary 和 stake。
- 首页 `Public Raw Snapshot 导入` 区块已显示签名预检状态、approval 文件和发布预检 PDF。
- 状态机：`waiting_for_snapshot_import` -> `waiting_for_signature` -> `blocked_signature_mismatch` 或 `ready_for_snapshot_publish_preflight`。
- 修复了 preview raw hash 不稳定问题：有效 public snapshot preview raw 的 `generated_at/captured_at` 使用来源 timestamp，不使用每次运行当前时间，避免签名后重建失效。
- 安全边界：发布预检通过不自动 publish，不写正式 raw，不写 batch manifest，不点击 TAB，不下注，stake 保持 `AUD 0`。
- 当前验证：public snapshot 4 个目标测试 OK；`py_compile` OK。

## 最新追加更新（2026-06-14 01:20 AEST）

- 新增 Public Raw Snapshot 导入器：
  - `tab_research/public_snapshot_importer.py`
  - `public_snapshot_import_manifest_template_latest.json`
  - `public_snapshot_import_status_latest.json`
  - `public_snapshot_import_status_latest.md`
  - `public_snapshot_import_status_latest.pdf`
  - `public_snapshot_import_preview_raw_latest.json`
- 功能目的：当 TAB public raw 被 `ai_controlled_access_rejected` 阻断时，允许用户或外部工具把公开导出的 Matches JSON 放到 `manual_verification/public_raw_snapshots/`，系统生成 research-only preview raw 与 hash，供分析和交接复核。
- 支持 JSON 形态：顶层 `matches[]`，或顶层 `raw_snapshot.matches[]`。每条 match 需要 `match` 和 `markets`。
- 当前默认状态：无导入文件时 `waiting_for_snapshot_import`，match `0`，preview ready `false`，formal publish `false`，full automation `false`，stake `AUD 0`。
- 首页新增 `Public Raw Snapshot 导入` 区块；顶部导航新增 `Snapshot导入`；`/api/status.public_snapshot_import` 返回状态、文件、hash、match_count、market_coverage、issue_count 和 next action。
- 安全边界：preview raw 不覆盖正式 raw，不写 raw batch manifest，不证明 TAB 页面真实性，不跳过 TAB 人工最终校验，不自动下注。
- 当前验证：`python3 -m py_compile tab-research-pipeline/tab_research/public_snapshot_importer.py tab-research-pipeline/scripts/build_downloads_app_entry.py tab-research-pipeline/scripts/tab_fifa_app_server.py` OK；public snapshot 3 个目标测试 OK。

## 最新追加更新（2026-06-14 01:07 AEST）

- 新增人工 Team Total overlay 发布预检层：
  - `provider_manual_overlay_approval_template_latest.json`
  - `provider_manual_overlay_publish_preflight_latest.json`
  - `provider_manual_overlay_publish_preflight_latest.md`
  - `provider_manual_overlay_publish_preflight_latest.pdf`
- 当前状态：status `waiting_for_import`，approval file `manual_verification/provider_team_total_overlay_approval.json`，overlay_publish_preflight_passed `false`，approved_by_user `false`，publish_compatible_with_provider_raw `false`，formal_publish_allowed `false`，stake `AUD 0`。
- 首页人工导入区块新增发布预检状态、签名状态和问题数；`/api/status.provider_manual_overlay_publish_preflight` 已返回 approval path、hash、preflight passed、publish compatibility 和 stake。
- 签名规则：必须匹配 `refresh_id + board_id + manual_import_sha256 + overlay_raw_sha256`，且 `approved_by_user=true`、`operator_initials`、`signed_at_aest` 均存在。签名不匹配时状态为 `blocked_signature_mismatch`。
- 当前没有人工 CSV，所以发布预检停在 `waiting_for_import`；不会覆盖正式 raw，不会进入正式 publish，不会生成新增下注金额。
- 当前验证：provider manual 目标测试 `3 tests OK`；`py_compile` OK；Downloads app build OK；desktop/mobile smoke 无横向 overflow。

## 最新追加更新（2026-06-14 00:54 AEST）

- 新增人工 Team Total overlay raw 预览层：
  - `provider_manual_overlay_preview_latest.json`
  - `provider_manual_overlay_preview_latest.md`
  - `provider_manual_overlay_preview_latest.pdf`
  - `provider_manual_team_total_overlay_raw_latest.json`
- 当前状态：status `waiting_for_import`，overlay `0/68`，ready_for_publish_preflight `false`，approved_by_user `false`，publish_compatible_with_provider_raw `false`，formal_publish_allowed `false`，stake `AUD 0`。
- 首页人工导入区块新增 Overlay 预览状态、合入比赛、Overlay SHA 和 PDF 链接；`/api/status.provider_manual_overlay_preview` 已返回 preview raw hash、completion、publish preflight、approval boundary。
- 当前没有人工导入 CSV，所以 overlay raw 是空预览 envelope；不会覆盖正式 provider raw，不会进入正式 publish，不会生成新增下注金额。
- 浏览器验证：desktop `1280px` 与 mobile `390px` 均显示 Overlay 预览且无横向 overflow。
- 当前验证：provider manual 目标测试 `2 tests OK`；`py_compile` OK；Downloads app build OK。
- safety unchanged：该 overlay 是人工导入后的 preview-only merge，不是正式 TAB 证明，不自动登录、不点击赔率、不下注。

## 最新追加更新（2026-06-14 00:40 AEST）

- 新增人工导入 Hash Gate：
  - `provider_manual_hash_gate_latest.json`
  - `provider_manual_hash_gate_latest.md`
  - `provider_manual_hash_gate_latest.pdf`
- 当前状态：status `waiting_for_import`，complete `0/68`，ready_for_manual_signature `false`，approved_by_user `false`，publish_compatible_with_provider_raw `false`，stake `AUD 0`。
- 首页人工导入区块新增 Hash Gate 状态和 PDF 链接；`/api/status.provider_manual_hash_gate` 已返回 hash、completion、signature readiness、approval boundary。
- 浏览器验证：desktop `1280px` 与 mobile `390px` 均显示 Hash Gate 状态且无横向 overflow。
- 当前验证：full suite `Ran 176 tests in 11.505s OK`；`py_compile` OK。
- safety unchanged：该 gate 是人工导入 CSV 审计 hash，不是正式 provider raw publish approvals，不自动下注。

## 追加更新（2026-06-14 00:30 AEST）

- 新增 `provider_manual_verification.py`，把 Team Total fallback 队列转成可填写、可校验、可追踪的人工导入闭环。
- 新增输出：
  - `provider_manual_verification_template_latest.csv`
  - `provider_manual_verification_status_latest.json/md/pdf`
- 当前状态：status `import_missing`，complete `0/68`，high priority complete `0/55`，invalid rows `0`，stake `AUD 0`。
- Downloads 首页新增 `人工校验导入状态` 区块，顶部导航新增 `导入状态`，并提供 CSV 模板下载。
- `/api/status.provider_manual_verification` 已返回 ready/status/import path/completion/error count/next action/stake。
- 移动端 UI 已修复：desktop `1280px` 与 mobile `390px` 均显示导入状态且无横向 overflow。
- 当前验证：full suite `Ran 176 tests in 11.423s OK`；desktop `1280px` 与 mobile `390px` 均显示导入状态且无横向 overflow。
- safety unchanged：导入完成也只进入 hash gate，不自动下注，不点击 TAB odds。

## 追加更新（2026-06-14 00:12 AEST）

- 新增 `provider_fallback_verification.py`，生成 Team Total 人工最终校验队列 `provider_fallback_verification_latest.json/md/pdf`。
- 当前队列：status `provider_blocked_manual_verification_required`，queue `68`，high priority `55`，blocker `opticodds_access_denied_1010`，stake `AUD 0`。
- Downloads 首页新增 `Team Total 人工校验队列` 区块，顶部导航新增 `人工校验`。
- `/api/status.provider_fallback_verification` 已返回 ready/status/queue/top_priority/blocker/next_action；LaunchAgent 已重启到 PID `13768`。
- 新增回归测试 `test_provider_fallback_verification_builds_manual_queue`。
- 当前验证：full suite `Ran 174 tests in 11.680s OK`；desktop `1280px` 与 mobile `390px` 均显示人工校验队列且无横向 overflow。
- safety unchanged：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-14 00:00 AEST）

- 已继续执行 The Odds API Total O/U live probe，最新 refresh_id：`20260613T135338Z-provider-50380e82`。
- 覆盖更新：Result `68/68`、Handicap `47/68`、Total O/U `55/68`、Team Total O/U `0/68`。
- Credit 更新：used `180`、remaining `320`、last cost `13`。
- The Odds API Total O/U probe queue 已变为 `0`；Total O/U 已达 `80.88%`，超过 `70%` 可用阈值，但剩余 `13` 场不再消耗 The Odds API credits。
- Provider alternate plan 状态细化为 `fallback_required`；Team Total fallback queue `68`，下一步为 OpticOdds 官方访问或 TAB 人工最终校验。
- UI 已更新：Provider 模块显示“Provider 路径：转人工校验”，并解释 Total O/U 队列耗尽和 Team Total fallback。
- 新增回归测试 `test_provider_alternate_plan_marks_exhausted_provider_path_as_fallback`。
- 当前验证：full suite `Ran 173 tests in 9.960s OK`；`/api/status` 返回 alternate status `fallback_required`；desktop `1280px` 与 mobile `390px` 无横向 overflow。
- safety unchanged：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-13 23:43 AEST）

- 已执行 OpticOdds live probe，结果被 Cloudflare `1010 Access denied` 阻断：
  - blocker_code：`opticodds_access_denied_1010`
  - 不允许绕过 browser signature；后续需要 OpticOdds 官方允许的服务端/API 访问方式、白名单环境或 TAB 人工最终校验。
- 已修复 provider blocked artifact：
  - 新增 `ODDS_PROVIDER_BLOCKED_LATEST = odds_provider_blocked_latest.json`
  - `write_blocked_provider_payload()` 会写 blocker artifact。
  - 如果 `odds_provider_coverage_latest.json` 仍有 last-good targets，则失败 refresh 不覆盖 last-good coverage。
  - 新增回归测试 `test_provider_blocked_attempt_preserves_last_good_coverage`。
- 已执行 The Odds API totals-only 下一批 live probe：
  - refresh_id：`20260613T134035Z-provider-a3daa59b`
  - coverage：Result `68/68`、Handicap `47/68`、Total O/U `15/68`、Team Total O/U `0/68`
  - credit：used `76`，remaining `424`，last cost `13`
  - alternate queue：The Odds API Total O/U `53`；Team Total fallback `68`
- Provider KPI 当前 score：`59.65%`；完整测试最新为 `172 tests OK`。
- Provider KPI、首页和 `/api/status` 已接入 last blocked attempt；UI 会显示 `opticodds_access_denied_1010` 和 `last-good 已保留`。
- safety unchanged：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-13 23:31 AEST）

- 已修复 The Odds API alternate probe 重复打同一批 event 的 credit 浪费问题：
  - 新增 `historical_market_covered_event_ids()`，从 `outputs/provider_raw/*/tab_fifa_matches_main_markets_raw_v0_9.json` 读取历史已补目标 market 的 event_id。
  - `refresh_odds_provider_raw.py` 的 event-level probe 现在会排除历史已覆盖 event。
  - 新增 `merge_historical_provider_raws()`，新 staging raw 会合并历史已补目标 markets，并写入 `provider_historical_merge` 与研究用途警告。
  - CLI 调用历史合并时会传入 `--event-odds-markets`，当前只合并 `totals,alternate_totals` 对应的 `Total Goals Over/Under`，不把旧宽口径 BTTS/DNB/Double Chance 当作当前覆盖。
- 已执行修复后的 live probe：
  - refresh_id：`20260613T132806Z-provider-40fc69ff`
  - request_kind_counts：odds `1`、event_markets `5`、event_odds `5`
  - reported last cost `13`，used `63`，remaining `437`
  - coverage：Result `68/68`、Handicap `47/68`、Total O/U `10/68`、Team Total O/U `0/68`
  - alternate queue：The Odds API Total O/U `58`；Team Total fallback `68`
- 已新增回归测试：
  - 历史 Total O/U 覆盖会被下一批 probe 排除。
  - 新 refresh 会合并历史 event odds。
  - 历史合并可限制为本次请求 markets，避免误合并 Team Total 或其他旧宽口径 markets。
- 已重建 Downloads 首页/app assets，并同步最新 provider KPI/alternate plan 到 `artifacts/latest`。
- safety unchanged：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-13 23:11 AEST）

- 已执行第二轮真实 The Odds API live 小批量 alternate probe：
  - command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals,team_totals,alternate_team_totals --timeout-seconds 30`
  - refresh_id：`20260613T130210Z-provider-0583770a`
  - request_kind_counts：odds `1`、event_markets `5`、event_odds `5`
  - reported last request cost `13`；reported used `37`；reported remaining `463`
- 最新 provider coverage：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `5/68`，从上一轮 `3/68` 增加到 `5/68`
  - Team Total O/U `0/68`
- Event-market evidence：
  - 5/5 sampled events 提供 `alternate_totals`
  - 0/5 sampled events 提供 `team_totals` 或 `alternate_team_totals`
  - 结论：The Odds API 当前 TAB sample 可继续补 Total O/U；Team Total 不再继续用 The Odds API 盲扫，转 OpticOdds 或 TAB 人工最终校验。
- Provider alternate plan 已更新：
  - The Odds API Total O/U probe queue `63`
  - Team Total fallback queue `68`
  - recommended batch `5`
  - estimated next credit `5-15`
  - recommended command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals`
- Downloads 首页 Provider 板块已显示 fallback 队列、totals-only 推荐命令和 Team Total fallback 说明；desktop `1280px` 与 mobile `390px` 浏览器验证均无横向 overflow。
- formal publish、full automation 仍为 `false`；current executable new stake 仍为 `AUD 0`。

## 最新追加更新（2026-06-13 22:48 AEST）

- 新增 `tab_research/provider_alternate_plan.py`：
  - 生成 `provider_alternate_plan_latest.json/md/pdf`
  - 从 provider coverage + staged raw 派生 Team Total/Total O/U 缺口、下一批 probe 队列、credit 预算和停止条件。
  - 从 staged raw 的 `provider_request_kinds` 排除已拉过 event odds 的比赛，避免重复消耗 credits。
- `refresh_odds_provider_raw.py` 已在每次 provider staging 后写补齐计划。
- `provider_kpi.py` 已接入补齐计划摘要与 `alternate_probe_plan` KPI 行；当前 KPI score `59.00%`，但 Team Total 覆盖仍是 `0/68`。
- Downloads 首页 Provider 板块新增：
  - `补齐计划` PDF 链接
  - `下一批 Probe`
  - 推荐命令
  - 前 5 场 probe 队列
- `/api/status.provider_alternate_plan` 当前返回：
  - `status=in_progress`
  - `probe_queue_count=65`
  - `recommended_batch_size=5`
  - `estimated_next_batch_credit_floor=5`
  - `estimated_next_batch_credit_ceiling=25`
  - `current_executable_new_stake_aud=0`
- 当前本地服务已由 LaunchAgent `com.linzezhang.tab-fifa-research` 托管，PID `86499`，运行路径为 `github_sync/FIFA/tab-research-pipeline`，日志 `/tmp/tab_fifa_app_server.log`；模板已同步到 `ops/launch_agents/com.linzezhang.tab-fifa-research.plist`。
- 浏览器验证：desktop `1280px` 和 mobile `390px` 均无横向 overflow，Provider 补齐计划可见。
- 验证：`py_compile` OK；目标测试 2 个 OK；full suite `Ran 168 tests in 12.540s OK`；`git diff --check` OK；secret scan 无真实 key 命中。

## 最新追加更新（2026-06-13 22:29 AEST）

- 已修复 `refresh_odds_provider_raw.py` 本地 env 读取顺序：CLI 会先加载默认 `config/odds_providers.local.env`，再解析参数，因此本地 `TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT`、`TAB_FIFA_THE_ODDS_API_EVENT_ODDS_LIMIT`、`TAB_FIFA_THE_ODDS_API_EVENT_ODDS_MARKETS` 会稳定进入默认参数。
- 用户不需要改 `odds_providers.local.env.example` 的文件名；该文件只作为 GitHub 模板保留。真实 key 放在同目录 `odds_providers.local.env`，该文件已被 `.gitignore` 排除。
- `/api/status.provider_kpi` 当前验证：ready `true`、status `in_progress`、score `58.33%`、refresh `20260613T121414Z-provider-51410a2f`、Matches `68`、primary gap `Team Total Score O/U 覆盖: 0/68 (0.00%)`。
- 当前 8767 服务返回 `ok=true`、raw `blocked`、private position `profile_login_required`；新增执行金额继续为 `AUD 0`。
- 已验证：`py_compile` OK；`git diff --check` OK；secret scan 无真实 key 命中；full suite `Ran 167 tests in 65.505s OK`。

## 最新追加更新（2026-06-13 22:17 AEST）

- 已新增 credit-aware alternate markets 路线：
  - `/events/{eventId}/markets` 用于探测 TAB 单场可用 market keys。
  - `/events/{eventId}/odds` 只在目标 market 可用时拉取。
  - CLI 参数：`--event-market-probe-limit`、`--event-odds-limit`、`--event-odds-markets`。
  - 默认 `TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT=0`，避免自动消耗 credits。
- live 小样本 probe 已成功：
  - `refresh_id=20260613T121414Z-provider-51410a2f`
  - `request_kind_counts`: odds `1`、event_markets `3`、event_odds `3`
  - reported last cost `18`，remaining `476`
  - market coverage：`Result 68/68`、`Handicap 47/68`、`Total O/U 3/68`、`Team Total O/U 0/68`
  - 结论：event-level odds 能补 `Total O/U`；`Team Total` 仍未覆盖。
- 已把默认 event odds markets 从宽口径收窄到 `totals,alternate_totals,team_totals,alternate_team_totals`，BTTS/DNB/Double Chance 不默认拉取。
- 新增 `tab_research/provider_kpi.py`，输出 `provider_kpi_latest.json/md/pdf`。
- 首页新增 Provider KPI 板块，并接入 `今日决策中心` 与 `/api/status.provider_kpi`。
- 已把 public-safe KPI 同步到 GitHub `artifacts/latest/provider_kpi_latest.*`。
- 验证：full suite `Ran 167 tests in 44.476s OK`。

## 最新追加更新（2026-06-13 21:51 AEST）

- 已修复 The Odds API `Unknown sport`：
  - Matches 默认 sport key 为 `soccer_fifa_world_cup`。
  - Futures 默认 sport key 为 `soccer_fifa_world_cup_winner`。
  - CLI 默认先调用 `/v4/sports` 做 discovery/filter，配置里混入旧 key `soccer_world_cup` 时会自动丢弃。
- 本机已创建 Git ignored secret 文件 `config/odds_providers.local.env`；tracked `config/odds_providers.local.env.example` 已恢复 placeholder，禁止提交真实 key。
- live 验证结果：
  - `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches` 已成功。
  - `refresh_id=20260613T114657Z-provider-728d17c6`
  - request cost reported `3`，remaining reported `494`。
  - The Odds API/TAB 当前返回 Matches `68` 场：`Result 68/68`、`Handicap 47/68`、`Total O/U 0/68`、`Team Total O/U 0/68`。
- Provider coverage 已分层：
  - `provider_analysis_ready=true`，可用于 Result/Handicap 主盘口研究。
  - warning 明确说明 Total O/U 和 Team Total O/U 当前 provider payload 未返回。
  - `formal_publish_allowed=false`、`full_automation_allowed=false`、`current_executable_new_stake_aud=0` 不变。
- 已验证：`py_compile` OK；provider 目标测试 OK；full suite `Ran 163 tests in 17.264s OK`。

## 最新追加更新（2026-06-13 21:27 AEST）

- 已按用户要求把 provider raw 路线调整为 `Matches` 优先，地区盘口默认忽略。
- `refresh_odds_provider_raw.py` 新增 `--scope matches|futures|all`，默认 `matches`；新增 `--include-region-markets`，不传时排除 `world_cup_australia_markets`。
- The Odds API 默认市场从 `h2h,spreads,totals,outrights` 改为 Matches 省 credit 模式：`h2h,totals,spreads`。
- `Team Total Goals Over/Under` 已接入 provider payload 解析和候选评分；The Odds API 扩展请求通过 `TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS=team_totals,alternate_team_totals` 手动开启，未验证前不默认消耗 credit。
- 新增本地 secret 配置模板 `config/odds_providers.local.env.example`；真实 `config/odds_providers.local.env`、`.env`、`*.local.env` 已加入 `.gitignore`，不会同步 GitHub。
- Coverage 现在区分：
  - `provider_analysis_ready`：Matches 主盘口可用于候选研究。
  - `formal_publish_allowed`：当前 scope raw 严格校验+人工 TAB hash 校验后可发布。
  - `full_automation_allowed`：完整自动日报 gate，Matches-only 不会误放行。
- `publish_verified_provider_raw()` 已修成 scope-aware；Matches-only 发布不会尝试生成 5/5 batch manifest。
- 新增/更新测试覆盖 Matches-only 默认请求、地区盘口忽略、Team Total 映射、scope-aware publish、Team Total 候选生成。
- 已验证：
  - `py_compile` 通过。
  - provider/Team Total 目标单测 6 个通过。
- 未完成：
  - 真实 API key 未在仓库中配置，也不能配置进 GitHub；需要本机 env 或 keychain/CI secret。
  - 未跑 live The Odds API coverage。
  - 正 CLV 仍依赖后续 closing line 对比数据，目前只能输出正 EV/价格容忍度/CLV 待验证状态。

## 最新追加更新（2026-06-13 19:50 AEST）

- 已新增授权 odds provider raw 框架，路径为 `tab_research/odds_provider_adapter.py` 与 `refresh_odds_provider_raw.py`。
- 支持 The Odds API：AU region、`bookmakers=tab`、decimal odds、markets 默认 `h2h,spreads,totals,outrights`。
- 支持 OpticOdds：默认 endpoint `/fixtures/odds`，`TAB_FIFA_OPTICODDS_ENDPOINT` 与 `TAB_FIFA_OPTICODDS_QUERY` 可按账号文档配置。
- Provider 数据只进入 staging，不默认发布正式 raw：
  - `outputs/provider_raw/<refresh_id>/`
  - `outputs/odds_provider_raw_latest.json`
  - `outputs/odds_provider_coverage_latest.json`
- 正式 publish 必须通过人工 TAB final verification，校验 `refresh_id + board_id + sha256`；且 5/5 required boards 未全 ready 时仍阻断 full automation，新增执行金额保持 `AUD 0`。
- 新增配置样例：`config/odds_providers.example.json`。
- 新增说明：`../docs/ODDS_PROVIDER_INTEGRATION_20260613.md`。
- 已更新 README/RUNBOOK/仓库 docs，把用户导出快照降为兜底方案，授权 provider 成为主 raw 恢复路径。
- 已验证：
  - provider 单测 3 个通过。
  - `py_compile` 通过。
  - 无 `THE_ODDS_API_KEY` 时 CLI 以 exit `2` fail-closed，写明 `current_executable_new_stake_aud=0`。
- 未完成：真实 API key 未配置，未跑 provider live coverage；Australia Markets 的 provider 覆盖未知；My Bets 仍需用户授权。

## 最新追加更新（2026-06-13 18:59 AEST）

- 已完成并行审查与修复收口；仓库级摘要位于 `../docs/PARALLEL_REVIEW_SUMMARY_20260613.md`。
- 本地 app POST action 已加固：per-process action token + local Host/Origin/Referer 校验；前端所有 POST 附带 `X-TAB-FIFA-Action-Token`。
- 私有 My Bets 快照现在拒绝写入 public `outputs/private/**`；public safety scan 会检测 nested private position 文件。
- 新增 `tab_research/paths.py`，统一 workspace/output/private 目录解析；GitHub worktree 和原始本地 workspace 均可运行。
- 主动测试修复：先显示缓存快照，再返回实时结果；research-only 日报未 ready 时写 `未达到 ready`，不会错误显示“已补写”。
- 后台 runner 启动加锁，PID 由父进程写入，减少重复启动/竞态。
- 已重建 Downloads HTML 和 macOS app；当前 `http://127.0.0.1:8767/` 运行 PID `3984`，cwd 为 `github_sync/FIFA/tab-research-pipeline`。
- 浏览器实测通过：首页关键模块存在，主动测试返回 `fresh_timeline_direct_api` 且无空白失败。
- 验证通过：Python full suite `Ran 155 tests in 67.990s OK`；Node raw/My Bets security tests OK；bash syntax OK。
- 交付包相关文档：`../docs/FEATURE_LIST.md`、`../docs/DELIVERY_STANDARDS.md`、`../docs/DELIVERY_PACKAGE_MANIFEST_20260613.md`。
- 未完成阻塞不变：正式 raw 未 5/5、Australia Markets 不可用、My Bets 登录授权未完成；当前新增执行金额仍为 `AUD 0`。

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
