# CodexProject Agent Contract

This repository is a multi-project source hub. This root contract applies to
the repository and every registered project. Nested `AGENTS.md` files may add
project-specific rules, but they may not weaken this file. Keep detailed field
rules in `docs/governance/STANDARD.md`.

## Permanent Rules

- Every active project must be registered in `governance/projects.yaml`.
- Every active project must expose these exact project-root human entry files:
  `功能清单.md`, `开发记录.md`, and `模型参数文件.md`.
- These three Chinese files may not be replaced by English aliases, one-line
  redirects, compatibility indexes, or pages that only link to
  `docs/governance/`.
- 中文优先，默认全局中文: this applies to the whole repository and every
  registered project. Unless the user or a stricter project-specific contract
  explicitly requests another language, agent-facing responses, governance
  summaries, PR descriptions, CI-facing summaries, owner-facing docs, and
  project human-entry files should use Chinese by default.
- For `arxiv-daily-push`, any future source or board addition, deletion,
  rename, enablement, or disablement must follow the project source/board
  user-center sync gate in `arxiv-daily-push/AGENTS.md`: update the GitHub
  user-center source page, related user-center summaries, generated source
  catalog, project human-entry files, and pass the required user-center and
  owner-controls tests in the same delivery. Agents must not change only
  config or code and then claim the source/board change is complete.
- `开发记录.md` must directly contain the project's full Roadmap: Stage -> Phase ->
  Task, a task ID matching `^S[1-9][0-9]*P[A-Z]T[0-9]{2}$`, estimated hours,
  derived percentages, Stop Conditions, Stop Gates, required evidence, and
  failure actions.
- If a project exposes `docs/pursuing_goal/**/V*_ROOT_LOCK.yaml`, that lock is
  the highest-priority project execution contract below this root file. Agents
  must read the lock, verify the referenced contract and roadmap hashes when a
  validator exists, and keep accepted stage gates separate from later integrated
  production gates.
- Canonical facts should converge to the Lean v2 minimal source set:
  `docs/governance/project.yaml`, `docs/governance/roadmap.yaml`,
  `docs/governance/events.jsonl`, `VERSION`, and `CHANGELOG.md`.
- Derived views, dashboards, status pages, ledgers, manifests, and owner
  summaries preserve governance truth but must not become duplicate editable
  fact sources.
- One Codex run handles one project, one Roadmap task ID, and one Acceptance ID
  by default.
- Use the `T0`-`T3` risk-tier routing in `docs/governance/STANDARD.md`. Default
  to `T0`/`T1` unless a concrete model, formula, parameter, schema, safety,
  release, legal, privacy, money, or production risk requires `T2`/`T3`.
- Non-trivial `T2`/`T3` software development, refactoring, model changes,
  releases, or multi-file fixes must explicitly invoke `$codex-dex`.
- Before implementation, report files to read, files to modify, test commands,
  risks, rollback, stop conditions, and the single Acceptance target.
- Default to a bounded PLAN / READ-ONLY pass before implementation unless the
  user explicitly provides a narrow implementation contract.
- Do not scan directories unrelated to the current project and task.
- Do not infer iteration count from Git commit count.
- Do not invent formulas, parameters, historical versions, test results, owner
  decisions, or evidence.
- `UNKNOWN` must link to a concrete unresolved Roadmap task. Do not use vague
  `TBD` placeholders.
- Hotfix or rollback work requires a concrete incident ID, affected version,
  target rollback version, and evidence. Do not invent incidents.
- Local checkout rule: `LinzeColin/CodexProject` has one canonical local working
  checkout. On this machine it is
  `/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject`.
  Do not create parallel `CodexProject*`, `PFI_OS`, `EVA_OS`, or project-specific
  shadow clones for active work. Temporary recovery copies must stay outside the
  product root, be named as backups, and must not become app launcher targets.
- App launcher rule: before editing, deleting, moving, or cleaning any local
  project directory, inspect `.app` launchers, LaunchAgents, PID files, and
  listening process cwd for affected projects. PFI, EEI, Alpha, Serenity,
  OpenAIDatabase/Memory Atlas, and arxiv-daily-push must resolve to the
  canonical checkout above unless a newer root contract explicitly supersedes it.
- GitHub source-of-truth rule: persistent product changes must be committed and
  pushed under this repository. Local `.app` packages, runtime state, caches,
  SQLite WAL/SHM files, and temporary recovery folders are operational artifacts,
  not alternate product roots.

## Run Modes

- `READ_ONLY`, `REVIEW`, `PLAN`, `CI`, and Hook execution must not modify
  repository files, append events, update versions, run write-mode generators,
  or create repair loops.
- `IMPLEMENT` may update only the selected project or root-governance files
  required by the selected task.
- Normal development must not perform repository-wide physical rewriting.
- Full semantic sweeps, generated-view drift checks, and attestation proof
  belong to scheduled, manual, release, or root-governance gates.
- Done means the focused tests pass and changed-scope Project Governance passes
  when governed files change.
- Development runs must not leave open PRs as their delivery state. Before a
  run closes, every PR the agent created, reopened, or took over must be merged
  or closed. Stale, conflicting, superseded, or draft PRs that cannot be safely
  merged must be closed with the reason recorded; if the content is still
  needed, re-cut it from current `main` as a clean branch instead of keeping the
  old PR open.
- Locking a new root contract is not permission to enable production side
  effects. SMTP, schedules, Release uploads, paid APIs, and source inclusion in
  formal delivery still require their own task gate and evidence.

## Low-Token Contract

- Read the smallest evidence set that can prove the current task.
- Prefer compact deterministic CLI output over loading parallel governance
  views into context.
- Exclude dependencies, caches, generated outputs, artifacts, backups, binaries,
  and large data unless the selected task explicitly requires them.
- Do not perform opportunistic refactors.

## Model Definition

In this repository, a model includes mathematical models, statistical models,
machine-learning models, ranking or scoring models, backtest strategies, risk
models, salary or business calculation formulas, deterministic rule engines,
heuristic algorithms, and LLM routing or fallback strategies.

Technology stack names are not models. A project with no model still needs
`MODEL_SPEC.md`, with evidence-backed `NOT_APPLICABLE` status.
