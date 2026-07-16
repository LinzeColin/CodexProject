# CANARY_PLAN · ADP-S8-P02-T088｜Feature-flagged Canary 框架

> 逐项打开新路径而不是大爆炸切换。框架**验证于既有稳定 live worker（b189d3cc0703），不部署任何新东西**；某个 held 能力的真实 canary 执行是**逐能力 Owner 门控**的后续。

## 1. Flag 清单（从 worker 源解析，每个可独立回滚）
| Flag | 类型 | 现值 | 门控（自身侧路径） | kill switch | 回滚路径 |
|---|---|---|---|---|---|
| `BOARD3_A0_ONLY` | bool | false | Board3 A0-only 过滤（媒体不作证据） | set false | 一次部署 / versions deploy b189d3cc0703(T040) |
| `RAW_DUALWRITE` | bool | true(SHADOW) | R2 原文双写旁路（try/catch，不改发布主链） | set false | set false / versions deploy 657fe32a(T022) |
| `RUM_ENABLED` | bool | true | RUM 客户端注入 + /api/rum ingest | set false | set false（不注入；端点 202 忽略） |
| `RUM_SAMPLE` | dial[0,1] | 1 | RUM 采样率——**canary 拨盘**（限流/降 D1 写） | set 0 | 向 0 下调（DIR-007 预算旋钮） |

**独立回滚**：每个 flag 是独立 const boolean/dial，门控**自身**侧路径（additive gate，off=跳过侧路径、发布主链完好），无跨 flag 耦合（验证器负控制证实）。

## 2. Cohorts（逐级放量）
`off（安全默认）` → `shadow（flag 开，无用户可见变化/限流）` → `dial-up（RUM_SAMPLE 或 按 board/route 切片）` → `full`。

## 3. Kill switches
每个 flag 的 off 值即 kill switch（见上表）；worker 内 `wrangler versions deploy <target>` 为版本级回滚。

## 4. Monitoring
RUM Core Web Vitals（LCP/CLS/INP，按 theme/route/device，T081）+ DIR-007 预算用量（R2 storage/Class A/B）。

## 5. 错误预算自动停止（fail-closed）
- **成本预算（live 已有）**：DIR-007 `R2_BUDGET`（10GB / 1e6 Class A / 1e7 Class B，`guardFrac=0.9`）——写前核对，≥90% 即 `over_budget` **停写**（fail-closed，真实 live 自动停止）。
- **质量预算（canary 规则）**：CWV 错误预算被突破（如 LCP/INP p75 越阈值且够样本）→ 自动**降 RUM_SAMPLE / 关 canary flag**（复用各 flag 的 kill switch 作自动停止杠杆）。

## 6. Held 能力的 canary 上线（逐能力 Owner 门控）
- **A1/A2 子国家**：每 cohort behind source-enable flag；per-cohort Owner 晋级门。
- **S5 深度 / S6 模型**：behind NOT_DEPLOYED feature flag；晋级门控，按 cohort canary。
