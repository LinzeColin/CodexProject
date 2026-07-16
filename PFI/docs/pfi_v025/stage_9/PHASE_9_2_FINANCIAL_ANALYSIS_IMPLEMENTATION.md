# PFI v0.2.5 Stage 9 Phase 9.2 财务分析与模型验证

## Run Contract

- Phase：`V025-S9-P9.2`
- Tasks：`S9-P2-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE9-WHOLE-REVIEW`，本轮只形成 Phase candidate，不等于整阶段通过。
- Risk：`T3_FINANCIAL_MODEL_VALIDATION_UI`
- 产品提交：`7566107dfb3e2e3612ea28b9a2c31d8a8a553747`
- 输入：Phase 9.1 report manifest、Stage 2 source manifest、Stage 4 read model、Stage 5 model/sensitivity/invariant/metamorphic、Stage 7 workflow、当前 formula/parameter registries。
- 明确不做：Phase 9.3、Stage 9 whole-stage review、建议或自动交易、多格式导出、公式/参数/模型值修改、数据库或真实财务行读取、push、App install、production/final acceptance。

## 实现结果

| 报告 | 状态 | 当前允许结论 |
|---|---|---|
| 净资产 | `blocked` | 余额、负债、持仓、价格、FX 与完整 lineage 未 ready，只显示公式、限制和复核入口。 |
| 现金 | `blocked` | 余额与负债来源未 ready，不把缺失输入解释为零。 |
| 投资 | `blocked` | 持仓、成本、价格与 FX 未 ready，不生成收益或市值结论。 |
| 消费 | `partial` | 只展示 8,815 条真实来源记录的发布/待复核分区；生活消费、投资资金流出与投资配置拆分，投资活动不等于净资产损失。 |
| 现金流 | `partial` | 只展示 7/21/30/60/90/180/360 日窗口的覆盖记录变化与财务指纹，不公开金额。 |

- `FORM-PFI-015/019` 继续使用 Stage 5 真实快照验证结果。
- `FORM-PFI-016/017` 因 required sources 缺失保持 blocked；`FORM-PFI-018` 因 dated chain 不完整保持 blocked；`FORM-PFI-020` 只声明 structure-only。
- 4 组 sensitivity preview 中，现金流窗口只公开非金额 impact；分类阈值、XIRR policy 与 money quantum 在证据不足时保持 blocked。
- `MOD-PFI-010` 显示 invariant、metamorphic、limitations、counter-evidence；historical/out-of-sample 因 ground truth 不足保持 blocked。
- 7 个来源/adapter 复核入口映射到正式 `/data`、`/accounts`、`/investment`、`/settings` 与 `/reports/metric-drilldown` 路由。

## 一致性与隐私

- 5 份报告共享 Phase 9.1 base manifest，以及 data/read-model/formula/parameter hashes。
- 分析快照 `pack_hash=sha256:c3df8b878038bffdb28bfe4112d9a875e43e5d41cb910f86b6482768223a19e9`；当前输入重建必须字节语义一致，任一报告状态、公式验证状态、敏感性状态或 pack 内容篡改均 fail closed。
- Tracked snapshot、浏览器 Evidence 与 sanitized trace 不含财务金额、私有路径、账户标识或 runtime token；本轮 `financial_values_emitted=0`。
- 本轮没有修改 model、formula 或 parameter 数值；参数影响只引用已登记 IDs 和已有验证状态。

## 正式 UI 与验证

- 正式 `PFI/web/index.html` 加载 `stage9Analysis.js`；`shell.js` 在 Stage 5 私有运行时表面之后应用 Phase 9.2 合同，保留可用的私有金额卡，同时公开报告/公式/敏感性/模型/复核结构保持脱敏。
- 无头浏览器只使用临时 loopback：5 张报告卡、23 个分析/复核入口、3 blocked/2 partial、无假完整结论、无金额、无浏览器错误和无外网请求，`11/11` 通过。
- Python Phase 9.2 target `10/10`；Stage 9 schema + Phase 9.2 + release identity `27/27`；Stage 4/5/7/8 selected regression `68/68`；Stage 7/9 Node contracts 均通过。

## Stop 与回滚

- 本轮严格停在 Phase 9.3 前；下一任务为 `S9-P3-T1`，必须新 run 执行。
- 任何未有真实输入支撑的自然语言结论、低完整度却显示确定性、surface/export hash 分叉、财务值进入公开 Evidence、自动交易或 Phase 9.3 scope leak 都使本 Phase fail。
- 回滚：依次 revert 两笔 Phase 9.2 产品提交与其直接 Evidence/治理提交；Phase 9.1 immutable snapshots 与所有 accepted inputs 保持不变。
