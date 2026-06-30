# PFI v0.2.4 Stage 2 Entry Consistency

## Current Run

本轮只执行 `Stage 2 / Phase 2.1 - 入口链路映射`。
本轮不实现版本链路、不修改 app bundle、不执行真实 app/browser 验收、不上传 GitHub main。

## Phase 2.1 Result

Phase 2.1 已定位当前入口链路：

1. macOS app launcher resolves `Contents/Resources/PFI_PROJECT_ROOT`.
2. Native launcher executes `PFI/StartPFI.command`.
3. `StartPFI.command` delegates to `PFI/scripts/startPFI.sh`.
4. `startPFI.sh` starts or reuses Streamlit on localhost `8501..8510`.
5. Streamlit host `PFI/src/pfi_os/app/streamlit_app.py::_pfi_web_shell_html()` reads `PFI/web/index.html`.
6. Streamlit inlines CSS, routes, page modules, and `PFI/web/app/shell.js`.
7. `PFI/web/app/version.js` currently provides the Stage 1 version read interface.

## Current Findings

- `/Applications/PFI.app`, `~/Downloads/PFI.app`, and `~/Desktop/PFI.app` dry-run all resolve to the current project root:
  `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI`.
- `PFI/web/index.html`, `PFI/scripts/startPFI.sh`, and `PFI/web/app/shell.js` still contain v0.2.3 Stage 1 app-entry signatures.
- `PFI/web/app/version.js` contains v0.2.4 Stage 1 shell integrity metadata.
- The mismatch is recorded for Phase 2.2. It is not fixed in Phase 2.1.

## Phase 2.1 Artifacts

- `PFI/reports/pfi_v024/stage_2/phase_2_1/entry_map.md`
- `PFI/reports/pfi_v024/stage_2/phase_2_1/old_ui_signatures.json`
- `PFI/reports/pfi_v024/stage_2/phase_2_1/build_hash_display_spec.md`
- `PFI/reports/pfi_v024/stage_2/phase_2_1/evidence.json`

## Explicitly Not Done

- Stage 2 Phase 2.2 version-link implementation.
- Stage 2 Phase 2.3 real app/browser validation.
- App bundle reinstall or launcher rewrite.
- GitHub main upload.
