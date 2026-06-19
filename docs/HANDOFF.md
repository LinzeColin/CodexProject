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
- 录入方式改为 8 场比赛一行：
  - 用户填写队伍范围、line、Over/Under 赔率、观察时间、操作员、证据和状态。
  - 后端保存时固定写入 `outputs/manual_verification/provider_team_total_manual_verification.csv`，自动展开为 16 行 Over/Under CSV。
  - 未完整填写的比赛保持 `pending` 空行，不产生 invalid row。
- 安全边界：
  - POST 使用本地 action token 和本地 Host/Origin/Referer 检查。
  - JSON body 限制 128KB。
  - 不接受用户传入路径。
  - 不触发 provider refresh、不消耗 API credits、不点击 TAB、不改 Bet Slip、不自动下注。
  - 保存后复用现有 manual verification/hash/overlay/preflight bundle。
- 当前验证：
  - API smoke：`/api/manual-team-total-entry` 返回 `ready=true`、`event_count=8`、`row_count=16`、stake `0`。
  - 工作队列：下一任务仍为 `TT-001`，Team Total missing `64`，credit runway `next_batch_would_cross_reserve`。
  - Browser smoke desktop/mobile 均可见 TT-001 录入区块，8 行，console error `0`，页面本体无横向溢出。
  - `py_compile` OK；focused tests `5 OK`；full suite `206 tests OK`；`git diff --check` OK；真实 key scan 无命中。
- 后续接手重点：
  - 用户/操作员在网页中根据 TAB 真实页面只读填写 TT-001。
  - 完整保存后复核 `provider_manual_verification_status_latest.json`、hash gate、overlay preview、publish preflight。
  - 未完成 manual signature 前 formal publish/full automation 不解锁，stake 仍为 `AUD 0`。

## 最新追加更新（2026-06-14 06:25 AEST）

- 新增 runtime `/api/status.position_monitor`，把已有 `position_monitor_latest.json` 变成网页主控台可动态读取的 public-safe 状态块：
  - 只暴露 ready/blocked、文件存在性、preflight、下一步、公开占位金额和 monitor rows。
  - 不暴露账户余额、逐笔下注、私有路径、账号密码或 OTP。
  - 当前 HTTP 状态：`ready=false`，`artifact_ready=true`，`status=blocked`，`report_date=14062026`，`snapshot_ready=false`，`profile_exists=true`，`public_visible_balance=account-update-pending`，`stake=0`。
- `Automation 工作队列` 的 `MY-BETS-READONLY` 任务现在使用 `position_monitor` 证据：
  - `blocker=尚未运行只读持仓读取，需要启动本地授权 profile 流程。`
  - `evidence=profile_exists=True; snapshot_exists=False`
  - 仍禁止自动下注、赔率点击和 Bet Slip 修改。
- 已重启本地 LaunchAgent 服务，当前 `http://127.0.0.1:8767/` 由新 PID 提供服务，真实 HTTP smoke 通过。
- 验证：
  - `py_compile` OK。
  - Focused tests：`2 passed, 203 deselected`。
  - Full suite：`205 passed, 5 warnings in 14.61s`。
  - HTTP smoke：`/api/status.position_monitor` 200；`/api/status.automation_work_queue` 200，`automation_ready=false`，`stake=0`，`next_task_id=TT-001`。
- 本轮没有触发 provider refresh、没有消耗 The Odds API credits、没有点击 TAB、没有修改 Bet Slip。
- 下一步仍是 `TT-001` 人工只读导入；并行可启动 My Bets 只读持仓读取，但必须由用户完成 TAB 授权窗口，系统只读取快照并重跑门禁。

## 最新追加更新（2026-06-14 06:18 AEST）

- 新增平台级 `Automation 工作队列`，把 Team Total、credit reserve、OpticOdds、My Bets、formal publish gate 和最终 readiness 串成同一个可读队列：
  - API：`/api/status.automation_work_queue`
  - 首页位置：Provider 采集控制台之后，导航新增 `工作队列`
  - 当前 `automation_ready=false`，`current_executable_new_stake_aud=0`
  - 当前任务：`6` 个，blocked `6` 个，P0 `2` 个
  - 第一行动项：`TT-001 Team Total 人工导入`
- 当前 API smoke 结果：
  - `next_task_id=TT-001`
  - `team_total_missing_event_count=64`
  - `team_total_next_batch_pair_rows=16`
  - `credit_runway_status=next_batch_would_cross_reserve`
  - task order：`TT-001`、`CREDIT-RESERVE`、`OPTICODDS-ACCESS`、`MY-BETS-READONLY`、`FORMAL-PUBLISH-GATE`、`AUTOMATION-READINESS`
- 首页工作队列新增复制命令按钮；浏览器拒绝 clipboard 时现在直接显示完整命令，不再只提示“手动复制”。
- 本轮没有触发 provider refresh、没有消耗 API credits、没有点击 TAB 赔率、没有修改 Bet Slip、没有新增下注金额。
- 验证：
  - `py_compile` OK。
  - Focused tests：`2 passed, 203 deselected`。
  - Full suite：`205 passed, 5 warnings in 14.34s`。
  - Browser smoke desktop：工作队列可见，6 行任务，第一项 `TT-001`，console error `0`，body scroll width `1280/1280`。
  - Browser smoke mobile `390x844`：工作队列可见，6 行任务，document/body scroll width `390/390`，console error `0`。
- 当前下一步：人工只读填写 `TT-001` 的 `16` 行 Team Total Over/Under，保存到 `outputs/manual_verification/provider_team_total_manual_verification.csv` 后运行 `TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`。
- 剩余 gate：The Odds API next batch 会跌破 200 credit reserve，OpticOdds 未配置/未白名单，My Bets 仍需 profile login，formal publish/full automation 仍为 `false`，stake 仍为 `AUD 0`。

## 最新追加更新（2026-06-14 06:04 AEST）

- 已把 Team Total `TT-001` 从“CSV 模板提示”升级为网页/API/artifact 都可读的 `manual_intake_contract`：
  - 当前批次：`TT-001`。
  - 模板：`provider_manual_next_batch_pair_template_latest.csv`。
  - 导入目标：`outputs/manual_verification/provider_team_total_manual_verification.csv`。
  - 重建命令：`TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py`。
  - 当前缺口：missing `64`，partial `0`，invalid `0`，complete `0`，下一批需 `16` 行。
  - 禁止动作仍包括自动下注、点击赔率、加入 Bet Slip。
- API 已扩展：
  - `/api/status.provider_manual_workbench.manual_intake_contract` 返回导入目标、重建命令、验收条件、当前缺口、禁止动作和 stake boundary。
  - `/api/status.provider_command_center.team_total_manual.manual_intake_contract` 返回同一 contract，便于首页和后续 agent 统一读取。
- 首页 `人工校验导入状态` 新增 `TT-001 Intake Contract`：
  - 显示导入目标、重建命令、签名后显式 publish 命令、当前缺口、导入步骤和验收条件。
  - 新增 `复制导入目标`、`复制重建命令` 按钮；复制反馈已从“推荐命令”改为通用 label，复制路径时不误导。
- 已重建 Downloads app 并同步 24 个 Team Total/manual public-safe artifacts 到 `artifacts/latest/`。
- 本轮验证：
  - `py_compile` OK。
  - Focused tests：`3 tests OK`。
  - Full suite：`Ran 205 tests in 13.329s OK`。
  - API smoke：manual workbench contract 返回 `TT-001`、import target、rebuild command、missing `64`、stake `0`；command center 仍返回 `can_run_provider_batch=false` 和 credit runway blocked。
  - Browser smoke：desktop/mobile 均显示 `TT-001 Intake Contract`、导入目标、重建命令、stake `AUD 0`；overflow `0`，console error `0`。
- 当前下一步不变但更可执行：先人工只读填写 `TT-001` 的 `16` 行 Team Total Over/Under，再运行重建命令；未通过 hash gate、overlay preview、approval preflight、explicit publish 前，formal publish/full automation 仍为 `false`，stake `AUD 0`。

## 最新追加更新（2026-06-14 05:55 AEST）

- 已确认 API key 放置方式：真实 The Odds API key 只保留在 ignored `tab-research-pipeline/config/odds_providers.local.env`；tracked `config/odds_providers.local.env.example` 保持固定文件名和占位值，可同步 GitHub，但不得放真实 key。
- 已把本机 ignored env 的非敏感 event market 参数同步到当前推荐值：`alternate_totals,alternate_spreads,btts,double_chance,draw_no_bet`；`TAB_FIFA_THE_ODDS_API_SPORTS=soccer_fifa_world_cup`，sports discovery 开启。
- 已继续完成 3 轮小批量 The Odds API value-support 补齐，最新 refresh `20260613T194716Z-provider-2fec0bef`：
  - queue `53 -> 50`；usage `used=299`、`remaining=201`、latest cost `7`。
  - Matches event count `64`；Result `64/64`，Handicap `46/64`，Total O/U `51/64`，Team Total `0/64`。
  - Event-market evidence：`spreads=14`、`totals=14`、`btts=14`、`double_chance=11`、`draw_no_bet=12`、`h2h=14`。
- 新增 Provider Credit Runway guard：
  - `/api/status.provider_command_center.credit_runway.status=next_batch_would_cross_reserve`。
  - 当前剩余 `201`，下一批预计 `4-7` credits，按 200 credits reserve 计算下一批后最低 `194`，因此 `can_run_provider_batch=false`。
  - 首页 Provider 采集控制台显示 `下一批会破保底`、安全批次数 `0`，推荐动作改为暂停 API，转 `TT-001` Team Total 人工校验或 OpticOdds 官方访问。
- 已重启 LaunchAgent 并验证本地服务：`http://127.0.0.1:8767/api/health` OK；`/api/status.provider_command_center` 返回 queue `50`、credit runway blocked、stake `AUD 0`。
- 已重建 Downloads app 和 public-safe artifacts，同步 25 个 latest artifacts 到 `artifacts/latest/`。
- 本轮验证：
  - `py_compile` OK。
  - Focused tests：`2 tests OK`。
  - Full suite：`Ran 205 tests in 13.210s OK`。
  - API smoke：`can_run_provider_batch=false`、credit runway `next_batch_would_cross_reserve`、remaining `201`、after ceiling `194`、stake `0`。
  - Browser smoke：desktop/mobile 均显示 `Credit Runway`、`下一批会破保底`、queue `50`、stake `AUD 0`；overflow `0`，console error `0`。
  - `git diff --check` OK；tracked secret scan 对已知 key 和 key-like env assignment 无命中。
- 当前下一步：不要继续 The Odds API batch；优先处理 `provider_manual_next_batch_pair_template_latest.csv` 的 `TT-001` Team Total 人工只读校验，或解决 OpticOdds 官方访问/白名单。
- 不变 gate：formal publish `false`，full automation `false`，current executable new stake `AUD 0`；系统不自动下注、不点击 TAB 赔率、不修改 Bet Slip。

## 最新追加更新（2026-06-14 05:40 AEST）

- 已继续执行 1 轮 The Odds API credit-conservation batch `1`：
  - `20260613T193148Z-provider-0bf93159`，cost `7`，probe queue `58 -> 53`。
  - Event count 当前为 `64`；Result `64/64`，Handicap `46/64`，Total O/U `51/64`，Team Total `0/64`。
  - Event-market evidence：sample `11`；BTTS `11/64`，Double Chance `8/64`，Draw No Bet `9/64`；Team Total available sample 仍为 `0`。
  - Usage：used `278`，remaining `222`，remaining ratio `44.40%`；下一批仍为 batch `1`，预计 `4-7` credits。
- 首页新增 `Provider 采集控制台`：
  - 集中显示 API 小批量补齐、Team Total 人工路径、credit 风控、formal/full automation gate、推荐命令、停止条件、覆盖进度条和下一批队列。
  - 新增复制推荐命令按钮；当浏览器拒绝剪贴板写入时降级为明确“手动复制下方命令”，不误报成功。
- API 新增 `/api/status.provider_command_center`，暴露同一控制台摘要，便于后续前端动态刷新和 agent 交接验证。
- 现有 LaunchAgent `/Users/linzezhang/Library/LaunchAgents/com.linzezhang.tab-fifa-research.plist` 已从 `KeepAlive=false` 改为 `KeepAlive=true` 并重新加载；当前服务由 `launchctl` 运行在 `http://127.0.0.1:8767/`，PID `80606`，`/api/health` OK。
- 已重建 Downloads app，并同步 25 个 latest artifacts 到 `artifacts/latest/`。
- 本轮验证：
  - `py_compile` OK。
  - Focused app status test：`Ran 1 test OK`。
  - Full suite：`Ran 204 tests in 12.816s OK`。
  - API smoke：`provider_command_center` 返回 refresh `20260613T193148Z-provider-0bf93159`、batch `1`、queue `53`、credit `4-7`、remaining `222`、TT batch `TT-001`、stake `0`、formal/full automation `false`。
  - Browser smoke：desktop/mobile 均显示 Provider 采集控制台、新 refresh、queue `53`、credit `222`/`4-7`、stake `AUD 0`；page overflow `0`，console error `0`。
- 不变 gate：formal publish `false`，full automation `false`，current executable new stake `AUD 0`；Team Total 仍需 OpticOdds 官方访问/白名单或 TT-001 人工只读校验。

## 最新追加更新（2026-06-14 05:20 AEST）

- 修正 provider alternate plan 的 credit 估算：下一批 `estimated_next_batch_credit` 现在包含 primary odds refresh 基础成本。当前 batch `1` 的真实估算从旧 `1-4` 改为 `4-7` credits，与最新实际 cost `7` 对齐。
- 修正 value-support 队列优先级：`recommended_markets` 现在按覆盖缺口排序为 `double_chance,draw_no_bet,btts`，优先补更稀缺的 Double Chance / Draw No Bet。
- 加固 event selector：无 plan queue 时也会跳过已做过 event-market probe 的事件，避免只 probe 过但未返回目标 odds 的事件被重复消耗。
- 执行一轮修正后的 batch：
  - `20260613T191940Z-provider-371af48a`：cost `7`，queue `59 -> 58`。
  - BTTS `9/68 -> 10/68`
  - Double Chance `6/68 -> 7/68`
  - Draw No Bet `7/68 -> 8/68`
- 当前 usage：used `271`，remaining `229`，remaining ratio `45.80%`。继续 batch `1` 仍可行，但如连续低增量应暂停 The Odds API，转 OpticOdds 或 TAB 人工。
- 已重建 Downloads app 并同步 latest artifacts 到 `artifacts/latest/`。
- 本轮最终验证：`py_compile` OK；focused credit/selector tests `5 tests OK`；完整 suite `Ran 204 tests in 13.061s OK`；API smoke `/api/status` 返回 refresh `20260613T191940Z-provider-371af48a`、queue `58`、batch `1`、credit `4-7`、command `double_chance,draw_no_bet,btts`、stake `0`，`/api/status.provider_kpi` equivalent field `overall_progress_pct=0.615`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示 latest refresh、`4-7`、命令顺序、BTTS `10/68`、Double Chance `7/68`、Draw No Bet `8/68`、Team Total `0/68`、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露。
- 不变边界：formal publish `false`，full automation `false`，current executable new stake `AUD 0`；Team Total 仍为 `0/68`。

## 最新追加更新（2026-06-14 05:10 AEST）

- 已继续执行 The Odds API credit-conservation batch `1`，并发现/修复一个会浪费 credits 的事件选择问题：
  - `20260613T190633Z-provider-b35cbe30`：cost `5`，queue 仍为 `60`，覆盖无新增；根因是 refresh 脚本没有优先使用 `provider_alternate_plan_latest.json.next_probe_queue`，可能重复抓取已做过 event_odds 的部分覆盖事件。
  - 已修复：`refresh_odds_provider_raw.py` 现在优先按 plan queue 选择 event；没有 plan queue 时跳过已有 `event_odds_event_ids`，避免同一事件反复消耗。
  - `20260613T190906Z-provider-404dcf06`：cost `5`，queue `60 -> 59`，BTTS `8/68 -> 9/68`。
- 最新 Matches 覆盖：Result `68/68`，Handicap `50/68`，Total O/U `55/68`，BTTS `9/68`，Double Chance `6/68`，Draw No Bet `7/68`，Team Total `0/68`。
- The Odds API credits 当前 used `264`、remaining `236`，remaining ratio `47.20%`；继续保持 batch `1`，预计 `1-4` credits，但如果连续低增量应暂停 API 并转 OpticOdds/TAB 人工。
- 首页 Provider KPI 已新增 `额度效率` 和 `Value-support 覆盖` 卡片，减少用户读技术日志的成本。
- 已重建 Downloads app 并同步 latest artifacts 到 `artifacts/latest/`。
- 本轮最终验证：`py_compile` OK；focused provider selector/alternate tests `4 tests OK`；完整 suite `Ran 202 tests in 13.876s OK`；API smoke `/api/status.provider_kpi` 返回 refresh `20260613T190906Z-provider-404dcf06`、`overall_progress_pct=0.615`、stake `0`；API smoke `/api/status` 返回 provider alternate `in_progress`、queue `59`、batch `1`、credit `1-4`、stake `0`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示 latest refresh、`额度效率`、`Value-support 覆盖`、batch `1`、BTTS `9/68`、Double Chance `6/68`、Draw No Bet `7/68`、Team Total `0/68`、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露；`git diff --check` OK；tracked secret scan 无命中。
- 不变边界：formal publish `false`，full automation `false`，current executable new stake `AUD 0`；Team Total 仍需 OpticOdds 官方访问/白名单或 TAB 人工最终校验。

## 最新追加更新（2026-06-14 04:55 AEST）

- 已按上轮 recommended command 连续执行 3 轮 The Odds API credit-safe alternate/value-support 小批量补齐，均成功 staged，均未触发 formal publish/full automation，stake 仍为 `AUD 0`：
  - `20260613T185314Z-provider-083b0da8`：queue `68 -> 65`，cost `18`。
  - `20260613T185358Z-provider-c45e751e`：queue `65 -> 62`，cost `13`。
  - `20260613T185434Z-provider-ee1955d8`：queue `62 -> 60`，cost `12`。
- 当前 Matches 覆盖：
  - Result `68/68`
  - Handicap `50/68`，已过 `70.00%` 阈值。
  - Total O/U `55/68`，已过 `70.00%` 阈值。
  - BTTS `8/68`
  - Double Chance `6/68`
  - Draw No Bet `7/68`
  - Team Total `0/68`，仍走 OpticOdds/TAB 人工路径。
- The Odds API credits 当前 used `254`、remaining `246`，remaining ratio `49.20%`；系统按 credit policy 自动降速，下一批从 `3` 场改为 `1` 场，预计 `1-4` credits。
- 当前 KPI 为 `61.50%`。注意：覆盖实际增加，但 KPI 因 credit reserve 从 `>=50%` 降到 `<50%` 自动扣分，所以从 66.50% 回落；这是风控信号，不是 raw 失败。
- 下一步若继续抓取，使用降速命令：

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 1 --event-odds-limit 1 --event-odds-markets btts,double_chance,draw_no_bet
```

- 已重建 Downloads app 并同步 latest artifacts：`odds_provider_raw_latest.json`、`odds_provider_coverage_latest.json`、`provider_alternate_plan_latest.*`、`provider_kpi_latest.*`、`provider_config_doctor_latest.*`、dashboard PDF。
- 本轮最终验证：`py_compile` OK；focused provider/status tests `4 tests OK`；完整 suite `Ran 200 tests in 13.259s OK`；API smoke `/api/status` 返回 refresh `20260613T185434Z-provider-ee1955d8`、`probe_queue_count=60`、batch `1`、credit `1-4`、KPI progress `0.615`、stake `0`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示 latest refresh、batch `1`、KPI `61.50%`、BTTS/Double Chance/Draw No Bet coverage、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露；`git diff --check` OK；tracked secret scan 无命中。
- 不变边界：Team Total 仍无真实官方/API/manual 完整数据；OpticOdds key 当前未配置；My Bets 私有持仓、TAB 人工最终校验和 formal publish gate 未通过前，新增下注金额保持 `AUD 0`。

## 最新追加更新（2026-06-14 04:38 AEST）

- Alternate markets plan 已从旧的 `fallback_required / probe_queue=0` 更新为 `in_progress / probe_queue=68`：非 Team Total 的 alternate/value-support markets 可小批量补齐，Team Total 继续人工/官方路径。
- 当前运营决策：`alternate_probe_plus_team_total_manual`，标题为 `非 Team Total 可小批量补齐，Team Total 转人工`。
- 当前可见样本：`spreads`、`totals`、`btts`、`double_chance`、`draw_no_bet`、`h2h` 均在 3 个 TAB event-market 样本中出现；`team_totals` 与 `alternate_team_totals` 仍未出现。
- 推荐下一步命令：

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 3 --event-odds-limit 3 --event-odds-markets spreads,alternate_spreads,btts,double_chance,draw_no_bet
```

- KPI 当前为 `60.00%`；Result `68/68`、Handicap `47/68`、Total O/U `55/68`、Team Total `0/68`；reported used `211`，remaining `289`，last cost `3`。
- Provider config doctor status `ready`；The Odds API key present `true`，OpticOdds key present `false`；真实 key 不进入 GitHub，只通过 ignored `config/odds_providers.local.env` 或当前 shell 环境提供。
- 已更新 Downloads app、`artifacts/latest/provider_alternate_plan_latest.*`、`provider_alternate_probe_evidence_latest.json`、`provider_kpi_latest.*`、`provider_config_doctor_latest.*`。
- 验证：目标 py_compile + provider/status 回归测试 OK；完整 suite `Ran 200 tests in 13.162s OK`；API smoke `/api/status` 确认 `alternate_probe_plus_team_total_manual`、recommended batch `3`、credit `3-18`、KPI progress `0.6`、stake `AUD 0`；Browser smoke desktop `1280px` 与 mobile `390px` 均显示新决策、BTTS/Double Chance/Draw No Bet、batch 3、`AUD 0`，page overflow `0`，console error `0`，无 key 泄露。
- 不变边界：没有 Team Total 真实官方/API/manual 数据，没有 My Bets 私有持仓确认，没有 formal publish gate；因此新增下注金额仍锁定 `AUD 0`。

## 最新追加更新（2026-06-14 04:24 AEST）

- 用户反馈的 `Unknown sport` raw 问题已复测并修复到诊断层：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches` 当前成功，active refresh id `20260613T181704Z-provider-1d88f0e3`。
- The Odds API 当前主盘口 coverage：Result `68/68`，Handicap `47/68`，Total O/U `55/68`，Team Total `0/68`。reported usage：used `208`，remaining `292`，latest request cost `3`。
- `.local.env.example` 可作为固定文件名 fallback 被读取，但占位值 `replace_with...` 会被跳过；真实 key 仍不得提交 GitHub。Config doctor 已同步该规则，当前本机 status `ready`。
- `Unknown sport` blocked payload 现在包含 request context 与 discovery/credit-safe 诊断，避免只返回一段 404 文本。
- Team Total manual workbench 新增导入质量矩阵：`import_quality`、`next_batch_quality`、`quality_gate_summary`。当前 `waiting_for_manual_rows`，missing events `68`；TT-001 下一批 8 场均为 `missing_rows`，逐场列出缺字段和缺 over/under 方向。
- 首页新增 `质量 Gate` 与 `质量诊断`，字段检查完整显示 11 项；API `/api/status.provider_manual_workbench` 已暴露质量诊断字段。
- 已重建 Downloads HTML/App 和 `artifacts/latest` provider/manual/config/KPI 产物。
- 验证：完整 suite `200 tests in 13.494s OK`；API smoke OK；Browser desktop/mobile 均显示 `质量 Gate / 质量诊断 / missing_rows / TT-001`，横向 overflow `0`，console error `0`。
- 未完成：Team Total 仍需 OpticOdds 官方允许访问或 TAB 人工最终校验；formal publish/full automation 仍为 `false`，stake `AUD 0`。

## 最新追加更新（2026-06-14 04:08 AEST）

- 已把 Team Total 人工补齐工作台升级为平台操作台：`operator_cockpit`、`next_batch_summary`、`field_checklist`、`workflow_steps`、`action_contract`。
- 当前操作台：`TT-001`，8 场，16 个 Over/Under 成对待填行，字段检查 8 项，流程步骤 5 项。
- 首页 `人工校验导入状态` 新增 `TT-001 操作台`、`操作台流程`、`字段检查`、下一批摘要；移动端局部溢出已修复。
- `/api/status.provider_manual_workbench` 现在返回操作台字段、publish status、can publish 状态；当前 publish status 为 `blocked_until_manual_import_and_signature`，stake `AUD 0`。
- 已同步 manual workbench 与相关 public-safe artifacts 到 `artifacts/latest/`。
- 验证：目标测试 `3 tests OK`；完整 suite `197 tests in 13.198s OK`；API smoke OK；Browser desktop/mobile overflow `0`、console error `0`；tracked secret scan `0`。
- 剩余 gate：仍需人工 CSV/OpticOdds 官方允许访问，之后才可走 hash gate、overlay preview、签名预检、显式 publish；未完成前不进入 formal automation。

## 最新追加更新（2026-06-14 03:56 AEST）

- 已复测用户反馈的 raw 命令：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --timeout-seconds 30` 当前成功，返回 `provider_raw_staged`。
- 最新 active refresh id：`20260613T175342Z-provider-9141af88`。
- The Odds API 最新 usage：last cost `3`，reported used `207`，remaining `293`。
- Provider KPI：`53.50%`；Result `68/68`，Handicap `47/68`，Total O/U `55/68`，Team Total O/U `0/68`；stake `AUD 0`。
- 已加固旧 sport key 防护：`soccer_world_cup` 会在请求构造前按 scope 自动映射为当前有效 key，避免 discovery 关闭或 shell 环境污染时继续请求无效 sport。
- 用户不需要改 `config/odds_providers.local.env.example` 文件名。该文件保留为 GitHub 模板；真实 key 只放 ignored `config/odds_providers.local.env`，不提交。
- 已同步 public-safe artifacts 到 `artifacts/latest/`：raw manifest、coverage、KPI、config doctor、alternate plan、alternate evidence。
- 验证：config doctor `ready`；legacy sport count `0`；目标测试 `4 tests OK`；`py_compile` OK；`git diff --check` OK。
- 当前阻塞不变：formal publish `false`，full automation `false`，Team Total 仍需 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验。

## 最新追加更新（2026-06-14 03:46 AEST）

- 已复测 `python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches`：本机配置有效，The Odds API Matches 主盘口 refresh 成功，不再复现 `UNKNOWN_SPORT`。
- 最新 provider refresh：`20260613T173737Z-provider-e531900e`；Result `68/68`，Handicap `47/68`，Total O/U `55/68`，Team Total O/U `0/68`；reported used `204`，remaining `296`，last cost `3`。
- 已修复 provider refresh 成功后 KPI 滞后的问题：`refresh_odds_provider_raw.py` 现在会在同一成功路径重建 `provider_kpi_latest.*`，CLI 输出包含 `provider_kpi_refresh_id`、`provider_kpi_status`、`provider_kpi_primary_gap`。
- 已新增 `provider_alternate_probe_evidence_latest.json`：持久保存 event-market evidence，避免普通主盘口 refresh 把 Team Total 低收益样本证据清空。
- 当前 alternate plan 仍为 `fallback_required`：event-market sample `3`，Team Total available sample `0`，Total O/U available sample `3`，probe queue `0`，fallback queue `68`，operational decision `manual_or_official_provider_priority`。
- 当前 KPI score：`53.50%`；primary gap：`Team Total Score O/U 覆盖: 0/68 (0.00%)`；current executable new stake：`AUD 0`。
- 首页 UI/API 已改进：
  - Provider KPI 卡片区分 `当前阻塞` 与 `历史失败`。
  - 旧 `odds_provider_blocked_latest.json` 在当前 KPI 中标为 `stale_history_only=true`，不代表 active refresh 失败。
  - app_assets 新增 `provider_alternate_probe_evidence_latest.json` 链接。
  - `/api/status.provider_alternate_plan` 返回 event_probe_evidence counts。
- 已同步 public-safe artifacts 到 `artifacts/latest/`：raw manifest、coverage、alternate plan、alternate evidence、KPI、config doctor、fallback verification、manual workbench 等 19 个文件。
- 当前验证：
  - 目标测试：KPI same-refresh rebuild、stale blocked-attempt labeling、persistent low-yield evidence across primary refresh、status API，`5 tests OK`。
  - 完整 suite：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 197 tests in 15.130s`，`OK`。
  - API smoke：`/api/status` 返回最新 KPI refresh `20260613T173737Z-provider-e531900e`、alternate plan `fallback_required`、evidence sample `3/0/3`、stake `AUD 0`。
  - Browser smoke：desktop `1280px` 与 mobile `390px` 均显示 Provider KPI、`Team Total 转人工/官方访问优先`、`历史失败` 且 `不代表当前 refresh 失败`、evidence link、`AUD 0`；无横向 overflow，console error `0`。
- 下一步仍是：Team Total 走 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验；当前最快人工路径是 `provider_manual_next_batch_pair_template_latest.csv` 的 `TT-001`。在 raw/private/preflight 未全部 ready 前，不发布正式下注日报、不解锁新增金额。

## 最新追加更新（2026-06-14 03:27 AEST）

- 已把 alternate markets plan 从“继续默认 The Odds API Team Total 小批量 probe”改为“低收益样本后转人工/官方访问优先”：
  - `provider_alternate_plan_latest.json.status`：`fallback_required`
  - `operational_decision.status`：`manual_or_official_provider_priority`
  - `probe_queue_count`：`0`
  - `fallback_queue_count`：`68`
  - recommended command：暂停 The Odds API `team_totals`；改查 OpticOdds 或 TAB 人工最终校验候选比赛。
- 判断依据：
  - The Odds API 已完成 `3` 个 TAB event-market 样本。
  - Team Total 可用样本 `0`。
  - Total O/U 已覆盖 `55/68`，达到当前可用阈值。
  - 继续盲扫 68 场会消耗 500 credits/月预算，低 ROI。
- 首页 UI 已新增 `运营决策` banner：
  - 显示 `Team Total 转人工/官方访问优先`
  - 显示原因、下一步、credit guidance
  - 今日决策中心的 Provider 任务行也显示运营动作，不再只显示 gap。
- `/api/status.provider_alternate_plan` 已返回：
  - `ready=true` for `fallback_required`
  - `operational_decision`
  - fallback queue、recommended command、stake `0`
- 当前 KPI：
  - Provider KPI score：`60.00%`
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `55/68`
  - Team Total O/U `0/68`
  - current executable new stake：`AUD 0`
- 当前验证：
  - 目标测试：alternate plan low-yield Team Total fallback、status API operational decision，`2 tests OK`。
  - 完整 suite：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 193 tests`，`OK`。
  - API smoke：`/api/status.provider_alternate_plan` 返回 `fallback_required`、`ready=true`、`manual_or_official_provider_priority`、fallback `68`、stake `0`；`/api/status.provider_kpi` 返回 progress `0.6`、stake `0`。
  - Browser smoke：desktop `1280px` 与 mobile `390px` 均显示 `运营决策`、`Team Total 转人工/官方访问优先`、`不再默认扩大 The Odds API Team Total probe`、`AUD 0`；无横向 overflow，console error `0`。
  - `py_compile` OK；`git diff --check` OK；secret scan 无真实 key 命中。
- 下一步仍然是：从 `provider_manual_next_batch_pair_template_latest.csv` 的 `TT-001` 开始人工只读补 Team Total，或解决 OpticOdds 官方允许访问/白名单；没有这些外部数据前不进入正式下注 automation。

## 最新追加更新（2026-06-14 03:13 AEST）

- 已修复 The Odds API `Unknown sport` 后暴露的本机 Python SSL CA 阻断：
  - `tab_research/odds_provider_adapter.py` 新增 `provider_ssl_attempts()` 与 `urlopen_provider_json()`。
  - 行为：先用 urllib 默认 TLS；如果本机 CA 缺失导致 `CERTIFICATE_VERIFY_FAILED`/`URLError`，自动切到 `certifi` CA bundle；不关闭 TLS、不使用 unverified context。
  - HTTP 4xx/5xx 仍直接 fail-closed，不会把真实 provider/sport/权限/额度错误伪装成成功。
- 已修复 event-level Team Total probe 导致历史 Total O/U 覆盖倒退的问题：
  - `refresh_odds_provider_raw.py` 新增 `historical_merge_market_keys()`。
  - 历史 merge 现在同时保留基础 Matches markets（`h2h,totals,spreads`）和 event-level 补齐 markets，避免 `--event-odds-markets team_totals...` 排除已覆盖的 `Total Goals Over/Under`。
- 已执行 credit-safe live refresh：
  - 主盘口 refresh：`20260613T170821Z-provider-2f478c14`，成功 staged。
  - 小批量 Team Total event-market probe：`20260613T170935Z-provider-1b4980a2`，成功 staged；未发现可用 Team Total odds payload。
  - 最新 provider request usage：payload `4`，request kinds `odds=1,event_markets=3`，latest reported cost `6`，used `201`，remaining `299`。
- 最新 provider coverage：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `55/68`
  - Team Total O/U `0/68`
  - KPI score `66.5%`
  - formal publish `false`，full automation `false`，current executable new stake `AUD 0`
- `artifacts/latest/odds_provider_raw_latest.json` 已新增同步，作为后续 agent 判断 refresh id、request usage 和 staging manifest 的 public-safe 证据。
- 新增/更新回归测试：
  - sports discovery 使用 certifi SSL fallback。
  - provider odds request 使用 certifi SSL fallback，并记录 `transport_ssl_mode`。
  - Team Total probe 时 historical merge keys 保留 primary `totals`。
- 当前验证：
  - 完整 suite `python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 192 tests`，`OK`。
  - `git diff --check` OK；`py_compile` OK；secret scan 无真实 key 命中。
  - API smoke：`/api/status.provider_config_doctor` 返回 `ready`、legacy `[]`、recommended `soccer_fifa_world_cup`、stake `0`。
  - API smoke：`/api/status.provider_kpi` 返回 refresh `20260613T170935Z-provider-1b4980a2`、status `in_progress`、progress `0.665`、stake `0`。
  - Browser smoke：desktop `1280px` 和 mobile `390px` 均显示 Provider 配置、Provider KPI、Team Total gap、recommended sport；无旧 `soccer_world_cup`、无横向 overflow、console error `0`。
- 当前仍未完成：
  - Team Total 仍需 OpticOdds 官方允许访问/白名单或 TAB 人工最终校验。
  - TAB 人工最终校验、My Bets 私有持仓、Australia Markets、完整 5-board formal raw batch 和正式日报 automation gate 仍未通过。
  - 新增下注金额继续锁定为 `AUD 0`。

## 最新追加更新（2026-06-14 02:54 AEST）

- 新增 Provider 配置医生，解决 The Odds API `Unknown sport` 和 provider credit 误用风险：
  - 模块：`tab-research-pipeline/tab_research/provider_config_doctor.py`
  - CLI：`python3 scripts/build_provider_config_doctor.py`
  - 输出：`provider_config_doctor_latest.json/md/pdf`
  - 首页区块：`Provider 配置医生`
  - API：`/api/status.provider_config_doctor`
- 当前本机诊断状态：
  - status：`ready`
  - local env：存在
  - The Odds API key：存在但不写入产物
  - OpticOdds key：存在但不写入产物
  - sports discovery：开启
  - requested sports：`soccer_fifa_world_cup`
  - recommended sports：`soccer_fifa_world_cup`
  - 本机 ignored env 已移除旧/疑似无效 `soccer_world_cup`，避免 discovery 关闭时触发 Unknown sport。
  - event-market probe limit：`0`，避免日常 automation 误消耗 credits。
  - current executable new stake：`AUD 0`
- UI 已新增导航 `Provider配置`、快捷按钮 `Provider配置`、下载清单 `Provider 配置医生 PDF/JSON/Markdown`。
- 当前验证：
  - 完整测试：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 189 tests`，`OK`。
  - API smoke：`/api/status.provider_config_doctor` 返回 `ready`、legacy sport `[]`、recommended sport `soccer_fifa_world_cup`、stake `0`。
  - Browser smoke：桌面 `1280px` 与移动 `390px` 均显示 Provider 配置医生、Unknown Sport 防护开启、推荐 sport、Event Probe `0`、`AUD 0`；横向溢出 `0`，console error `0`，未检测到 key 样式泄露。
  - Secret scan：无真实 key 命中。
- 安全边界不变：配置医生不请求 odds、不消耗 odds credits、不登录 TAB、不点击赔率、不生成新增下注金额。

## 最新追加更新（2026-06-14 02:39 AEST）

- Team Total 人工校验工作台已新增成对录入模板：
  - 全量成对模板：`provider_manual_pair_template_latest.csv`，覆盖 68 个候选，共 136 行。
  - 下一批成对模板：`provider_manual_next_batch_pair_template_latest.csv`，覆盖下一批 `TT-001` 的 8 场，共 16 行。
  - 模板预留同一 `team_scope + line` 的 `Over` / `Under` 两行，核心赔率字段默认留空；只有人工只读 TAB 后填写并保存到 `manual_verification/provider_team_total_manual_verification.csv`，才会进入导入校验。
- 首页 `人工校验导入状态` 区块已新增 `下一批成对模板`、`全量成对模板` 按钮和成对模板统计卡；顶部快捷入口和文件清单也已加入成对模板。
- `/api/status.provider_manual_workbench` 新增：
  - `all_pair_template_csv`
  - `next_batch_pair_template_csv`
  - `all_candidate_pair_rows`
  - `next_batch_pair_rows`
- 当前验证：
  - 完整测试：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 187 tests`，`OK`。
  - API smoke：`/api/status.provider_manual_workbench` 返回 `waiting_for_first_batch`、`TT-001`、remaining `68`、pair rows `136/16`、stake `0`。
  - Browser smoke：桌面 `1280px` 与移动 `390px` 均显示 `下一批成对模板`、`全量成对模板`、`成对模板`、`TT-001`、`16/136`、`AUD 0`；横向溢出 `0`，console error `0`。
- 安全边界不变：成对模板只是减少人工填写错误的录入辅助，不证明 TAB 页面真实性，不发布正式 raw，不解锁 full automation，不生成新增下注金额。

## 最新追加更新（2026-06-14 02:26 AEST）

- 修复 Team Total 人工导入模板截断问题：
  - 之前 `provider_manual_verification_status_latest.json.queue` 截断为 50，导致 CSV 模板只覆盖 50/68 个候选。
  - 现在 `provider_manual_verification_template_latest.csv` 覆盖完整 `68/68` 个候选。
- 新增 Team Total 人工校验工作台：
  - 输出：`provider_manual_workbench_latest.json/md/pdf`
  - 首页 `人工校验导入状态` 区块新增 `校验工作台`、剩余候选、下一批表格。
  - `/api/status.provider_manual_workbench` 已接入。
  - 当前状态：`waiting_for_first_batch`；批次数 `9`；下一批 `TT-001`；下一批 8 场；剩余候选 `68`；高优先级剩余 `55`；stake `AUD 0`。
- 当前验证：
  - 完整测试：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 187 tests`，`OK`。
  - API smoke：`/api/status.provider_manual_workbench` 返回 `waiting_for_first_batch`、`TT-001`、remaining `68`、high remaining `55`、stake `0`。
  - Browser smoke：桌面 `1280px` 与移动 `390px` 均显示 workbench、`TT-001`、`68`、`55`、`AUD 0`；横向溢出 `0`，console error `0`。
- 未完成不变：仍需要真实人工 Team Total CSV + matching approval 才能进入 overlay publish 成功路径；My Bets、Australia Markets、完整 5-board raw batch 和正式 automation 仍未完成。

## 最新追加更新（2026-06-14 02:13 AEST）

- Team Total 人工 overlay 显式 publish 命令已完成本轮端到端验证：
  - 完整测试：`python3 -m unittest tab-research-pipeline.tests.test_pipeline`，`Ran 186 tests`，`OK`。
  - API smoke：`/api/status.provider_manual_overlay_publish` 返回 `status=blocked_overlay_publish_preflight`、`ok=false`、`formal_raw_publish_performed=false`、`raw_batch_manifest_written=false`、`current_executable_new_stake_aud=0`。
  - Browser smoke：`http://127.0.0.1:8767/` 桌面 `1280px` 和移动 `390px` 均显示 Overlay 发布链接、阻断状态、`AUD 0` 和“不要手工复制 overlay raw 到正式 raw”边界；横向溢出 `0`，console error `0`。
- 新增通用只读子状态路由：`/api/status.<status_key>`，当前用于精确读取 `provider_manual_overlay_publish`，未知 key 返回 404，非法 key 返回 400。
- `README.md` 和 `RUNBOOK.md` 已补充 Team Total manual overlay 的命令顺序和 fail-closed 发布边界。
- 当前仍未解锁正式下注/正式 full automation：缺真实 Team Total CSV、匹配 approval 文件、My Bets 私有持仓、Australia Markets 和完整 5-board raw batch。

## 最新追加更新（2026-06-14 02:05 AEST）

- 已新增 Team Total 人工 overlay 显式 publish 命令：
  - 脚本：`tab-research-pipeline/publish_provider_manual_overlay.py`
  - 模块函数：`tab_research.provider_manual_verification.publish_provider_manual_overlay`
  - 输出：`provider_manual_overlay_publish_latest.json/md/pdf`
  - 首页 `人工校验导入状态` 区块新增 Overlay 发布状态、发布文件、batch manifest 状态、发布 Gate。
  - `/api/status.provider_manual_overlay_publish` 已接入。
- 发布规则：
  - 必须先有人工 Team Total CSV 导入，生成非空 overlay raw preview。
  - 必须有 `manual_verification/provider_team_total_overlay_approval.json`，且匹配 refresh、manual import hash、overlay raw hash、board、market family、operator。
  - publish 成功只写 `world_cup_matches` 的正式 Matches raw slot，不写 5-board `raw_refresh_batch_latest.json`。
  - 不解锁 full automation，不更新 My Bets，不生成新增下注金额，stake 保持 `AUD 0`。
- 当前真实状态：
  - 已运行一次 CLI 生成 fail-closed 状态。
  - status：`blocked_overlay_publish_preflight`
  - ok：`false`
  - overlay_event_count：`0`
  - formal_raw_publish_performed：`false`
  - raw_batch_manifest_written：`false`
  - current executable new stake：`AUD 0`
- 当前验证：
  - provider manual overlay publish 目标测试 `2 tests OK`
  - provider manual overlay 全目标测试 `5 tests OK`
  - 完整 suite `186 tests OK`
  - API 子状态 smoke OK
  - Browser 桌面/移动 overlay publish smoke OK
  - `py_compile` OK
  - Downloads app build OK
- 未完成不变：还需要真实人工 Team Total CSV + 人工签名文件才能 publish overlay；My Bets、Australia Markets 和完整正式 automation 仍未完成。

## 最新追加更新（2026-06-14 01:56 AEST）

- 已新增 Public Snapshot 显式 raw publish 命令：
  - 脚本：`tab-research-pipeline/publish_public_snapshot_raw.py`
  - 模块函数：`tab_research.public_snapshot_importer.publish_public_snapshot_raw`
  - 输出：`public_snapshot_raw_publish_latest.json/md/pdf`
  - 首页 `Public Raw Snapshot 导入` 区块新增 Raw 发布状态、发布文件、batch manifest 状态、Raw Gate 状态。
  - `/api/status.public_snapshot_raw_publish` 已接入。
- 发布规则：
  - 必须先有有效 public snapshot preview。
  - 必须有 `manual_verification/public_snapshot_import_approval.json`，且匹配 snapshot hash、preview raw hash、board、operator、source note。
  - publish 成功只写 `world_cup_matches` 的正式 Matches raw slot，不写 5-board `raw_refresh_batch_latest.json`。
  - 不解锁 full automation，不更新 My Bets，不生成新增下注金额，stake 保持 `AUD 0`。
- 当前真实状态：
  - 已运行一次 CLI 生成 fail-closed 状态。
  - status：`blocked_publish_preflight`
  - ok：`false`
  - formal_raw_publish_performed：`false`
  - raw_batch_manifest_written：`false`
  - current executable new stake：`AUD 0`
- 当前验证：
  - public snapshot 目标测试 `6 tests OK`
  - `py_compile` OK
  - Downloads app build OK
- 未完成不变：还需要真实 public snapshot JSON + 人工签名文件才能 publish Matches raw；Team Total、My Bets、Australia Markets 和完整正式 automation 仍未完成。

## 最新追加更新（2026-06-14 01:36 AEST）

- 已新增 Public Snapshot 签名发布预检层：
  - 输出 `public_snapshot_import_approval_template_latest.json`
  - 输出 `public_snapshot_import_publish_preflight_latest.json/md/pdf`
  - 首页 `Public Raw Snapshot 导入` 区块新增签名预检状态、approval 文件路径、预检问题数和发布预检 PDF 链接。
  - `/api/status.public_snapshot_publish_preflight` 已接入。
- 预检状态机：
  - 无有效 snapshot：`waiting_for_snapshot_import`
  - preview ready 但无签名文件：`waiting_for_signature`
  - hash/board/operator/source note 不匹配：`blocked_signature_mismatch`
  - 签名匹配：`ready_for_snapshot_publish_preflight`
- 关键修复：同一 public snapshot 现在生成稳定 `preview_raw_sha256`；不再把运行时当前时间写入 preview raw hash 内容，否则签名会在重建后失效。
- 当前默认状态仍为：`waiting_for_snapshot_import`，approval file `manual_verification/public_snapshot_import_approval.json`，snapshot_publish_preflight_passed `false`，formal_publish_allowed `false`，stake `AUD 0`。
- 重要边界：签名预检通过也不自动写正式 raw、不生成 raw batch manifest、不解锁下注金额；它只是后续显式 publish gate 的前置证据。
- 当前验证：public snapshot 目标测试 `4 tests OK`；`py_compile` OK。

## 最新追加更新（2026-06-14 01:20 AEST）

- 已新增 Public Raw Snapshot 导入器，作为 TAB 拒绝 AI controlled access 时的研究预览兜底入口：
  - 新模块：`tab-research-pipeline/tab_research/public_snapshot_importer.py`
  - 输出 `public_snapshot_import_manifest_template_latest.json`
  - 输出 `public_snapshot_import_status_latest.json/md/pdf`
  - 输出 `public_snapshot_import_preview_raw_latest.json`
  - 首页新增 `Public Raw Snapshot 导入` 区块和导航 `Snapshot导入`
  - `/api/status.public_snapshot_import` 已接入。
- 当前 public snapshot 状态在未放入导入文件时为：
  - status：`waiting_for_snapshot_import`
  - import dir：`manual_verification/public_raw_snapshots`
  - match_count：`0`
  - snapshot_import_preview_ready：`false`
  - formal_publish_allowed：`false`
  - full_automation_allowed：`false`
  - current executable new stake：`AUD 0`
- 支持导入形态：
  - `{ "matches": [...] }`
  - `{ "raw_snapshot": { "matches": [...] } }`
  - 每场至少需要 `match` 和 `markets`；可统计 Result、Total Goals O/U、Team Total Goals O/U、Handicap 等覆盖。
- 重要边界：该入口只生成 preview-only raw 和 hash，不能证明 TAB 页面真实性，不替代授权 odds provider raw、TAB 人工最终校验、hash/signature gate，不允许正式发布 raw，不允许新增下注金额。
- 当前验证：`py_compile` OK；public snapshot 目标测试 `3 tests OK`。
- 未完成不变：需要真实 public snapshot JSON 才能进入 preview ready；正式 raw publish、My Bets 登录授权、Australia Markets、完整正式 automation 仍未完成。

## 最新追加更新（2026-06-14 01:07 AEST）

- 已新增人工 Team Total overlay 发布预检层：
  - 输出 `provider_manual_overlay_approval_template_latest.json`
  - 输出 `provider_manual_overlay_publish_preflight_latest.json/md/pdf`
  - GitHub public-safe copy：`artifacts/latest/provider_manual_overlay_approval_template_latest.json` 与 `provider_manual_overlay_publish_preflight_latest.*`
  - `/api/status.provider_manual_overlay_publish_preflight` 已接入。
- 当前发布预检状态：
  - status：`waiting_for_import`
  - approval file：`manual_verification/provider_team_total_overlay_approval.json`
  - overlay_publish_preflight_passed：`false`
  - approved_by_user：`false`
  - publish_compatible_with_provider_raw：`false`
  - formal_publish_allowed：`false`
  - current executable new stake：`AUD 0`
- 发布预检说明：后续如果人工 CSV 生成非空 overlay raw，用户/操作员仍需按模板签名，并匹配 `refresh_id + board_id + manual_import_sha256 + overlay_raw_sha256`；预检通过也只是进入后续显式 publish 流程的前置条件，不自动覆盖正式 raw，不自动下注。
- 首页 `人工校验导入状态` 区块已显示发布预检、签名状态和问题数；desktop `1280px` 与 mobile `390px` 均显示发布预检且无横向 overflow。
- 当前验证：
  - provider manual 目标测试 `3 tests OK`
  - full suite `Ran 177 tests in 10.849s OK`
  - Node raw/My Bets security tests OK；bash syntax OK
  - `py_compile` OK
  - build Downloads app OK
  - `/api/status.provider_manual_overlay_publish_preflight` 返回 `waiting_for_import`、`passed=false`、`formal_publish_allowed=false`、`stake=0`。
- 未完成不变：需要真实人工 Team Total CSV 后才能进入签名流程；overlay 显式 publish 命令已实现；真实发布仍需人工 Team Total CSV 与签名，My Bets 登录授权仍未完成。

## 最新追加更新（2026-06-14 00:54 AEST）

- 已新增人工 Team Total overlay raw 预览层：
  - 输出 `provider_manual_overlay_preview_latest.json/md/pdf`
  - 输出 `provider_manual_team_total_overlay_raw_latest.json`
  - GitHub public-safe copy：`artifacts/latest/provider_manual_overlay_preview_latest.*` 与 `provider_manual_team_total_overlay_raw_latest.json`
  - `/api/status.provider_manual_overlay_preview` 已接入。
- 当前 overlay 状态：
  - status：`waiting_for_import`
  - overlay：`0/68`
  - high priority complete：`0/55`
  - ready_for_publish_preflight：`false`
  - approved_by_user：`false`
  - publish_compatible_with_provider_raw：`false`
  - formal_publish_allowed：`false`
  - current executable new stake：`AUD 0`
- Overlay 说明：只把通过结构校验的人工 Team Total CSV 合入 preview-only raw；当前没有人工 CSV 时只生成空预览 envelope。它不覆盖正式 raw、不证明 TAB 盘口真实性、不替代正式 provider publish gate、不自动下注。
- 首页 `人工校验导入状态` 区块已显示 Overlay 预览、合入比赛数、Overlay SHA、preflight 和发布边界；顶部/文件清单已新增 Overlay 预览链接。
- 当前验证：
  - provider manual 目标测试 `2 tests OK`
  - `py_compile` OK
  - build Downloads app OK
  - `/api/status.provider_manual_overlay_preview` 返回 `waiting_for_import`、`0/68`、`formal_publish_allowed=false`、`stake=0`
  - in-app browser desktop `1280px` 与 mobile `390px` 均显示 overlay 状态且无横向 overflow。
- 未完成不变：需要真实人工导入 CSV 后才能生成非空 Team Total overlay；overlay 显式 publish 命令已实现；真实发布仍需人工签名，My Bets 登录授权仍未完成。

## 最新追加更新（2026-06-14 00:40 AEST）

- 已新增人工导入 Hash Gate：
  - 输出 `provider_manual_hash_gate_latest.json/md/pdf`
  - GitHub public-safe copy：`artifacts/latest/provider_manual_hash_gate_latest.*`
  - `/api/status.provider_manual_hash_gate` 已接入。
- 当前 Hash Gate 状态：
  - status：`waiting_for_import`
  - complete：`0/68`
  - ready_for_manual_signature：`false`
  - approved_by_user：`false`
  - publish_compatible_with_provider_raw：`false`
  - current executable new stake：`AUD 0`
- Hash Gate 说明：只证明人工导入 CSV 的规范化内容可复核；不证明 TAB 盘口真实性，不替代 provider raw sha256 publish gate，不自动设置 `approved_by_user=true`。
- 首页 `人工校验导入状态` 区块新增 Hash Gate 状态和 PDF 链接；desktop `1280px` 与 mobile `390px` 均显示 `waiting_for_import`、`0/68`、`0/55`、`approved_by_user false` 且无横向 overflow。
- 当前验证：full suite `Ran 176 tests in 11.505s OK`；`py_compile` OK。

## 追加更新（2026-06-14 00:30 AEST）

- 已新增 Team Total 人工校验导入闭环：
  - `tab-research-pipeline/tab_research/provider_manual_verification.py`
  - 输出 `provider_manual_verification_template_latest.csv`
  - 输出 `provider_manual_verification_status_latest.json/md/pdf`
  - GitHub public-safe copy：`artifacts/latest/provider_manual_verification_*`
- 当前导入状态：
  - status：`import_missing`
  - queue：`68`
  - high priority：`55`
  - complete：`0/68`
  - high priority complete：`0/55`
  - invalid rows：`0`
  - current executable new stake：`AUD 0`
- 首页新增 `人工校验导入状态` 区块和顶部导航 `导入状态`，支持下载 CSV 模板、查看导入状态 PDF/JSON/Markdown。
- `/api/status.provider_manual_verification` 已接入，当前返回 import file、完成度、错误行、next action 和 stake `0`。
- 移动端 UI 修复：长 CSV 文件名、导入路径、表格内容、按钮和卡片均可断行；desktop `1280px` 与 mobile `390px` 均无横向 overflow。
- 新增测试：
  - `test_provider_manual_verification_writes_template_when_import_missing`
  - `test_provider_manual_verification_accepts_complete_over_under_pair`
- 当前验证：full suite `Ran 176 tests in 11.423s OK`；desktop `1280px` 与 mobile `390px` 均显示导入状态且无横向 overflow。
- safety unchanged：导入文件只做结构校验，不证明 TAB 真实性；不自动登录 TAB、点击赔率、加入 Bet Slip 或自动下注。

## 追加更新（2026-06-14 00:12 AEST）

- 已新增 Team Total 人工最终校验队列模块：
  - `tab-research-pipeline/tab_research/provider_fallback_verification.py`
  - 输出 `provider_fallback_verification_latest.json/md/pdf`
  - GitHub public-safe copy：`artifacts/latest/provider_fallback_verification_latest.*`
- 当前队列状态：
  - status：`provider_blocked_manual_verification_required`
  - refresh_id：`20260613T135338Z-provider-50380e82`
  - queue_count：`68`
  - high priority：`55`
  - provider_blocker_code：`opticodds_access_denied_1010`
  - current executable new stake：`AUD 0`
- 首页已新增 `Team Total 人工校验队列` 区块和顶部导航 `人工校验`；动作链接包括 PDF/JSON/Markdown。
- `/api/status.provider_fallback_verification` 已接入，LaunchAgent 已重启，当前 PID `13768`。
- 队列用途：只把 provider 无法覆盖的 Team Total 转成人工记录任务；禁止自动登录 TAB、点击赔率、加入 Bet Slip、自动下注或绕过 Cloudflare/browser signature。
- 新增测试 `test_provider_fallback_verification_builds_manual_queue`。
- 当前验证：full suite `Ran 174 tests in 11.680s OK`；desktop `1280px` 与 mobile `390px` 均显示人工校验队列且无横向 overflow。
- safety unchanged：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-14 00:00 AEST）

- 已继续执行 The Odds API credit-safe Total O/U 补齐批次，最新 refresh_id：`20260613T135338Z-provider-50380e82`。
- 最新 provider coverage：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `55/68`，已达到 `70%` 可用阈值；剩余 `13` 场当前无可继续补齐的 The Odds API TAB event-level 队列。
  - Team Total O/U `0/68`，保持 fallback。
- Credit 状态：reported used `180`，remaining `320`，last request cost `13`，inferred monthly limit `500`。
- Provider alternate plan 状态已从普通 blocked 细化为 `fallback_required`：
  - The Odds API Total O/U probe queue `0`
  - Team Total fallback queue `68`
  - recommended batch `0`
  - recommended command：暂停 The Odds API team_totals；改查 OpticOdds 或 TAB 人工最终校验候选比赛。
- 已修复状态文案：
  - 首页 Provider 模块显示“Provider 路径：转人工校验”，不再提示继续跑无效 probe。
  - `provider_alternate_plan_latest.*` 标记 Total O/U 为 `coverage_threshold_met_no_remaining_the_odds_api_queue`。
  - `provider_kpi_latest.*` 的下一步改为 Team Total 走 OpticOdds 官方访问或 TAB 人工最终校验。
- 已同步 public-safe artifacts 到 GitHub worktree：
  - `artifacts/latest/provider_kpi_latest.*`
  - `artifacts/latest/provider_alternate_plan_latest.*`
  - `artifacts/latest/odds_provider_blocked_latest.json`
  - `artifacts/latest/odds_provider_coverage_latest.json`
- 当前验证：
  - full suite `Ran 173 tests in 9.960s OK`
  - `/api/status` 返回 latest provider refresh `20260613T135338Z-provider-50380e82`、alternate status `fallback_required`、stake `0`
  - in-app browser desktop `1280px` 与 mobile `390px` 均显示 `55/68`、`fallback_required`、`转人工校验`，无横向 overflow。
- safety unchanged：formal publish `false`，full automation `false`，current executable new stake `AUD 0`。

## 最新追加更新（2026-06-13 23:43 AEST）

- 已验证 OpticOdds live path：
  - command：`python3 refresh_odds_provider_raw.py --provider opticodds --scope matches --timeout-seconds 30`
  - result：OpticOdds 返回 Cloudflare `1010 Access denied` / `opticodds_access_denied_1010`
  - safety：不绕过 browser signature；Team Total 继续保持 OpticOdds 官方允许访问方式或 TAB 人工最终校验 fallback。
- 已修复 provider failure 状态管理：
  - 失败 refresh 现在写入 `odds_provider_blocked_latest.json`
  - 有 last-good coverage 时不再覆盖 `odds_provider_coverage_latest.json`
  - `/api/status.provider_blocked` 与 Provider KPI 现在显示最近阻断、blocker_code、last_good_coverage_preserved 和 next_safe_action。
- 已继续执行 The Odds API totals-only live probe：
  - refresh_id：`20260613T134035Z-provider-a3daa59b`
  - reported last request cost `13`
  - reported used `76`，remaining `424`
- 覆盖变化：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `15/68`，从上一轮 `10/68` 增加到 `15/68`
  - Team Total O/U 仍为 `0/68`
- Provider alternate plan 当前：
  - The Odds API Total O/U probe queue `53`
  - Team Total fallback queue `68`
  - recommended next batch `5`
  - estimated next credit `5-15`
- Provider KPI 当前 score：`59.65%`；完整测试最新为 `172 tests OK`。
- 首页 Provider 模块已显示 OpticOdds blocker 与 last-good preserved 状态；desktop `1280px` 与 mobile `390px` 浏览器验证均无横向 overflow。
- formal publish、full automation 仍为 `false`；current executable new stake 仍为 `AUD 0`。

## 最新追加更新（2026-06-13 23:31 AEST）

- 已发现并修复 alternate probe 跨 refresh 重复消耗 credit 的问题：
  - 23:23 AEST 执行 totals-only probe 后，The Odds API used `37→50`，但 Total O/U 仍停在 `5/68`；原因是 CLI 每次都从同一批前 5 个 event 重新 probe。
  - 已新增历史 staged raw 读取：下一批 event probe 会排除历史已补过目标 market 的 event_id。
  - 已新增历史 event odds 研究层合并：新 staging raw 会合并历史已补 Total O/U，并标记 `provider_historical_merge=true`；正式发布和新增下注仍必须通过 TAB 人工最终校验。
  - 历史合并在 CLI 中限制为本次请求的 target markets，避免旧宽口径 BTTS/DNB/Double Chance 被误当作当前主研究覆盖。
- 修复后已执行第三轮真实 live 小批量 probe：
  - command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals --timeout-seconds 30`
  - new refresh_id：`20260613T132806Z-provider-40fc69ff`
  - provider_payload_count `11`：odds `1`、event_markets `5`、event_odds `5`
  - reported last request cost `13`
  - reported used `63`，remaining `437`
- 覆盖变化：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `10/68`，从上一轮 `5/68` 增加到 `10/68`
  - Team Total O/U 仍为 `0/68`
- Provider alternate plan 已更新：
  - The Odds API Total O/U probe queue `58`
  - Team Total fallback queue `68`
  - recommended next batch `5`
  - estimated next credit `5-15`
  - recommended command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals`
- 已重建 Downloads 首页/app assets，并同步 public-safe `provider_kpi_latest.*` 与 `provider_alternate_plan_latest.*` 到 GitHub artifacts。
- formal publish、full automation 仍为 `false`；current executable new stake 仍为 `AUD 0`。

## 最新追加更新（2026-06-13 23:11 AEST）

- 已按补齐计划执行一次真实 live 小批量 alternate probe：
  - command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals,team_totals,alternate_team_totals --timeout-seconds 30`
  - new refresh_id：`20260613T130210Z-provider-0583770a`
  - provider_payload_count `11`：odds `1`、event_markets `5`、event_odds `5`
  - reported last request cost `13`
  - reported used `37`，remaining `463`
- 覆盖变化：
  - Result `68/68`
  - Handicap `47/68`
  - Total O/U `5/68`，从上一轮 `3/68` 增加到 `5/68`
  - Team Total O/U 仍为 `0/68`
- Event-market evidence：
  - 5/5 probes 有 `alternate_totals`
  - 0/5 probes 有 `team_totals` 或 `alternate_team_totals`
  - 结论：The Odds API 当前 TAB sample 可继续补 Total O/U；Team Total 不再继续用 The Odds API 盲扫。
- Provider alternate plan 已更新：
  - The Odds API probe queue `63`
  - Team Total fallback queue `68`
  - recommended next batch `5`
  - estimated next credit `5-15`
  - recommended command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals`
  - recommended next action：继续用 The Odds API 小批量补 Total O/U，同时把 Team Total 转入 OpticOdds/TAB 人工校验。
- 首页 Provider 板块已显示 Fallback 队列、totals-only 命令和 Team Total fallback 说明；浏览器验证 desktop `1280px` 与 mobile `390px` 均无横向 overflow。
- formal publish、full automation 仍为 `false`；current executable new stake 仍为 `AUD 0`。

## 最新追加更新（2026-06-13 22:48 AEST）

- 新增 credit-aware alternate markets 补齐计划模块：
  - `tab-research-pipeline/tab_research/provider_alternate_plan.py`
  - 输出 `provider_alternate_plan_latest.json/md/pdf`
  - public-safe GitHub artifacts：`artifacts/latest/provider_alternate_plan_latest.*`
- `refresh_odds_provider_raw.py` 在 provider staging/coverage 后会同步写补齐计划；不会自动下注，不会绕过 TAB，不会发布 formal raw。
- `provider_kpi_latest.*` 已接入补齐计划摘要，并新增 KPI 行 `Alternate markets 补齐计划`；当前 overall score 因 KPI 行变化为 `59.00%`，不代表 Team Total 覆盖改善。
- 当前 alternate plan：
  - status `in_progress`
  - probe queue `65`，已排除 3 场已拉过 event odds 的样本，避免重复花 credits。
  - recommended batch `5`
  - estimated next batch credit `5-25`
  - recommended command：`python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 5 --event-odds-limit 5 --event-odds-markets totals,alternate_totals,team_totals,alternate_team_totals`
- 首页 Provider 板块已新增“补齐计划”链接、下一批 Probe、推荐命令和前 5 场队列；`/api/status.provider_alternate_plan` 已返回 status/queue/batch/credit/command。
- 当前本地服务已由 LaunchAgent `com.linzezhang.tab-fifa-research` 托管，PID `86499`，运行路径 `github_sync/FIFA/tab-research-pipeline`，日志 `/tmp/tab_fifa_app_server.log`；模板已同步到 `ops/launch_agents/com.linzezhang.tab-fifa-research.plist`。
- 浏览器验证：
  - desktop `1280px`：Provider 板块可见、补齐计划链接可见、队列 `65`、batch `5`、无横向 overflow。
  - mobile `390px`：Provider 板块可见、长命令可读、无横向 overflow。
- 已验证：
  - `py_compile` -> OK
  - target tests `2` -> OK
  - full suite `Ran 168 tests in 12.540s OK`
  - `git diff --check` -> OK
  - secret scan excluding ignored local env -> no hits
- 未完成不变：
  - Team Total O/U 仍为 `0/68`。
  - formal publish 和 full automation 仍为 `false`。
  - current executable new stake 仍为 `AUD 0`。
  - The Odds API key 曾在远端历史出现过，仍应在 provider 后台 rotate。

## 最新追加更新（2026-06-13 22:29 AEST）

- 已修复 CLI 本地 env 读取顺序：`refresh_odds_provider_raw.py` 现在先预加载默认 `config/odds_providers.local.env`，再解析参数，确保 `TAB_FIFA_THE_ODDS_API_EVENT_MARKET_PROBE_LIMIT`、`TAB_FIFA_THE_ODDS_API_EVENT_ODDS_LIMIT`、`TAB_FIFA_THE_ODDS_API_EVENT_ODDS_MARKETS` 等本地配置不用手动 `source` 也能生效。
- 配置放置规则保持不变：
  - tracked 模板：`tab-research-pipeline/config/odds_providers.local.env.example`
  - 本机真实 key：`tab-research-pipeline/config/odds_providers.local.env`
  - 真实 key 文件由 `.gitignore` 排除，禁止同步 GitHub。
- `/api/status.provider_kpi` 当前验证：
  - `ready=true`
  - `status=in_progress`
  - `overall_progress_pct=0.5833`
  - `refresh_id=20260613T121414Z-provider-51410a2f`
  - `event_count=68`
  - `formal_publish_allowed=false`
  - `full_automation_allowed=false`
  - `current_executable_new_stake_aud=0`
  - primary gap：`Team Total Score O/U 覆盖: 0/68 (0.00%)`
- 当前 8767 服务已验证：`ok=true`、`raw_status=blocked`、`private_status=profile_login_required`，符合当前 fail-closed 边界。
- 已验证：
  - `py_compile` -> OK
  - `git diff --check` -> OK
  - secret scan excluding ignored local env -> no hits
  - full suite `Ran 167 tests in 65.505s OK`

## 最新追加更新（2026-06-13 22:17 AEST）

- 已实现 credit-aware alternate markets 补齐路径：
  - 新增 The Odds API event-level `/events/{eventId}/markets` 探测请求。
  - 新增 `/events/{eventId}/odds` 拉取逻辑，只在探测发现目标 market 后执行。
  - `adapt_matches_raw()` 改为按 event 合并 markets，event odds 补回来的 `Total Goals Over/Under` 会并入原比赛行，不产生重复 match。
  - `refresh_odds_provider_raw.py` 新增 `--event-market-probe-limit`、`--event-odds-limit`、`--event-odds-markets`；默认 probe limit 为 `0`，防止 automation 意外消耗 credits。
- 已执行 live 小样本 probe：
  - `refresh_id=20260613T121414Z-provider-51410a2f`
  - payload count `7`：`odds=1`、`event_markets=3`、`event_odds=3`
  - reported last request cost `18`，remaining `476`
  - Matches `68`
  - coverage：`Result 68/68`、`Handicap 47/68`、`Total O/U 3/68`、`Team Total O/U 0/68`
  - 结论：event-level alternate path 可以补 `Total O/U`；当前未补到 `Team Total O/U`。
- 为保护 500 credits/月，已把默认 event odds market 收窄为：
  - `totals,alternate_totals,team_totals,alternate_team_totals`
  - `btts,draw_no_bet,double_chance` 不再默认拉取，只能手动加入。
- 新增 Provider KPI 系统：
  - `tab_research/provider_kpi.py`
  - 输出 `provider_kpi_latest.json/md/pdf`
  - GitHub public-safe 备份：`artifacts/latest/provider_kpi_latest.*`
  - 当前 KPI score `58.33%`，primary gap 为 `Team Total Score O/U 覆盖: 0/68`。
- 首页已新增 `Provider 覆盖与缺口` 板块，并加入顶部“今日决策中心”和导航；API `/api/status` 新增 `provider_kpi` 字段。
- 已验证：full suite `Ran 167 tests in 44.476s OK`。

## 最新追加更新（2026-06-13 21:51 AEST）

- 已修复 The Odds API `Unknown sport` live 阻塞：
  - 默认 Matches sport key 改为 `soccer_fifa_world_cup`。
  - Futures sport key 改为 `soccer_fifa_world_cup_winner`。
  - `refresh_odds_provider_raw.py` 默认启用 The Odds API `/v4/sports` discovery，自动过滤配置中已失效的 sport key，例如旧的 `soccer_world_cup`。
- 已把用户误放在 tracked `.example` 模板里的真实 key 复制到本机 Git 忽略文件 `tab-research-pipeline/config/odds_providers.local.env`，并把 `.example` 恢复为 placeholder；真实 key 不同步 GitHub。
- 已修复 env 模板里 `TAB_FIFA_OPTICODDS_QUERY` 的 shell source 风险，改为带引号。
- 已完成 live The Odds API Matches 拉取：
  - `refresh_id=20260613T114657Z-provider-728d17c6`
  - provider payload count `1`
  - reported last request cost `3`
  - reported requests remaining min `494`
  - sport `soccer_fifa_world_cup`
  - markets `h2h,spreads,totals`
  - staged Matches `68`
  - market coverage：`Result 68/68`、`Handicap 47/68`、`Total O/U 0/68`、`Team Total O/U 0/68`
- Coverage 分层已优化：
  - `provider_analysis_ready_target_count=1`，Matches 主盘口研究可用。
  - `formal_publish_allowed=false`、`full_automation_allowed=false`、`current_executable_new_stake_aud=0` 保持不变。
  - coverage warning 明确写出当前 TAB-labeled provider payload 未返回 Total O/U 和 Team Total O/U。
- 已验证：
  - Codex runtime Python `py_compile` -> OK
  - provider 目标测试 7 个 -> OK
  - full suite `Ran 163 tests in 17.264s OK`

## 最新追加更新（2026-06-13 21:27 AEST）

- 已把授权 provider raw 路线改为 Matches 优先，地区盘口默认忽略。
- `tab-research-pipeline/refresh_odds_provider_raw.py` 新增 `--scope matches|futures|all`，默认 `matches`；新增 `--include-region-markets`，不传时排除 `world_cup_australia_markets`。
- The Odds API 默认 market 改为省 credit 的 Matches 主盘口：`h2h,totals,spreads`；`outrights` 只在 `--scope futures/all` 使用。
- `Team Total Goals Over/Under` 已支持 provider payload 解析和候选评分；The Odds API 扩展 market 通过 `TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS=team_totals,alternate_team_totals` 手动开启，未验证前不默认请求。
- 新增本地 secret 模板 `tab-research-pipeline/config/odds_providers.local.env.example`；真实 `config/odds_providers.local.env`、`.env`、`*.local.env` 已加入 `.gitignore`，不会同步 GitHub。
- Coverage 分离三层状态：
  - `provider_analysis_ready`：Matches 主盘口可用于候选研究。
  - `formal_publish_allowed`：当前 scope raw 严格校验+人工 TAB hash 校验后可发布。
  - `full_automation_allowed`：完整自动日报 gate；Matches-only 不会误放行。
- `publish_verified_provider_raw()` 已修成 scope-aware；Matches-only 发布不会尝试生成 5/5 batch manifest。
- 已更新 README/RUNBOOK/ODDS provider docs/DEVELOPMENT_STATUS/工作区 handoff。
- 已验证：
  - `PYTHONPYCACHEPREFIX=/private/tmp/tab-fifa-pycache-match-provider python3 -m py_compile tab_research/odds_provider_adapter.py refresh_odds_provider_raw.py tab_research/pipeline.py tab_research/parser.py tab_research/model.py tests/test_pipeline.py` -> OK
  - provider/Team Total 目标单测 6 个 -> OK
- 未完成：真实 API key 不进 GitHub，未跑 live API coverage；正 CLV 仍需后续 closing line 数据闭环。

## 最新追加更新（2026-06-13 19:50 AEST）

- 已把 raw 解决路线从“用户全量截图/导出兜底”升级为“授权第三方 TAB-labeled odds API 主路径 + TAB 人工最终校验 gate”。
- 新增 `tab-research-pipeline/tab_research/odds_provider_adapter.py`：
  - The Odds API 请求构造：`regions=au`、`bookmakers=tab`、`oddsFormat=decimal`、markets 默认 `h2h,spreads,totals,outrights`。
  - OpticOdds 请求构造：默认 `/fixtures/odds`，endpoint/query 可用环境变量按账号文档配置。
  - TAB bookmaker 过滤、The Odds API/OpticOdds nested/flat odds payload 兼容。
  - Matches raw adapter、Futures outright adapter、provider staging manifest、coverage manifest。
  - 人工 TAB final verification：必须匹配 `refresh_id + board_id + sha256` 才能标记单板块 publish-ready。
  - 全部 required boards publish-ready 前，formal publish 被阻断，新增执行金额保持 `AUD 0`。
- 新增 CLI：`tab-research-pipeline/refresh_odds_provider_raw.py`。
  - 无 key 时 fail-closed，写 `provider_raw_blocked`，退出码 `2`。
  - 有 key 或 `--input-json` 时只写 staging：`outputs/provider_raw/<refresh_id>/`、`outputs/odds_provider_raw_latest.json`、`outputs/odds_provider_coverage_latest.json`。
  - `--publish-verified` 只有在 coverage 和人工 verification 全通过时才发布到正式 raw snapshots。
- 新增配置/说明：
  - `tab-research-pipeline/config/odds_providers.example.json`
  - `docs/ODDS_PROVIDER_INTEGRATION_20260613.md`
- 已更新 `README.md`、`RUNBOOK.md`、`docs/FEATURE_LIST.md`、`docs/DELIVERY_STANDARDS.md`、`docs/DEVELOPMENT_STATUS.md`。
- 已新增并通过 provider 单测：
  - The Odds API 请求必须 AU/TAB/decimal 且 redacted URL 不泄露 key。
  - TAB-labeled provider matches raw 可通过现有 matches raw validation。
  - 未人工校验时只 staging，不写正式 raw。
  - 单板块人工 hash 校验通过仍不能绕过 5/5 required board formal publish gate。
- 验证：
  - `PYTHONPYCACHEPREFIX=/private/tmp/tab-fifa-pycache-provider python3 -m unittest tests.test_pipeline.PipelineTests.test_the_odds_api_request_is_tab_au_decimal_only tests.test_pipeline.PipelineTests.test_provider_adapter_stages_tab_labeled_matches_without_formal_publish tests.test_pipeline.PipelineTests.test_provider_adapter_publishes_only_when_manual_verification_hash_matches` -> `Ran 3 tests ... OK`
  - `PYTHONPYCACHEPREFIX=/private/tmp/tab-fifa-pycache-provider python3 -m py_compile tab_research/odds_provider_adapter.py refresh_odds_provider_raw.py tests/test_pipeline.py` -> OK
  - `python3 refresh_odds_provider_raw.py --provider the_odds_api --output-dir /private/tmp/tab-fifa-provider-smoke` -> expected fail-closed exit `2` because `THE_ODDS_API_KEY` is missing; output kept executable stake `0`。
- 当前未完成：真实 API key 未配置，未跑 The Odds API / OpticOdds live coverage，Australia Markets provider 覆盖未知，My Bets 仍需用户授权。

## 最新追加更新（2026-06-13 18:59 AEST）

- 已完成用户要求的并行审查与修复收口，审查摘要见 `docs/PARALLEL_REVIEW_SUMMARY_20260613.md`。
- 已修复本地 app POST 安全：所有 `/api/*` POST 需要 per-process action token，并验证 local Host/Origin/Referer；前端所有 POST 统一附带 `X-TAB-FIFA-Action-Token`。
- 已修复私有 My Bets 泄露风险：私有快照拒绝写入 public `outputs/private/**`，public artifact safety scan 不再跳过 nested private position files。
- 已修复 GitHub worktree 输出目录问题：新增 `tab_research.paths`，统一解析 workspace/output/private 目录，避免 fixed parent-depth 指到 `github_sync/outputs`。
- 已修复主动测试文案和交互：点击后先显示缓存快照，再返回实时结果；research-only 日报未 ready 时明确写 `未达到 ready`，不再错误声称“已补写”。
- 已修复后台 runner 竞态：关键启动路径加锁，父进程写 PID。
- 已重建真实入口：`/Users/linzezhang/Downloads/FIFA Report/TAB FIFA盘口研究系统.html`、`/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`。
- 已重启本地服务：当前 `http://127.0.0.1:8767/` PID `3984`，cwd 为 `github_sync/FIFA/tab-research-pipeline`。
- 浏览器实测通过：首页推荐下注、市场资金、主动测试、导航、只读边界和 action token 存在；主动测试返回 `fresh_timeline_direct_api`，无空白失败。
- 验证通过：
  - `PYTHONPYCACHEPREFIX=/private/tmp/tab-fifa-pycache-review python3 -m unittest tests.test_pipeline` -> `Ran 155 tests in 67.990s OK`
  - `node scripts/refresh_tab_readonly_security.test.mjs` -> OK
  - `node scripts/capture_tab_my_bets_readonly_security.test.mjs` -> OK
  - `bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh scripts/verify_fifa_automation_readiness.sh` -> OK
- 新增文档：`docs/FEATURE_LIST.md`、`docs/DELIVERY_STANDARDS.md`、`docs/DELIVERY_PACKAGE_MANIFEST_20260613.md`。
- 当前仍不能进入完整正式 automation：raw 仍被 `ai_controlled_access_rejected` 阻断，Australia Markets 仍缺失/route mismatch，My Bets 仍需用户本机授权登录，当前新增执行金额保持 `AUD 0`。

## 最新追加更新（2026-06-13 17:15 AEST）

- 已为 `TAB FIFA盘口研究系统.app` 设计并安装新 macOS 图标。
- 图标概念：`Research Compass`，使用足球核心、盘口/概率雷达、数据价值线和金色价值标记；避免博彩筹码、投注单、美元符号等低质博彩视觉。
- 本地源文件：
  - `work/tab-research-pipeline/assets/app_icon/TABFIFAResearch.png`
  - `work/tab-research-pipeline/assets/app_icon/TABFIFAResearch.icns`
  - `work/tab-research-pipeline/assets/app_icon/generate_app_icon.py`
  - `work/tab-research-pipeline/assets/app_icon/design_notes.md`
- 已更新 `work/tab-research-pipeline/scripts/build_downloads_app_entry.py`，每次重建 app 会自动复制 `TABFIFAResearch.icns` 到 `Contents/Resources/`，并写入 `CFBundleIconFile=TABFIFAResearch`。
- 已重建并刷新 `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`；当前 app bundle 已包含 `Contents/Resources/TABFIFAResearch.icns`。
- `generate_app_icon.py` 默认清理 `.iconset` 中间目录；当前源目录只保留正式 PNG、ICNS、脚本和设计说明，无 `__pycache__`/`.iconset` 缓存。
- 已验证：`CFBundleIconFile=TABFIFAResearch`、ICNS 文件有效、`py_compile` 通过、app 入口 contract 单测通过。

## 最新追加更新（2026-06-13 17:05 AEST）

- 已将后续开发主仓库确定为 `https://github.com/LinzeColin/FIFA`；本地工作副本为 `github_sync/FIFA`。
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
