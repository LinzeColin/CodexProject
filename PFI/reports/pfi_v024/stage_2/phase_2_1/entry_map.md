# PFI v0.2.4 Stage 2 Phase 2.1 Entry Map

Generated: 2026-06-30T12:40:53Z

## App Entry Chain

| Layer | Current Surface | Observed Mapping |
| --- | --- | --- |
| Installed app | `/Applications/PFI.app` | Dry-run resolves to current project root and `PFI/StartPFI.command`. |
| Installed app | `~/Downloads/PFI.app` | Dry-run resolves to current project root and `PFI/StartPFI.command`. |
| Desktop entry | `~/Desktop/PFI.app` | Symlink to `/Applications/PFI.app`; dry-run resolves to current project root. |
| Native launcher | `PFI/macos/PFI_launcher.c` | Reads `Contents/Resources/PFI_PROJECT_ROOT`, then spawns `StartPFI.command`. |
| Installer | `PFI/scripts/installPFIEntryApps.sh` | Writes `Contents/Resources/PFI_PROJECT_ROOT` into installed bundles. |
| Command entry | `PFI/StartPFI.command` | Executed by native launcher. |
| Service entry | `PFI/scripts/startPFI.sh` | Starts/reuses Streamlit on localhost ports `8501..8510`. |

## Web Entry Chain

| Layer | Current Surface | Observed Mapping |
| --- | --- | --- |
| Streamlit host | `PFI/src/pfi_os/app/streamlit_app.py::_pfi_web_shell_html()` | Reads `PFI/web/index.html`; inlines tokens CSS, legacy CSS, routes, page modules, and `shell.js`. |
| Static HTML | `PFI/web/index.html` | Provides body metadata and shell scaffold. |
| Runtime shell | `PFI/web/app/shell.js` | Provides shell metadata fallback, routing, and `window.PFI_STAGE1_SHELL`. |
| Version read model | `PFI/web/app/version.js` | Provides `window.PFI_STAGE1_VERSION` and `window.PFI_READ_STAGE1_VERSION`. |

## Installed App Root Probe

```text
/Applications/PFI.app -> /Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI
~/Downloads/PFI.app -> /Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI
~/Desktop/PFI.app -> /Applications/PFI.app -> /Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi/PFI
```

## Current Artifact Hashes

| File | SHA256 |
| --- | --- |
| `PFI/web/index.html` | `020813e22e2f566bf726429cc88df1cd261af232ffcc7b8f337dc099d6ca3254` |
| `PFI/web/app/shell.js` | `e8fded83cf99a0c7e2df6891a2f4273b2a311d070639ea42b58605ab80c30151` |
| `PFI/web/app/version.js` | `0eb03a0345480823ff191cae8046b0a69a231e76219f26f7ef94b45740f05a71` |
| `PFI/src/pfi_os/app/streamlit_app.py` | `09b70ee81e5e437d927f1f6af35befbd047ec1e9dd89cb21c40f10af3876eafd` |
| `PFI/scripts/startPFI.sh` | `757b2e6b5cfe6816dc3409266ec131a9c02f827235792059f5668788b74c2d7b` |
| `PFI/scripts/installPFIEntryApps.sh` | `4ba3c89382a581c8efd0f6b97c1b5b3da292abf8276f081aee5f4c9461229508` |
| `PFI/macos/PFI_launcher.c` | `23f1bbec1a73b646ede0859977967e6ba61944ddacb57b4cc856415f63fa969d` |

## Phase 2.1 Boundary

This map records the chain only. Phase 2.2 must implement the visible version,
build id, bundle hash, and entry audit logic. Phase 2.3 must verify app,
localhost, clean-cache, and new-profile paths with real browser evidence.
