# Memory Atlas 发布、本地 App 与回滚安全验收

- Version: v1.1.6 Stage 8 Phase 1
- Contract ID: `memory_atlas_release_rollback_contract`
- Task ID: `MA-V116-S8P01`
- Status: `phase_8_1_contract_created_pending_stage_review`

## Required Checks

Stage 8 Phase 1 passes only when the product contract and records prove all of
the following:

1. `local_app_bundle`, `runtime_manifest`, `redacted_static_artifact`,
   `cloudflare_preflight`, `live_deploy_authorization_gate`,
   `rollback_matrix`, `proposal_only_writeback_gate` and `cleanup_guard` are
   all required.
2. The rollback matrix covers `memory_starfield`, `memory_river`,
   `data_map_2_0`, `search_review_workflows`, `proposal_queue`,
   `local_app_runtime` and `cloudflare_release`.
3. Release records include `release_item_id`, `surface`, `artifact_path`,
   `git_commit`, `snapshot_generated_at`, `source_scope`, `build_mode`,
   `audit_status`, `rollback_path`, `fallback_mode`, `owner_gate`,
   `evidence_refs`, `risk_level`, `inspector_link` and `proposal_hint`.
4. The contract explicitly fails stale runtime manifest, stale local app,
   raw/private release artifact, unauthorized Cloudflare deploy, unauthorized
   Access policy change, missing rollback path, weakened proposal-only boundary
   and untracked cleanup evidence.
5. The phase remains contract-only: no runtime UI, no CSS, no browser run, no
   installer run, no production build, no Cloudflare live deploy, no Access
   policy change, no direct writeback and no GitHub main upload.

## Future Evidence Requirements

Future runtime/release implementation must capture:

- Local app runtime manifest with current `HEAD`.
- Release artifact audit result.
- Overall acceptance audit result.
- Offline Cloudflare Pages + Access preflight result.
- Rollback matrix evidence for Memory Starfield and Memory River.
- Cleanup evidence for port 4177 and transient build/package outputs.

This phase only creates the contract and acceptance file, so build, browser,
installer, live deploy and local app evidence are future implementation
requirements, not evidence for this phase.

## Failure Conditions

Fail the future implementation if:

- Runtime manifest is missing or points to an old commit.
- Local app serves stale data without rebuilding or refusing launch.
- Release artifact includes raw/private/cookie/session/secret payloads.
- Cloudflare deployment or Access policy change runs without explicit owner
  authorization.
- Memory Starfield or Memory River rollback path is missing.
- Proposal-only writeback boundary is weakened.
- `.DS_Store`, caches, app bundles or transient build outputs are staged.
- External deploy readiness is reported as complete without live evidence.

## Safety

- No runtime UI.
- No CSS change.
- No browser screenshot run.
- No installer run.
- No production build.
- No raw/private data read.
- No raw/private/cookie/session/secret payload.
- No direct writeback.
- No agent apply.
- No Cloudflare live deploy.
- No Access policy change.
- No external account operation.
- No Stage 8 review, Stage 9 or Stage 10 work.
- No GitHub main upload.

Machine-readable boundary summary: No runtime UI; No raw/private data read; No
direct writeback; No GitHub main upload; No live deploy.

## Validation

Required local validator:

```bash
pnpm --dir OpenAIDatabase/apps/memory-atlas run validate:v1.1.6-stage8-phase1
```

The validator must verify this file, the product contract, package script,
delivery record, model parameters, feature list, development record, model
parameter file, changelog, changed-path scope and runtime/writeback/deploy
boundary.
