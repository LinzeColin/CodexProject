# TAB FIFA 开源模型库 Dashboard

本报告把 GitHub / 开源足球模型整理成可复用能力、Dashboard 布局、许可风险和下一步转换任务。它只服务研究分析，不自动下注。

## Executive Summary

- status: `ready_with_license_controls`
- automation_reuse_ready: `是`
- reference_count: `6`
- implemented / design: `3 / 3`
- license_risk_count: `2`
- reusable_feature_count: `35`
- layout_pattern_count: `23`
- ui_blueprint: `4/6` implemented，partial `1`，data_required `1`
- UI界面覆盖 / ui_dashboard_coverage: `6/6`，gated `2`，layout_ready `是`
- live_metadata: `ready`，ready `6/6`，stars `1431`，open issues `47`
- freshness_sla: `4h`，status `stale_or_partial`，fresh `0`，stale `6`，max_age `6.62`h
- next_conversion_task: 只保留时间衰减和攻防参数思想；因无明确 license 与 Python 2.7 legacy，不复制实现代码。

## 新旧模型库变化

- compare_status: `compared`
- previous_generated_at: `2026-06-13T14:36:08.766553+10:00`
- implemented_delta: `0`
- license_risk_delta: `0`

## Source Registry

| 来源 | License风险 | 采用状态 | 得分 | 可复用功能 | Dashboard布局 | 当前用途 | 下一步 |
|---|---|---|---:|---|---|---|---|
| Hicruben/world-cup-2026-prediction-model | low | 已吸收 | 100.00% | 48队赛事路径 Monte Carlo 接口; walk-forward + reliability curve 回测摘要; CLI 预测与校准脚本分层 | 方法论、回测指标、示例预测分块展示; 用进度条/百分比呈现三结果概率; 把 track record、calibration、widgets/open data 作为一眼可扫的运营区块 | 用于48队强弱先验、低比分修正和比赛结果概率交叉验证；其walk-forward/reliability/track-record思路进入本地模型审计，Monte Carlo路径作为晋级/淘汰赛模拟接口。 | 把 live track record、reliability curve、bracket simulator 和 open data widgets 转成日报可回测组件。 |
| opisthokonta/goalmodel | medium | 已吸收 | 83.75% | 同一 xG 分布同时驱动 1X2、OU、BTTS; 市场概率反推 xG; 时间衰减权重和评分规则 | 按预测函数族分组展示能力覆盖; 把模型公式和可调用函数并列作为证据; 在报告中把 1X2、OU、BTTS 放入同一模型能力矩阵 | 用于市场隐含概率反推xG，并把同一xG分布转换为1X2、大小球、BTTS和评分规则敏感性检查。 | 把 xG -> 1X2 / OU / BTTS / score_predictions 做成统一市场概率校准层，并输出偏差审计。 |
| RyanSCodes/Dixon-Coles-Football-Predictor | high | 设计参考 | 32.92% | 指数时间衰减思路; 主场优势参数; 攻防参数拆分 | 把时间衰减列为模型风险说明，不直接复制旧实现; 用攻防参数解释模型分歧来源; 把 legacy runtime/license 风险作为人工复核提示 | 作为后续回测/时间衰减权重设计参考；当前不复制其Python 2.7实现。 | 只保留时间衰减和攻防参数思想；因无明确 license 与 Python 2.7 legacy，不复制实现代码。 |
| martineastwood/penaltyblog | low | 已吸收 | 100.00% | 赔率去水和 overround removal 统一口径; Poisson / Bivariate Poisson / Dixon-Coles 模型覆盖; Asian handicap 与大小球概率扩展路线 | 把数据、模型、赔率、ratings 和可视化分成能力矩阵; 用 Quick Start / Examples 引导用户从预测到 implied probability; 把 bookmaker odds decoding 单独列为下注前置校验 | 用于强化本地 no-vig、EV、Edge、大小球/让球和模型不确定性口径；本地仍使用自有实现，不直接依赖外部包执行下注。 | 把 no-vig、Asian handicap、大小球、Bayesian uncertainty 和 ratings 口径映射到本地盘口概率/风险解释层。 |
| ML-KULeuven/socceraction | low | 设计参考 | 72.50% | 把球员事件数据转为可比较的 action value 指标; xT / VAEP 作为基本面强弱和伤停影响的解释层; SPADL/Atomic-SPADL 数据标准化路径 | 球员/球队 action value 雷达或 Top贡献表; 事件数据来源质量标签：sample、paid、missing; 把战术/球员基本面与盘口概率分开展示 | 用于未来把球员事件、战术和基本面转成 xT/VAEP 解释层；当前无事件流原始数据时只作设计参考和缺口提示。 | 等待可用事件流数据后，把 xT/VAEP/action value 转成球员基本面、伤停影响和战术状态解释层。 |
| openfootball/worldcup.json | low | 设计参考 | 72.50% | 2026 World Cup 赛程与阶段校验; raw JSON 公开源作为 TAB raw 以外的赛程 fallback; source text file trace 便于定位赛程变更 | 赛程源状态卡：TAB raw / openfootball fallback / 手动复核; 按 group、round、date 展示 fixture sanity check; 把 public-domain 数据源与 TAB 盘口源分开标注 | 用于赛程、日期、阶段和本地数据库 seed 的公开交叉验证；不提供赔率，不替代 TAB 实时盘口 raw。 | 把 2026 World Cup public JSON 接入 fixture sanity-check 与 SQLite seed，只校验赛程不替代 TAB 盘口。 |

## UI / Dashboard Blueprint

| 组件 | 来源 | 借鉴模式 | 本地UI合同 | 用户价值 | 实现状态 | 界面覆盖 | 可用界面 | 数据门禁 | 下一步 |
|---|---|---|---|---|---|---|---|---|---|
| 推荐下注指挥台 | Hicruben/world-cup-2026-prediction-model; martineastwood/penaltyblog; opisthokonta/goalmodel | Track record / reliability style cards; No-vig、EV、Edge、Risk controls side-by-side; Poisson/xG model comparison badge | 首页首屏用一张推荐表和操作卡片展示时间、板块、盘口、下注、赔率、金额、EV、Edge、套利率、Risk of ruin、置信度和门禁动作。 | 让用户先看到该怎么下注和为什么，而不是先阅读技术报告。 | implemented | covered_live | 首页推荐下注板块；Recommendation Operations PDF/JSON/Markdown | none | 接入真实结算和收盘赔率后，把 CLV/ROI 反馈直接回写到推荐卡片的 Edge 阈值。 |
| 模型分歧复核队列 | RyanSCodes/Dixon-Coles-Football-Predictor; opisthokonta/goalmodel; Hicruben/world-cup-2026-prediction-model | Dixon-Coles time decay disagreement; score matrix / 1X2 / OU probability comparison; Monte Carlo scenario confidence | 开源模型 Dashboard 以比赛为行展示共识注、置信度、最大分歧和高分歧标记，并进入人工复核，不解锁下注。 | 把模型不一致的盘口提前暴露，避免只按单一概率模型下注。 | implemented | covered_live | 模型分歧复核 Dashboard；开源模型对比 PDF/JSON/Markdown | none | 把高分歧队列接入主动测试和周报复盘，统计哪些分歧类型最容易造成误判。 |
| 赛程校验与路径模拟 | openfootball/worldcup.json; Hicruben/world-cup-2026-prediction-model | World Cup public fixture JSON sanity-check; 48-team bracket / path simulator; stage-aware report sections | 赛程校验 Dashboard 区分 TAB-only、openfootball-only、matched fixtures，并在报告里标注 public source delayed，不替代 live odds。 | 防止比赛、阶段、开球时间或板块映射错误进入下注研究。 | partial | covered_gated | 赛程校验 Dashboard；分阶段路径位以 public fixture gate 展示 | public_fixture_and_bracket_stability_required | 等 FIFA/TAB 完整分组与淘汰赛路径稳定后，把 bracket path 概率写入分阶段报告。 |
| 赔率校准实验室 | martineastwood/penaltyblog; opisthokonta/goalmodel | Overround removal / no-vig implied probability; Asian handicap and over/under market interface; Bayesian uncertainty / ratings context | 推荐操作报告和首页统一展示盈亏平衡概率、模型概率、EV、Edge 门槛差、半 Kelly 与 Risk of ruin。 | 把赔率价值、盘口风险和资金纪律放在同一决策面板，减少只看赔率高低的误判。 | implemented | covered_live | 推荐操作 Dashboard；概率/赔率编辑即时重算面板 | none | 加入同盘口历史 CLV bucket，自动调整主流/小市场 Edge 门槛。 |
| 基本面解释层 | ML-KULeuven/socceraction; opisthokonta/goalmodel | xT / VAEP action value; xG distribution as market probability driver; player and tactical state explanation | 在盘口原因中预留球员状态、伤停、战术节奏、xG/xT/VAEP 解释位；无事件流数据时只标为 data_required。 | 让概率不是黑箱数字，能解释为什么某个盘口比 TAB 隐含概率更有价值。 | data_required | covered_gated | 推荐理由中的基本面解释位；缺事件流时显示 data gate 和复核清单 | legal_event_stream_or_public_team_stats_required | 接入合法事件流或公开统计源后，补齐球员/战术基本面评分和伤停影响。 |
| 证据与许可审计面板 | Hicruben/world-cup-2026-prediction-model; opisthokonta/goalmodel; RyanSCodes/Dixon-Coles-Football-Predictor; martineastwood/penaltyblog; ML-KULeuven/socceraction; openfootball/worldcup.json | Source registry table; GitHub API metadata freshness; License risk gate | 开源模型库 Dashboard 展示 license 风险、GitHub stars/open issues/pushed_at、FACT/INFERENCE 证据层和下一步转换任务。 | 保证借鉴来源透明，避免把高许可风险或旧运行时项目误当成可直接复用代码。 | implemented | covered_live | 开源模型库 Dashboard；证据层、GitHub freshness、license 风险表 | none | 把高许可风险项目默认留在 design_reference，除非人工确认许可和实现替代方案。 |

## Live GitHub Metadata

| 来源 | Fetch | Freshness | Age h | Stars | Forks | Open issues | Pushed at | Live license |
|---|---|---|---:|---:|---:|---:|---|---|
| Hicruben/world-cup-2026-prediction-model | ready | stale | 6.62 | 29 | 7 | 2 | 2026-06-12T21:07:25Z | MIT License |
| opisthokonta/goalmodel | ready | stale | 6.62 | 115 | 23 | 1 | 2024-03-30T19:51:23Z |  |
| RyanSCodes/Dixon-Coles-Football-Predictor | ready | stale | 6.62 | 12 | 6 | 0 | 2016-08-20T13:04:28Z |  |
| martineastwood/penaltyblog | ready | stale | 6.62 | 174 | 21 | 0 | 2026-06-09T07:58:56Z | MIT License |
| ML-KULeuven/socceraction | ready | stale | 6.62 | 781 | 153 | 37 | 2026-01-07T08:40:05Z | MIT License |
| openfootball/worldcup.json | ready | stale | 6.62 | 320 | 53 | 7 | 2026-06-12T21:48:35Z | Creative Commons Zero v1.0 Universal |

## 证据层

| 来源 | Evidence layer | 内容 |
|---|---|---|
| Hicruben/world-cup-2026-prediction-model | FACT | GitHub API live metadata: stars 29, forks 7, open issues 2, pushed_at 2026-06-12T21:07:25Z. |
| Hicruben/world-cup-2026-prediction-model | FACT | 公开 README 描述为 Elo ratings -> Dixon-Coles bivariate Poisson -> Monte Carlo simulation。 |
| Hicruben/world-cup-2026-prediction-model | FACT | README 提到 48-team、50,000-simulation、real bracket conditioning 和自动按赛果更新。 |
| Hicruben/world-cup-2026-prediction-model | FACT | README 提供 backtest.mjs、calibrate.mjs、predict.mjs、track-record.mjs，以及 RPS/log-loss/Brier/ECE 评价。 |
| Hicruben/world-cup-2026-prediction-model | FACT | 2026-06-12 复核：README 显示 7 commits、MIT license、live track record 2/2 correct picks updated 2026-06-12。 |
| Hicruben/world-cup-2026-prediction-model | INFERENCE | 用于48队强弱先验、低比分修正和比赛结果概率交叉验证；其walk-forward/reliability/track-record思路进入本地模型审计，Monte Carlo路径作为晋级/淘汰赛模拟接口。 |
| opisthokonta/goalmodel | FACT | GitHub API live metadata: stars 115, forks 23, open issues 1, pushed_at 2024-03-30T19:51:23Z. |
| opisthokonta/goalmodel | FACT | 公开 README 列出 predict_expg、predict_goals、predict_result、predict_ou、predict_btts。 |
| opisthokonta/goalmodel | FACT | README 列出 p1x2、pbtts、expg_from_ou、expg_from_probabilities、weights_dc、score_predictions。 |
| opisthokonta/goalmodel | FACT | 默认模型使用攻防参数、主场优势和 Poisson 进球强度表达，并包含 CMP/Negative Binomial、two-step 与 extra-time offset 讨论。 |
| opisthokonta/goalmodel | FACT | 2026-06-12 复核：README 明确 score_predictions 支持 log、brier、rps，并说明 expg_from_probabilities 可从 bookmaker odds 反推 xG。 |
| opisthokonta/goalmodel | INFERENCE | 用于市场隐含概率反推xG，并把同一xG分布转换为1X2、大小球、BTTS和评分规则敏感性检查。 |
| RyanSCodes/Dixon-Coles-Football-Predictor | FACT | GitHub API live metadata: stars 12, forks 6, open issues 0, pushed_at 2016-08-20T13:04:28Z. |
| RyanSCodes/Dixon-Coles-Football-Predictor | FACT | 公开 README 标注 Python 2.7，并说明基于 Dixon-Coles method。 |
| RyanSCodes/Dixon-Coles-Football-Predictor | FACT | README 描述主场优势、每队攻防参数和 Poisson 进球分布。 |
| RyanSCodes/Dixon-Coles-Football-Predictor | FACT | README 说明历史结果按时间指数衰减，旧结果对当前状态影响更低。 |
| RyanSCodes/Dixon-Coles-Football-Predictor | FACT | 2026-06-12 复核：GitHub 页面未显示 license 文件，当前只能作为 design reference，不复制实现。 |
| RyanSCodes/Dixon-Coles-Football-Predictor | INFERENCE | 作为后续回测/时间衰减权重设计参考；当前不复制其Python 2.7实现。 |
| martineastwood/penaltyblog | FACT | GitHub API live metadata: stars 174, forks 21, open issues 0, pushed_at 2026-06-09T07:58:56Z. |
| martineastwood/penaltyblog | FACT | GitHub README 标注 penaltyblog 是生产级 Python football analytics 包，覆盖数据分析、outcome modelling 和 betting insights。 |
| martineastwood/penaltyblog | FACT | README features 列出 Poisson、Bivariate Poisson、Dixon-Coles、Bayesian 模型、Elo/ratings、Asian handicap、over/under 和 bookmaker margin removal。 |
| martineastwood/penaltyblog | FACT | GitHub 页面显示 MIT license、v1.11.0 latest Jun 2 2026、833 commits。 |
| martineastwood/penaltyblog | FACT | 2026-06-12 复核：README 提供 Colab examples，包括 match prediction、implied probabilities、xT 和 StatsBomb 数据。 |
| martineastwood/penaltyblog | INFERENCE | 用于强化本地 no-vig、EV、Edge、大小球/让球和模型不确定性口径；本地仍使用自有实现，不直接依赖外部包执行下注。 |
| ML-KULeuven/socceraction | FACT | GitHub API live metadata: stars 781, forks 153, open issues 37, pushed_at 2026-01-07T08:40:05Z. |
| ML-KULeuven/socceraction | FACT | GitHub About 描述为把足球 event stream 转成 SPADL，并用 VAEP 或 xT 评价球员动作。 |
| ML-KULeuven/socceraction | FACT | 官方 FAQ 说明 socceraction 提供 VAEP、API clients 和 proprietary data formats 到 SPADL 的 converters。 |
| ML-KULeuven/socceraction | FACT | 官方 FAQ 提到 StatsBomb/Wyscout 免费 sample 或 StatsBomb/Wyscout/Opta 订阅数据源，适合事件流预处理。 |
| ML-KULeuven/socceraction | FACT | 2026-06-12 复核：GitHub 页面显示 MIT license，latest release v1.5.3 Aug 15 2024。 |
| ML-KULeuven/socceraction | INFERENCE | 用于未来把球员事件、战术和基本面转成 xT/VAEP 解释层；当前无事件流原始数据时只作设计参考和缺口提示。 |
| openfootball/worldcup.json | FACT | GitHub API live metadata: stars 320, forks 53, open issues 7, pushed_at 2026-06-12T21:48:35Z. |
| openfootball/worldcup.json | FACT | GitHub About 描述 worldcup.json 为 free open public domain football data，包含 Canada/USA/Mexico 2026，No API key required。 |
| openfootball/worldcup.json | FACT | README 提供 raw GitHub URL 示例：/2026/worldcup.json，可作为公开 JSON HTTP API 使用。 |
| openfootball/worldcup.json | FACT | README 指出 2026 World Cup group stage 与 knockout source text files 分别在 /worldcup/2026--usa/cup.txt 和 cup_finals.txt。 |
| openfootball/worldcup.json | FACT | README License 说明 schema、data 和 scripts dedicated to public domain，no restrictions whatsoever。 |
| openfootball/worldcup.json | INFERENCE | 用于赛程、日期、阶段和本地数据库 seed 的公开交叉验证；不提供赔率，不替代 TAB 实时盘口 raw。 |

> 本库记录方法和布局借鉴，不声称复制外部代码；无明确许可或 legacy runtime 的项目只能作为设计参考。

> 该开源模型库只增强研究报告和概率交叉验证，不自动下注、不点击 TAB 赔率、不写入 下注单。