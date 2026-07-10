# Cloudflare Compatibility Envelope — Deployment Evidence

- Task: `CF-L2-20260710`
- Acceptance: `ACC-CF-L2-20260710`
- Evidence time: 2026-07-10 (Australia/Sydney)
- Truth policy: a dry-run is never recorded as a deploy; an existing live domain is explicitly separated from deployment of the current source commit.

| Project | Source commit | Worker | Actual URL | Custom domain | Dry-run | Private scan | Deployment result |
|---|---|---|---|---|---|---|---|
| LinzeHomeHub | `3f2b1ee1559c2f049c556b6dff5e3aa86f45b508` | `linze-home-hub` | `https://home.linzezhang.com` | HTTP 200 existing deployment | Wrangler 4.107.0 PASS | PASS | `deployed_custom_domain_verified`; current commit redeploy blocked by auth |
| Archive/nab | `10129d6c40883941e0845cb15222a46b7b2e3dc9` | `nab` | `https://nab.linzezhang.com` | HTTP 200; live content byte-equivalent to Archive source | Wrangler 4.110.0 PASS | PASS | `deployed_custom_domain_verified`; current commit redeploy evidence blocked by auth |
| EEI | `7b017d0a58569eebfcf0d5da81f4bdf346585153` | `codex-eei` | — | not configured | Wrangler 4.110.0 PASS | PASS | `deploy_ready_auth_blocked` |
| OpenAIDatabase / MemoryAtlas | `7b017d0a58569eebfcf0d5da81f4bdf346585153` | `openai-memory-atlas` | — | `memoryatlas.linzezhang.com` is Access-protected, not anonymous public | Wrangler 4.110.0 PASS | PASS, including release privacy/accessibility | `deploy_ready_auth_blocked` |
| PFI | `7b017d0a58569eebfcf0d5da81f4bdf346585153` | `codex-pfi` | — | not configured | Wrangler 4.110.0 PASS | PASS | `deploy_ready_auth_blocked` |
| Serenity-Alipay | `7b017d0a58569eebfcf0d5da81f4bdf346585153` | `serenity-alipay` | — | not configured | Wrangler 4.110.0 PASS | PASS | `deploy_ready_auth_blocked` |

## Authentication evidence

- The discovered API token verified as active, but Workers deployment returned Cloudflare authentication error `10000`; no deployment was recorded from that attempt.
- Two browser OAuth attempts timed out without an authorization code. The second requested only `account:read`, `user:read`, and `workers:write`, with macOS Keychain storage requested.
- Wrangler's unauthenticated `--temporary` route was not used as a final deployment because Cloudflare documents that an unclaimed preview account and its deployments expire after 60 minutes.
- No new live URL, custom-domain binding, or successful deployment timestamp is claimed for EEI, MemoryAtlas, PFI, or Serenity-Alipay.

## Owner action still required

Authorize permanent Wrangler Workers access on this computer, deploy the four blocked L2 surfaces, smoke-check their `workers.dev` URLs, update the deployment manifest and HomeHub cards, then redeploy HomeHub. The private EEI, OpenAIDatabase, PFI, and Serenity cores remain out of deployment scope.
