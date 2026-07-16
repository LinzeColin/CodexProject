# Known gaps · ADP-S3-P01-T032

- **NOT_DEPLOYED（任务边界，非缺陷）**：契约测试与 fixtures 是离线安全网，未接 worker/CI 流水线的真实 A0 抓取。把契约测试接进项目 CI（随 `lean_governance`/bootstrap 一起跑）属后续接线；本任务只交付 harness + fixtures + golden。
- **参考连接器为通用模板**：`ReferenceOfficialConnector` 解析一个**定义好的**官方文件模板（class 锚定）。真实各站（国务院/统计/发改委/网信办）DOM 各异，T034+ 的适配器按站替换选择器；本任务的 fixtures 用统一模板演示漂移检测机制，不代表任一真实站点当前 DOM。
- **golden 需人工同步**：真实站点**合法改版**时，contract 会失败（预期）——需人工判断是错抓还是改版，再重抓 fixture + 更新 golden。这正是「CI 发现」的设计，但意味着改版时有一次人工确认成本（已在 cost 的 human_maintenance 记）。
- **fixtures 为构造样本非实抓快照**：为可复现与不提交大 HTML，fixtures 是**手工构造**的最小官方模板样本，非某真实页的整页快照。T034+ 接真实站时会用实抓页的精简快照替换/补充。
- **未覆盖的漂移类型**：本任务覆盖字段漂移/附件丢失/分页断裂三类（验收明列）；编码变化、反爬跳转、软 404、时间格式漂移等由后续适配器各自的 fixtures 增补。
