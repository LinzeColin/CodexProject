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

## C3: Issue Form / Prefilled Issue

Use `.github/ISSUE_TEMPLATE/codex-task.yml` when the Owner does not want to
open GitHub Actions. The form has one large textarea for the full Task Pack and
convenience labels:

- `source:chatgpt-approved`
- `agent:run`

These labels are not required for startup. GitHub Issue Form labels may fail to
apply if labels do not already exist; the workflow adds missing labels itself.

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
- For old smoke issues, edit the issue body after deploying this fix. Adding a
  comment marker such as `<!-- rerun: after-c3-opened-trigger-fix -->` triggers
  `issues: edited`.
