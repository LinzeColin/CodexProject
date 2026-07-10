# Cloudflare Compatibility Envelope — Deployment Evidence

- Task: `CF-L2-20260710`
- Acceptance: `ACC-CF-L2-20260710`
- Evidence time: 2026-07-10 (Australia/Sydney)
- Truth policy: a dry-run is never recorded as a deploy; an existing live domain is explicitly separated from deployment of the current source commit.

| Project | Source commit | Worker | Actual URL | Custom domain | Dry-run | Private scan | Deployment result |
|---|---|---|---|---|---|---|---|
| LinzeHomeHub | `da2fd0fa2f9eb208231bd5abc61da7d1795a1fda` | `linze-home-hub` | `https://home.linzezhang.com` | HTTP 200 existing deployment | Wrangler 4.107.0 PASS | PASS | `deployed_custom_domain_verified`; current commit redeploy blocked by auth |
| Archive/nab | `10129d6c40883941e0845cb15222a46b7b2e3dc9` | `nab` | `https://nab.linzezhang.com` | HTTP 200; live content byte-equivalent to Archive source | Wrangler 4.110.0 PASS | PASS | `deployed_custom_domain_verified`; current commit redeploy evidence blocked by auth |
| EEI | `ffd41fc27322f995a82d5382202dc105493416a5` | `codex-eei` | — | not configured | Wrangler 4.110.0 PASS | PASS | `deploy_ready_auth_blocked` |
| OpenAIDatabase / MemoryAtlas | deployed `5a24333eb2afa766f5f7416b877a8a560c5302ab`; Workers-ready source `ffd41fc27322f995a82d5382202dc105493416a5` | `openai-memory-atlas` | `https://memoryatlas.linzezhang.com` | owner-allowlist Access verified on custom, production Pages and preview Pages hostnames | Wrangler 4.110.0 PASS | PASS, including release privacy/accessibility and published-artifact audit | `deployed_custom_domain_verified` (Access protected) |
| PFI | `ffd41fc27322f995a82d5382202dc105493416a5` | `codex-pfi` | — | not configured | Wrangler 4.110.0 PASS | PASS | `deploy_ready_auth_blocked` |
| Serenity-Alipay | `ffd41fc27322f995a82d5382202dc105493416a5` | `serenity-alipay` | — | not configured | Wrangler 4.110.0 PASS | PASS | `deploy_ready_auth_blocked` |

## Authentication evidence

- The discovered API token verified as active, but Workers deployment returned Cloudflare authentication error `10000`; no deployment was recorded from that attempt.
- Two browser OAuth attempts timed out without an authorization code. The second requested only `account:read`, `user:read`, and `workers:write`, with macOS Keychain storage requested.
- Wrangler's unauthenticated `--temporary` route was not used as a final deployment because Cloudflare documents that an unclaimed preview account and its deployments expire after 60 minutes.
- No new live URL, custom-domain binding, or successful deployment timestamp is claimed for EEI, PFI, or Serenity-Alipay. MemoryAtlas instead uses the independently committed protected Pages evidence from deployment `82988d29-504a-437e-a8b5-621a59e701af`, verified at `2026-07-10T07:06:03Z`.

## Owner action still required

Authorize permanent Wrangler Workers access on this computer, deploy the three blocked L2 surfaces (EEI, PFI and Serenity-Alipay), smoke-check their `workers.dev` URLs, update the deployment manifest and HomeHub cards, then redeploy HomeHub. Preserve MemoryAtlas owner-allowlist Access if its current Pages deployment is migrated to Workers. The private EEI, OpenAIDatabase, PFI, and Serenity cores remain out of deployment scope.
