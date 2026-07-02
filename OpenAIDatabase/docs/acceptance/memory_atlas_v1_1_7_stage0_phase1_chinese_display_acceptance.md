# Memory Atlas v1.1.7 Stage 0 Phase 1 Chinese Display Acceptance

Acceptance ID: `ACC-MA-V117-S0P01`

Task ID: `MA-V117-S0P01`

Required validator: `validate:v1.1.7-stage0-phase1`

Status: `phase_0_1_chinese_display_foundation_completed_pending_stage0_review`

## Acceptance Checklist

| Check | Pass condition |
|---|---|
| UTF-8 scan | Selected Markdown, JSON, TS/TSX, CSS and CSV files contain no replacement character, common Latin-1 mojibake markers, null bytes or trailing whitespace. |
| Copy registry | `src/i18n/types.ts` and `src/i18n/zh-CN.ts` define the required groups and stable Chinese labels. |
| Runtime usage | `App.tsx` imports `zhCNCopy`, binds it to `uiCopy` and uses it for navigation, filters, load state, overview, Inspector and proposal labels. |
| Font fallback | `styles.css` defines `--memory-atlas-font-family` with `PingFang SC`, `Hiragino Sans GB`, `Heiti SC`, `Noto Sans CJK SC` and `Microsoft YaHei`. |
| Text tolerance | `styles.css` applies `overflow-wrap: anywhere`, `word-break: normal`, `line-break: loose` and `min-width: 0` to app shell, buttons, cards, Inspector and proposal surfaces. |
| Boundary | This phase does not add Help panel implementation, empty/error workflow implementation, browser screenshots, build, deploy, raw/private reads, direct writeback or GitHub upload. |

## Deferred Proof

This acceptance does not prove browser screenshot quality, responsive visual QA,
the Help panel, empty/error state copy, full detail visibility, Search 2.0,
Review / Summary / Iteration, Data Map 2.0, Memory River or Memory Starfield.
Those belong to later phases and stages.

## Failure Conditions

- Any selected file contains blocked mojibake characters.
- The registry omits a required group.
- Navigation or proposal labels remain disconnected from the registry.
- Chinese font fallback is missing.
- Long Chinese labels can force button/card/Inspector overflow because the
  global tolerance rules are missing.
- The phase modifies raw/private data or writes long-term memory.

## Rollback

Revert the Stage 0 Phase 0.1 commit. No data migration rollback is required.
