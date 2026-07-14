# DWS Auth Keepalive｜钉钉认证自动保活

This automation only maintains DWS CLI authentication health. It must not read
business group data or run archive, attendance, routine-check, fund-report, or
other business workflows.

Run exactly one deterministic entrypoint from any working directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /Users/linzezhang/CodexProject/KMFA/tools/automation/dws_auth_keepalive.py --attempts 3 --backoff-seconds 5 --dws-timeout-seconds 20 --command-timeout-seconds 25 --profile-config /Users/linzezhang/.codex/automations/dws-auth-keepalive-2/expected_profile.json --ledger-path /Users/linzezhang/.codex/automations/dws-auth-keepalive-2/memory.md --state-path /Users/linzezhang/.codex/automations/dws-auth-keepalive-2/state.json
```

Execution contract:

1. The wrapper is the only auth command entrypoint. It invokes
   `dws auth status --format json --profile <private-pinned-profile> --timeout 20`,
   which is the DWS CLI's official automatic access-token refresh path. The
   outer process timeout is 25 seconds, leaving grace after DWS's bounded HTTP
   timeout instead of killing a token write in progress.
2. The expected organization profile is pinned in the machine-private 0600 file
   `/Users/linzezhang/.codex/automations/dws-auth-keepalive-2/expected_profile.json`.
   The wrapper passes it explicitly and requires the returned profile to match.
   If it is missing, stop with `pin_expected_profile`; the owner-only recovery
   command is documented in the takeover handoff. The scheduled run must never
   bootstrap, switch, or print the profile value.
3. Success requires all of `success=true`, `authenticated=true`,
   `token_valid=true`, `refresh_token_valid=true`, profile match, and parseable
   access/refresh expiry timestamps later than the current time. Report
   `refreshed` only when the wrapper reports `status=refreshed` and
   `refreshed=true`; otherwise the fully renewable state is `healthy`.
4. No single exit code or boolean is sufficient. Missing/false `token_valid`
   after all retries is `auto_refresh_failed`; inconsistent fields, profile
   mismatch, stale/malformed expiry, or failed diagnostics must fail closed.
5. Do not execute any `dws auth login` command. In particular,
   `dws auth login --no-browser` is interactive OAuth loopback login, not refresh.
   For `auto_refresh_failed` or `needs_manual_auth`, only display the wrapper's
   `dws auth login --device` next action for a one-time user authorization.
6. The wrapper runs profile-pinned `dws doctor --json --timeout 20` only after
   strict auth health passes. Doctor warn with zero fails is allowed; doctor
   fail, command failure, malformed JSON, or unavailable summary returns nonzero.
7. Never read browser cookies, Keychain contents, shell history, environment
   secrets, DingTalk live databases, raw access tokens, or raw refresh tokens.
8. The wrapper exclusively owns reminder dedupe and the active ledger:

   ```text
   /Users/linzezhang/.codex/automations/dws-auth-keepalive-2/memory.md
   ```

   Do not manually append or rewrite memory. The wrapper atomically writes 0600
   state/ledger files, keeps at most 24 sanitized runs, deduplicates the 24-hour
   and final 4-hour refresh-expiry reminders, and never stores corp/user identity,
   token bodies, authorization URLs, user codes, cookies, or secrets. Its
   `notification_required` field is a delivery request for Scheduled final/inbox,
   not proof that an external notification was delivered.
9. Do not modify business repositories, create branches/PRs/issues/worktrees, or
   start any browser/login process.

Final Chinese output must include: progress percentage; completed; incomplete;
status (`healthy|refreshed|auto_refresh_failed|needs_manual_auth|blocked`);
`authenticated`; `token_valid`; `refresh_token_valid`; access expiry; refresh
expiry; profile match; attempts used; doctor summary; reminder window/due;
notification requirement; affected automation risk; estimated remaining
iterations/time/confidence; and next action.
