# Memory Atlas v1.1.7 Stage 0 Phase 1 Chinese Display Contract

Contract ID: `memory_atlas_v1_1_7_stage0_phase1_chinese_display_contract`

Stage: `v1.1.7 Stage 0`

Phase: `0.1`

Task ID: `MA-V117-S0P01`

Acceptance ID: `ACC-MA-V117-S0P01`

Status: `phase_0_1_chinese_display_foundation_completed_pending_stage0_review`

## Purpose

Stage 0 Phase 0.1 establishes the runtime foundation for readable Chinese UI.
It covers UTF-8 scanning, Chinese UI copy registry and baseline layout tolerance
for long Chinese labels. It does not implement the Help panel, empty/error
state workflow, detail visibility workbench, browser screenshot evidence,
production build, local app install, deployment or GitHub main upload.

## Scope

| Surface | Requirement | Evidence |
|---|---|---|
| UTF-8 / Unicode | Markdown, JSON, TS/TSX, CSS and CSV in the selected Memory Atlas surfaces must have no replacement characters, common mojibake markers or trailing whitespace. | `validate:v1.1.7-stage0-phase1` |
| Chinese UI copy registry | Navigation, filters, load states, overview, Inspector and proposal labels must have stable Chinese entries in `src/i18n/zh-CN.ts`. | `src/i18n/types.ts`, `src/i18n/zh-CN.ts` |
| Runtime copy usage | The app shell, navigation, filters, overview, Inspector and proposal panel must read critical labels from the registry. | `src/App.tsx` |
| Font fallback | The UI must prefer common macOS and cross-platform Chinese fonts before generic sans-serif. | `src/styles.css` |
| Layout tolerance | Buttons, cards, Inspector text, proposal text and panel headings must allow safe wrapping without breaking layout. | `src/styles.css` |

## Required Registry Groups

The registry must include:

- `app`
- `navigation`
- `metrics`
- `filters`
- `states`
- `overview`
- `inspector`
- `proposal`

The registry is deliberately small and runtime-owned. Later phases may move
more hard-coded copy into it, but they must not remove these groups.

## Runtime Boundaries

- No new external data source.
- No raw/private/cookie/session/secret read.
- No direct active-memory writeback.
- No proposal write as part of validation.
- No feature flag default switch.
- No browser screenshot or production build in this phase.
- No GitHub main upload in this phase.

## Validation

Required commands:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.7-stage0-phase1
git diff --check -- OpenAIDatabase
```

## Rollback

Revert the Stage 0 Phase 0.1 commit. This removes the registry, validator,
contract, acceptance and CSS/App copy changes without changing data files or
long-term memory state.
