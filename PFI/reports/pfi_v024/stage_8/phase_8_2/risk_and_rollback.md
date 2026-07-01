# Stage 8 Phase 8.2 Risk and Rollback

## Risk

- 本轮只执行 Stage 8 Phase 8.2 截图验收。
- 本轮不执行 Phase 8.3 人工验收、Stage 8 whole-stage review、Stage 9 或 GitHub main upload。
- 本轮不重装 app bundle，不写入或改写真实财务数据。

## Rollback

如截图验收失败，保留截图和 browser_validation.json 后定位 app/localhost 入口、bundle hash 或响应式问题。
本轮变更可通过回退 Stage 8.2 合同、脚本、测试、文档和 evidence 文件撤销。
