# Stage C2/C3/D1 Usage

## C2: Issue-Triggered Task Pack

Use this when the Owner has an approved Task Pack and wants GitHub Issues to
start Agent Loop automatically.

Steps:

1. Create an issue whose body is the complete dual-plane Task Pack.
2. For trusted issue authors, no manual labels are required.
3. The workflow starts on `opened` or `edited` if the body contains
   `AGENT_LOOP_METADATA` and metadata `source` is `chatgpt-approved`.
4. The workflow starts if the issue has no state labels:
   - `agent:running`
   - `agent:done`
   - `agent:blocked`

The workflow creates missing labels, adds `source:chatgpt-approved`,
`agent:run`, and `agent:running` at start. On success it removes
`agent:running`, adds `agent:done`, comments the result, and closes the issue.
On failure or routing block it removes `agent:running`, adds `agent:blocked`,
and comments a failure summary.

The workflow also checks live issue labels through GitHub before expensive
work. If an `opened` event and a `labeled` event both fire for the same issue,
one run acquires `agent:running`; the later duplicate run exits successfully as
`DUPLICATE_IGNORED`.

## ROI Hotfix v1 Runtime Defaults

T1 tasks default to `executor_mode=codex-one-shot`. The workflow validates the
Task Pack and routing first, then makes one paid `openai/codex-action@v1` call.
That single prompt requires Codex to state a brief implementation plan, make the
scoped change, and return the Result Pack.

T1 does not run separate paid plan + implementation calls. Codex review,
Architect Review, and autofix are disabled by default. This protects the Owner's
trial budget and avoids the same-job second `drop-sudo` failure seen in run
`28429923364`.

T2 remains plan-first, but ROI Hotfix v1 does not implement the future multi-job
T2 orchestration. T2 is blocked before paid calls with
`T2_MULTI_JOB_NOT_IMPLEMENTED`.

After any paid-call failure, do not blindly rerun. Inspect these artifacts first:

- `agent-loop-roi-summary.md`
- `failure-git-status.txt`
- `failure-diff-name-only.txt`
- `failure-diff-stat.txt`

For Issue #257 or similar blocked smoke issues, remove `agent:blocked` and edit
the issue only after the hotfix is on `main` and the artifact review is complete.
The expected T1 paid-call count after this hotfix is `1`.

## C3: Issue Form / Prefilled Issue

Use `.github/ISSUE_TEMPLATE/codex-task.yml` when the Owner does not want to
open GitHub Actions. The form has one large textarea for the full Task Pack.

No manual labels are required. The workflow adds missing labels itself after it
verifies the trusted issue author and the Task Pack metadata source. Avoid
manual `agent:run` labels on new issues because they can create duplicate
`opened`/`labeled` events; duplicate runs are safe but waste Actions startup
time.

Human-plane headings may be Chinese, English, or bilingual. The metadata JSON
remains strict. The validator accepts headings such as `## 1. 人类摘要` and
`## Human Summary`, but every canonical section is still required.

For browser prefill, run:

```bash
python3 scripts/agent_loop/build_prefilled_issue_url.py \
  --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack.md \
  --repo LinzeColin/CodexProject
```

If the URL is too long, create a normal issue with the same template and paste
the Task Pack. D1 issue mode is available, but it is not the default Owner
path.

## D1: Local GitHub CLI Submitter

The local submitter uses existing `gh` authentication. It does not ask for a
PAT and does not store tokens. This is optional; Owner-facing default paths are
C2 issue trigger and C3 Issue Form.

Issue mode:

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --mode issue \
  --repo LinzeColin/CodexProject
```

Dispatch mode:

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --mode dispatch \
  --repo LinzeColin/CodexProject
```

Workflow fallback:

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack path/to/taskpack.md \
  --mode workflow \
  --repo LinzeColin/CodexProject \
  --dry-run
```

Local dry run, no GitHub calls:

```bash
python3 scripts/agent_loop/submit_taskpack.py \
  --taskpack docs/governance/agent_loop/examples/minimal_t1_taskpack.md \
  --mode issue \
  --repo LinzeColin/CodexProject \
  --dry-run-local
```

## Future D2/D3

D2 may use a webhook bridge such as Cloudflare Workers or a similar service to
forward approved Task Packs to `repository_dispatch`. It is not implemented in
this task. The bridge design is documented in
`docs/governance/agent_loop/WEBHOOK_BRIDGE_DESIGN.md`.

D3 may use a direct ChatGPT connector, MCP, or external action. It is not
implemented in this task and must not be treated as a current dependency.

## Troubleshooting

- `Skipped` means the job-level guard did not match. Common causes are missing
  `AGENT_LOOP_METADATA`, untrusted issue author, or an existing
  `agent:running`, `agent:done`, or `agent:blocked` label.
- No labels on a newly created issue is not fatal after the C3 opened-trigger
  fix. The workflow bootstraps labels itself.
- Duplicate issue events should show a successful `DUPLICATE_IGNORED` preflight
  summary instead of running Codex twice.
- For old smoke issues, edit the issue body after deploying this fix. Adding a
  comment marker such as `<!-- rerun: after-c3-opened-trigger-fix -->` triggers
  `issues: edited`.
