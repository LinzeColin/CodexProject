# Cloudflare Compatibility Envelope — Final Report

## 1. Decision

- Task: `CF-L2-20260710`
- Acceptance: `ACC-CF-L2-20260710`
- State at handoff: `repo_configured + dry_run_ready + deployment_blocked_by_auth`
- Completion: partial; repository, UI, privacy, dry-run, migration, governance, GitHub and cleanup work is complete, but permanent Cloudflare deployment of EEI, MemoryAtlas, PFI and Serenity-Alipay is not complete.
- Truth rule: no dry-run, protected login page, old live deployment, or expiring temporary preview is represented as deployment of the current source commit.

## 2. Repository commits

| Repository | Immutable source/evidence commit | Meaning |
|---|---|---|
| `LinzeColin/CodexProject` | `9a3b9ae977275f4774e08ae69f61b54f7270b419` | L2 adapters, governance records and auth-blocked deployment evidence base; the report carrier is resolved after clone with `git log -1 --format=%H -- FINAL_ACCEPTANCE_BUNDLE/cloudflare_compatibility_envelope/FINAL_REPORT.md` |
| `LinzeColin/LinzeHomeHub` | `3f2b1ee1559c2f049c556b6dff5e3aa86f45b508` | Five-card Launch Constellation and deploy-ready/live routing |
| `LinzeColin/Archive` | `10129d6c40883941e0845cb15222a46b7b2e3dc9` | Self-contained `nab` source on Archive `main` |

The four CodexProject public-surface implementations are rooted at `7b017d0a58569eebfcf0d5da81f4bdf346585153`; `9a3b9ae9…` binds their blocked deployment evidence and formal governance.

## 3. Deployment results

| Project | Result | Actual URL | Custom domain state | Current-source deploy evidence |
|---|---|---|---|---|
| LinzeHomeHub | `deployed_custom_domain_verified` | `https://home.linzezhang.com` | HTTP 200 existing deployment | current Launch Constellation commit redeploy blocked by auth |
| Archive/nab | `deployed_custom_domain_verified` | `https://nab.linzezhang.com` | HTTP 200; content byte-equivalent to Archive source | Archive source is on remote main; redeploy timestamp not available |
| EEI | `deploy_ready_auth_blocked` | — | not configured | no successful deploy claimed |
| OpenAIDatabase / MemoryAtlas | `deploy_ready_auth_blocked` | — | `memoryatlas.linzezhang.com` returns Cloudflare Access, not anonymous public content | no successful anonymous deployment claimed |
| PFI | `deploy_ready_auth_blocked` | — | not configured | no successful deploy claimed |
| Serenity-Alipay | `deploy_ready_auth_blocked` | — | not configured | no successful deploy claimed |

Machine-readable facts are in `governance/cloudflare/deployments.json` and `urls.json`; the human deployment ledger is `deployments.md`.

## 4. Build, scan, dry-run and UI evidence

Passed:

- Cloudflare compatibility unit tests: 13/13.
- Cloudflare governance unit tests: 3/3.
- Compatibility registry validation: 15 projects.
- Required public distribution scan: EEI, MemoryAtlas, PFI and Serenity-Alipay all passed.
- Wrangler dry-run: HomeHub 4.107.0; Archive/nab, EEI, MemoryAtlas, PFI and Serenity-Alipay 4.110.0.
- HomeHub: `npm ci`, `npm run validate`, `npm run build`, `npm run acceptance:visual`; npm audit reported 0 vulnerabilities. The build retained one pre-existing 2.94 MB chunk warning.
- MemoryAtlas release privacy/accessibility validation passed.
- Desktop 1440×1000 and mobile 390×844 browser QA passed for all four CodexProject surfaces: no horizontal overflow, no visible undersized link targets, and no console warning/error.
- HomeHub visual acceptance covered desktop/mobile, four quality modes, six visual models, keyboard navigation, scroll gravity and five project links.
- `git diff --check` passed before evidence commit.

Executed but not green:

- `python3 scripts/lean_governance.py ci --changed-only --base-ref origin/main` stopped only on ten pre-existing WDA lean-v2 schema errors after all Cloudflare task errors were removed. `git diff --name-only origin/main -- WDA` was empty. Local evidence id: `5dd39049386d`.
- Real HomeHub deploy with the discovered API token returned Cloudflare error `10000`.
- Two OAuth callbacks timed out; the second requested only `account:read`, `user:read`, `workers:write`, and Keychain storage.

Not run because of the stop condition:

- Permanent deploy and public URL smoke checks for EEI, MemoryAtlas, PFI and Serenity-Alipay.
- New custom-domain bindings for those four surfaces.
- Final HomeHub redeploy after public URLs are known.
- Full unrelated repository suites; targeted tests were used to avoid expanding into unchanged projects.

## 5. Security boundary

- EEI publishes an illustrative explorer only; no production graph database, scheduler, legal/brand clearance claim, A209 closure or A210 closure.
- OpenAIDatabase publishes only a redacted derived MemoryAtlas viewer; no raw archive, private import, cookie, session, local database or plaintext secret.
- PFI publishes a qualitative redacted shell; no account, portfolio value, broker credential, order, payment or private report.
- Serenity-Alipay is read-only and illustrative; no Alipay, MooMoo/OpenD, Apple Mail, notification, launchd, trade or external-account action.
- Public distributions passed the private-data scanner. No hard-coded token, password, private key or local absolute path was accepted.

## 6. Migration and HomeHub

- `nab.html` and the root Wrangler config were removed from CodexProject; CodexProject root is again a governance hub.
- `Archive/nab` is self-contained and deployable; its source is on Archive remote `main`.
- HomeHub contains exactly five whole-card links: EEI, OpenAIDatabase / MemoryAtlas, PFI, Serenity-Alipay and NAB IR Roadshow.
- HomeHub fills `liveUrl` only for the verified NAB surface; blocked projects use GitHub source fallbacks and remain `Deploy-ready`.

## 7. GitHub and branch hygiene

- GitHub connector audit returned zero open pull requests for CodexProject, LinzeHomeHub and Archive.
- Each local repository has only local branch `main`.
- LinzeHomeHub and Archive have only remote branch `main`.
- CodexProject also has protected archive branches `macdata-airM2` and `macdata-proM2`. Repository tests and governance explicitly classify `macdata-proM2` as protected and not a managed temporary branch; neither branch was created by this task or deleted.
- No task branch or task PR was created.

## 8. Local cleanup

- Stopped four local QA servers and finalized the in-app browser QA tabs.
- Removed task-scoped `node_modules`, `dist`, `.wrangler`, `.vite`, HomeHub visual artifacts, Playwright output, screenshots and temporary test output.
- Preserved tracked EEI evidence and all user-home, OS Keychain and Wrangler credential locations.

## 9. Exact continuation on an authorized computer

1. Clone or fast-forward the three repositories and verify the commits above.
2. Run `npx wrangler login --scopes account:read --scopes user:read --scopes workers:write --use-keyring`, then confirm `npx wrangler whoami`.
3. Reinstall and build each safe surface; rerun its private scan and Wrangler dry-run.
4. Deploy EEI, MemoryAtlas, PFI and Serenity-Alipay serially. Smoke-check every returned `workers.dev` URL before writing it to the manifests.
5. Update `governance/cloudflare/deployments.json`, `urls.json`, `deployments.md`, and HomeHub `src/data/projects.json`; rebuild, visually accept and deploy HomeHub last.
6. Re-run the targeted validators, commit directly to `main`, push all affected repositories, verify remote SHA equality, re-audit open PRs/temporary branches, and clean regenerated caches.

Do not use an unclaimed `wrangler deploy --temporary` preview as completion evidence: Cloudflare documents that the temporary account and deployments are deleted after 60 minutes unless claimed.
