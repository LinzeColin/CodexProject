# Changelog

## Unreleased - Archive offload (bomb A)

- 将 5 个大型运行时归档（101 个 90MB 分片，共 6.08GB）迁至私有 AgentDatabase 的 Release，全部 sha256 逐字节校验；原位留迁移说明。数据零丢失，仓库摆脱大文件膨胀。

## Unreleased - OpenAIDatabase Shared Memory RUN 1

- Extended the existing personalization pipeline to deterministically generate ChatGPT, Codex, and Claude projections from one canonical source set, with a shared `bundle_id`, `canonical_source_hash`, and provider-neutral manifest.
- Added a minimal `claude_personalization` route, a generated Claude projection capped at 4096 bytes, and focused coverage for shared identity, deterministic reruns, source-change invalidation, generated-only artifacts, and raw/private path rejection.
- Independent final review found that bundle identity omitted auxiliary projection inputs and evaluator trusted manifest source proof. The premature accepted marker was revoked; v2 projection-input provenance and fail-closed source-proof recomputation were added, 22 targeted tests plus all renderer/governance/CI/diff gates passed, and a second independent review found no remaining P0/P1.

This RUN does not execute RUN 2 or RUN 3, read or write raw/private data, prove independent real-agent consumption, commit, or push.

This file records the current release line. Detailed stage-by-stage history remains
recoverable from Git and is intentionally not duplicated here.

## Unreleased - Memory Atlas v1.2.1

### Current delivery state

- Initiative: `Memory Atlas v1.2.1`, ST00-ST16.
- Machine Roadmap: S01-S16, 50 phases, 149 Tasks; ST00 is the external intake wrapper.
- Current completed Task count after this change: `19/149`.
- Current repository package version remains `OpenAIDatabase/VERSION = 0.2.0`.
- Parent baseline: `8329d94b7b2068c6a8d01b3b7edce52c47b10113` on `main`.
- Delivery remains local-only: one final GitHub main upload occurs only after all Tasks,
  final review, review remediation and final recovery proof pass.
- Current boundary: no intermediate branch, PR, push, deploy, app reinstall or cache
  cleanup.

### S03-P1-T2 - Current owner files

- Replaced 9,259 lines of append-only stage narration in `CHANGELOG.md`,
  `开发记录.md` and `模型参数文件.md` with bounded current-state summaries.
- Preserved the current v1.2 R8 release evidence, v1.2.1 Task progress, active formulas,
  active parameter values, security boundaries, validation commands and recovery route.
- Kept historical detail in Git instead of creating an archive, legacy or history copy.
- Did not delete source, documentation, raw data, source packages or generated data.
- Did not change runtime code, validators, package configuration or deployment state.
- Did not push or deploy; the local atomic commit is retained for the final overall upload.

### S01 and S02 audit closure

- S01 completed 9 Tasks covering Git/version/runtime baselines, lineage boundaries,
  retained/replaced/deprecated surfaces, quality debt, completion gaps and S02 scope.
- S02 completed 9 Tasks covering full-tree inventory, cleanup candidates, maintenance
  hotspots, reference evidence, disposition, Git recovery, cleanup batches, protected
  paths and the exact S03 planning surface.
- S02 reports are machine-local audit evidence and are not treated as product completion.
- The v1.2.1 package source remains external and hash-pinned; its Task Pack must not be
  copied into the repository during implementation.

### S03 deletion boundary

- `S03-P1-T1` is not complete.
- The planned document deletions are deferred because the audited candidates remain
  referenced by current validators, owner files or recovery entry points.
- The user permits deletion only for files exclusive to the current Task; shared or
  active files and cache cleanup wait for the final cleanup review.
- No deletion candidate becomes eligible solely because a broad project goal exists.
- Human-document consolidation, governance/generated cleanup, dead-reference repair,
  cleanup manifest, full regression and final S03 delivery remain pending.

### Validation and recovery

- Current Task validator: `/tmp/validate_memory_atlas_s03_p1_t2.py`.
- Historical owner files: `git log --follow -- OpenAIDatabase/<owner-file>`.
- Restore a prior file: `git show <commit>^:OpenAIDatabase/<owner-file>`.
- Canonical v1.2 release evidence:
  `机器治理/证据与日志/remediation/v1_2_r8/status.json` and
  `机器治理/证据与日志/remediation/v1_2_r8/final_acceptance.json`.
- Canonical v1.2 source recovery:
  `docs/source_packages/memory_atlas_v1_2/SOURCE_MANIFEST.json`.

## Memory Atlas v1.2 - Current predecessor release

- Machine status:
  `R8_ACCEPTANCE_AND_LIVE_DELIVERY_VERIFIED_PENDING_SINGLE_FINAL_PUSH`.
- R8 records 17/17 release gates, 58/58 requirements, 4/4 upgrade lines and 14/14
  verified v1.2 stages at runtime commit
  `12734c10bf37ee7afc86d62f72e70369a1bcd732`.
- The accepted snapshot records 435 nodes, 2,325 edges and 401 timeline items and uses
  three browser viewports: 1470x661, 1440x900 and 390x844.
- This predecessor evidence is not evidence that v1.2.1 is complete.

## Historical versions

Older v1.1.x, v1.2 stage, acceptance, review and remediation narratives are available
through Git history. They are not current release claims and must not be copied into a
new archive directory.
