# Memory Atlas v1.1.5 Stage 8.2 Release Safety Acceptance

Date: 2026-07-01

## Scope

Stage 8.2 covers release safety only:

- 8.2.1 Feature Flag Rollback.
- 8.2.2 Acceptance Audit.
- 8.2.3 Release Notes.

This acceptance record does not claim Stage 8 whole-stage review or GitHub main
upload. It does not perform Cloudflare deployment or Access policy changes.

## Checklist

| Task | Requirement | Evidence | Result |
|---|---|---|---|
| 8.2.1 Feature Flag Rollback | Galaxy can roll back from `memory-starfield` to `legacy`; Timeline can roll back from `memory-river` to `legacy`; both can be restored through in-app toggles. | `validate:stage8-release-safety` browser toggle test | PASS |
| 8.2.1 URL rollback | URL params support `?galaxyRenderer=legacy&timelineRenderer=legacy`. | real-browser test | PASS |
| 8.2.1 Storage rollback | in-app toggles persist `memory-atlas.galaxy-renderer` and `memory-atlas.timeline-renderer`. | real-browser localStorage test | PASS |
| 8.2.1 Environment rollback | `VITE_MEMORY_ATLAS_GALAXY_RENDERER` and `VITE_MEMORY_ATLAS_TIMELINE_RENDERER` are supported by source contract. | source contract audit | PASS |
| 8.2.2 Visual and interaction audit | Default visual/interaction gates remain available; rollback test covers Galaxy and Timeline runtime modes. | Stage 7 validators plus Stage 8.2 browser test | PASS |
| 8.2.2 Data and safety audit | Release artifact still uses public redacted read-only snapshot and proposal-only writeback. | `audit_memory_atlas_release.py`, `audit_memory_atlas_acceptance.py` | PASS |
| 8.2.2 Performance audit | Stage 7 FPS/cleanup gates remain the performance authority for current renderers. | Stage 7.2 validator and Stage 8.2 release-safety review | PASS |
| 8.2.3 Release notes | Notes are Chinese-readable and include rollback, safety boundary, and not-yet-done items. | `docs/release_notes/memory_atlas_v1_1_5_stage8_release_notes.md` | PASS |

## Boundaries

- No Cloudflare live deploy.
- No Access policy change.
- No raw/private/cookie/session/secret data access.
- No direct frontend writeback.
- No Stage 8 whole-stage review yet.
- No GitHub main upload yet.

## Residual Risks

- Vite still warns that the GalaxyScene chunk is larger than 500 kB after
  minification. This remains a known performance/packaging risk, not a release
  blocker for Stage 8.2 because Stage 7.2 FPS gates and Stage 8.2 rollback
  gates pass.
- Cloudflare release ownership and Access policy still require explicit user
  authorization before any live deploy.
- Stage 8 whole-stage review must rerun 8.1 and 8.2 gates together before the
  final GitHub main upload.

## Validation Commands

```bash
PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:stage8-release-safety

PATH="$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH" \
  pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:stage8-local-app

python3 OpenAIDatabase/scripts/audit_memory_atlas_release.py \
  --repo-root OpenAIDatabase \
  --publish-dir OpenAIDatabase/apps/memory-atlas/dist

python3 OpenAIDatabase/scripts/audit_memory_atlas_acceptance.py \
  --repo-root OpenAIDatabase \
  --publish-dir OpenAIDatabase/apps/memory-atlas/dist
```
