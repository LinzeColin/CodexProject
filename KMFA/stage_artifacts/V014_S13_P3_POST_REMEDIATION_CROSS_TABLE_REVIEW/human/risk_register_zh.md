# S13-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 候选键标签被误读为逐行绑定 | 四维统一标记 NOT_COMPARABLE，精确比较数为 0 | controlled |
| 无法比较被误读为一致 | match 与 mismatch 均为 0，单独记录 not-comparable=4 | controlled |
| 金额 null 被补零或 0.01 被忽略 | 金额字段保持 null；容差锁为 0 分；禁止补零 | controlled |
| 队列项重复累计全局差异 | 四项均标记 non-additive，不改变 3-9-2-1 | controlled |
| 历史 12 pending 或完成声明回流 | 历史产物仅作 policy fixture，动态状态不具权威性 | controlled |
| raw/private/secret 进入 Git | 详细诊断和截图只写 ignored private runtime | controlled |
