# PFI v0.2.3 真实数据与非假零规则

## 禁止数据

以下财务数据不得参与正式 UI、验收、报告、图表、首页摘要或建议：

- mock
- sample
- synthetic
- fixture
- demo
- fake
- 测试样例
- 自动生成流水
- 自动生成持仓
- 写死趋势线
- 写死净资产
- 写死现金余额
- 写死投资市值

## 允许数据

只允许以下来源进入正式财务结论：

- 用户真实上传或导入的数据。
- `MetaDatabase/PFI` 保存的真实原始数据和标准化派生数据。
- 明确标记来源、时间、hash 和状态的本机 operational DB/read model。
- 中文真实空态或错误态。

## 非假零规则

核心财务指标不得在未加载真实数据时显示 `CNY 0.00`。只有以下状态可以显示数值：

- `ready`
- `confirmed_zero`

`confirmed_zero` 必须有证据链。其它状态必须显示中文状态，不得伪造数值：

- `not_loaded`
- `not_mounted`
- `path_error`
- `permission_error`
- `parse_error`
- `outdated`
- `filter_empty`
- `calculation_error`
- `review_required`

## 核心指标最小元信息

后续 Stage 的核心指标至少要能追溯：

```json
{
  "metric_id": "net_worth_cny",
  "label": "净资产",
  "value": null,
  "currency": "CNY",
  "status": "not_loaded",
  "source": null,
  "as_of": null,
  "evidence_hash": null,
  "message_zh": "未加载真实数据"
}
```

Stage 0 不实现这个 read model，只把它作为后续开发合同。
