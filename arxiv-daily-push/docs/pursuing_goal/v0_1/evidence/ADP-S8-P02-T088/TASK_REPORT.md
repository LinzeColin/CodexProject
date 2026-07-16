# TASK_REPORT · ADP-S8-P02-T088｜执行 Feature-flagged Canary（框架）

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S8-P02-T088（Stage S8 / S8-P02，size M；Canary、浸泡与停线演练）
- **release_mode**: NOT_DEPLOYED（框架 spec + 验证于既有 worker，不部署新东西；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S8-P01-T087（Owner 已签署，授权推进）

## 6 个前置问题
1. **唯一目标？** — 交付 Feature-flagged Canary **框架**：清点 worker feature flags，证每个可独立回滚 + kill switch + off-safe，定义 cohorts/拨盘/监控 + 错误预算自动停止（锚 live DIR-007 fail-closed 守卫）。逐项开新路径而非大爆炸。**验证于既有 worker，不部署新能力**。
2. **允许改的文件？** — 仅新增：`tools/canary_framework.py`、`evidence/ADP-S8-P02-T088/**`；治理走 gov 脚本。不改 worker/schema/production。
3. **绝不能改的行为？** — live `b189d3cc0703`（NOT_DEPLOYED，框架只读 worker、不部署）；不动生产 flag 值。
4. **基线 build+data？** — flags：`BOARD3_A0_ONLY=false`/`RAW_DUALWRITE=true`/`RUM_ENABLED=true` + `RUM_SAMPLE=1`；DIR-007 `R2_BUDGET guardFrac=0.9` fail-closed 自动停止；回滚目标（T022 657fe32a / T040 b189d3cc0703）已录。
5. **验收命令？** — `python3 test-results/t088_verify.py` → ACCEPTANCE=PASS，exit 0（每 flag 独立回滚 + kill switch + off-safe；错误预算自动停止存在；3 载重负控制）。
6. **NOT_DEPLOYED？** — 纯 docs/tool 新增；rollback=revert commit。

## 诚实范围（关键）
- **本任务=canary 框架/机制 + 验证，非某能力的真实 canary 执行**。系统已有 canary-ready 基础设施（3 独立 boolean flags + RUM_SAMPLE 拨盘 + 版本回滚 + DIR-007 fail-closed 预算守卫）；T088 把它们形式化为框架并逐项验证其 canary 安全性，**不部署新能力**（那是逐能力 Owner 门控的后续）。故 release_mode 记 NOT_DEPLOYED（框架验证于稳定 live worker，live 不变）。

## 交付物
- **工具** `tools/canary_framework.py`：从 worker 源解析 flag 清单、证每个独立回滚（独立 boolean、门控自身侧路径 additive、无跨 flag 耦合）、锚错误预算自动停止于 DIR-007 fail-closed 守卫、产出 canary plan。
- **canary_framework.json**（flags + error_budget_autostop + canary_plan + acceptance）+ **CANARY_PLAN.md**（人话版：清单/cohorts/kill switches/monitoring/错误预算自动停止/held 能力上线）。
- **验证器** `test-results/t088_verify.py`（3 载重负控制）+ `canary_tests.txt`（PASS）+ `realtime_check.txt`。

## 验收（PASS，verifier 独立重算，exit 0）
证据：`test-results/canary_tests.txt`（ACCEPTANCE = PASS）。

1. **每个 flag 可独立回滚** — 4 个 canary 杠杆（3 boolean + 1 dial）全独立回滚：独立 const、门控自身侧路径（RAW_DUALWRITE→R2 双写 try/catch；BOARD3_A0_ONLY→A0 过滤；RUM_ENABLED→RUM 注入 ternary+`if(!RUM_ENABLED)`；RUM_SAMPLE→采样拨盘），off=safe default（发布主链完好），无跨 flag 耦合。每个有 kill switch。**负控制**:①去掉某 flag 的条件门→该 flag 不独立;②把两个 flag 耦合进一个条件→两者皆不独立。
2. **错误预算触发自动停止** — live DIR-007 `R2_BUDGET`(guardFrac 0.9) 写前核对、≥90% 即 `over_budget` **停写**(fail-closed 真实自动停止);canary 质量预算规则=CWV 越阈值→降 RUM_SAMPLE/关 flag（复用 kill switch 作杠杆）。**负控制**:把 `over_budget:true` 翻掉→自动停止检测失败。

## 实时未回归
NOT_DEPLOYED：框架只读 worker、不部署。live `/build.json`=`b189d3cc0703`。1 次只读 GET。

## 成本（unknown 不填 0）
生产 0（NOT_DEPLOYED）;经常性 $0/mo（免费档）。只读 GET 1；人工=canary 框架工具 + 验证器 + 负控制 + canary plan + 证据。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
