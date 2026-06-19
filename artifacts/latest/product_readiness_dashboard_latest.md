# TAB FIFA 产品完成度 Dashboard

本报告从用户视角验收当前系统是否已经达到下注研究日报/自动化前的产品水位。它不是下注执行指令。

## Executive Summary

- status: `in_progress`
- product_readiness_score: `82.20%`
- ready / partial / blocked: `8 / 4 / 1`
- current_executable_new_stake_aud: `AUD 0`
- primary_user_action: 导入只读 私有持仓 结算结果和开赛前/收盘赔率后，按板块、EV bucket 和 CLV/ROI 偏差校准下注阈值。
- primary_gap: 每日 automation 准入
- recommended_next_action: 每日 automation 准入：导入只读 私有持仓 结算结果和开赛前/收盘赔率后，按板块、EV bucket 和 CLV/ROI 偏差校准下注阈值。

## 新旧完成度变化

- compare_status: `compared`
- previous_generated_at: `2026-06-13T14:45:25.465657+10:00`
- score_delta: `0.0385`
- status_delta: `in_progress -> in_progress`

## Capability Matrix

| 能力 | 状态 | 得分 | 用户结论 | 证据 | 下一步 | 相对静态报告价值 |
|---|---|---:|---|---|---|---|
| 下注决策首页 | ready | 100.00% | 首页第一屏已显示推荐下注板块、主动测试、补跑按钮和概率/赔率即时 EV 编辑。 | 推荐表字段 21/21；EV 输入 11 个。 | 保持并随每次日报重算。 | 强于静态报告：打开入口即可看到该怎么操作、为什么暂停或下注、金额和 EV。 |
| 推荐操作归档 | ready | 100.00% | 首页推荐下注板块已沉淀为正式 PDF/JSON/Markdown 操作研究报告，并写入本地 SQLite 快照。 | 候选盘口 0；研究候选金额 AUD 0；当前可执行金额 AUD 0；状态 research_only_blocked。 | 保持并随每次日报重算。 | 比静态报告更直接：用户可以把首页操作建议、暂停原因、新旧变化和金额归档到同一份研究报告。 |
| 策略表现与回测闭环 | partial | 75.00% | 历史推荐、EV/Edge、研究金额、预期收益、CLV/ROI 准备度和新旧变化已形成策略表现 Dashboard；真实收益缺失时明确 outcome_pending。 | 历史推荐 2318；买入样本 427；研究金额 AUD 5,210；加权EV 12.89%；ROI=outcome_pending；CLV=clv_pending；状态 tracking_ready_outcome_pending。 | 导入只读 私有持仓 结算结果和开赛前/收盘赔率后，按板块、EV bucket 和 CLV/ROI 偏差校准下注阈值。 | 不只给下注建议，还能追踪这些建议后来有没有变好：预期收益、真实收益、CLV、EV 分桶和板块表现能逐日优化。 |
| 可视化报告体系 | ready | 100.00% | 公开报告族已纳入图表、表格、Dashboard、自动化状态、新旧对比和 GitHub 参考审计。 | 报告族 21；图表 21；Dashboard 21；新旧对比 21/21。 | 保持并随每次日报重算。 | 比单一 PDF 更适合每日复盘：报告、仪表盘、状态门禁和源证据能一起看。 |
| 新旧报告变化总控 | ready | 100.00% | 已把日报 diff、报告族目录、推荐操作变化、策略表现变化和产品完成度变化汇总成跨报告族新旧变化总控台。 | status=tracking_ready；diffs=20；报告族=21；新旧覆盖=21；目录变化=1。 | 保持并随每次日报重算。 | 比静态报告更适合长期优化：能直接看新报告相对旧报告哪些变了、哪些退化、哪些仍不能执行。 |
| 开源模型吸收 | ready | 100.00% | 已把 Hicruben、goalmodel、Dixon-Coles、penaltyblog、socceraction、openfootball 等 GitHub/开源模型和公开数据源转为本地模型审计、分歧、基本面、赛程校验、布局参考和 UI/Dashboard 蓝图。 | 参考源 6；已落地 3；design reference 3；GitHub元数据 ready 6/6；4小时freshness=stale_or_partial 0/6，stale=6，max_age=6.62h；stars/open issues 1431/47。 UI蓝图 4/6；partial 1；data_required 1。 UI界面覆盖 6/6；gated 2；layout_ready=True。 | 保持并随每次日报重算。 | 下注建议不只看隐含概率，能展示模型共识、赔率去水、基本面、赛程校验、分歧、开源方法来源和对应的报告界面设计。 |
| 公开赛程校验 | ready | 100.00% | 已把 openfootball/worldcup.json 公开赛程接入为 TAB Matches raw 的辅助校验，帮助发现队名、日期、分组、场地和赛果差异。 | status=ready_with_delayed_public_source；openfootball=104；TAB raw=26；matched=23；review=84。 | 保持并随每次日报重算。 | 比静态报告更可靠：能把公开赛程源与 TAB raw 做每日差异检查，并写入新旧对比。 |
| 数据库与新旧对比 | ready | 90.00% | 日报 run、推荐、artifact、report diff、automation audit 和当前产品成熟度快照写入 SQLite。 | runs=61；diffs=61；recommendations=2318；report_evolution=125；strategy_performance=125；fixture_sanity=128；report_catalog=5305；visual_inventory=256；automation_maturity=101；automation_doctor=86；product_snapshots=398。 | 保持并随每次日报重算。 | 能做日报/周报、回测、能力变化和旧报告差异追踪。 |
| 实时盘口与板块门禁 | partial | 57.00% | 系统已把 TAB Live discovery、available board strategy 和 raw refresh 作为执行建议前置门禁。 | raw_ready=False；discovery_ready=True；listed=3/5；missing=2；route_mismatch=True；matches_live_targets=9；partial_refresh=4/5。 | Matches/Futures/Group Betting 已能只读刷新，当前 Matches live targets=9；最新 raw diagnostics 已证明 4/5 个尝试板块可研究；Australia Markets、Team Futures Multi 未在 TAB live 导航中列出并出现 route mismatch。保持这两个板块 unavailable，不用旧盘口；等待 TAB 重新列出或只生成研究-only 诊断，新增执行金额维持 AUD 0。 | 阻止用旧盘口或被拦截页面生成误导性下注建议。 |
| 主动测试与补缺 | partial | 55.00% | 主动测试会按每天至少 4 次分析、每天 1 份报告检查时间线，并在 raw 通过后补跑缺口。 | 检查天数 9；分析缺口日 5；日报缺口日 8；补跑队列 8。 | raw_ready=true 后运行 safe_no_latest_publish 补跑，再重跑日报门禁。 | 减少人工漏跑，后续 automation 能主动发现缺口并修复。 |
| 持仓金额与收益率闭环 | partial | 45.00% | 已建立公开安全的持仓监控 Dashboard；私有资金状态、已下注金额和收益率未 ready 时显示 funding-update-pending。 | snapshot_ready=False；funding_state=funding-update-pending。 | 从 .app 启动只读持仓读取，用户完成 TAB 授权后导入当前日期私有快照。 | 胜负结果会影响下一期可用余额和下注金额，而不是静态预算分配。 |
| 每日 automation 准入 | blocked | 61.54% | 系统已将每日自动报告和不自动下注分离；automation 只允许生成研究、PDF、Dashboard 和补缺报告。 | maturity_ready=8/13；latest_success=04062026；current_executable=0；public_safety=是/是；blockers=3。 | 先恢复 Live/raw/private snapshot，再安装 recurring automation；allow_auto_betting 保持 false。 | 成熟后可每日生成报告，但不会越权下注。 |
| 正式 PDF 归档 | ready | 85.00% | 最新可信成功报告继续通过 latest_commit 指针和 FIFA Report/DDMMYYYY.pdf 管理。 | latest_status=ready_for_manual_report；latest_date=04062026；intelligence_changed=0。 | 保持并随每次日报重算。 | 避免 PDF 存在就误认为可下注，保留真实可信的报告版本线。 |

> 该 Dashboard 只评估产品/报告系统成熟度；raw/private/preflight 未通过时仍不得发布当前可执行下注日报，也不会自动下注。

> 本面板不声称访问到 ChatGPT 私有实现；只把用户要求中的 ChatGPT 版本参照转化为可验证能力：本地 Dashboard、PDF、SQLite、新旧对比、开源模型审计、主动测试和 fail-closed 门禁。