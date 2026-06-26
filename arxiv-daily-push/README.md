# arxiv-daily-push 中文 Owner 可读入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。本段是 Owner 首屏摘要，用来回答“这是什么、现在到哪、我下一步看哪里、风险是什么”。技术名词、路径、API 名称可以保留英文，但解释必须先给中文结论。

## 一句话结论
arXiv Daily Push 自动化项目，当前重点是区分已接受生产能力、Stage2 仍未生产验收的能力和当前 Owner 操作路径。

这份中文入口不是目录索引，也不是给机器看的字段清单；它先服务 Owner 决策。读者应该先看到当前是否可用、证据是否足够、哪里有风险、下一步该做什么，以及如果判断错误如何回滚。只有在这些中文结论清楚之后，才需要进入下方的详细路径、测试命令和历史记录。

## 摘要
- project_id: `arxiv-daily-push`
- 项目路径：`arxiv-daily-push`
- current_stage: `S2`
- current_phase: `S2PC`
- current_task: `S2PCT02`
- next_gate: `S2PC-GATE-V7-2-REVALIDATION`
- evidence_status: `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。

## 当前状态
这个项目已经纳入 Lean v2 治理入口，首屏必须先说明业务含义、当前阶段、可用证据和限制。Owner 不需要先读源码，也不需要先理解 schema，应该能在本页判断是否继续验证、暂停、回滚或进入下一步。

## Owner 操作入口
1. 先读本文件首屏，确认项目目的、当前任务和下一步。
2. 需要看功能范围时读 `功能清单`，只把有证据的能力当作当前事实。
3. 需要看推进历史时读 `开发记录`，按 Stage -> Phase -> Task 和 stop_gate 判断是否能继续。
4. 需要看模型、公式、参数时读 `模型参数文件`，重点看 active 项和未确认项。
5. 需要机器证据时打开 `docs/governance/` 下的 registry、roadmap、events、STATUS 和 OWNER_STATUS。

## 证据与验证
- active_model_count: `99`
- active_formula_count: `101`
- active_parameter_count: `812`
- 总模型数：`99`；总公式数：`101`；总参数数：`829`。
- 当前证据以仓库文件为准；测试命令、CI 结果或 run manifest 缺失时，只能标记为待验证，不能写成已完成。

## 风险与边界
- 不把历史归档、示例、旧报告、生成物或草稿当成当前生产事实。
- 不因为存在文件路径就默认功能已可用；必须有治理证据、测试结果或 Owner 接受记录。
- 不在没有 Owner 明确确认时改变业务含义、模型参数、公式政策、隐私边界或外部自动化行为。

## 下一步
先补齐中文可读入口，再运行 changed-only 治理检查；若检查失败，优先修复证据、状态和中文说明，不用英文索引页绕过验收。普通开发只走 changed-only compact gate，完整治理计算放到计划任务或手动 all scope。

## 回滚
本次中文可读重做只改文档入口、测试和治理验收规则；如需回滚，恢复本文件和对应人类入口文件即可，不需要迁移数据、不需要改业务代码、不需要触发外部服务。

## 中文验收
- 合格入口不是出现几个中文关键词，而是让 Owner 在第一页就能判断能否继续、是否缺证据、是否有风险、下一步由谁做、做错以后怎样退回。
- 如果读者必须先读字段名、路径、编号、英文状态或长表格才能知道真实情况，就视为中文可读失败；应先改前导区，再补机器字段。
- 后续改动必须保持中文判断在前、治理事实在后、验证命令可复核；任何为了省 token 而删除事实来源的做法都不能通过验收。
- 本页允许保留项目编号和任务编号，但这些编号只能辅助定位，不能替代中文解释；编号越多，越要增加清楚的中文判断。
- 对这个项目尤其要区分已经接受的生产能力、仍在 Stage2 复核的能力、只保留为历史背景的能力；不能因为旧文档里有命令或英文描述，就把它当成当前已验收事实。

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
