# PFI v0.2.5 时间真相与 FX 合同

## 八类时间字段

| 字段 | 语义 | 缺失策略 |
|---|---|---|
| `transaction_time` | 来源记录描述的交易发生时间。 | 无来源值则 `null`，不得用导入时间代替。 |
| `posted_at` | 金融机构完成入账或记账的时间。 | 未验证则 `null`。 |
| `effective_at` | 经济或会计影响开始生效的时间。 | 不从 transaction time 自动猜测。 |
| `imported_at` | PFI 接收该来源记录的时间。 | 仅由真实导入流程写入。 |
| `reconciled_at` | 对账完成并确认关系的时间。 | 未对账则 `null`。 |
| `valued_at` | 余额、持仓或价格被估值的时间。 | 无估值来源则 `null`。 |
| `fx_effective_at` | 所用 FX snapshot 的有效时间。 | 无 ready snapshot 则 `null`。 |
| `report_as_of` | 报告或 read model 截止时间。 | 不得晚于其依赖的已验证事实。 |

非空时间使用带 UTC offset 的 RFC3339 date-time。naive datetime 一律拒绝；保存来源 offset，不把缺失值补为当前时间。产品默认展示与 FX 业务日计算使用 `Australia/Sydney`，但来源时区仍可作为额外 metadata 保存。

## 06:00 有效 FX 业务日

1. 把 evaluation instant 转换到 `Australia/Sydney`。
2. 本地时间早于 `06:00:00`，候选日期减一日；达到或晚于该时刻，候选日期为本地当日。
3. 候选日期为周六、周日或 source 明确提供的 closed date 时，逐日回退到最近开放业务日。
4. 不根据地区名称自行猜测假日；production source 必须显式提供 closed dates 或等价 source calendar。

公式：`effective_business_date = previous_open_date(local_date - I(local_time < 06:00:00))`。

## FX snapshot 真相

- 方向固定为 `AUD/CNY`，含义为 `1 AUD = rate CNY`。
- `source_hash` 是 snapshot 去除自身 hash 字段后的 canonical JSON SHA-256。
- snapshot 日期等于预期业务日时为 `current`；早于预期日时为 `stale`；晚于预期日 fail-closed。
- 当前 `SRC-FX-SNAPSHOT` 在 Source Manifest 中仍为 `not_loaded`，因此 production rate、snapshot id、source hash 与 stale age 均保持 `null/unavailable`，依赖指标继续 blocked。
- 旧 `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json` 只作 reference-only hash 证据，不绑定 canonical private root，不作为 v0.2.5 production rate。

## 网络与数据边界

v0.2.5 policy module 不导入或调用网络库；普通运行只评估本地 policy/status。旧 refresh 路径仍要求显式 `allow_network`，本 Phase 不调用它。不使用 Finder，不修改 source，不使用财务 fixture。
