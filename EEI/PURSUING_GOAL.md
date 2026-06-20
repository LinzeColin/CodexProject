# Pursuing Goal

Generated: 2026-06-20 Australia/Sydney

## Objective

开发推进到满足 MVP 的交付标准。

## Product Identity

- Chinese name: 商域图谱
- English name: Enterprise Ecosystem Intelligence
- Subtitle: 企业商业版图与供应链递归探索系统
- Repository target: LinzeColin/CodexProject/EEI
- Target product version: v0.1; do not claim or tag v0.1 until this pursuing goal is actually complete.
- Task Pack baseline: v4.2.0 + v5.0 production-blocker sync

## MVP Boundary

The MVP is a production-shaped, evidence-backed system, not only the existing offline prototype.

Required MVP scope:

- Complete gates G0 through G9 for P0 scope.
- Use PostgreSQL as the production MVP system of record.
- Preserve source, evidence, time, amount semantics, unknown values, and disputed/revoked fact states.
- Provide recursive exploration from one entity to another without losing path, filters, time context, model profile, or snapshot context.
- Use the NVIDIA-centered semiconductor and AI infrastructure ecosystem as the Golden Vertical.
- Keep fixture, curated official fixture, dry-run, and live records visibly separated in API and UI.
- Keep scoring research-oriented; do not output buy/sell, return probability, or deterministic investment conclusions.

v5 production blockers now included in the MVP boundary:

- Real data ingestion, entity resolution and evidence chain.
- Production API, recursive graph query and scoring service.
- Model config versioning, transactional activation and atomic global refresh.
- Background scheduler, auto wake, idempotency, retry and dead-letter.
- Server-side saved views, conflict control and recovery.
- 10k, 100k and 1m relationship scale tests.
- 4h and 24h soak tests.
- Production componentized frontend, real routes and real controls.
- Formal EEI brand legal and market clearance before public brand launch.

Closed in this pursuing-goal run:

- T1300/A201 PostgreSQL production database migration, reversible rollback path, and separate fact/evidence/time/version layers.

In progress in this pursuing-goal run:

- T1301/A202 curated official NVIDIA/ASML ingestion now has PostgreSQL audit tables, a deterministic loader, raw snapshot preservation, entity-resolution candidates, Golden Vertical relationship fact candidates, parser version, review status, review queue, evidence chain and counter-evidence contract.
- A202 is not closed yet: live/full-text official connector, published reviewed NVIDIA -> TSMC -> ASML relationship facts, independent source cross-check and human review approval remain required.

## Golden Vertical

Frozen Golden Vertical:

`NVIDIA-centered semiconductor and AI infrastructure ecosystem`

Minimum path and branch requirements:

- Required path: NVIDIA -> TSMC -> ASML.
- Required branch: at least one data-center or energy dependency branch.
- Required layers: 商业版图, 集团结构, 业务板块, 供应链, 资本网络, 并购交易, 控制关系, 政策环境, 战略信号, 时间演变, 证据中心, 模型中心, 数据中心, 我的关注, 探索记录, 系统状态.

## Operating Rules

- Execute one bounded gate at a time.
- Do not mark MVP complete until every required P0 Acceptance ID has current evidence.
- Do not present fixture or synthetic data as live fact.
- Do not auto-activate calibration or model changes.
- Stop and report if a required validation cannot run or fails for a non-environment reason.
