# Execution Plan and Gate Ledger

## Status table

| Gate | Scope | Status | Required evidence |
|---|---|---:|---|
| G0 | Plan, dependency lock, ADRs, repository inventory | NOT STARTED | approved read-only plan; no product changes |
| G1 | Monorepo bootstrap, Compose, Makefile, health checks | NOT STARTED | clean bootstrap + health tests |
| G2 | Core schema, ontology, migrations, fixtures, research universe | NOT STARTED | migration round-trip + invariants |
| G3 | User-oriented home, industry taxonomy, Watchlist, search | NOT STARTED | home/industry/watchlist E2E |
| G4 | Recursive explorer, reroot, graph budget, breadcrumb, URL state | NOT STARTED | three-reroot E2E + bounded graph tests |
| G5 | Company empire, supply chain, dossier, paths, evidence drawer | NOT STARTED | eight-layer company workflow |
| G6 | Scoring formulas, custom profiles, preview, audit log, calibration | NOT STARTED | formula/weights/version/log/14-day tests |
| G7 | SEC connector, provenance, freshness and change pipeline | NOT STARTED | fixture + optional live smoke |
| G8 | Capital, M&A, policy, strategic signals, timeline and export | NOT STARTED | cross-view and amount semantics |
| G9 | Performance, a11y, security, failure modes, release and rollback | NOT STARTED | `make verify` + clean reproduction |

Allowed states: `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, `PASS`, `PASS WITH DEBT`, `FAIL`.

## Recommended MVP work budget

“时间档”表示资源/等价工作量，不改变验收定义，也不是日历承诺。

| Track | Equivalent effort | Meaning |
|---|---:|---|
| Prototype | 7 days | 只用于交互验证；可跳过部分来源和硬化，不能称为完整 MVP |
| **Recommended MVP** | **15 days** | 完成 G0-G9 的 P0 核心验收 |
| Robust | 30 days | 增加更多连接器、人工审核、调度、生产部署和数据深度 |

Codex 默认执行 Recommended MVP。若资源不足，应报告阻断和未通过验收，不得静默把 prototype 标成 MVP。

## Recommended allocation

| Equivalent days | Gate | Outcome |
|---:|---|---|
| 0.5 | G0 | scope lock, exact files/commands/tests/rollback |
| 1.0 | G1 | reproducible local platform |
| 1.5 | G2 | schema, 120+20 universe, ontology and fixtures |
| 1.5 | G3 | home, industry, search and Watchlist |
| 2.5 | G4 | recursive focus transfer and navigation state |
| 2.0 | G5 | company empire, supply chain and evidence workflow |
| 2.0 | G6 | scoring, tuning, logs and calibration |
| 1.5 | G7 | SEC connector and provenance |
| 1.0 | G8 | capital/policy/signals/timeline/export |
| 1.5 | G9 | non-functional gates and release |

## Gate template

```markdown
### Gate Gx - <name>
Status: IN PROGRESS
Goal:
Acceptance IDs:
Files to read:
Files to create/modify:
Commands:
Risks and mitigations:
Rollback:
Implementation notes:
Diff summary:
Test results:
Remaining risks:
Status: PASS | PASS WITH DEBT | BLOCKED | FAIL
```

## G0 exact work

- 只读 Task Pack 和现有 top-level tree；不全仓扫描。
- 锁定依赖、目录、OpenAPI/SQL/JSON Schema 生成策略。
- 对 reroot 状态、评分版本、日志追加性、14 天校准和图预算写 ADR。
- 映射任务到 acceptance IDs。
- 未明确测试和回滚前不创建产品代码。

## Completion ledger

Codex 从此处向后追加；不得重写历史。

### Gate G0 - Goal, scope and architecture freeze

Status: PASS
Goal: Freeze MVP scope, Golden Vertical, architecture decisions, repository target, product naming, navigation, and Phase 1/2 Acceptance ID mappings.
Acceptance IDs: A001, A002, A003, A004, A008, A009
Files read: `AGENTS.md`, `CODEX_MASTER_TASK.md`, `README.md`, `RUN_CODEX.md`, `PLANS.md`, `docs/11_DECISION_LOG.md`, `data/task_backlog.csv`, `data/release_gate_catalog.csv`, `specs/api_contract.yaml`, `specs/domain_schema.sql`
Files created/modified: `PURSUING_GOAL.md`, `CURRENT_PHASE.md`, `docs/adr/ADR-006` through `ADR-015`, `data/product_navigation_catalog.csv`, `data/release_gate_catalog.csv`, `scripts/validate_governance.py`, `scripts/validate_catalog_integrity.py`
Commands: `PYTHONPATH=/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages python scripts/validate_task_pack.py`
Risks and mitigations: Product navigation has 16 user-facing modules while internal function catalog remains 17 rows; mitigation is `data/product_navigation_catalog.csv` mapped to existing function IDs.
Rollback: `git revert <g0_governance_commit_sha>`
Implementation notes: Phase 0 has exited into G1 under the active pursuing goal. The MVP is not complete.

### Gate G1 - Repository foundation

Status: IN PROGRESS
Goal: Create a reproducible monorepo foundation, local health checks, validation commands, and first web/API shells.
Acceptance IDs: A004, A005, A006, A007, A008, A009, A010, A131, A132, A133, A134, A135, A153, A169, A177
Files to read: `package.json`, `pyproject.toml`, `Makefile`, `docker-compose.yml`, `apps/web`, `apps/api`, `.github/workflows/governance-validation.yml`
Files to create/modify: G1 repository/tooling files only.
Commands: `make bootstrap`, `make validate-governance`, `make validate-contracts`, `make test`, `make verify`
Risks and mitigations: The host currently lacks global `pnpm`, `uv`, and `docker`; Make targets must use pinned fallback commands or report environment debt explicitly.
Rollback: `git revert <g1_commit_sha>` and remove generated local `.venv`, `node_modules`, `.next`, and Docker volumes.
