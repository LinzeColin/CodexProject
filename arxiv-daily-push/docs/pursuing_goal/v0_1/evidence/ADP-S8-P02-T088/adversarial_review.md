# 独立对抗复核 · ADP-S8-P02-T088｜Feature-flagged Canary 框架

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **实现者不自签 PASS**：交独立 Agent（general-purpose skeptic）复核。
- **裁决**：**CONFIRMED_SOUND**（五点全 PASS；复核者从 worker 源独立重算，绝不写仓库）。

## 复核者独立重算的五点
- **①独立回滚（真·逐 flag）**：逐个读 gate 确认每个是独立 const、门控**自身** additive 侧路径、无跨 flag 耦合。`BOARD3_A0_ONLY`(400 `if(BOARD3_A0_ONLY && !a0Board3Eligible)`,helper 非 flag)、`RAW_DUALWRITE`(246 `if(RAW_DUALWRITE && env && env.RAW && sourceId){try…catch}`,off→dualwrite 跳过、fetchFeedText 仍返回、发布链完好)、`RUM_ENABLED`(1172 `if(!RUM_ENABLED)return` + 1202 ternary,off→不注入、页仍渲染)、`RUM_SAMPLE`(1178 拨盘)。**跨耦合扫描:全 NONE**。
- **②完整性（无漏 flag，关键）**：复核者**从源独立发现** flag（非信工具 FLAG_SPEC）——`const [A-Z_]+ = (true|false)` 恰好 3 个 {BOARD3_A0_ONLY, RAW_DUALWRITE, RUM_ENABLED}，"NOT in FLAG_SPEC: NONE"；env 引用只有 `env.DB`/`env.RAW`(D1/R2 绑定,非 toggle)；`RAW_MAX_PER_RUN`(3)/`ABSTAIN_THRESHOLD`(59.6)/`ARXIV_CAP`(220)=常开调参上限非 canary flag(正确排除)；6 个 THEME_* = T077 冻结设计合同非全局 toggle。**框架 4 项 FLAG_SPEC 覆盖 live 全部 feature flag**。
- **③错误预算自动停止（真 fail-closed）**：`R2_BUDGET`(10GB/1e6/1e7,guardFrac 0.9)逐字匹配；47 行在 `env.RAW.put`(48)**之前**核对、超 guardFrac 返回 `{wrote:false,over_budget:true}` = fail-closed 停写；框架诚实区分此 live 成本自动停止 vs CWV 质量预算(JSON 标 rule,known_gaps §8 明记"真实触发需部署侧错误率/CWV 监控接线"——尚非 live 自动化,无过度声称)。
- **④负控制载重**：验证器 exit 0；复核者独立复现 NC1(去 RAW_DUALWRITE gate→非独立)/NC2(耦合 RAW_DUALWRITE&&RUM_ENABLED→皆非独立)/NC3(翻 over_budget→无自动停止)+额外(剥两个 RUM_ENABLED gate→False),全翻。
- **⑤诚实/NOT_DEPLOYED**：TASK_REPORT/known_gaps/CANARY_PLAN 一致 scope 为「框架+验证·不部署新能力」,不称已执行 canary(真 canary 执行+停线演练留 T089/逐能力 Owner 门);T088 只增 untracked tool+evidence,worker 无 T088 引用(工作树脏是 pre-existing);复核者只读 GET live=b189d3cc0703。

## 复核者的次要 caveat（非 hole）
- (a) `off_is_safe_default = gated` 是启发式(非证明主链存活)——但复核者**独立追踪每个 off-path 确认发布/渲染主链完好**,故声称为真;
- (b) R2 守卫门 Class A+storage 未门 Class B 对其 1e7 上限——Class A(写)是约束瓶颈,超出 T088 范围;
- (c) 当前源 flags 为 ON(未部署工作树),但独立可回滚性与当前值无关,live 仍 b189d3cc0703。

## 结论
框架的独立回滚、完整性(无漏 flag)、fail-closed 错误预算自动停止、负控制载重、诚实/NOT_DEPLOYED 全 **CONFIRMED_SOUND**。满足「实现者不自签 PASS」门槛,可进入治理登记与合入。**★教训:canary 框架/完整性类任务,「无漏 flag」是关键——独立复核者从源重新发现 flag 集(非信工具清单)才能证完整;always-on 调参上限 vs on/off canary flag 要区分。★**
