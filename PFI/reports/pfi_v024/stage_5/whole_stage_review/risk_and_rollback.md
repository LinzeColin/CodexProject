# PFI v0.2.4 Stage 5 Whole-Stage Review Risk And Rollback

## Scope

本轮只执行 Stage 5 whole-stage review，复审 Phase 5.1、5.2、5.3 并修复复审暴露问题。

## Risk

- `shell.js` 调整了可选 `/api/read-model-status` 拉取条件，风险是 Streamlit runtime 必须显式提供 `readModelStatusApi=true` 才会继续拉取该 endpoint。
- Review-time browser validation 新增 20 张截图，属于 evidence，不修改用户数据。
- 本轮不重装 app bundle，不执行 GitHub main upload。

## Rollback

回滚本轮 whole-stage review 提交即可移除 review evidence、browser validation 脚本、截图和 `readModelStatusApi` optional fetch 调整。Stage 5 Phase 5.1、5.2、5.3 三个 candidate pass 提交不需要回滚。
