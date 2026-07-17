# KMFA v1.5 S01-P2 迁移决策报告

## 决策摘要

37 项能力按 KEEP / REFACTOR / DEPRECATE / UNVERIFIED 分类：

| 决策 | 数量 | 含义 |
|---|---:|---|
| KEEP | 12 | 证据已验证，保留契约和测试意图；不继承 v1.5 通过状态 |
| REFACTOR | 12 | 有局部证据，需进入真实服务、持久化和端到端流程 |
| DEPRECATE | 5 | 与 v2.0 冲突或仅是静态假运行时 |
| UNVERIFIED | 8 | 证据不足，证明前不得标记 KEEP |

完整清单见 machine/migration_decision_matrix_public_safe.csv。

## 必须保留的不变量

- Money 只允许整数分或 Decimal，不得使用 float。
- 任意一分差异必须失败或进入差异队列。
- raw 永不写入、删除、移动、覆盖或原地转换。
- 人工处置必须形成追加式审计事件。
- 派生版本必须绑定来源、公式、映射与 lineage。
- 缺少证据时必须 NO_GO，不得静默降级为通过。

## 必须重构

文件导入、差异队列、人工确认与 rerun、lineage、registry 单一事实源、测试分层、项目/主体模型、项目成本事实、报告导出、权限、通知和产品数据层都需要接入未来真实运行时。保留的是业务规则和拒绝条件，不是当前文件布局或历史 Phase wrapper。

## 必须废弃

- v0.1.4 静态 HTML launcher 作为产品运行时。
- 旧静态信息架构、机械卡片堆叠和技术控制台式页面。
- 按钮可点或 DOM 文案变化作为真实功能验收。
- 普通页面直接展示 Q4、D、NO_GO、hash、lineage 等技术词。
- owner 授权上传 raw/plaintext 的公开仓库例外。

历史文件暂不在 P2 删除；DEPRECATE 是迁移决策，不是本轮清理授权。

## 待证实

完整 field→metric→report lineage、真实黄金数据 zero-delta、v1.5 App/API/数据库、多主体多账户隔离、跨格式报告一致性、真实身份授权、压力/并发/浸泡/恢复/可访问性，以及红圈/OpMe connector 均须在对应 Stage 提供新证据。
