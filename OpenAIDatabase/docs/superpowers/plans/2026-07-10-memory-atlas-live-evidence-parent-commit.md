# Memory Atlas Live Evidence Parent-Commit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the v1.2 completion audit accept a protected deployment commit followed by exactly one GitHub-portable final-evidence commit, without allowing stale application deployments to pass.

**Architecture:** The live evidence continues to name the exact commit deployed to Cloudflare. The audit accepts either an exact `HEAD` match or a canonical evidence file whose deployed commit is `HEAD^`; in the parent case, every path changed by `HEAD` must belong to a narrow final-delivery record allowlist and the canonical evidence file must be part of that commit. The deployment commit and evidence commit remain local until one final push.

**Tech Stack:** Python 3 standard library, `unittest`, Git CLI, Cloudflare API/Wrangler, existing Memory Atlas audit and installer scripts.

## Global Constraints

- One Final Delivery phase only; do not reopen Stage 0-14 implementation.
- No intermediate GitHub push, branch, or pull request.
- Preserve unrelated local changes and reconcile `origin/main` before final push.
- Do not publish Cloudflare tokens, account IDs, cookies, sessions, or the owner email.
- Keep unauthenticated `memoryatlas.linzezhang.com` behind Cloudflare Access and keep the direct `pages.dev` surface fail closed.
- Final completion requires GitHub `main`, deployed commit evidence, both local app launchers, runtime manifest, and acceptance audits to agree.

---

### Task 1: Parent-Commit Completion Contract

**Files:**
- Modify: `scripts/audit_memory_atlas_goal_completion.py`
- Modify: `tests/test_memory_atlas_goal_completion.py`

**Interfaces:**
- Consumes: `audit_live_evidence(repo_root: Path, evidence_path: Path | None, checks: list[dict[str, str]]) -> bool`
- Produces: `validate_live_git_commit(repo_root: Path, evidence_path: Path, deployed_commit: str) -> tuple[bool, str]`

- [ ] **Step 1: Write failing parent-commit tests**

Add tests that create temporary Git repositories and assert:

```python
self.assertTrue(module.audit_live_evidence(repo_root, evidence_path, checks))
self.assertIn("immediate parent", checks[-1]["evidence"])
```

Also commit `apps/memory-atlas/src/App.tsx` with the evidence and assert rejection, then add a third commit and assert that a grandparent deployment is rejected as stale.

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
python3 -m unittest OpenAIDatabase.tests.test_memory_atlas_goal_completion -v
```

Expected: new parent-commit acceptance test fails because only exact `HEAD` equality is currently supported.

- [ ] **Step 3: Implement the narrow contract**

Add the canonical allowlist:

```python
POST_DEPLOY_RECORD_PATHS = frozenset(
    {
        "docs/MEMORY_ATLAS_DELIVERY_RECORD.md",
        "功能清单.md",
        "开发记录.md",
        "模型参数文件.md",
        "机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json",
        "机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json",
    }
)
```

Implement validation with these exact rules:

```python
if deployed_commit == head:
    return True, "live evidence git commit matches current HEAD"
if deployed_commit != git_output(repo_root, "rev-parse", "HEAD^"):
    return False, "deployed commit must match current HEAD or its immediate parent"
if evidence_relative_path != CANONICAL_LIVE_EVIDENCE_PATH:
    return False, "parent-commit evidence must use the canonical repository path"
changed = set(git_output(repo_root, "diff", "--name-only", "--relative", f"{deployed_commit}..HEAD", "--", ".").splitlines())
if evidence_relative_path not in changed:
    return False, "final evidence commit does not contain the canonical evidence file"
if changed - POST_DEPLOY_RECORD_PATHS:
    return False, f"post-deploy commit contains non-record paths: {sorted(changed - POST_DEPLOY_RECORD_PATHS)}"
return True, "deployed commit is the immediate parent and HEAD only adds final-delivery records"
```

- [ ] **Step 4: Run focused and related tests and confirm GREEN**

Run:

```bash
python3 -m unittest OpenAIDatabase.tests.test_memory_atlas_goal_completion -v
python3 -m unittest OpenAIDatabase.tests.test_memory_atlas_cloudflare_deploy OpenAIDatabase.tests.test_cloudflare_pages_access_preflight -v
```

Expected: all tests pass.

- [ ] **Step 5: Create the local deployable commit without pushing**

Stage only the plan, audit script, and tests:

```bash
git add OpenAIDatabase/docs/superpowers/plans/2026-07-10-memory-atlas-live-evidence-parent-commit.md \
  OpenAIDatabase/scripts/audit_memory_atlas_goal_completion.py \
  OpenAIDatabase/tests/test_memory_atlas_goal_completion.py
git commit -m "Fix Memory Atlas live evidence commit contract"
```

Expected: local `main` is ahead of `origin/main`; no push occurs.

### Task 2: Protected Deployment From the Deployable Commit

**Files:**
- Preserve: `机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json`
- Modify when the builder refreshes real source dates: `data/derived/visualization/memory_atlas.json`
- Generate then clean: `apps/memory-atlas/node_modules`, `apps/memory-atlas/dist`, `.wrangler`

**Interfaces:**
- Consumes: clean deployable Git commit from Task 1 and `~/.config/memory-atlas/cloudflare.env`
- Produces: successful Cloudflare Pages production deployment whose metadata commit hash equals the Task 1 commit

- [ ] **Step 1: Temporarily isolate the pre-existing final-status diff**

```bash
git stash push -m memory-atlas-final-status-before-live-evidence -- \
  OpenAIDatabase/机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json
```

Expected: the tracked tree is clean before the deploy helper runs.

- [ ] **Step 2: Run authorized build, release audits, preflight, and deployment**

```bash
set -a
source "$HOME/.config/memory-atlas/cloudflare.env"
set +a
cd OpenAIDatabase
python3 scripts/deploy_memory_atlas_cloudflare.py --execute
```

Expected: all build/audit commands pass and Wrangler returns a production deployment URL. If the builder refreshes the tracked redacted snapshot, treat this first upload as provisional because its metadata is dirty.

- [ ] **Step 3: Promote any refreshed tracked snapshot and redeploy from a clean commit**

When the tracked snapshot changed, prove it is exactly the audited publish JSON, amend it into the deployable commit, remove only Wrangler's generated cache, and upload the already-audited `dist` again:

```bash
cmp data/derived/visualization/memory_atlas.json apps/memory-atlas/dist/memory_atlas.json
git add data/derived/visualization/memory_atlas.json \
  docs/superpowers/plans/2026-07-10-memory-atlas-live-evidence-parent-commit.md
git commit --amend --no-edit
rm -rf .wrangler
npx wrangler pages deploy apps/memory-atlas/dist --project-name openai-memory-atlas
```

Expected: Cloudflare deployment metadata reports the amended local commit and `commit_dirty=false`.

- [ ] **Step 4: Verify both unauthorized and authorized paths**

Verify API metadata reports the local Task 1 commit, unauthenticated custom-domain requests return the Access challenge, the direct Pages hostname returns fail-closed `403`, and an allowed Chrome identity loads the app plus the `memory_atlas.json` fetch resource.

- [ ] **Step 5: Restore the status diff**

```bash
git stash pop
```

Expected: the original final-status changes are restored with no conflicts and no stash remains.

### Task 3: Canonical Sanitized Live Evidence Commit

**Files:**
- Create: `机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json`
- Modify: `机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json`
- Modify: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- Modify: `功能清单.md`
- Modify: `开发记录.md`
- Modify only if needed for contract consistency: `模型参数文件.md`

**Interfaces:**
- Consumes: verified deployment commit and browser/API evidence from Task 2
- Produces: canonical, secret-free, GitHub-portable operator evidence and final delivery records

- [ ] **Step 1: Generate canonical evidence without publishing the owner email**

Use the existing helper in dry-run evidence mode, overriding only the evidence value:

```bash
set -a
source "$HOME/.config/memory-atlas/cloudflare.env"
set +a
MEMORY_ATLAS_ALLOWED_EMAIL=REDACTED_OWNER_EMAIL_ALLOWLIST_VERIFIED \
python3 scripts/deploy_memory_atlas_cloudflare.py \
  --deployment-url https://memoryatlas.linzezhang.com \
  --write-evidence \
  --evidence-out 机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json \
  --operator Codex \
  --access-challenge-verified \
  --allowed-user-app-load-verified \
  --memory-atlas-json-fetch-verified \
  --published-artifact-audited \
  --no-raw-sensitive-artifacts-verified
```

Expected: evidence names the Task 1 deployed commit and contains no token, account ID, cookie, session, secret, or literal owner email.

- [ ] **Step 2: Update final delivery records with verified facts**

Replace the external-blocked status with completed live Access evidence, retain the historical fail-closed incident as history, and record deployment timestamp, custom hostname, production deployment identity, direct-host `403`, Access challenge, allowed-user load, JSON fetch, and artifact audit.

- [ ] **Step 3: Validate evidence before committing**

```bash
python3 -m json.tool 机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json >/dev/null
python3 scripts/audit_memory_atlas_goal_completion.py \
  --require-local-apps \
  --live-evidence 机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json \
  --require-complete
git diff --check -- .
```

Expected before the evidence commit: `COMPLETE_WITH_OPERATOR_EVIDENCE` through exact `HEAD` deployment equality.

- [ ] **Step 4: Commit only final-delivery record paths**

```bash
git add docs/MEMORY_ATLAS_DELIVERY_RECORD.md 功能清单.md 开发记录.md 模型参数文件.md \
  机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json \
  机器治理/证据与日志/final_delivery/v1_2_final_delivery_cleanup_status.json
git commit -m "Record Memory Atlas protected live delivery evidence"
```

Expected: the deployed commit is `HEAD^`; the second commit contains only allowlisted record paths.

- [ ] **Step 5: Validate the parent-commit model**

Run the same completion audit again. Expected: `COMPLETE_WITH_OPERATOR_EVIDENCE` with evidence that the deployed commit is the immediate parent and `HEAD` only adds final-delivery records.

### Task 4: One Final Main Push, App Reinstall, and Deep Cleanup

**Files:**
- Local install: `/Applications/Memory Atlas.app`
- Local install: `~/Downloads/Memory Atlas.app`
- Runtime manifest: `~/Library/Application Support/OpenAIDatabase/MemoryAtlas/runtime/memory_atlas_build.json`

**Interfaces:**
- Consumes: two validated local commits from Tasks 1 and 3
- Produces: synchronized GitHub `main`, app/runtime entrypoints, final audits, and a clean machine state

- [ ] **Step 1: Reconcile immediately before the only push**

```bash
git fetch origin main
git rev-parse origin/main
```

If `origin/main` advanced, integrate it before pushing, redeploy from the rebased deployable commit, regenerate evidence, and rerun Task 3. Never force push stale deployment evidence.

- [ ] **Step 2: Push both local commits once**

```bash
git push origin main
```

Expected: `HEAD == origin/main`; no other push occurred in this phase.

- [ ] **Step 3: Reinstall app entrypoints from final `HEAD`**

```bash
cd OpenAIDatabase
python3 scripts/install_memory_atlas_app.py
```

Expected: both launcher `INSTALLED_GIT_COMMIT` values and runtime manifest commit equal final `HEAD`.

- [ ] **Step 4: Run final acceptance and real first-path smoke**

```bash
python3 scripts/audit_memory_atlas_acceptance.py --require-local-apps
python3 scripts/audit_memory_atlas_goal_completion.py \
  --require-local-apps \
  --live-evidence 机器治理/证据与日志/final_delivery/memory_atlas_cloudflare_live_evidence.json \
  --require-complete
python3 scripts/atlasctl.py audit
```

Expected: local acceptance passes, goal completion is `COMPLETE_WITH_OPERATOR_EVIDENCE`, and all atlas gates pass.

- [ ] **Step 5: Deep-clean reproducible residue and prove final state**

Remove only `apps/memory-atlas/node_modules`, `apps/memory-atlas/dist`, `apps/memory-atlas/tsconfig.tsbuildinfo`, `.wrangler`, and Memory Atlas `/private/tmp` artifacts. Verify no listener remains on port `4177`, no stash/branch/PR remains, `git status` is clean, `HEAD == origin/main`, and the app/runtime commits still match final `HEAD`.
