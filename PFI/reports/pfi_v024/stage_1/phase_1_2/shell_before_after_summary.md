# PFI v0.2.4 Stage 1 Phase 1.2 Shell Repair Summary

## Scope

本轮只执行 `Stage 1 / Phase 1.2 - 最小恢复`。不执行 Phase 1.3、
Stage 1 whole-stage review、业务 UI 重建、app bundle 修改或数据逻辑修改。

## Before

- Phase 1.1 shell snapshot SHA256:
  `bb2492ead4404dd8affd730b3c231884281aa163ce3adb1a438a3e26e9c3aa90`
- Phase 1.1 诊断结论：无 merge marker 或 syntax-fragment range，但缺少统一导出的
  Stage 1 shell integrity API。

## After

- `PFI/web/app/shell.js` SHA256:
  `e8fded83cf99a0c7e2df6891a2f4273b2a311d070639ea42b58605ab80c30151`
- `PFI/web/app/version.js` SHA256:
  `0eb03a0345480823ff191cae8046b0a69a231e76219f26f7ef94b45740f05a71`
- `shell.js` now exposes `window.PFI_STAGE1_SHELL`.
- `version.js` now exposes `window.PFI_STAGE1_VERSION` and
  `window.PFI_READ_STAGE1_VERSION`.
- DOM initialization and browser route events are routed through the Stage 1
  error boundary.

## Not Done

- Phase 1.3 validation closeout.
- Stage 1 whole-stage review.
- Stage 2 entry consistency and `index.html` script wiring.
- Business UI or data logic changes.
