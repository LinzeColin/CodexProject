# Cloudflare Compatibility Envelope — Deployment Evidence

- Task: `CF-L2-20260710`
- Acceptance: `ACC-CF-L2-20260710`
- Evidence time: 2026-07-10 (Australia/Sydney)
- Truth policy: a dry-run is never recorded as a deploy; an existing live domain is explicitly separated from deployment of the current source commit.

| Project | Source commit | Worker | Actual URL | Custom domain | Dry-run | Private scan | Deployment result |
|---|---|---|---|---|---|---|---|
| LinzeHomeHub | `3dc34a3d7fd051c57c7aa8b47a02e767245ce640` | `linze-home-hub` | `https://home.linzezhang.com` | current main deployment HTTP 200; workers.dev also 200 | Wrangler 4.107.0 PASS | PASS | `deployed_custom_domain_verified`; version `2a05edc7-1feb-4856-a869-31f96467e16d` |
| Archive/nab | `10129d6c40883941e0845cb15222a46b7b2e3dc9` | `nab` | `https://nab.linzezhang.com` | current Archive main deployment HTTP 200; workers.dev also 200 | Wrangler 4.110.0 PASS | PASS | `deployed_custom_domain_verified`; version `ef260ee4-ca7e-4783-adc9-d9297a77ecb5` |
| EEI | `b864009c657c6a9cebbf451e30389c1aa5809700` | `codex-eei` | `https://codex-eei.linzezhang35.workers.dev` | custom domain manual step; workers.dev verified | Wrangler 4.110.0 PASS | PASS | `deployed_workers_dev_domain_pending`; version `d84eb7f9-f564-4e0b-b202-d95a86b2b225` |
| OpenAIDatabase / MemoryAtlas | deployed `5a24333eb2afa766f5f7416b877a8a560c5302ab`; Workers-ready source `ffd41fc27322f995a82d5382202dc105493416a5` | `openai-memory-atlas` | `https://memoryatlas.linzezhang.com` | owner-allowlist Access verified on custom, production Pages and preview Pages hostnames | Wrangler 4.110.0 PASS | PASS, including release privacy/accessibility and published-artifact audit | `deployed_custom_domain_verified` (Access protected) |
| PFI | `b864009c657c6a9cebbf451e30389c1aa5809700` | `codex-pfi` | `https://codex-pfi.linzezhang35.workers.dev` | custom domain manual step; workers.dev verified | Wrangler 4.110.0 PASS | PASS | `deployed_workers_dev_domain_pending`; version `c371544d-4184-48be-80a1-3ca23f11b576` |
| Serenity-Alipay | `b864009c657c6a9cebbf451e30389c1aa5809700` | `serenity-alipay` | `https://serenity-alipay.linzezhang35.workers.dev` | custom domain manual step; workers.dev verified | Wrangler 4.110.0 PASS | PASS | `deployed_workers_dev_domain_pending`; version `d7a0a069-9754-4a86-ab37-aa7833352049` |

## Authentication evidence

- The discovered API token and an initial aggregate `workers:write` OAuth token both returned Cloudflare authentication error `10000`; neither failed attempt created deployment evidence.
- A fresh Wrangler OAuth grant requested only `account:read`, `user:read`, `workers_scripts:write`, and `offline_access`. Credentials are encrypted on disk with the encryption key stored in macOS Keychain.
- The dedicated `workers_scripts:write` token successfully deployed EEI, PFI, Serenity-Alipay, HomeHub and Archive/nab. Every returned workers.dev URL was reached; HomeHub and NAB custom domains were also reached.
- Wrangler's unauthenticated `--temporary` route was not used as a final deployment because Cloudflare documents that an unclaimed preview account and its deployments expire after 60 minutes.
- MemoryAtlas continues to use independently committed protected Pages evidence from deployment `82988d29-504a-437e-a8b5-621a59e701af`, verified at `2026-07-10T07:06:03Z`; its owner-allowlist Access boundary was not weakened or migrated.

## Optional owner domain steps

The acceptance is complete on permanent `workers.dev` URLs. Optionally bind and verify `eei.linzezhang.com`, `pfi.linzezhang.com`, and `serenity.linzezhang.com`; until then the registry correctly records `domain_manual_step_required`. Preserve MemoryAtlas owner-allowlist Access if its Pages deployment is ever migrated to Workers. The private EEI, OpenAIDatabase, PFI, and Serenity cores remain out of deployment scope.
