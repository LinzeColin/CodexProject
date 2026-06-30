# PFI v0.2.4 Stage 2 Entry Consistency

## Current Run

本轮只执行 `Stage 2 whole-stage review - 复审并解决暴露问题`。
本轮不进入 Stage 3、不上传 GitHub main。

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
- Phase 2.3 discovered that a same-cwd Streamlit process started before Phase 2.2 could still serve old Stage 1 runtime metadata on port `8501`.
- `PFI/StartPFI.command` and `PFI/scripts/startPFI.sh` now reuse only services with a current build-scoped `pfi_active_service.env` marker.
- Real browser validation runs on the current build service at `http://127.0.0.1:8502`.

## Phase 2.2 Result

Phase 2.2 已实现：

1. `PFI/web/index.html` body dataset and visible status strip expose `PFI v0.2.3 Repair`, build id, bundle version, bundle hash placeholder, and UI contract version.
2. `PFI/web/app/version.js` exposes `window.PFI_STAGE2_ENTRY_VERSION` and `window.PFI_READ_STAGE2_ENTRY_VERSION`.
3. `PFI/web/app/shell.js` reads runtime metadata, updates body dataset, and writes dynamic bundle hash into the visible status strip.
4. `PFI/web/app/entry_audit.js` exposes `window.PFI_STAGE2_ENTRY_AUDIT` and `window.PFI_READ_STAGE2_ENTRY_AUDIT`.
5. `PFI/web/styles/tokens.css` keeps the entry identity strip stable in the top-bar layout and is part of `frontendBundleFiles`.
6. Streamlit iframe injection inlines `version.js`, `entry_audit.js`, and Stage 2 runtime metadata from `build_v024_stage2_entry_runtime_metadata`.
7. `StartPFI.command` and `scripts/startPFI.sh` open the new Stage 2 build/query contract.

## Phase 2.3 Result

Phase 2.3 已实现：

1. `localhost` path captured `PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/localhost_home.png`.
2. `app` path captured `PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/app_home.png` after installed app dry-run bindings resolved to this checkout.
3. clear-cache browser context captured `PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/clear_cache_home.png`.
4. new browser profile captured `PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/new_profile_home.png`.
5. `PFI/reports/pfi_v024/stage_2/phase_2_3/browser_validation.json` proves all four paths expose the same build id and bundle hash.
6. Stage 2 is now candidate complete, but whole-stage review has not been executed.

## Whole-Stage Review Result

Stage 2 whole-stage review 已完成：

1. Phase 2.1、Phase 2.2、Phase 2.3 evidence 均存在且为 candidate pass。
2. Stage 2 real browser validation 已重新运行，`localhost`、`app`、`clear_cache`、`new_profile` 四路径仍共用同一 build id 和 bundle hash。
3. 复审发现并修复 Phase 2.3 evidence 在 rebase 后仍记录旧 HEAD 的证据漂移；当前 Phase 2.3 evidence 记录 review baseline `93ca5280c06697d236c69cff97461db87a4f21b9`。
4. 新增 `PFI/docs/pfi_v024/STAGE2_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage2_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_2/whole_stage_review/evidence.json`。
5. Stage 2 本地复审完成；下一 gate 是 Stage 2 GitHub main upload，Stage 3 尚未执行。

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

## Phase 2.3 Artifacts

- `PFI/reports/pfi_v024/stage_2/phase_2_3/evidence.json`
- `PFI/reports/pfi_v024/stage_2/phase_2_3/browser_validation.json`
- `PFI/reports/pfi_v024/stage_2/phase_2_3/bundle_hash.txt`
- `PFI/reports/pfi_v024/stage_2/phase_2_3/terminal.log`
- `PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/`

## Explicitly Not Done

- Stage 3 navigation repair.
- App bundle reinstall or launcher C/Info.plist rewrite.
- GitHub main upload.
