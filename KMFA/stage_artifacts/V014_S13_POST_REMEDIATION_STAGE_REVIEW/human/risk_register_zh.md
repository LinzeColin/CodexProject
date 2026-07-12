# Stage 13 修补后整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 旧 review 的 pending=12 回流 | 新 review 仅以当前 3-9-2-1 分类状态为动态事实 | controlled |
| 旧优先级或责任事项被当作当前业务项 | 当前 identified/actionable/assigned 固定为 0/0/0 | controlled |
| NOT_COMPARABLE 被误读为一致或不一致 | 0 exact、0 match、0 mismatch、4 not-comparable 分开记录 | controlled |
| 4 个队列项重复累计全局差异 | 全部标记 non-additive，不改变 3-9-2-1 | controlled |
| 页面断链或移动端不可达 | 四页十二边、八视口、HTTP 和真实导航复验 | controlled |
| D/NO_GO 被页面绕过 | 四页强制显示 D/NO_GO，正式报告和决策依据继续阻断 | controlled |
| raw/private/secret 进入 Git | raw 前后/跨 phase/current 一致，private evidence ignored，提交前安全扫描 | controlled |
| 历史 upload-ready 被误用 | Stage 13 review 明确不上传、不重装 | controlled |
