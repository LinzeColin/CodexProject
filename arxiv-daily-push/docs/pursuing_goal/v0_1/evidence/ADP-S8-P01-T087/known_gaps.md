# Known gaps · ADP-S8-P01-T087｜最终 Value-Cost Gate

诚实披露**范围**、**验证形式**与 Owner Gate 语义。

## 范围（诚实）
- **本任务=准备 Value-Cost Gate 决策包 + 机器可核两条规则；门的关闭需 Owner 签署**（Owner Gate，实现者不自签）。`owner_signoff.status=PENDING`。**T088（CANARY）/T089（14 日浸泡）/T090（终交付）均 deps 本任务的 Owner 签署**——未签则下游不可开始。
- **经常性成本 = $0/mo（Cloudflare Free，DIR-007 硬顶）**：这是 FACT-013 VERIFIED（S0 Exit Owner 已确认 Free 档）。故 value-cost 结论强正：整系统免费档运行、交付 92/131 收益、所有未证/未晋级组件保持关闭。
- **scorecard 组件粒度**：10 个 recurring-cost/capability 组件（基础设施 6 + 能力/来源 4），非逐任务。价值指标锚定 131 parity registry(delivered 92) + 各能力的证据 ref。**「价值指标」是能力级定性 + parity 计数**，非精确 ROI 金额（经常性成本 $0，ROI 分母为 0，用交付收益计数替代金额）。
- **keep/scale/hold/stop**：无 `scale`（免费档不加规模）、无 `stop`（无需停的既有组件）；deployed+proven=keep(**7**)，proven-but-off/gated=hold(**3**)。所有 hold 组件**保持关闭**（NOT_DEPLOYED/SHADOW/flag off），符合「没有证据的组件保持关闭」并更严（连已证但未晋级的也保持关，待各自门）。
- **★R2 部署状态更正（独立复核抓到）★**：初版 R2 行误标 `deployed=false/off`，实为 `RAW_DUALWRITE=true` 自 T023 SHADOW 开启从未回退，在 live `b189d3cc0703` **活跃写入**永久 R2 桶（~90 Class A/mo·~4.7MB/mo,免费档内）。已修:R2 行 `deployed` **从 worker 实际 flag 派生**(`raw_dualwrite_live()`),如实标 SHADOW-active/keep;验证器加诚实不变式(row.deployed==worker.active)。**Owner 应知:R2 影子双写是一个活跃的免费档资源消费者(需按 DIR-007 监控),不是"关闭"状态。** 核实其余行诚实(S5/S6 在 live worker 0 出现、A1/A2 不在 live)。**教训:给 Owner 签署的部署状态断言必须从生产实际(worker flag/registry)派生,不能凭记忆手断——手断会失实,尤其"开/关"这类状态。**

## 验证形式（如实）
- **确定性 scorecard**：从 committed 事实（parity_registry_131 / TASK_INDEX release_mode / FREE_TIER_BUDGET DIR-007）重算；两条机器规则可核。
- **载重负控制**：①加无价值指标的 recurring 行 → rule(1) 翻 False；②标无证据组件为 deployed → rule(2) 翻 False；③标 off 组件为 keep → rule(2) 翻 False。
- **Owner 签署非机器可核**：门的第三条（Owner 签署）是人工步骤，验证器只断言其为 PENDING（不自签）；门的**关闭**留待 Owner 在 chat 中签署。
- **未做真实计费 API 拉取**：经常性 $0 依据 FACT-013(S0 Exit Owner 确认 Free 档) + DIR-007 硬顶 + 各任务 cost_value.json production_cost=0；未再拉 Cloudflare 计费 API（只读私有、S0 已核）。

## NOT_DEPLOYED / Owner Gate
- live 仍 `b189d3cc0703`；未改 worker/schema/production；未开付费/未改额度。
- **Gate 状态：机器规则 PASS + Owner 签署 PENDING → 门未关闭；T088-T090 阻塞待 Owner 签署（且 T089 需 14 真实日历日、T088 需真实生产 canary）。**
