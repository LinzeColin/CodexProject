# Memory Atlas Cloudflare Pages + Access Runbook

This runbook is for an authorized deployment operator. Do not deploy until the
user explicitly authorizes Cloudflare account/domain writes for this exact app.
必须先取得用户对本 Cloudflare 账号、Pages 项目、hostname 和 Access
allowlist 的明确授权，才可以执行任何会写入 Cloudflare 的命令。

Official references used by this runbook:

- Cloudflare Pages Direct Upload: https://developers.cloudflare.com/pages/get-started/direct-upload/
- Direct Upload with CI: https://developers.cloudflare.com/pages/how-to/use-direct-upload-with-continuous-integration/
- Pages Wrangler configuration: https://developers.cloudflare.com/pages/functions/wrangler-configuration/
- Workers Static Assets: https://developers.cloudflare.com/workers/static-assets/
- Wrangler Pages commands: https://developers.cloudflare.com/workers/wrangler/commands/pages/
- Access self-hosted public app: https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/self-hosted-public-app/
- Access policies: https://developers.cloudflare.com/cloudflare-one/access-controls/policies/

## 1. Local Preflight

Run from the repository root:

```bash
python3 scripts/build_memory_atlas_data.py \
  --database-dir . \
  --output data/derived/visualization/memory_atlas.json

npm ci --prefix apps/memory-atlas
npm run build --prefix apps/memory-atlas

python3 scripts/audit_memory_atlas_release.py \
  --publish-dir apps/memory-atlas/dist

python3 scripts/audit_memory_atlas_acceptance.py \
  --publish-dir apps/memory-atlas/dist

python3 scripts/preflight_cloudflare_pages_access.py \
  --publish-dir apps/memory-atlas/dist

python3 scripts/audit_memory_atlas_goal_completion.py \
  --publish-dir apps/memory-atlas/dist

python3 scripts/deploy_memory_atlas_cloudflare.py
```

Expected result: all scripts print `PASS`. Do not continue if any audit fails.
The goal-completion script should report
`LOCAL_PASS_EXTERNAL_AUTHORIZATION_REQUIRED` until live Cloudflare deployment
and Access verification evidence exists.

## 2. Deployment Authorization Gate

Before running any command that writes to Cloudflare, confirm:

- Cloudflare account ID is known.
- Target Pages project is `openai-memory-atlas`.
- Target hostname is known, either `openai-memory-atlas.pages.dev` or an approved custom domain.
- Allowed user email is known.
- The user explicitly approved this Cloudflare account, project, hostname, and allowlist.

Optional environment check:

```bash
export CLOUDFLARE_ACCOUNT_ID="<account id>"
export CLOUDFLARE_API_TOKEN="<token with Pages and Access permissions>"
export MEMORY_ATLAS_ACCESS_HOSTNAME="<memory-atlas.example.com or pages.dev host>"
export MEMORY_ATLAS_ALLOWED_EMAIL="<allowed user email>"

python3 scripts/preflight_cloudflare_pages_access.py \
  --publish-dir apps/memory-atlas/dist \
  --require-live-env
```

The token must not be committed. Do not store it in `.env` inside the repo.

## 3. Pages Direct Upload

Production uses mode
`pages_direct_upload_with_workers_migration_ready_config`: the helper performs
an explicit Pages Direct Upload with `wrangler pages deploy`. The root
`wrangler.jsonc` is a Workers Static Assets migration-ready config and is not
consumed by this Pages command. Do not run `wrangler deploy` or claim a Workers
migration unless that separate migration is explicitly approved and verified.

Only after the authorization gate:

```bash
export MEMORY_ATLAS_CLOUDFLARE_AUTHORIZED=I_AUTHORIZE_THIS_DEPLOY

python3 scripts/deploy_memory_atlas_cloudflare.py --execute
```

The script follows Cloudflare Direct Upload guidance: prebuilt assets are
uploaded with `npx wrangler pages deploy apps/memory-atlas/dist --project-name
openai-memory-atlas`. Cloudflare documents Direct Upload as uploading prebuilt
assets to Pages, and the Wrangler deploy form as `npx wrangler pages deploy
<BUILD_OUTPUT_DIRECTORY>`.

After deploy, record the deployment URL in the handoff or chat response.
Do not record Cloudflare API tokens, account IDs, cookies, sessions, or private
keys in the repository or in live evidence.

## 4. Access Protection

Protect the deployed Pages hostname with Cloudflare Zero Trust Access:

1. Create a self-hosted public hostname application for Memory Atlas.
2. Use the Pages hostname or approved custom domain as the application domain.
3. Add an allow policy for the approved user email.
4. Keep the default posture deny-by-default.
5. Do not use everyone/bypass selectors.
6. Do not add finance/trading agents unless they only need the redacted graph and still fail closed before broker, payment, or trading actions.

Use the templates in:

- `config/cloudflare/pages_direct_upload.template.json`
- `config/cloudflare/access_self_hosted_application.template.json`

These are operator templates, not secrets and not direct API credentials.

## 5. Post-Deploy Verification

Use a fresh browser session:

1. Open the protected hostname before authentication.
2. Confirm Cloudflare Access blocks direct app content and shows an identity challenge.
3. Authenticate as the allowed user.
4. Confirm the app loads and fetches `/memory_atlas.json`.
5. Confirm browser-visible UI is Chinese-first.
6. Confirm no raw exports, SQLite indexes, JSONL active memory, `.local_keys`, cookies, sessions, auth files, or plaintext secrets are present in the published artifact source.

Then create a sanitized local evidence file from:

```text
config/cloudflare/live_deploy_evidence.template.json
```

Run strict completion audit:

```bash
python3 scripts/audit_memory_atlas_goal_completion.py \
  --publish-dir apps/memory-atlas/dist \
  --live-evidence /path/to/sanitized_live_evidence.json \
  --require-complete
```

## 6. Rollback

Rollback unit:

```text
Cloudflare Pages deployment version + Git commit
```

If a deploy is unsafe:

1. Revert to the previous successful Pages deployment in Cloudflare.
2. Revert or fix the Git commit.
3. Re-run release audit, acceptance audit, and Cloudflare preflight.
4. Deploy again only after explicit authorization if the hostname or access policy changes.
