# R4 官方考勤数据还原一页结果

work_dates: 2026-07-09, 2026-07-10

status: PASS

scope_status: OFFICIAL_DATA_RECONSTRUCTION_PASS

current_availability: NO_SEND_RUNTIME_VERIFIED

production_acceptance: NOT_EVALUATED

owner_usability_status: NOT_ACCEPTED

## Owner 字段裁决

- 企业每日统计原件仍为 49 列。
- `部门`改为可选展示字段：有可靠来源就显示，无可靠主部门时记录 `UNVERIFIED`，不猜值。
- `部门`不参与人员匹配、异常判断、月累计、通知或官方考勤验收，不阻止通过。
- 正式必需字段为其余 48 列。

## 冻结证据与统一凭证

- 两个工作日的独立官方 Excel 原件与文件指纹保持冻结且未修改。
- 两天均按文本 UserId 逐员工对齐，保留前导零；2026-07-09 使用补卡审批后的最终状态。
- `official_report_reconstruction.py` 为每个工作日生成统一正式凭证；`final_reconciliation.py` 直接读取并验证同一 schema，没有第二套手工转换格式。
- 原件、员工明细、DWS raw 和逐格差异只保存在本机私有证据层；GitHub 仅保存本页脱敏结论。

## 正式必需字段复核

| 指标 | 2026-07-09 | 2026-07-10 | 合计 |
|---|---:|---:|---:|
| 官方人数 | 44 | 44 | 88 人次 |
| DWS 人数 | 44 | 44 | 88 人次 |
| UserId 匹配人数 | 44 | 44 | 88 人次 |
| 正式比较列 | 48 | 48 | 48 |
| 比较单元格 | 2,112 | 2,112 | 4,224 |
| 缺少人员 | 0 | 0 | 0 |
| 多出人员 | 0 | 0 | 0 |
| 必需列缺失 | 0 | 0 | 0 |
| 必需单元格缺失 | 0 | 0 | 0 |
| 真实值差异 | 0 | 0 | 0 |
| 可选未验证字段 | 部门 | 部门 | 部门 |
| 正式凭证状态 | PASS | PASS | PASS |

## 结论边界

- R4 官方考勤数据还原通过：4,224 个必需单元格达到零缺失、零真实差异门槛。
- 该结论不等于整个 skill 可用，不证明自然 automation、真实无发送运行或未来日期稳定性。
- 后续真实无发送运行已完成，当前状态晋升为 `NO_SEND_RUNTIME_VERIFIED`；钉钉发送继续关闭，owner usability 仍未验收。
- R4 数据还原阶段未运行 live DWS；Post-R4 仅执行获授权的只读 DWS 无发送验收。全程未发送钉钉消息，未修改 automation、schedule、time、timezone 或通知文案。

## Post-R4 运行验收

- 2026-07-10 evening 临时提醒按实际考勤组完成 42/42 覆盖，不强行等同官方 Excel 44 行。
- 随后使用冻结正式凭证完成 final：44/44/44 人、48 列、2,112 格、零必需缺失、零真实差异。
- 月累计只接受最新凭证绑定的 canonical final；未绑定凭证的旧 final、legacy、morning、evening 均排除。
- evening/final 发送状态均为 `NOT_SENT_OWNER_DISABLED`，消息数 0、目标调用数 0。
