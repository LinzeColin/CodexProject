# Production Trial Runbook

Project: `arxiv-daily-push`
Notification recipient: `linzezhang35@gmail.com`
Timezone: `Australia/Sydney`

## Purpose

This runbook prepares the real 30-day Phase 11 trial without claiming that the
trial has already passed. The GitHub workflow is manual-only and runs production
preflight first. A scheduled 05:00 production run must not be enabled until the
preflight artifact proves the runner, SMTP, Release target, disk, memory, Git
artifact hygiene, and local cache gates pass.

## GitHub Setup

Required private self-hosted runner:

- Label: `arxiv-daily-push` by default, or the label passed as the workflow
  `runner_label` input.
- Required commands on runner: `python3`, `git`, `node`, `npm`, `gh`, `ffmpeg`,
  `docker`, and `codex`.
- Python HTTPS certificate validation must work for
  `https://export.arxiv.org/api/query`; do not bypass TLS verification.
- Minimum free disk before production work: 80 GiB.
- Minimum memory before production work: 8 GiB.

Required GitHub Actions secrets:

- `ADP_SMTP_HOST`
- `ADP_SMTP_PORT`
- `ADP_SMTP_USERNAME`
- `ADP_SMTP_PASSWORD`

Required GitHub Actions variables:

- `ADP_RELEASE_TARGET`
- `ADP_PRODUCTION_ENABLED`
- `ADP_SCHEDULED_RUN_ENABLED`
- `ADP_DAILY_INPUT_PATH` optional override; leave empty to build from live arXiv
- `ADP_ARXIV_QUERY` optional; default `cat:cs.AI`
- `ADP_ARXIV_MAX_RESULTS` optional; default `10`
- `ADP_RECENT_SOURCE_IDS` optional comma-separated list of recently selected
  `source_id` values
- `ADP_TRIAL_EVIDENCE_INPUT_PATH` optional existing trial evidence JSON path
  available on the runner
- `ADP_TRIAL_ID` optional; default `adp-trial-current`
- `ADP_TRIAL_REF` required before final trial acceptance can pass
- `ADP_TEXT_DEGRADATION_VERIFIED` optional explicit flag for verified text
  degradation path evidence
- `ADP_VIDEO_DEGRADATION_VERIFIED` optional explicit flag for verified video
  degradation path evidence
- `ADP_ALLOW_SMTP_SEND`
- `ADP_ALLOW_RELEASE_UPLOAD`

Required workflow permissions for Release evidence:

- `actions: read` for prior artifact/state restore.
- `contents: write` for controlled draft GitHub Release creation when
  `ADP_ALLOW_RELEASE_UPLOAD=true`.

The workflow maps only secret names into environment variables. It must not echo
secret values, read `~/.codex/auth.json`, upload Releases, or send SMTP mail
unless the explicit side-effect variables are set for a controlled probe.

## Preflight Dispatch

Run the workflow:

```text
arXiv Daily Push production trial bootstrap
```

Use these inputs:

- `confirm_production_trial=true`
- `runner_label=arxiv-daily-push` unless the private runner uses another label
- `mode=preflight-only`
- `generated_at=<ISO timestamp>` optional

Expected first artifact:

```text
adp-production-preflight
```

The artifact must contain a JSON report from:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push preflight-production --path . --generated-at <ISO timestamp> --json
```

If preflight exits non-zero, stop. Do not start the 30-day trial.

## Scheduled Production Gate

The scheduled workflow is:

```text
.github/workflows/arxiv-daily-push-scheduled.yml
```

The workflow declares `timezone: "Australia/Sydney"` and these local schedule
slots:

- `04:45` health check;
- `05:00` daily run gate;
- `05:10` watchdog.

Scheduled runs skip by default unless `ADP_PRODUCTION_ENABLED=true` is set in
GitHub Actions variables. Even after that, the scheduled workflow runs
production preflight first and keeps daily side effects blocked unless
`ADP_SCHEDULED_RUN_ENABLED=true` is explicitly configured. The scheduled
workflow uploads two artifacts:

- `adp-scheduled-preflight`;
- `adp-scheduled-source-batch` for daily-run when no override input path is set;
- `adp-scheduled-daily-input` for daily-run when no override input path is set;
- `adp-scheduled-execution`;
- `adp-trial-ledger-update` for daily-run ledger accumulation attempts.
- `adp-trial-evidence-ledger` after a daily ledger append succeeds.

The execution artifact is produced by:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push run-scheduled-production \
  --mode <health-check|daily-run|watchdog> \
  --generated-at <ISO timestamp> \
  --preflight-report <adp-scheduled-preflight.json> \
  --json
```

Daily runs also require `ADP_DAILY_INPUT_PATH` to point to a small daily input
package, or the workflow builds a daily input report from live arXiv source
ingest using:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push fetch-arxiv-latest --query "${ADP_ARXIV_QUERY:-cat:cs.AI}" --max-results "${ADP_ARXIV_MAX_RESULTS:-10}" --generated-at <ISO timestamp> --json
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-daily-input --source-batch <source-batch.json> --date <YYYY-MM-DD> --generated-at <ISO timestamp> --json
```

The daily input builder uses only arXiv Atom `<summary>` and metadata claims. It
does not download PDFs, perform bulk harvest, or claim peer review from arXiv.
The selected daily input report is used as the initial Release evidence asset.
Dry-run SMTP or dry-run Release results are recorded as `degraded` with
`exit_code=2`; they cannot be counted toward Phase 11 production acceptance.
Production-ready daily evidence requires both real SMTP delivery and real
private Release creation to return evidence refs.

After a daily-run execution artifact exists, the scheduled workflow attempts to
append it to the trial evidence ledger with:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push update-trial-ledger \
  --scheduled-execution <adp-scheduled-execution.json> \
  --generated-at <ISO timestamp> \
  --trial-id "${ADP_TRIAL_ID:-adp-trial-current}" \
  --trial-ref "${ADP_TRIAL_REF:-}" \
  --json
```

When `ADP_TRIAL_EVIDENCE_INPUT_PATH` is set, the command also reads the existing
trial evidence JSON and appends one new daily entry. The ledger updater refuses
dry-run or degraded non-production evidence, duplicate daily dates, duplicate
source IDs, duplicate publication IDs, missing P0 traceability, unsupported
claim publication, misleading failure output, and missing daily Release/SMTP/
resource refs. It can record daily Release/SMTP/resource evidence from
production-ready scheduled execution, but it does not mark weekly/monthly replay
or recovery drill evidence complete unless those later evidence refs are
explicitly supplied.

If `ADP_TRIAL_EVIDENCE_INPUT_PATH` is not set, the workflow tries to restore the
previous successful run's `adp-trial-evidence-ledger` artifact using `gh run
download` with the workflow `GITHUB_TOKEN`. After a successful append, it exports
the updated `trial_evidence` object with:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push export-trial-ledger-state \
  --ledger-update <adp-trial-ledger-update.json> \
  --json
```

The exported state is uploaded as `adp-trial-evidence-ledger` and is the default
carry-forward input for later scheduled daily runs. If the ledger update blocks,
the state export also blocks and no replacement state artifact is uploaded.

After weekly replay, monthly replay, or recovery drill evidence exists, do not
hand-edit the trial evidence JSON. For weekly/monthly replay, first build a
replay evidence report from the accumulated trial ledger and archive that report
as a durable artifact or Release ref:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-trial-replay-evidence \
  --path <trial-evidence.json> \
  --generated-at <ISO timestamp> \
  --weekly-replay \
  --monthly-replay \
  --replay-ref <weekly-monthly-evidence-ref> \
  --json
```

The replay command validates production-ready daily refs, duplicate-free
coverage, at least 7 consecutive days for weekly replay, at least 30 consecutive
days for monthly replay, and a non-empty durable ref. It does not create Release
assets, send email, generate media, or mutate the trial ledger.

For recovery drill evidence, first archive both the failed/degraded scheduled
daily-run report and the recovered production-ready rerun report. Then build the
recovery evidence report:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-trial-recovery-evidence \
  --failure-execution <failed-or-degraded-scheduled-execution.json> \
  --recovery-execution <recovered-scheduled-execution.json> \
  --generated-at <ISO timestamp> \
  --failure-ref <failure-evidence-ref> \
  --recovery-ref <recovery-evidence-ref> \
  --json
```

The recovery command requires a real sent failure notification, a recovered
`production_evidence_ready=true` daily-run report with daily run, Release, SMTP,
and resource refs, and durable failure/recovery refs. It does not rerun the
scheduler, send mail, upload Releases, mutate the trial ledger, or claim
production acceptance.

For 30-day resource telemetry evidence, archive the passing production preflight
reports whose `resource_pressure_ok_ref` values appear in the daily trial
entries. Then build the resource evidence report:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-trial-resource-evidence \
  --path <trial-evidence.json> \
  --preflight-report <day-01-production-preflight.json> \
  --preflight-report <day-02-production-preflight.json> \
  ... \
  --generated-at <ISO timestamp> \
  --resource-ref <resource-telemetry-evidence-ref> \
  --json
```

The resource command requires 30 unique daily `resource_gate_ref` values, matching
passing production preflight reports, and a durable resource evidence ref. It
does not run preflight, mutate the trial ledger, or claim production acceptance.

Before starting a real acceptance-counting 30-day trial, build the start gate
from archived production-readiness evidence:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-trial-start \
  --preflight-report <passing-production-preflight.json> \
  --bootstrap-plan <trial-bootstrap-plan.json> \
  --scheduler-plan <production-scheduler-plan.json> \
  --source-batch <passing-live-source-batch.json> \
  --smtp-delivery <real-sent-smtp-report.json> \
  --release-delivery <real-created-release-report.json> \
  --generated-at <ISO timestamp> \
  --default-branch-ref <default-branch-commit-ref> \
  --runner-ref <private-runner-ref> \
  --preflight-ref <preflight-artifact-ref> \
  --source-ingest-ref <source-batch-artifact-ref> \
  --smtp-ref <smtp-delivery-ref> \
  --release-ref <private-release-ref> \
  --scheduler-ref <scheduled-workflow-ref> \
  --trial-state-ref <initial-ledger-state-ref> \
  --trial-start-ref <trial-start-gate-artifact-ref> \
  --confirm-start \
  --json
```

The start gate does not enable schedules, send mail, create Releases, mutate the
trial ledger, retain media/model/cache artifacts, or claim 30-day acceptance. It
only marks `trial_start_ready=true` when all upstream reports pass, real SMTP and
Release probes are present, every ref is durable, and the explicit confirmation
flag is set.

## Production Refs Readiness Bundle

Before the launch readiness report can be run with external refs, collect only
non-secret readiness metadata in a JSON file. The file may contain secret names
and durable evidence refs, but must not contain SMTP hosts, ports, usernames,
passwords, tokens, API keys, or credential values:

Generate the owner-fillable no-secret template first:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push print-production-refs-template \
  --runner-label arxiv-daily-push \
  --release-target <private-release-target> \
  > <production-refs-input.json>
```

The repository example at
`config/examples/production_refs.input.example.json` has the same structure and
defaults every `ready` flag to `false`. Fill only readiness booleans, names, the
Release target, and durable refs. Do not add secret values.

```json
{
  "runner": {
    "ready": true,
    "label": "arxiv-daily-push",
    "evidence_ref": "github-runner://LinzeColin/CodexProject/arxiv-daily-push"
  },
  "smtp_secrets": {
    "ready": true,
    "secret_names": ["ADP_SMTP_HOST", "ADP_SMTP_PORT", "ADP_SMTP_USERNAME", "ADP_SMTP_PASSWORD"],
    "evidence_ref": "github-secrets://LinzeColin/CodexProject/actions/smtp"
  },
  "release_target": {
    "ready": true,
    "var_name": "ADP_RELEASE_TARGET",
    "target": "main",
    "evidence_ref": "github-vars://LinzeColin/CodexProject/actions/ADP_RELEASE_TARGET"
  },
  "workflow_vars": {
    "ready": true,
    "var_names": ["ADP_RELEASE_TARGET", "ADP_ALLOW_SMTP_SEND", "ADP_ALLOW_RELEASE_UPLOAD"],
    "evidence_ref": "github-vars://LinzeColin/CodexProject/actions/workflow-vars"
  }
}
```

Build the machine-checkable refs report:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-refs \
  --readiness-input <production-refs-input.json> \
  --generated-at <ISO timestamp> \
  --json > <production-refs-report.json>
```

The report is ready only when all required names are present, each readiness ref
contains a durable scheme, and the input does not include secret-like keys or
values. This command does not inspect GitHub secret values, read Codex auth,
dispatch workflows, send SMTP mail, create Releases, or claim production
acceptance.

When running on a provisioned private runner with `gh` available, the no-secret
metadata collection can be generated directly from GitHub Actions metadata:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push discover-production-refs \
  --repo LinzeColin/CodexProject \
  --runner-label arxiv-daily-push \
  --generated-at <ISO timestamp> \
  --json > <production-refs-report.json>
```

This discovery command reads only GitHub Actions metadata exposed by `gh api`:
runner labels/status, secret names and update timestamps, and repository
variable names plus `ADP_RELEASE_TARGET`. It does not read secret values, print
`gh` stdout/stderr, dispatch workflows, send SMTP mail, create Releases, mutate
trial evidence, read Codex auth, or claim production acceptance. If `gh` is not
installed or GitHub metadata access fails, it exits blocked.

## Production Launch Readiness

Before dispatching the default-branch trial start workflow, build a launch
readiness report from current GitHub PR metadata and external readiness refs:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-launch \
  --path . \
  --pr-info <current-pr-info.json> \
  --generated-at <ISO timestamp> \
  --expected-head-sha <expected-pr-head-sha> \
  --default-branch-ref <merged-default-branch-ref> \
  --runner-ref <private-runner-readiness-ref> \
  --smtp-secret-ref <github-smtp-secrets-readiness-ref> \
  --release-target-ref <github-release-target-readiness-ref> \
  --workflow-vars-ref <github-vars-readiness-ref> \
  --trial-start-workflow-ref <default-branch-trial-start-workflow-ref> \
  --confirm-launch \
  --json
```

When a passing production refs report already exists, it can fill the external
runner, SMTP secret, Release target, and workflow variable refs:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-launch \
  --path . \
  --pr-info <current-pr-info.json> \
  --generated-at <ISO timestamp> \
  --expected-head-sha <expected-pr-head-sha> \
  --default-branch-ref <merged-default-branch-ref> \
  --trial-start-workflow-ref <default-branch-trial-start-workflow-ref> \
  --production-refs-report <production-refs-report.json> \
  --confirm-launch \
  --json
```

The PR metadata JSON must include `state`, `merged`, `draft`, `base`, and
`head_sha`. The gate blocks while the PR is draft, unmerged, pointed at a branch
other than `main`, missing the expected head SHA, missing any durable readiness
ref, or while the trial start workflow contract is not ready. It does not merge
the PR, dispatch workflows, read secret values, send SMTP mail, create Releases,
retain media/model/cache artifacts, or claim production acceptance.

## Post-Merge Launch Audit

After PR #32 was merged to `main`, the PR, expected-head, default-branch, and
trial-start workflow checks cleared. A production trial start precheck still
blocks because the remaining durable external refs and explicit launch
confirmation are not present:

- `runner_ref`
- `smtp_secret_ref`
- `release_target_ref`
- `workflow_vars_ref`
- `launch_confirmed`

Do not dispatch `.github/workflows/arxiv-daily-push-trial-start.yml` until those
refs are recorded and a fresh `plan-production-launch` report returns
`production_launch_ready=true`.

Current recorded refs:

- `default_branch_ref`:
  `git://LinzeColin/CodexProject/main@df28c70f255d4db0cabf15d6555ce34a8b2fa560`
- `trial_start_workflow_ref`:
  `github-actions://LinzeColin/CodexProject/.github/workflows/arxiv-daily-push-trial-start.yml@main#df28c70f255d4db0cabf15d6555ce34a8b2fa560`

## Trial Start Evidence Workflow

After the start gate command has been validated locally, the default-branch
workflow for collecting real start evidence is:

```text
.github/workflows/arxiv-daily-push-trial-start.yml
```

GitHub Actions display name:

```text
arXiv Daily Push trial start evidence
```

Dispatch inputs:

- `confirm_trial_start=true`
- `runner_label=arxiv-daily-push` unless the private runner uses another label
- `generated_at=<ISO timestamp>` optional

The workflow is manual-only and starts no private runner job when
`confirm_trial_start` is not `true`. It always runs production preflight,
no-secret production refs discovery, and `plan-production-launch` readiness
before live source ingest, SMTP probe, Release probe, or `plan-trial-start`.
Real SMTP and Release side effects remain disabled unless GitHub variables
`ADP_ALLOW_SMTP_SEND=true` and `ADP_ALLOW_RELEASE_UPLOAD=true` are explicitly
set for a controlled probe.
The workflow declares `contents: write` only so that the controlled Release
probe can create a draft Release after that variable is enabled; the permission
alone must not be treated as upload authorization.

Expected artifacts:

- `adp-trial-start-preflight`
- `adp-trial-start-production-refs`
- `adp-trial-start-launch-readiness`
- `adp-trial-start-bootstrap-plan`
- `adp-trial-start-scheduler-plan`
- `adp-trial-start-source-batch`
- `adp-trial-start-smtp-delivery`
- `adp-trial-start-release-delivery`
- `adp-trial-start-gate`

The workflow can be validated without running production side effects:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-trial-start-workflow --path . --generated-at <ISO timestamp> --json
```

Only a passing `adp-trial-start-gate` artifact from this workflow on the default
branch should be treated as trial start evidence for the 30-day acceptance
window.

Then merge the explicit evidence refs with:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push annotate-trial-ops-evidence \
  --path <trial-evidence.json> \
  --generated-at <ISO timestamp> \
  --weekly-replay-verified \
  --monthly-replay-verified \
  --weekly-monthly-ref <weekly-monthly-evidence-ref> \
  --recovery-drill-verified \
  --recovery-ref <recovery-drill-evidence-ref> \
  --resource-pressure-ok \
  --resource-ref <resource-telemetry-evidence-ref> \
  --json
```

The command can also merge explicit scheduler, manual rerun, Release, SMTP, and
resource refs when those are produced outside the daily ledger update. It blocks
verified flags without refs and does not generate weekly/monthly reports,
recovery drills, SMTP sends, Releases, or production acceptance claims.

To carry the annotated state forward without local persistence, export the state
only from a passing annotation report:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push export-trial-ops-state \
  --ops-update <trial-ops-update.json> \
  --json
```

Validate the scheduled workflow contract locally or on the runner:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push plan-production-scheduler --path . --generated-at <ISO timestamp> --json
```

Before enabling scheduled source collection, verify live arXiv source ingest:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push fetch-arxiv-latest --query 'cat:cs.AI' --max-results 1 --generated-at <ISO timestamp> --json
```

If this blocks on Python SSL certificate validation, update the runner CA trust
store or Python certificate bundle. Do not switch to insecure TLS behavior.

After source ingest succeeds, verify daily input construction with the emitted
source batch:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push build-daily-input --source-batch <source-batch.json> --date <YYYY-MM-DD> --generated-at <ISO timestamp> --json
```

If this blocks on missing Atom summary, duplicate recent source ID, metadata
conflict, or missing P0 evidence, stop the daily run and inspect the uploaded
`adp-scheduled-source-batch` and `adp-scheduled-daily-input` artifacts.

Before enabling real notification sending, verify the SMTP delivery boundary in
dry-run mode:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push send-notification \
  --run-id adp-notification-probe \
  --summary "SMTP delivery boundary probe" \
  --date <YYYY-MM-DD> \
  --generated-at <ISO timestamp> \
  --json
```

Real SMTP sending is allowed only after production preflight passes and the SMTP
secrets are configured. Use the explicit flag so accidental dispatches fail
closed by default:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push send-notification \
  --run-id adp-notification-probe \
  --summary "SMTP delivery boundary probe" \
  --date <YYYY-MM-DD> \
  --generated-at <ISO timestamp> \
  --allow-send \
  --json
```

The delivery report must be archived as evidence. It records the recipient,
subject, body SHA256, delivery status, and configured key names only; it must not
log SMTP secret values or the email body.

Before enabling private Release creation, verify the Release delivery boundary
in dry-run mode with a small metadata/report asset:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push publish-release \
  --tag adp-release-probe-<YYYYMMDD> \
  --title "arXiv Daily Push release probe" \
  --notes "Release delivery boundary probe" \
  --asset <trial-evidence-or-run-record.json> \
  --generated-at <ISO timestamp> \
  --json
```

Real GitHub Release creation is allowed only after production preflight passes,
`ADP_RELEASE_TARGET` is configured, and the asset list has passed the local
secret/model suffix and size gates. Use an explicit flag; published Releases
also require `--publish` because draft is the default:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push publish-release \
  --tag adp-release-probe-<YYYYMMDD> \
  --title "arXiv Daily Push release probe" \
  --notes-file <release-notes.md> \
  --asset <trial-evidence-or-run-record.json> \
  --generated-at <ISO timestamp> \
  --allow-upload \
  --json
```

The Release delivery report must be archived as evidence. It records asset
names, sizes, SHA256 values, tag, target, and a redacted command preview only.
It must not log Release notes text, secret values, `gh` stdout, or `gh` stderr.

## Trial Evidence

After production side effects are explicitly enabled in a later controlled step,
collect one evidence entry for each daily run. The final evidence package must
cover at least 30 unique daily dates and then pass:

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push evaluate-trial --path <trial-evidence.json> --generated-at <ISO timestamp> --json
```

The package must prove:

- no duplicate daily publication;
- key P0 claims are traceable;
- failures do not generate misleading content;
- 05:00 scheduler evidence and manual rerun evidence exist;
- private Release or equivalent publishing evidence exists;
- real SMTP evidence to `linzezhang35@gmail.com` exists;
- weekly and monthly replay evidence exists;
- recovery drill evidence exists;
- disk, memory, cache, Git artifact, and secret hygiene evidence exists.

Only a passing `adp-trial-evidence-v1` report can be used by `build-acceptance`
to mark production acceptance as complete.

## Current Boundary

The bootstrap workflow does not schedule production, upload a Release, send
SMTP mail, render media, download models, or claim 30-day acceptance. It is a
pre-production gate for starting the real trial safely.
