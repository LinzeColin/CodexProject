# S13-P2 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| WPS 私密容器被错误当作普通 Excel | 只读魔数探针；明确要求原生 WPS 转换；不对原文件另存或修改 | controlled |
| 结构接入被误读为行级绑定 | 结构、私有可解析、行级已证明三层状态分开显示 | controlled |
| 历史 12 pending 或静态优先级回流 | 历史产物只作 policy fixture，动态状态不具权威性 | controlled |
| 复核顺序被误用为催收优先级 | 优先级标记为 method-only；可执行业务项固定为 0 | controlled |
| 责任角色被误用为个人指派 | 只保留角色定义；责任人指派固定为 0 | controlled |
| raw/private/secret 进入 Git | 原始详情和差异只写 ignored private runtime；公开证据只含聚合计数 | controlled |
