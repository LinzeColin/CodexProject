# arXiv Daily Push Agent Rules

This project follows the root `AGENTS.md` and `docs/governance/STANDARD.md`.

## V0.3 重构指针（先读）

当前活动开发合同是 **V0.3 重构任务包**：从 `docs/v03/CONTRACT.md` 开始，只读 `docs/v03/`（<110 KB）与被任务直接点名的源码。参数唯一真相 `config/thresholds_v0_3.yaml`；阶段状态 `docs/v03/STATUS.yaml`。三大根级人读 md 与 docs/governance 巨型登记文件已按 R0-6 冻结（`archive/README.md`），不得作为阅读输入。本文件以下的 V7.2 规则仅约束旧运行时（保持失败关闭）。

## S4 精简执行胶囊

普通非来源变更先读本文件、`README.md` 和被任务直接点名的任务/证据文件。仅做文案、
README、owner 页面或治理说明改动时，不得默认读取完整 `用户中心/`、`docs/owner/`
或所有根级人类入口。

普通非来源变更验证命令：

```bash
PYTHONPATH=arxiv-daily-push/src python -B -m unittest arxiv-daily-push/tests/test_owner_controls.py arxiv-daily-push/tests/test_user_center_candidate_pool.py -q
python -B scripts/lean_governance.py check-render --project arxiv-daily-push
```

来源、板块、scheduler、SMTP、storage、security、ranking，或用户中心里的来源/板块
新增、删除、重命名、启用、停用变更，必须读取被点名的来源/板块契约，并走完整特殊
gate 路线。最低验证包括：

```bash
PYTHONPATH=arxiv-daily-push/src python -B -m unittest arxiv-daily-push/tests/test_security_boundary.py -q
PYTHONPATH=arxiv-daily-push/src python -B -m unittest arxiv-daily-push/tests/test_source_registry.py arxiv-daily-push/tests/test_user_center_candidate_pool.py arxiv-daily-push/tests/test_owner_controls.py -q
```

这条路线保留来源变更所需的完整 V7.2 和用户中心门禁，同时让普通非来源任务避免读取
完整用户中心。

## Permanent Rules

- Work one phase, one task ID, and one acceptance target at a time.
- Use `docs/pursuing_goal/CURRENT.yaml`,
  `docs/pursuing_goal/v7_2/V7_2_ROOT_LOCK.yaml`,
  `docs/pursuing_goal/v7_2/machine_readable/product_contract_v7_2.yaml`,
  `docs/pursuing_goal/v7_2/machine_readable/roadmap_v7_2.yaml`, and
  `docs/pursuing_goal/v7_2/HANDOFF/00_下一Agent先读.md` as the current execution
  contract. `docs/pursuing_goal/v7_1/V7_1_ROOT_LOCK.yaml` and the rest of
  `docs/pursuing_goal/v7_1/` remain a read-only historical baseline and must
  not be overwritten or deleted. V5/V6/V7.0 files remain historical evidence
  and alias references; they no longer override V7.2.
- Every implementation closeout must state the current V7.2 contract, the
  active contextual task, and any legacy alias. Stage 2 integrated acceptance 已
  记录并保持；当前事实以 `docs/pursuing_goal/CURRENT.yaml`,
  `FINAL_ACCEPTANCE_BUNDLE/manifest.json`, and
  `FINAL_ACCEPTANCE_BUNDLE/integrated_production_acceptance.json` 为准。
  S3/DAILY_OPERATION 仍未进入；当前实际阻断只剩 S3/DAILY_OPERATION 持久授权
  缺失，即 `persistent_daily_operation_authorization_missing` /
  `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`
  不存在。下一可执行任务是
  `S2PMT07-DAILY-OPERATION-PERSISTENT-ENABLEMENT-AUTHORIZATION`；缺该显式
  owner 持久授权 artifact 时，只能继续 MVP 复审修补、fail-closed 复核和证据
  同步，不得启用 SMTP、scheduler、Release、restore 或 DAILY_OPERATION。
  `S2PCT02`
  (`S2P2T02` legacy alias)
  Science/top-journal metadata-only no-send shadow evidence is completed
  history, not the current task. `S2PCT01`
  (`S2P2T01` legacy alias) Nature/top-journal metadata-only no-send shadow
  foundation has merged to main and remains a completed D2 shadow foundation
  record, not a D2 source-domain acceptance claim. `S2PBT01`
  (`S2P1T01` legacy alias) bioRxiv/medRxiv no-send replay and shadow evidence
  has passed and remains a D1 alias/history record, not the current task.
  Formal source production inclusion and DAILY_OPERATION remain blocked by the
  persistent authorization gate, not by reopening the old Stage 2 final gate.
  EMAIL_LEARNING_V1 M1-M4 renderer is merged to main through PR #152 and
  maintained through PR #153; future mail entrypoints must use the same Email
  V1 contract/readiness gate and must not bypass it. `S2PMT01` local security
  evidence covers `UNTRUSTED_DATA`, typed frontstage statements, safe URL
  rendering, zero-critical-claim blocking, and local supply-chain baseline
  receipt; `S2PMT02` local atomic recovery evidence covers staged writes,
  manifest hash verification, tamper detection, restore drill, and staging
  cleanup. `S2PMT03` local lease/concurrency evidence covers row_version
  compare-and-swap, lease expiry, fencing tokens, state-history consistency,
  idempotent transactional outbox identity, SMTP accept crash-window handling,
  and M4 cycle watermarks. `S2PMT04` local lifecycle/cache evidence covers
  disabled automatic wake dry-run, drain/checkpoint/cleanup lifecycle,
  startup reconciliation and convergence, durable shutdown and transaction
  completion receipts, low-disk cache degradation, whitelist/symlink guarded
  dry-run cache cleanup, parseable launchd plist generation, and no production
  side effects. `S2PMT05` local stress/fault/time/E2E evidence covers
  formal capacity baseline rows, deterministic load/stress/spike profiles,
  accelerated local 24h soak coverage, bounded recoverable queue age, 1x/2x/5x
  multipliers, throughput/latency/memory/disk/error-budget evidence,
  multi-actor duplicate-trigger race protection with `mail_key`,
  `lease_owner`, `fencing_token`, and reason-coded blocked attempts, SMTP
  accepted-before-local-commit crash-window handling with idempotent
  `message_id`, provider accept ref, and no-resend proof, ENOSPC/read-only/
  SQLITE_BUSY/corrupt JSON/PDF/backup fault injection with explicit recovery
  states, structured Australia/Sydney 05:00 schedule, DST fold/gap, 3600-second
  misfire grace, bounded one-cycle catch-up, 8h sleep recovery, NTP
  backward/forward clock-jump policy, and no duplicate M4 watermark, 35-day
  3+1/weekly/monthly/review/action/ROI E2E audit bundle, section artifacts,
  deterministic bundle hash, count conservation, reachable review/action/ROI links,
  semantic/evidence-bound non-template result validity, 2x/5x
  priority-aware backpressure/degradation with high-priority SLO and
  low-priority reason codes, deterministic isolation, and no production side
  effects. `S2PMT06` local owner UX evidence covers the Chinese
  first screen, fixed navigation, status feedback states, recoverable error
  cards, safe config-change flow, append-only revision ledger, queue
  search/filter/export/drilldown, safe manual actions, feedback visibility,
  accessibility/mail compatibility, source-to-ROI traceability, and no
  production side effects. `S2PMT07` historical local precheck records are
  history; they do not reopen current final-bundle, P0/P1 zero-proof, S2PLT04,
  independent review, or Stage 2 integrated acceptance gaps. They also do not
  enable DAILY_OPERATION.
  `ADP-S1P5T05` completed the Stage 1 local production and migration prep after
  `ARXIV_PRODUCTION_ACCEPTED`.
  Final Stage 1 production strategy is local Mac + Codex/local runner; GitHub
  is code, PR/CI, evidence, status, and backup only, not the daily production
  runner.
- Stage 1 starts with arXiv as the only production-acceptance source and remains
  `ARXIV_PRODUCTION_ACCEPTED`. Stage 2 may promote additional sources and
  boards only after the V7.2 contract is readable, hashes match, agent
  revalidation receipts are recorded, source-level gates pass, and P0/P1 audit
  findings are zero. Stage 2 is not complete until
  `S2PMT07 -> INTEGRATED_PRODUCTION_ACCEPTED -> DAILY_OPERATION`.
- Before any active or completed Stage2 agent starts new work, that agent must
  re-review its completed work against V7.2. Non-compliant completed work must
  be fixed before continuing. This revalidation rule does not block no-conflict
  Shadow source work that records a V7.2 receipt and avoids shared contract
  files.
- Legacy `S2P2T02` maps to the V7.2-inherited canonical `S2PCT02`; legacy
  `S2P2T01` maps to the V7.2-inherited canonical `S2PCT01`; legacy `S2P1T01`
  maps to the V7.2-inherited canonical `S2PBT01`. V7.1 is the historical source
  for these aliases, not the current execution contract. Preserve both
  canonical and legacy IDs in events, PR summaries, and closeouts until the
  Stage2 branch has reconciled aliases.
- Do not use OpenAI Platform API keys or paid API fallbacks.
- Do not read, print, or commit Codex auth, GitHub tokens, SMTP secrets, cookies,
  voice samples, model weights, or release media.
- Do not commit MP4, WAV, FLAC, MOV, model weights, render cache, `node_modules`,
  or virtualenv directories.
- V5 Stage 1 delivery is text-first: high-density reports, independent emails,
  Markdown/HTML/JSON audit artifacts, and no required video generation.
- 30-day-grade evidence means 30 independent unique-date artifacts and coverage
  checks, not waiting 30 wall-clock days when real-data evidence can be
  generated and verified faster.
- Email is the notification channel; dry-run rendering is allowed before real
  SMTP transport exists.
- GitHub-rendered Markdown is the owner-facing human-readable surface for
  status, mail, queue, review, action, and ROI summaries. Owner UX and mail
  status work must use a shallow GitHub entry such as
  `arxiv-daily-push/用户中心/README.md` plus adjacent status pages as the
  primary reading path. Local `.adp` files, SMTP reports, run JSON, and
  candidate queues are evidence sources only; owner-facing pages must directly
  summarize sent, blocked/not sent, and queued states without requiring the
  owner to open local absolute paths. Deep `docs/owner/...` pages may remain
  generated/internal references or pointers, but must not be the only owner
  reading entry.
- `arxiv-daily-push/用户中心/README.md` is the single owner-facing user-center
  index. Do not create or maintain a second user-center index page; merge any
  useful index content into README without losing
  entry links or evidence links.
- 后续新增、删除、重命名、启用或停用任何板块或数据源时，必须同步更新
  `用户中心/数据源与板块健康.md`、`用户中心/README.md`、
  `用户中心/一看三查.md`、`用户中心/关键结论与用户决策.md`、
  `docs/owner/SOURCE_CATALOG.md`、`模型参数文件.md`、`功能清单.md` 和
  `开发记录.md`。同一提交必须运行并通过
  `arxiv-daily-push/tests/test_user_center_candidate_pool.py` 和
  `arxiv-daily-push/tests/test_owner_controls.py`；没有同步用户中心或测试未过
  时，不得关闭任务、合并主线或宣称来源变更完成。
- Evidence positions in owner-facing Markdown must be clickable Markdown links,
  preferably relative links that work in GitHub. Do not leave evidence as raw
  backticked paths when the user needs to jump to it.
- Review, action, asset, and ROI owner pages must show the GitHub display
  fields even when the current daily report has not been persisted. Use
  `待今日运行快照写入` for missing real daily values; do not write that GitHub
  cannot display the information, and do not fill real daily counts from tests,
  old reports, chat content, or guesses.
- When real S2PJT02/S2PJT03 daily report JSON files exist, update
  `用户中心/复习行动与收益.md` through
  `scripts/update_user_center_learning_snapshot.py --write` and validate with
  `--check`. The script must leave missing or failed-report values as
  `待今日运行快照写入`.
- Owner-facing user-center Markdown must keep a concrete timestamp line in the
  format `更新时间：YYYY-MM-DD HH:MM:SS Australia/Sydney`. Do not hand-edit or
  invent this time. Before commit, run
  `python arxiv-daily-push/scripts/update_user_center_timestamps.py --write`
  and then
  `python arxiv-daily-push/scripts/update_user_center_timestamps.py --check`;
  missing, malformed, or future timestamps must block the PR.
- Any unsupported key factual claim must block publication.
- Connectors and source adapters must not generate final emails directly.
  Source output flows through EvidencePacket, routing, quality gates, review,
  action, ROI, and the 3+1 mail product contract.

## Stage 1 Window A Boundary

Allowed:

- code, schemas, fixtures, governance files, and tests.
- at most 10 online arXiv metadata records.
- small local artifacts needed for validation.

Forbidden:

- PDFs or bulk source downloads.
- large models, TTS model downloads, or media generation.
- formal scheduler installation before explicit owner smoke-test approval.
- new 30-day replay or production-acceptance claims unless the task explicitly
  requires them.
- broad non-arXiv source expansion before Stage 1 gates pass.
