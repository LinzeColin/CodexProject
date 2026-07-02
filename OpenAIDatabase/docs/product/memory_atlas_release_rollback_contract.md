# Memory Atlas 发布、本地 App 与回滚安全合同

- Version: v1.1.6 Stage 8 Phase 1
- Contract ID: `memory_atlas_release_rollback_contract`
- Task ID: `MA-V116-S8P01`
- Status: `phase_8_1_contract_created_pending_stage_review`

## Goal

Stage 8 defines the delivery safety contract after the v1.1.6 usability and
visual contracts. The system must be releasable through the local macOS app and
future Cloudflare Pages path without weakening privacy, rollback, Chinese
readability, proposal-only writeback, or stage-gate evidence.

This phase creates the product and acceptance contract only. It does not run a
production build, install or rebuild the local app, start browser validation,
deploy Cloudflare Pages, modify Access policy, change runtime UI, change CSS or
switch feature flags.

## Required Release Surfaces

The release and rollback contract must define these release surfaces:

1. `local_app_bundle`: `/Applications/Memory Atlas.app` and
   `~/Downloads/Memory Atlas.app` remain the local delivery targets.
2. `runtime_manifest`: runtime must expose current git commit, snapshot time,
   source workspace and build provenance.
3. `redacted_static_artifact`: publish output must contain only audited static
   files and redacted `memory_atlas.json`.
4. `cloudflare_preflight`: Cloudflare Pages + Access readiness is checked
   offline before any live deploy.
5. `live_deploy_authorization_gate`: live deployment and Access changes require
   explicit user authorization and sanitized evidence.
6. `rollback_matrix`: key visual/workflow surfaces keep documented rollback
   paths.
7. `proposal_only_writeback_gate`: frontend release must not mutate active
   memory directly.
8. `cleanup_guard`: temporary build, package and local server artifacts must be
   cleaned or explicitly recorded.

## Required Rollback Matrix

The rollback matrix must cover:

- `memory_starfield`: default starfield renderer can fall back to legacy Galaxy
  or a nonblank fallback renderer in later implementation phases.
- `memory_river`: future Memory River can fall back to legacy Timeline or a
  nonblank static fallback.
- `data_map_2_0`: Data Map 2.0 can fall back to a compact source/topic/asset
  summary without exposing raw evidence.
- `search_review_workflows`: Search 2.0 and Review/Summary/Iteration can fall
  back to read-only result/session summaries.
- `proposal_queue`: proposal-only data can be exported or cleared without
  applying active-memory writes.
- `local_app_runtime`: stale local runtime must rebuild or refuse to serve
  outdated artifacts.
- `cloudflare_release`: unauthenticated or unverified live deploy must remain
  blocked.

## Required Data Fields

Every release check, rollback entry or deploy-readiness record must be backed by
redacted derived fields:

- `release_item_id`
- `surface`
- `artifact_path`
- `git_commit`
- `snapshot_generated_at`
- `source_scope`
- `build_mode`
- `audit_status`
- `rollback_path`
- `fallback_mode`
- `owner_gate`
- `evidence_refs`
- `risk_level`
- `inspector_link`
- `proposal_hint`

## Required Checks

Future implementation phases must verify:

- Local app install or runtime refresh binds to current `HEAD`.
- Release artifact audit blocks raw/private/cookie/session/secret payloads.
- Offline Cloudflare preflight passes before any live deploy.
- No Pages deploy, Access policy change or external account operation runs
  without explicit authorization.
- Feature flag or fallback documentation exists before defaults can change.
- `.DS_Store`, caches, app bundles and transient build outputs are not staged.
- The release report distinguishes local pass from external authorization
  required.

## Anti-Regression Rules

Fail the future implementation if:

- Runtime manifest points to an old commit.
- Local app serves stale data without rebuilding or refusing launch
  (`stale local app`).
- Release artifact contains raw exports, SQLite files, cookies, sessions,
  private keys, `.env`, local absolute paths or plaintext secrets.
- Cloudflare deploy runs without owner authorization.
- Access policy changes run without owner authorization.
- Rollback path for Memory Starfield or Memory River is absent.
- Proposal-only writeback boundary is weakened.
- Temporary app bundles, dist folders or server processes are left without
  cleanup evidence.
- GitHub upload happens before final validation and remote parity checks.

## Safety Boundary

- `redacted_release_artifact_only`
- No raw/private/cookie/session/secret payloads.
- No direct active-memory writeback.
- No direct writeback.
- No agent apply.
- No runtime UI implementation.
- No CSS change.
- No browser screenshot run in this phase.
- No installer run in this phase.
- No production build in this phase.
- No Cloudflare live deploy.
- No Access policy change.
- No external account operation.
- No Stage 8 review, Stage 9 or Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload; No live deploy.

本 phase 不修改运行时，不读取 raw/private，不直接写长期记忆，不执行本地 App
安装，不部署 Cloudflare，不进入 Stage 8 整体复审，不上传 GitHub main。

## Acceptance Hook

Future implementation phases must provide:

- Local app runtime manifest evidence.
- Release artifact audit evidence.
- Offline Cloudflare Pages + Access preflight evidence.
- Rollback matrix evidence.
- Cleanup evidence for local server and transient package outputs.

This contract only defines the release, local app and rollback safety boundary.
