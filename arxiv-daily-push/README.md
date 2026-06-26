# arxiv-daily-push 中文 Owner 可读入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。

## 一句话结论

arXiv Daily Push 自动化项目，当前重点是区分已接受生产能力、Stage2 仍未生产验收的能力和当前 Owner 操作路径。
本页只提供 Owner 第一屏判断；详细字段、路径和历史放在下方原文与 `docs/governance/`。

## 中文瘦身原则

- 本入口瘦身不是删除事实，而是把反复计算、英文键名解释和历史索引移到下方；第一屏只留下 负责人当下要判断的状态、证据、风险、动作和回滚。
- 后续执行者 继续开发时，不应重新扫描全量治理目录；只取当前任务、下一门禁、必要证据和失败去向，避免上下文被重复材料消耗。
- 需要复盘时再读取机器字段、路线图、事件、登记表和运行清单；这些材料仍是事实源，但不进入每一次小开发动作的默认输入。
- 若为了变短而让 负责人看不懂、让证据来源消失或让 待定 被写成完成，本次瘦身即视为失败，必须回滚入口或补证据。
- 英文项目名、路径和命令只作定位；当英文数量变多时，必须用中文说明其业务含义、验收边界和开发影响。

## 当前状态
本项目已纳入 Lean v2 中文入口；当前事实以仓库文件、治理记录、测试命令和 run manifest 为准，缺证据时保持 待定。

## Owner 操作入口

先读本页，再按需进入 `功能清单`、`开发记录`、`模型参数文件` 和 `docs/governance/`；日常开发只带走当前任务、下一门禁、风险、回滚和必要证据。

## 证据与验证

证据以仓库事实和验证命令为准；中文说明只解释事实，不替代事实。

## 风险与边界

不把旧报告、示例、路径列表或英文键名当作当前完成事实；瘦身只移出重复治理计算，不删除治理真相。

## 下一步

先补缺失证据，再运行 变更范围快速门禁；完整治理计算留给计划任务或手动 all scope。

## 回滚

若入口误导 Owner，回滚本标记区文本；不迁移数据、不改业务代码、不触发外部服务。

## 中文验收补充

- 本项目历史正文包含较多英文命令、状态名和自动化术语，因此首屏必须先用中文说明哪些能力已经验收、哪些仍未生产通过、哪些动作需要负责人确认。
- 合格入口不是让执行者从英文段落中猜结论，而是直接说明当前能不能继续、缺什么证据、风险会怎样影响交付、下一步该走哪条验证路径。
- 如果后续为了节省篇幅把中文判断删掉，只留下命令、路径、任务号和历史英文说明，就视为中文可读回退；应先恢复本段，再补充新的事实来源。
- 本项目允许保留英文包名、命令和任务编号，但这些只能辅助定位，不能替代中文状态判断，也不能把未验收能力写成已完成。

## 摘要

- 项目 ID： `arxiv-daily-push`
- 项目路径：`arxiv-daily-push`
- 当前阶段： `S2`
- 当前分段： `S2PC`
- 当前任务： `S2PCT02`
- 下一门禁： `S2PC-GATE-V7-2-REVALIDATION`
- 证据状态： `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。
<!-- CODEX_CHINESE_READABILITY_END -->

# arxiv-daily-push 中文 Owner 可读入口

# arXiv Daily Push

`arXiv 日报推送 / arXiv Daily Push` is a private, evidence-first daily teaching
pipeline. V5 Stage 1 for the B1/arXiv single-source vertical slice is recorded
as `ARXIV_PRODUCTION_ACCEPTED`. `ADP-S1P5T05` completed local production and
2026-06-30 migration prep. Current V6 task pointer: `S2P1T01`.

The user-facing product must be an explanatory Chinese learning email, not a
shallow news digest. Stage 1 delivery is text-first: high-density Chinese
teaching report, email preview/delivery contract, and Markdown/HTML/JSON audit
artifacts. Video, TTS, MP4 rendering, GitHub Release video links, and media
attachments are historical/legacy capabilities only and are not Stage 1 V5
acceptance requirements.

Stage 1 acceptance is not the same as enabling unattended sends. The current
owner-approved production strategy is local Mac + Codex/local runner, with
state persisted under a local state directory and GitHub used for code, PR/CI,
evidence, status, and backup only. GitHub cloud scheduled production remains
disabled and must not become the daily runner without a new explicit task.

Baseline clarification: 30-day-grade Stage 1/2 evidence means 30 independent
unique-date artifacts and replay/coverage checks generated from real data where
available. It must not be interpreted as waiting 30 wall-clock days when the
same evidence can be produced and verified faster.

## Current Scope

Implemented foundations now:

- package and CLI foundation: `adp version`, `adp doctor`, `adp render-email`,
  `adp send-notification`, `adp validate-record`;
- arXiv adapter and source controls: `adp arxiv-url`, `adp parse-arxiv-atom`,
  `adp fetch-arxiv-latest`, `adp source-registry`;
- deterministic ranking, evidence gate, Chinese lesson JSON, publication gate,
  dry-run pipeline, handoff, and acceptance validators from earlier phases;
- owner controls: `config/owner_controls.yaml` plus generated owner views under
  `docs/owner/`;
- Stage 1 SQLite/WAL/FTS5 document and event storage model;
- Stage 1 source registry contract with only `SRC-ARXIV / arxiv.atom.v1` active;
- Stage 1 scoring, deterministic queue, and content ledger contract via
  `adp stage1-queue`;
- Stage 1 B1 report/email preview, 30 historical preview evidence, local
  runtime recovery, migration package, and post-migration bootstrap gates via
  `adp build-b1-report-email`, `adp historical-b1-previews`,
  `adp runtime-audit`, `adp migration`, and `adp post-migration-bootstrap`;
- Stage 1 local production prep via `adp local-runner preflight`,
  `adp local-runner daily`, and `adp local-runner launchd-package`.

Retained but inactive for V5 Stage 1 acceptance:

- historical TTS/storyboard/video commands;
- historical GitHub Release media delivery paths;
- Phase 12 all-arXiv/ROI/manual-delivery experiments.

These are not current acceptance gates for `ARXIV_PRODUCTION_ACCEPTED` unless a
later owner decision explicitly restores them.

Completed Stage 1 acceptance evidence:

- 30 independent historical B1 report/email previews.
- Two controlled Gmail SMTP refs on GitHub/cloud runner from run
  `28002478689`, both sent to `linzezhang35@gmail.com`.
- PR #82 live all-arXiv cloud dry-run artifact `7818287996`: 20/20 primary
  archive buckets, 49 real candidates, 30 selected samples, and
  `ARXIV_PRODUCTION_ACCEPTED`.

Not enabled yet:

- GitHub cloud scheduled production;
- real local SMTP production send without owner-controlled local env/Keychain
  setup and smoke test;
- actual launchd installation;
- Stage 2 source promotion completion.

## Goal Baseline

The current long-running baseline is locked at:

```text
docs/pursuing_goal/BASELINE_LOCK.md
docs/pursuing_goal/START_HERE_MASTER_TASK_PACK_TWO_STAGE_TEXT_DELIVERY_V5.md
docs/pursuing_goal/FULL_PURSUING_GOAL_PROMPT_TWO_STAGE_TEXT_DELIVERY_V5.txt
docs/pursuing_goal/ARXIV_DAILY_PUSH_TWO_STAGE_ROADMAP_V6.md
```

V4 and Phase 1-12 files remain historical context only. For the current goal,
Stage 1 covers only board one, B1/arXiv. Stage 2 may later promote the other
boards and sources.

V6 task-numbering rule: every completion report must state the current Task ID.
The current Task is `S2P1T01` - bioRxiv and medRxiv source promotion. Stage 1
arXiv is accepted, and local production/migration prep is complete.

Current V5-to-V6 Stage 1 task continuity:

- `S1-01-READONLY-AUDIT-001`: read-only package and repository audit.
- `S1-02-V5-BASELINE-GOVERNANCE-CALIBRATION-001`: V5 baseline lock and
  governance calibration.
- `S1-03-OWNER-CONTROLS-001`: owner controls and generated owner-readable
  views.
- `S1-04-SQLITE-DATA-MODEL-001`: unified local document/event store.
- `S1-05-ARXIV-CONNECTOR-CONTRACT-001`: arXiv source registry contract.
- `S1-06-SCORING-QUEUE-LEDGER-001`: research scoring, 10,000 queue behavior,
  and content ledger.
- `S1-07-B1_REPORT_EMAIL_TEXT-001`: B1 teaching report, claims, and email text
  preview.
- `S1-08-LOCAL_RUNTIME_RECOVERY-001`: tick, watchdog, backup, restore, runtime
  audit, and scheduler controls.
- `S1-09-MIGRATION_PACKAGE-001`: low-resource integration and migration package.
- `S1-10-POST_MIGRATION_BOOTSTRAP-001`: migration-bound target machine or
  GitHub-hosted runner bootstrap.
- `S1-11-HISTORICAL_B1_PREVIEWS-001`: completed 30 independent historical B1
  report/email previews.
- `S1-12-CONTROLLED_B1_LIVE_EMAIL_DAYS-001`: completed through the PR #82
  accelerated real-arXiv acceptance artifact and existing controlled SMTP refs.
- `S1P5T03-R`: completed 30 real historical arXiv as-of date backfill and
  CONTENT_LEDGER reconciliation.
- `S1P5T04`: completed controlled post-merge Gmail SMTP test10 and Stage 1
  arXiv acceptance evidence.
- `ADP-S1P5T05-LOCAL-PRODUCTION-AND-MIGRATION-PREP`: completed local
  production runner and 2026-06-30 migration prep without installing launchd or
  enabling GitHub cloud scheduled production.

## Local Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 -m unittest discover -s arxiv-daily-push/tests -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=arxiv-daily-push/src python3 scripts/validate_project_governance.py --project arxiv-daily-push
git diff --check
```

## Resource Policy

Do not commit media, model weights, voice samples, credentials, Codex auth,
GitHub tokens, SMTP secrets, render cache, or dependency directories. Local
production must keep secrets in owner-controlled environment or Keychain-backed
setup only. No PDF bulk downloads, no large model/TTS downloads, no uncontrolled
real SMTP send, no Release upload, no GitHub cloud production schedule, and no
Stage 2 source promotion without source gates.
