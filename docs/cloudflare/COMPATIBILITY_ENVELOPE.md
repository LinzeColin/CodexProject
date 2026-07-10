# Cloudflare Compatibility Envelope

- Task ID: `CF-L2-20260710`
- Acceptance ID: `ACC-CF-L2-20260710`
- Run mode: `IMPLEMENT / T3 live delivery and privacy`
- Source contract: `Cloudflare_Compatibility_Envelope_Final_Codex_Task_Package.md`
- Approved delivery path: direct commits to the three repositories' `main` branches; no feature branch or PR

## Objective

Give LinzeHomeHub, Archive/nab, EEI, OpenAIDatabase, PFI, and Serenity-Alipay a truthful, reproducible Cloudflare L2 surface while keeping every private, financial, payment, raw-memory, local-runtime, and production-automation core out of the public distribution.

## Verified baseline

| Repository | Verified `main` HEAD at source lock | Role |
| --- | --- | --- |
| `LinzeColin/CodexProject` | `cfee2cea2f1851cd192406ae70fc0aeef72ed996` | compatibility governance and four project surfaces |
| `LinzeColin/LinzeHomeHub` | `95b5842bd3141026bae9276b9b269761c3422ea7` | gateway and Launch Constellation |
| `LinzeColin/Archive` | `eda7ac6674dee57b864ad03bbadb698bc54453ad` | self-contained `nab` archive surface |

Read-only URL probes on 2026-07-10 Australia/Sydney established:

- `home.linzezhang.com`: public HTTP 200 and Linze Home Hub content.
- `nab.linzezhang.com`: public HTTP 200 and NAB content.
- `memoryatlas.linzezhang.com`: protected Pages deployment evidence verifies unauthenticated Access challenge plus owner-allowlist app and `/memory_atlas.json` loading; the content is online but not anonymously exposed.
- `eei.linzezhang.com`, `pfi.linzezhang.com`, and `serenity.linzezhang.com`: not reachable.
- The local Cloudflare API token is active, but account Workers access returns Cloudflare error `10000`; EEI, PFI and Serenity deploys remain blocked until OAuth or a correctly scoped account token succeeds. MemoryAtlas uses independently verified protected Pages evidence.

## Design decision

Three approaches were evaluated:

1. Publish each existing core application directly. Rejected because EEI depends on production APIs, PFI and Serenity contain financial/local workflows, and OpenAIDatabase contains a private raw/core layer.
2. Put every surface behind Cloudflare Access. Rejected as the sole answer because the approved L2 contract requires a public, no-login adapter.
3. Publish static-first, public-safe adapters while keeping the cores local or Access-protected. Selected because it satisfies the L2 outcome without weakening L1/L3 gates.

The selected architecture is:

```text
private/local core (L1 or future L3)
        |
        | no runtime connection, no secret, no write path
        v
public-safe static adapter or redacted derived snapshot (L2)
        |
        v
Cloudflare Workers Static Assets
        |
        v
verified URL -> deployment manifest -> LinzeHomeHub card
```

## Project boundaries

| Project | L2 surface | Public input | Explicitly excluded |
| --- | --- | --- | --- |
| LinzeHomeHub | existing Vite/Three.js gateway plus Launch Constellation | synchronized deployment facts | private project data, unverified live URLs, L3 dependency for navigation |
| nab | archived static presentation under `Archive/nab` | the existing public presentation | CodexProject root deploy ownership |
| EEI | dependency-free public explorer | illustrative topology only | production database, release/legal/brand claims, scheduler and worker jobs |
| OpenAIDatabase | existing MemoryAtlas UI using `memory_atlas.json` only after scan | redacted derived snapshot | raw archives, private imports, cookies, sessions, secrets, direct writeback |
| PFI | dependency-free redacted public product shell | qualitative illustrative bands and module map | accounts, balances, holdings, trades, brokers, reports, local databases |
| Serenity-Alipay | dependency-free dry-run public cockpit | illustrative Evidence → Review → Decision flow | Alipay data, MooMoo/OpenD, Apple Mail, notifications, trading, launchd |

## UI design extraction

The approved starter template supplies the required content structure. Project-specific art direction is deliberately different:

- EEI: black mineral surface, cyan and oxidized-copper ecosystem map, asymmetrical research-cartography hero, public demo topology.
- PFI: true neutral light field, charcoal type, committed ultramarine with a controlled coral signal, redacted product preview without currency values.
- Serenity: moonlit ink surface, pale jade and electric-blue review orbit, restrained vermilion human-confirmation stop ring.
- MemoryAtlas: preserve its existing mature dark visualization product UI; add only Cloudflare configuration and a quiet HomeHub return path.
- HomeHub: preserve its nocturnal archival WebGL identity; extend project planets into a truthful Launch Constellation instead of introducing a new dashboard.

All new surfaces must work without JavaScript for their primary explanatory content, remain usable below 390 px, preserve visible focus, meet WCAG AA text contrast, and disable non-essential motion under `prefers-reduced-motion`.

## Deployment truth model

Only these terminal values are allowed:

- `deployed_custom_domain_verified`
- `deployed_workers_dev_domain_pending`
- `deploy_ready_auth_blocked`
- `blocked_private_scan`
- `blocked_build_or_dry_run`

`actual_url` is empty until an HTTP smoke check succeeds. A dry run never becomes `deployed`. Access-protected MemoryAtlas may record its verified URL only together with challenge, allowlist, authorized app load and runtime JSON evidence; it is never described as anonymous public access.

## Runtime parameters

| Parameter | Value | Reason |
| --- | --- | --- |
| Wrangler validation version | `4.110.0` | version observed on the new computer and pinned in evidence commands |
| Compatibility date | `2026-07-10` | execution date for new or migrated configs |
| Adapter runtime | static assets only | preserves L2 optionality and removes secret/runtime coupling |
| Persistence | none | no public write path |
| Login | none on public adapter | L2 public contract |
| Private data in dist | `false` | hard release gate |
| HomeHub link priority | verified `liveUrl`, then public GitHub fallback | prevents false-live navigation |

No scoring model, financial formula, ranking model, or automated decision parameter is introduced by this task. The public visual examples are qualitative and illustrative.

## Failure handling and rollback

- Build or private scan failure stops that project's deploy only; other safe work may continue.
- Cloudflare auth failure records `deploy_ready_auth_blocked` and never creates a live claim.
- Custom-domain failure retains a verified workers.dev URL and records the manual domain step.
- Each Worker can be rolled back to the previous deployment through Cloudflare deployment history.
- Source rollback is a normal revert of the bounded commit on `main`; no force push is permitted.
- `nab` is removed from CodexProject only after the Archive copy has an identical SHA256 and a successful dry run.

## Acceptance

`ACC-CF-L2-20260710` passes only when:

1. The compatibility registry validates and every required surface is L2.
2. Required public distributions pass the private scan.
3. Each project has build and Wrangler dry-run evidence.
4. Every `deployed*` result has a verified HTTP URL.
5. HomeHub displays only synchronized truth.
6. `nab` is owned by `Archive/nab`, not the CodexProject root.
7. Three repository `main` branches contain the final facts and are clean.
8. No task-created branch or PR remains open.
