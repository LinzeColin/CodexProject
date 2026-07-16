# Known gaps · ADP-S8-P02-T088｜Feature-flagged Canary 框架

诚实披露**范围**、**验证形式**与 NOT_DEPLOYED 语义。

## 范围（诚实）
- **本任务=canary 框架/机制 + 验证，不是某能力的真实 canary 执行**。交付的是「逐项开新路径」的**框架**（flag 独立回滚 + kill switch + cohorts + 监控 + 错误预算自动停止规则），验证于既有稳定 live worker（b189d3cc0703）。**未部署任何新能力**——某个 held 能力（A1/A2/S5/S6）的真实 canary 上线是**逐能力 Owner 门控**的后续（各自晋级门）。
- **release_mode NOT_DEPLOYED**：框架只读 worker 源、逐项验证，不改生产 flag 值、不部署。这与 T088 的 CANARY 标签的关系：CANARY 指框架**赋能**的 canary 上线方式；本任务交付+验证该机制本身，不执行具体 canary。
- **错误预算自动停止**：**成本预算**（DIR-007 R2_BUDGET guardFrac 0.9）是 live 已有的 fail-closed 真实自动停止（写前核对、超即停）。**质量预算**（CWV 错误预算→降采样/关 flag）是本框架**定义的规则**——其真实触发需部署侧的错误率/CWV 监控接线（属后续 canary 执行时落地），本任务定义规则 + 复用既有 kill switch 作杠杆，不新部署监控自动化。
- **flag 清单**：4 个（BOARD3_A0_ONLY/RAW_DUALWRITE/RUM_ENABLED + RUM_SAMPLE），从 worker 源解析。若未来 worker 新增 flag，框架应扩 FLAG_SPEC（当前覆盖 live 全部 feature flag）。

## 验证形式（如实）
- **确定性源审计**：从 worker 源解析 flag + 门控形式（if/ternary/&&/!）+ 跨 flag 耦合检查 + DIR-007 fail-closed 守卫检查。3 载重负控制（去门→不独立;耦合两 flag→皆不独立;翻 over_budget→无自动停止）。
- **未做真实 canary 放量/停线演练**：本任务不真实开某能力放量、不真实触发错误预算停线（那需真实生产 + 监控 + 时间）——属 **T089**（14 日浸泡里演练每个 stop-the-line trigger 至少一次）。本任务只交付+验证框架机制。

## NOT_DEPLOYED
- live 仍 `b189d3cc0703`；未改 worker/schema/production flag 值；框架只读。
