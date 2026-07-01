# Stage 6 Whole-Stage Review Risk and Rollback

## Risk

- 本轮改动只覆盖 Stage 6 复审、亮色 fallback、趋势图 token 读取、浏览器验证脚本、测试、文档和 evidence。
- 不修改真实财务数据源，不写入 `MetaDatabase/PFI`，不补造财务指标。
- 不上传 GitHub main，不重装 app bundle。

## Review Fixes

- `styles.css`：给 v0.2.4 body 保留实体 `background-color`，用于浏览器可验证的亮色 fallback。
- `shell.js`：`cssColor()` 优先读取 body scoped tokens，避免趋势图继续使用旧 root token。
- `validate_v024_stage6_whole_review_browser.js`：生成桌面、移动和设置隔离截图，并验证 stop condition 不出现。

## Rollback

如需回滚本轮复审修复，可 revert 当前 Stage 6 whole-stage review commit。回滚不会影响用户真实数据，因为本轮没有数据写入或 app bundle 重装。
