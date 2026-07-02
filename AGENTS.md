# CodexProject Agent Contract

本仓库是多项目源码与治理中心。默认中文优先；代码、API、库名、
模型名、错误可保留英文。项目级 `AGENTS.md` 可追加规则但不能弱化本文件；
细节以 `docs/governance/STANDARD.md` 为准。

## 永久规则

- 所有 active project 都必须注册在 `governance/projects.yaml`。
- Active projects 必须在项目根目录暴露 `功能清单.md`、`开发记录.md`、
  `模型参数文件.md`。这三份文件必须保持完整中文 human entries，不能变成
  English aliases、redirects、compatibility indexes、或 link-only pages。
- `开发记录.md` 必须直接包含完整 Roadmap：Stage -> Phase -> Task、有效 task ID、
  hours、percentages、Stop Conditions、Stop Gates、Acceptance、evidence、rollback、
  以及 current result。
- `docs/pursuing_goal/**/V*_ROOT_LOCK.yaml` 存在时，是本文件之下最强的项目契约；
  stage gates 不等于 production acceptance。
- Canonical facts 应收敛到 `docs/governance/project.yaml`、
  `docs/governance/roadmap.yaml`、`docs/governance/events.jsonl`、`VERSION`、
  `CHANGELOG.md`。Derived views、dashboards、ledgers、manifests、owner summaries
  可以保留事实，但不得变成重复可编辑事实源。
- 默认一个 Codex run 只处理一个 project、一个 Roadmap task ID、一个 Acceptance ID。
  不要扫描无关目录。
- 使用 `docs/governance/STANDARD.md` 中的 `T0`-`T3` 路由。默认 `T0`/`T1`；
  model、formula、parameter、schema、safety、release、legal、privacy、money、
  payroll、deletion、live delivery、production work 必须升级到 `T2`/`T3`。
  不得让普通 `T0`/`T1` fast path 绕过 `T2`/`T3`。
- 实施前必须说明将读取/修改的文件、测试、风险、rollback、stop conditions、
  以及唯一 Acceptance target。
- 不得编造 formulas、parameters、versions、test results、owner decisions、
  incidents、或 evidence。`UNKNOWN` 必须链接到具体 Roadmap task。
- `arxiv-daily-push` 的 source 或 board add/delete/rename/enable/disable 必须遵守
  source/board user-center sync gate；config/code-only changes 不算完成。
- GitHub source-of-truth：持久 product changes 必须 commit 并 push 到
  `LinzeColin/CodexProject`；local apps/caches/WAL/SHM/recovery folders 不是
  product roots。

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
