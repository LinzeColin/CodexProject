# Stage 8 Phase 8.1 Risk and Rollback

## Risk

- 本轮只执行 Stage 8 Phase 8.1 自动验收。
- 本轮不执行 Phase 8.2 截图验收、Phase 8.3 人工验收、Stage 8 whole-stage review、Stage 9 或 GitHub main upload。
- 本轮不重装 app bundle，不写入或改写真实财务数据。

## Rollback

如自动验收失败，保留 JSON 证据并回到对应失败 Stage 修复；不要用 Stage 8 文档覆盖失败。
本轮变更可通过回退 Stage 8.1 合同、脚本、测试、文档和 evidence 文件撤销。
