# CodexProject Agent Contract

本仓库是多项目源码与治理中心。默认中文优先；代码、API、库名、
模型名、错误可保留英文。项目级 `AGENTS.md` 可追加规则但不能弱化本文件；
细节以 `docs/governance/STANDARD.md` 为准。

## 永久规则

- Every active project must be registered in `governance/projects.yaml`.
- Active projects must expose project-root `功能清单.md`, `开发记录.md`,
  and `模型参数文件.md`. They must stay complete Chinese human entries, not
  English aliases, redirects, compatibility indexes, or link-only pages.
- `开发记录.md` must directly contain the full Roadmap: Stage -> Phase ->
  Task, valid task ID, hours, percentages, Stop Conditions, Stop Gates,
  Acceptance, evidence, rollback, and current result.
- `docs/pursuing_goal/**/V*_ROOT_LOCK.yaml`, when present, is the strongest
  project contract below this file; stage gates are not production acceptance.
- Canonical facts should converge to `docs/governance/project.yaml`,
  `docs/governance/roadmap.yaml`, `docs/governance/events.jsonl`, `VERSION`,
  and `CHANGELOG.md`. Derived views, dashboards, ledgers, manifests, and
  owner summaries preserve truth but must not become duplicate editable facts.
- One Codex run handles one project, one Roadmap task ID, and one Acceptance ID
  by default. Do not scan unrelated directories.
- Use `T0`-`T3` routing from `docs/governance/STANDARD.md`. Default to
  `T0`/`T1`; upgrade model, formula, parameter, schema, safety, release,
  legal, privacy, money, payroll, deletion, live delivery, or production work
  to `T2`/`T3`. Never let ordinary `T0`/`T1` fast paths bypass `T2`/`T3`.
- Before implementation, state files to read/modify, tests, risks, rollback,
  stop conditions, and the single Acceptance target.
- Do not invent formulas, parameters, versions, test results, owner decisions,
  incidents, or evidence. `UNKNOWN` must link to a concrete Roadmap task.
- For `arxiv-daily-push`, source or board add/delete/rename/enable/disable
  must follow its source/board user-center sync gate; config/code-only changes
  are not complete.
- GitHub source-of-truth: persistent product changes must be committed and
  pushed to `LinzeColin/CodexProject`; local apps/caches/WAL/SHM/recovery
  folders are not product roots.

## Run Modes

- `READ_ONLY`, `REVIEW`, `PLAN`, `CI`, and Hook execution must not change
  tracked/source repository files (`zero tracked/source write`), append events,
  update versions, run write-mode generators, or create repair loops. Declared
  temp/evidence artifacts are allowed only when the command contract says so.
- `IMPLEMENT` may update only selected project or root-governance files needed
  by the selected task.
- Done means focused tests pass and changed-scope Project Governance passes
  when governed files change. Do not leave created/taken-over PRs open as
  delivery state.
- New root contracts do not enable SMTP, schedules, Release uploads, paid APIs,
  source promotion, or production side effects without their own gate.

## Low-Token Contract

- Ordinary `T0`/`T1` initial governance context target: <= 12KB and <= 5 files.
- Root `AGENTS.md` target: <= 4KB.
- Read the smallest evidence set that proves the task. Prefer compact
  deterministic CLI output plus `full_evidence_ref` over loading parallel views.
- Do not default-read full `scripts/lean_governance.py` or list/read the whole
  `governance/run_manifests` directory. Read local code or manifest files only
  when a failure, task ID, evidence ref, or root-governance change requires it.
- Exclude dependencies, caches, generated outputs, artifacts, backups,
  binaries, and large data unless the selected task explicitly needs them.

## Model Definition

Model = math/stat/ML, ranking/scoring, backtests, risk, salary/business
formulas, rule engines, heuristics, and LLM routing/fallbacks. Stack names are
not models; no-model projects still need evidence-backed `NOT_APPLICABLE`
`MODEL_SPEC.md`.
