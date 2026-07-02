# WDA Stage 2 Sprint 2B-C Route Decision

Generated: 2026-07-03T09:04:48+10:00

Purpose: decide the next feasible WDA Raw Data route after Sprint 2B-A/B proved that the copied candidate bundle is not readable as plain SQLite through the approved schema-only safe path.

Inputs:
- `WDA/docs/stage2_sprint2_safe_readability/`
- `WDA/docs/stage2_sprint2b_candidate_bundle/`
- `WDA/docs/stage2_sprint2b_schema_probe/`
- `WDA/docs/HANDOFF.md`

Decision:
- Sprint 2B-A/B are complete.
- Sprint 2B-C did not require or access the external hard drive.
- Raw Gate remains `Conditional Investigation`, not Go.
- No WDA `messages.jsonl` artifact exists yet in repo stage outputs.
- WDA RAG/Web/Matrix development remains blocked until a safe, authorized message-level import path exists.

Recommended next route: define and request an owner-provided readable export or other explicitly authorized message-level artifact contract. Do not implement it in Sprint 2B-C.
