# Recommended Sprint 2I-B Plan

## Recommendation

Run Sprint 2I-B as one bounded old-computer remediation run, only after explicit
approval.

## Goal

Resolve or classify the post-bootstrap hang and attempt one minimal
message-level sample.

## Allowed Scope If Approved

Use only the already selected and pinned primary route:

- repo: `https://github.com/r266-tech/wechat-cli.git`
- commit: `5c76757e849da3f595a0ef7402d23fe15fd78322`
- release: `wechat-cli v1.6.19`, `darwin-arm64`

Suggested bounded sequence:

1. Confirm only the original WeChat process is running.
2. Keep existing key config on the old computer only.
3. Run a bounded `wxkey doctor --scan` with timeout.
4. Run a bounded `wechat-cli cache status` with timeout.
5. Run a bounded `wechat-cli sessions --limit 1` with timeout.
6. If and only if `sessions --limit 1` returns a selected chat identifier, run
   `timeline <selected_chat> --limit 1`.
7. Produce shape-only reports and do not transfer raw output by default.

## Required Approval

Before execution, the user must approve:

- old-computer execution
- use of the pinned primary tool route only
- timeout limits
- whether stored sudo credential use is allowed
- whether additional `wxkey` scan is allowed
- where new local outputs may be written
- what non-sensitive reports may be transferred back to the new computer

## Stop Conditions

- Any command attempts upload, message sending, UI automation, or broad export.
- Any command requires transferring key config or raw logs to the new computer.
- A live-read command hangs again after the bounded timeout.
- The tool tries to write outside the approved WDA_MetaData output root.
- A minimal sample cannot be produced without expanding scope.

## Gate

Raw Gate remains `Conditional Investigation` unless a later approved step
produces a valid `messages.jsonl` or equivalent minimal message-level sample and
then validates it against the WDA import contract.

