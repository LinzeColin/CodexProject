# PFI v0.2.4 Stage 2 Entry Consistency

## Current Run

本轮只执行 `Stage 2 / Phase 2.2 - 版本链路实现`。
本轮不执行真实 app/browser 四路径验收、不做 Stage 2 整体复审、不上传 GitHub main。

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
- Phase 2.2 replaces the old Stage 1 build/query/UI-contract signature in `PFI/StartPFI.command`, `PFI/scripts/startPFI.sh`, `PFI/web/index.html`, and `PFI/web/app/shell.js`.
- `PFI/web/app/version.js` now exposes Stage 2 entry version metadata while preserving Stage 1 shell integrity compatibility fields.
- `PFI/web/app/entry_audit.js` exposes a read model for Phase 2.3 app/local/browser validation.
- `PFI/web/styles/tokens.css` now carries the entry identity strip layout and is included in the Stage 2 bundle hash.
- Real app/browser screenshot validation remains Phase 2.3 and is not claimed by Phase 2.2.

## Phase 2.2 Result

Phase 2.2 已实现：

1. `PFI/web/index.html` body dataset and visible status strip expose `PFI v0.2.3 Repair`, build id, bundle version, bundle hash placeholder, and UI contract version.
2. `PFI/web/app/version.js` exposes `window.PFI_STAGE2_ENTRY_VERSION` and `window.PFI_READ_STAGE2_ENTRY_VERSION`.
3. `PFI/web/app/shell.js` reads runtime metadata, updates body dataset, and writes dynamic bundle hash into the visible status strip.
4. `PFI/web/app/entry_audit.js` exposes `window.PFI_STAGE2_ENTRY_AUDIT` and `window.PFI_READ_STAGE2_ENTRY_AUDIT`.
5. `PFI/web/styles/tokens.css` keeps the entry identity strip stable in the top-bar layout and is part of `frontendBundleFiles`.
6. Streamlit iframe injection inlines `version.js`, `entry_audit.js`, and Stage 2 runtime metadata from `build_v024_stage2_entry_runtime_metadata`.
7. `StartPFI.command` and `scripts/startPFI.sh` open the new Stage 2 build/query contract.

## Phase 2.1 Artifacts

- `PFI/reports/pfi_v024/stage_2/phase_2_1/entry_map.md`
- `PFI/reports/pfi_v024/stage_2/phase_2_1/old_ui_signatures.json`
- `PFI/reports/pfi_v024/stage_2/phase_2_1/build_hash_display_spec.md`
- `PFI/reports/pfi_v024/stage_2/phase_2_1/evidence.json`

## Phase 2.2 Artifacts

- `PFI/reports/pfi_v024/stage_2/phase_2_2/evidence.json`
- `PFI/reports/pfi_v024/stage_2/phase_2_2/bundle_hash.txt`
- `PFI/reports/pfi_v024/stage_2/phase_2_2/version_link_summary.md`
- `PFI/reports/pfi_v024/stage_2/phase_2_2/terminal.log`

## Explicitly Not Done

- Stage 2 Phase 2.3 real app/browser validation.
- App bundle reinstall or launcher rewrite.
- GitHub main upload.
