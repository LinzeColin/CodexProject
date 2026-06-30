# PFI v0.2.4 Stage 2 Phase 2.2 Risk and Rollback

## Scope

本轮只实现版本链路和入口身份可见化。不执行 Phase 2.3 真实 app/browser 验收，不重装 app bundle，不修改 launcher C 或 Info.plist，不修改财务数据逻辑。

## Risks

- 启动 URL query 已更新，若用户有旧浏览器 tab，仍需 Phase 2.3 清缓存和新 Profile 验收确认。
- Static HTML 的 bundle hash 先显示 `runtime-computed`，Streamlit 注入 runtime metadata 后由 `shell.js` 写入真实 hash。
- Stage 1 whole-review evidence 是历史证据；当前 Stage 2 修改会改变 `shell.js` 和 `version.js` 当前 hash，因此 Stage 1 测试改为验证历史 evidence 自洽。

## Rollback

1. Revert this Phase 2.2 commit.
2. Restore `PFI/StartPFI.command`, `PFI/scripts/startPFI.sh`, `PFI/web/index.html`, `PFI/web/app/shell.js`, and `PFI/web/app/version.js` to Phase 2.1 state.
3. Remove `PFI/web/app/entry_audit.js` and `PFI/reports/pfi_v024/stage_2/phase_2_2/` if rolling back the phase completely.
4. Keep Phase 2.1 evidence intact for re-diagnosis.
