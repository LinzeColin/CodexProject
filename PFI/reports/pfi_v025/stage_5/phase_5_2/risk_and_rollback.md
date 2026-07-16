# Phase 5.2 风险与回滚

- 双计风险：source record 与 `economic_event_id + event_type` 两层去重；冲突重复直接失败，不选择最大金额。
- 退款风险：必须唯一链接原 economic event，累计退款不得超过原事件；否则失败关闭。
- 口径风险：投资入金和域内配置分别展示并说明为不同活动阶段，不解释为净资产损失。
- 模型风险：XIRR 多次符号变化、无法括根或不收敛均 blocked；零分母拖累率为 null。
- 假零风险：无事件窗口为 `filtered_empty/null`；Phase 5.2 contract example 不得当成生产值。
- 参数风险：公式注册表、YAML、Python、UI/report contract 与中文模型参数文件必须零冲突。
- 回滚：回滚 Phase 5.2 单一 local commit；不涉及真实数据、数据库、网络、GitHub 或应用安装。
