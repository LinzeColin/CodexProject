# TASK_REPORT · ADP-S8-P01-T087｜最终 Value-Cost Gate

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S8-P01-T087（Stage S8 / S8-P01，size S；**Owner Gate**——验收含「Owner 签署」）
- **release_mode**: NOT_DEPLOYED（scorecard 准备 + 新工具/证据，不改生产；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S8-P01-T085；ADP-S8-P01-T086
- **⚠ 卡下游**：T088（CANARY）/T089（14 日浸泡）/T090（终交付）均 deps 本任务的 **Owner 签署**。

## 6 个前置问题
1. **唯一目标？** — 用实际数据召开最终 Value-Cost Gate：决定哪些来源/功能/模型/历史规模值得持续；交付 scorecard + keep/scale/hold/stop decisions + budget guardrails；**Owner 签署**关门。
2. **允许改的文件？** — 仅新增：`tools/value_cost_scorecard.py`、`evidence/ADP-S8-P01-T087/**`；治理走 gov 脚本。不改 worker/schema/production。
3. **绝不能改的行为？** — live 仍 `b189d3cc0703`；NOT_DEPLOYED；**不自签 Owner gate**；不开付费/不改额度（DIR-007）。
4. **基线 build+data？** — DIR-007 免费档（$0 经常性）；131 竞品收益(92 delivered)；90 任务 release_mode 分布(NOT_DEPLOYED 73/SHADOW 12/CANARY 3/PRODUCTION 2)。
5. **验收命令？** — `python3 test-results/t087_verify.py` → ACCEPTANCE=PASS(机器规则)，exit 0（所有 recurring cost 有价值指标 + 无证据组件保持关闭 + 免费档 $0 + guardrails；3 载重负控制）**+ Owner 签署(PENDING)**。
6. **NOT_DEPLOYED？** — 纯 docs/tool 新增；rollback=revert commit。

## 交付物
- **工具** `tools/value_cost_scorecard.py`：用实际数据（131 parity registry/90 任务 release_mode/DIR-007）给 10 个 recurring-cost/capability 组件评分 + keep/scale/hold/stop + budget guardrails + Owner 签署包；`acceptance()` 编码两条机器规则。
- **value_cost_scorecard.json**（scorecard 10 行 + decisions + guardrails + owner_signoff PENDING + acceptance）。
- **验证器** `test-results/t087_verify.py`（3 载重负控制）+ `scorecard_tests.txt`（PASS）+ `realtime_check.txt`。

## Scorecard 决策（keep 7 / hold 3，$0/mo 经常性，92/131 收益 delivered）

> **复核记录**：独立复核抓到 **R2 行事实错误**——初版标 `deployed=false / RAW_DUALWRITE=false (off)`，但 committed `worker_cloud.js:28` 是 `const RAW_DUALWRITE=true`（T023 SHADOW 开启后从未回退），R2 `adp-raw-artifacts` 已绑定、双写路径在 live `b189d3cc0703` **活跃写入**（~90 Class A/mo,~4.7MB/mo,免费档内）。这是给 Owner 签署的文件里的**部署状态失实**。**已修**：R2 行的 `deployed` 现**从 worker 实际 flag 派生**（`raw_dualwrite_live()` 解析 `const RAW_DUALWRITE`），如实标 SHADOW-active/keep；验证器加**诚实不变式**（row.deployed == worker.active）防再漂移。核实其余行诚实:S5/S6 深度层在 live worker **0 出现**、A1/A2 子国家源不在 live worker（hold 属实）。
| 组件 | 部署 | 经常性 | 决策 | 价值指标（摘要） |
|---|---|---|---|---|
| cloudflare_worker(adp-cloud) | ✔ | $0 免费 | **keep** | 承载整个 live 认知系统;92/131 收益;build b189d3cc0703 |
| d1(adp-mirror) | ✔ | $0 免费 | **keep** | canonical 文档 + 2016+ 可恢复历史 + 复习;查询索引 |
| cron(每日 30 20) | ✔ | $0 免费 | **keep** | 每日新鲜 抓取→选择→讲义 流水线 |
| domains/DNS | ✔ | $0 免费 | **keep** | 公开访问 adp/home.linzezhang.com |
| deployed sources(5 板块+A0 Board3) | ✔ | $0 免费 | **keep** | 板块覆盖 + A0 官方原文权威 |
| six-theme UI+motion+a11y | ✔ | $0 免费 | **keep** | 六主题高级动效/移动/组件态/a11y/推断标注 |
| r2 dual-write | ✔(SHADOW-active) | $0 免费 | **keep** | RAW_DUALWRITE=true 影子活跃写入不可变内容寻址 A0-A2 原文(live b189,免费档内~90 Class A/mo·~4.7MB/mo);需按 DIR-007 监控用量 |
| A1/A2 省市源 | ✘(SHADOW) | $0 免费 | **hold** | 地域深度(影子已证);每 cohort Owner 晋级门未签→保持关 |
| S5 多板块深度 | ✘(NOT_DEPLOYED) | $0 免费 | **hold** | 131-parity 深度层(证据确定性已证);晋级门控→保持关 |
| S6 预测模型 | ✘(NOT_DEPLOYED) | $0 免费 | **hold** | 结算/防泄漏/回测/台账(in-evidence MODEL card);未注入运营 MODEL_SPEC,晋级门控 |

## 验收（机器规则 PASS，verifier 独立重算，exit 0；Owner 签署 PENDING）
证据：`test-results/scorecard_tests.txt`。

1. **所有 recurring cost 有价值指标** — 每个 recurring/deployed 行都带价值指标。**负控制**:加一条无价值指标的 recurring 行 → rule(1) 失败。
2. **没有证据的组件保持关闭** — 每个 deployed 行 has_value_evidence=True;每个 off 行 decision∈{hold,stop}(不 keep/scale)。**负控制**:标一个无证据组件为 deployed → rule(2) 失败;标一个 off 组件为 keep → rule(2) 失败。
3. **免费档 $0 + DIR-007 guardrails** — 总经常性 $0;guardrails 在位（R2 10GB/1M/10M、Free 档、fail-closed、非 Owner 三确认不开付费）。
4. **Owner 签署** — `owner_signoff.status = PENDING`（**实现者不自签**）;门只在 Owner 签署后关闭。

## 实时未回归
NOT_DEPLOYED：纯 scorecard 准备 + 新工具。live `/build.json`=`b189d3cc0703`。1 次只读 GET。

## 成本（unknown 不填 0）
生产 0（NOT_DEPLOYED）;经常性系统总额 **$0/mo**（Cloudflare Free，DIR-007）。只读 GET 1；人工=scorecard 工具 + 验证器 + 负控制 + 证据。

## 独立验证 + Owner Gate
实现者**不自签 PASS，也不自签 Owner gate**。机器规则交独立 Agent 复核（见 adversarial_review.md）；**Value-Cost Gate 的关闭需 Owner 签署**（呈交 Owner）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
