# S10-P1 修补后报告入口风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 缺失现金被显示为零 | 明确保持三项未决，missing-to-zero 固定为 0 | controlled |
| 历史 12 pending 状态污染当前入口 | 仅复用旧模板结构，动态状态绑定最新 Stage 9 证据 | controlled |
| inherited grade 被误解为 S10-P2 计算 | 标记仅继承展示，grade calculation=false | controlled |
| 模板被误当成正式报告 | formal report、decision basis、delivery 均为 false | controlled |
