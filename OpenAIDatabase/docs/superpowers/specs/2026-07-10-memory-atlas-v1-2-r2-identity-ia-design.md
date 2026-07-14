# Memory Atlas v1.2 R2 Product Identity And Information Architecture Design

## Decision Status

This design implements the already approved R0-R8 remediation plan, Task 2 only.
It is bounded to local source, tests and evidence. It does not execute commands,
change raw data, push GitHub, reinstall the app or deploy Cloudflare.

The plan's `src/copy.ts` path is obsolete. The current authoritative copy module is
`src/i18n/zh-CN.ts` with its schema in `src/i18n/types.ts`; R2 will modify those files
instead of creating a duplicate copy layer.

## Problem

R1 made the shell usable, but the default product surface still looks like an
internal stage demo. The first route exposes `S12 P1`, CLI commands, English safety
tokens, `Universe State`, revision/source fields and stage-oriented visualization
names. The sidebar lists implementation views rather than the questions a user is
trying to answer. On mobile, title metrics, focus metadata and the command panel still
consume too much of the viewport before the actual answer appears.

## Approaches Considered

### A. Preserve Routes, Reframe The Shell (selected)

Keep the existing sidebar, route keys, view components and data contracts. Add a
v1.2 release identity, group navigation by user intent, translate visible analytical
labels, compact the first-screen hierarchy and fold machine details.

Trade-off: the shell remains familiar and low risk, but R2 does not replace the
underlying large Home Overview or make commands executable.

### B. Replace Sidebar With Top Navigation

Move every route into a top navigation and turn Home into a large workspace.

Rejected for R2: this changes all ten routes, keyboard behavior and visual-view
dimensions at once. It would mix shell redesign with later P0 visualization work.

### C. Home-Only Copy Cleanup

Rename Home headings and hide the command detail while leaving the existing brand and
navigation unchanged.

Rejected: it would pass a narrow text scan but would not establish a v1.2 release
identity or user-question-first information architecture.

## Product Identity

- Brand: `Memory Atlas`
- Product line: `记忆决策台 · v1.2`
- Home route title: `发生了什么`
- Topbar context: `先看变化，再核对证据，最后决定下一步`
- Product personality remains evidence-led, restrained and operational.
- Existing dark palette, icons, route keys and visualization identity remain.

The app shell will expose a machine-readable R2 identity attribute while keeping all
stage/version contract attributes for validators. Machine contract attributes are not
rendered as user copy.

## Navigation

Navigation is grouped by the decision question, not by implementation chronology:

| Group | User question | Routes and visible labels |
|---|---|---|
| 判断 | 我现在应该先判断什么 | `home` 发生了什么; `summary` 决定下一步 |
| 探索 | 我需要从哪里找证据 | `galaxy` 哪些主题在变化; `notion` 资料如何关联; `timeline` 变化何时发生; `search` 查找与核对 |
| 复盘 | 哪里值得投入或降噪 | `roi` 哪里值得投入; `obsidian` 关系网络; `contribution` 投入节奏; `wordcloud` 反复出现什么 |

The active route remains visibly selected. Mobile keeps the existing icon-only
horizontal navigation; group labels and long route labels are hidden there but remain
available through `title` and accessible names.

## First-Screen Hierarchy

The DOM order remains topbar, filters, current focus, quick actions and content. The
visual weight changes:

1. Topbar identifies the current user question and keeps the four human-readable
   counts. On mobile the four counts fit one row and Help becomes an icon-sized action.
2. Current focus keeps the selected memory and filter actions. Runtime signal, source
   and revision move into a closed technical-details disclosure.
3. Quick actions remain visible, but become a compact action strip. Selected action
   explanation stays in Chinese; CLI and English safety contracts move into a closed
   disclosure named `运行边界与技术详情`.
4. Home content receives the remaining viewport height. Its headings use human
   questions and Chinese analytical names rather than Stage/Phase or framework labels.
5. Snapshot timestamps and server mode move into a closed sidebar disclosure named
   `数据状态`.

## Visible Copy Rules

The default Home route must not visibly contain:

- Stage/Phase labels such as `S12 P1`, `S11 P4` or `Stage`;
- CLI snippets such as `python3 scripts/atlasctl.py` or `--dry-run`;
- English safety internals such as `No automatic send`, `No raw mutation`,
  `prefill_only` or `auto_submit`;
- machine hierarchy labels such as `Universe State`, revision IDs or source IDs;
- raw schema keys or source paths.

Accepted product terms such as `Memory Atlas`, `ChatGPT`, `Codex`, `agent`, `ROI`,
`proposal` and `personalization` may remain when paired with clear Chinese context.

Visible Home visualization names become Chinese: theme hierarchy, bubble distribution,
topic-cluster exploration, task share, automation versus assistance, ROI distribution,
opportunity radar, execution decision flow, rework friction, latent signals, evidence
timeline, formula explanation and question/action map. Machine labels and source paths
remain available only after explicit disclosure.

## Accessibility And Interaction

- Navigation buttons retain native buttons, accessible names and visible focus states.
- Closed `<details>` elements are keyboard-operable and expose human summaries.
- All primary controls must be reachable by Tab without traps or invisible focus.
- No route change, command execution or external side effect occurs during acceptance.
- Reduced-motion and existing loading/error behavior remain unchanged.

## Automated Acceptance

The R1 browser gate will be extended and must pass at `1470x661`, `1440x900` and
`390x844`:

- exact release identity and three navigation groups are rendered;
- active Home route is `发生了什么` and route order matches this design;
- forbidden internal strings have zero visible matches on the default route;
- technical disclosures are closed by default, can be opened by keyboard/click, and
  contain the preserved machine contract;
- topbar, focus, quick actions and content have no overlap or horizontal clipping;
- the first Home heading appears after the quick-action region in DOM/visual order;
- tab focus reaches navigation, search, Help, focus controls, quick actions and Home;
- R1 nested-content, S06 Chinese-summary and port-release gates still pass;
- TypeScript lint, production build and Stage 7 Galaxy/Memory River regressions pass.

## Requirement Impact

R2 may promote only requirements directly proven by the final browser evidence:

- `S03-AC05`, `S05-AC04`, `S09-AC04`, `S10-AC02`, `S10-AC03`.

The command-workflow, proposal, owner-daily, visualization, snapshot-parity, recovery
and final-audit requirements remain for R3-R8. The release stays
`FAIL_REMEDIATION_REQUIRED` after R2.

## Rollback

Revert the local R2 commits. R1 layout evidence and source recovery remain intact;
raw data, credentials, the installed app, Cloudflare and GitHub main are unaffected.
