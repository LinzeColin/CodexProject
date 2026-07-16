# PFI v0.2.5 Stage 0 Phase 0.2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze the auditable v0.2.5 active requirements, historical disposition, product boundaries, and one-Phase execution policy for `S0-P2-T1..T4`, then prove `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT` through one exact twenty-file local implementation commit and an external post-commit governance attestation.

**Architecture:** One normalized JSON contract is the machine authority; three focused Markdown policies explain history, boundaries, and execution. Twelve existing PFI governance companions make the eight Roadmap artifacts auditable without changing runtime code, model/formula/parameter values, private data, App entries, or remote state. A selective non-private shadow worktree supplies missing sparse-checkout validator inputs while keeping the canonical PFI worktree and real data untouched.

**Tech Stack:** zsh on macOS, Git, `apply_patch`, JSON/Markdown/YAML/CSV/JSONL, `jq`, Node.js CommonJS assertions, Python 3.12 project virtualenv, `jsonschema`, ZIP streaming, and CodexProject Lean Governance v2.

## Global Constraints

- Execute only `PFI v0.2.5 Stage 0 / Phase 0.2`; do not enter Phase 0.3, whole-Stage review, Stage 1, or any later Phase.
- Roadmap tasks are exactly `S0-P2-T1`, `S0-P2-T2`, `S0-P2-T3`, and `S0-P2-T4`; the only Acceptance is `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT`.
- The implementation diff is exactly eight new core artifacts plus twelve modified governance companions. The design and this plan are committed separately and are not part of that twenty-file diff.
- Use the user approval recorded on 2026-07-11 for override `PFI-V025-S0-GOVERNANCE-COMPANIONS`; do not infer future evidence-based acceptance before checks run.
- Do not modify UI, routes, runtime code, tests, schemas, README, HANDOFF, VERSION, `功能清单.md`, `开发记录.md`, `模型参数文件.md`, `project.yaml`, `roadmap.yaml`, `DELIVERY_PLAN.md`, or `ASSURANCE_STATUS.yaml`.
- Do not read financial rows or values, launch services, open browsers, run Apps, touch SQLite, mutate `PFI/data`, expand `MetaDatabase/PFI`, install dependencies, update refs through ordinary fetch, rebase/merge, push, or install/replace any App entry. The only network-object exception is the exact advertised live-main SHA hydration defined in Task 1 Step 2 and Task 7 Step 4; it must use `--no-write-fetch-head --no-tags` and prove the complete ref snapshot unchanged.
- Preserve current model/formula/parameter values and versions. Governance registry edits may record Phase applicability and evidence only; no runtime financial/model claim is created.
- Existing v0.2 records remain historical evidence. The active v0.2.5 contract, not legacy registry labels or old completion prose, controls future development.
- `development_events.jsonl` is append-only. Its Phase record uses the plan/base commit and `approved_pending_postcommit_attestation`; it never claims its own future commit SHA.
- The twenty implementation files form one atomic commit because evidence, event append, traceability, and companion sync must describe the same staged tree. This Phase-specific atomicity overrides the ordinary frequent-commit preference.
- Every command records its real exit code. A missing source, failed check, private-value exposure, unexplained drift, or needed twenty-first file prevents candidate pass.
- Local commits are allowed. No GitHub upload or canonical App reinstall occurs before the Stage 12 final transaction.

---

## Approval and Run Contract

| Field | Frozen value |
|---|---|
| Approval | User: `批准，再完成前不要再block，全部都同意` on 2026-07-11 |
| Design | `PFI/docs/pfi_v025/stage_0/PHASE_0_2_DESIGN.md` |
| Design commit | `e117583df788d7a9043cce74ea984b1144d10008` before approval-status sync |
| Roadmap SHA-256 | `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` |
| Task Pack SHA-256 | `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` |
| Iteration ID | `ITER-20260711-PFI-V025-S0-P02` |
| Contract ID | `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS` |
| Acceptance | `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT` |
| Risk tier | `T2` |
| Maximum run scope | one Phase |

`$PHASE_BASE` is the clean commit containing this plan and the approved design-status sync. Capture it after the plan commit; do not hardcode a future SHA into this file.

## File Map

**Read only:**

- `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md`
- `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip`
- `PFI/docs/pfi_v025/stage_0/PHASE_0_2_DESIGN.md`
- `PFI/web/app/routes.js`, `PFI/web/app/shell.js`, `PFI/web/index.html`
- root and PFI governance validators/contracts needed by the selective shadow validation

**Create — eight Roadmap core artifacts:**

1. `PFI/config/pfi_v025_active_requirements.json`
2. `PFI/docs/pfi_v025/stage_0/history_deprecation.md`
3. `PFI/docs/pfi_v025/stage_0/scope_boundary.md`
4. `PFI/docs/pfi_v025/stage_0/run_contract.md`
5. `PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json`
6. `PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log`
7. `PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt`
8. `PFI/reports/pfi_v025/stage_0/phase_0_2/risk_and_rollback.md`

**Modify — twelve approved governance companions:**

1. `PFI/docs/governance/MODEL_SPEC.md`
2. `PFI/docs/governance/model_registry.yaml`
3. `PFI/docs/governance/formula_registry.yaml`
4. `PFI/docs/governance/parameter_registry.csv`
5. `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
6. `PFI/docs/governance/development_events.jsonl`
7. `PFI/docs/governance/delivery_tasks.yaml`
8. `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
9. `PFI/docs/governance/VERSION_MATRIX.yaml`
10. `PFI/docs/governance/STATUS.md`
11. `PFI/docs/governance/OWNER_STATUS.md`
12. `PFI/CHANGELOG.md`

**Explicitly not modified:** every other tracked path and every user/runtime/data/App path.

---

### Task 1: Freeze inputs, approval, base, and the exact twenty-file boundary

**Files:**

- Read: the three approved source/spec artifacts and current Git metadata
- Create later: `PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log`

**Interfaces:**

- Consumes: clean `codex/pfi`, plan commit, `origin/main`, live main, pinned source files.
- Produces: `$PHASE_BASE`, source hashes, live-remote classification, and exact allowed-path array consumed by every later task.

- [ ] **Step 1: Capture the clean Phase base and repository identity**

Run:

```bash
set -euo pipefail
export PHASE_BASE="$(git rev-parse HEAD)"
pwd
git rev-parse --show-toplevel
git branch --show-current
git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}'
git remote get-url origin
git rev-parse "$PHASE_BASE"
git rev-parse origin/main
git ls-remote origin refs/heads/main
git status --porcelain=v1 --untracked-files=all
test "$(git branch --show-current)" = "codex/pfi"
test "$(git rev-parse --abbrev-ref --symbolic-full-name '@{upstream}')" = "origin/main"
test "$(git remote get-url origin)" = "git@github.com:LinzeColin/CodexProject.git"
test -z "$(git status --porcelain=v1 --untracked-files=all)"
```

Expected: canonical PFI worktree/root, branch `codex/pfi`, upstream `origin/main`, the configured GitHub remote, and empty porcelain status. Live main may be ahead only through non-PFI commits; an unconfirmable ref or dirty tree stops the run.

- [ ] **Step 2: Prove live-remote drift does not touch PFI**

Use the contemporaneous advertised SHA. If the commit object is absent locally, hydrate only that exact advertised object without writing `FETCH_HEAD`, tags, tracking refs or any other ref; prove the complete ref snapshot is unchanged before continuing:

```bash
set -euo pipefail
export LIVE_MAIN="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test -n "$LIVE_MAIN"
INITIAL_HYDRATED=false
if ! GIT_NO_LAZY_FETCH=1 git cat-file -e "$LIVE_MAIN^{commit}" 2>/dev/null; then
  INITIAL_HYDRATED=true
  REFS_BEFORE="$(git for-each-ref --format='%(refname) %(objectname)')"
  FETCH_HEAD_PATH="$(git rev-parse --git-path FETCH_HEAD)"
  if [ -e "$FETCH_HEAD_PATH" ]; then
    FETCH_HEAD_STATE=present
    FETCH_HEAD_BEFORE="$(openssl dgst -sha256 "$FETCH_HEAD_PATH" | awk '{print $NF}')"
  else
    FETCH_HEAD_STATE=missing
  fi
  SHALLOW_PATH="$(git rev-parse --git-path shallow)"
  if [ -e "$SHALLOW_PATH" ]; then
    SHALLOW_STATE=present
    SHALLOW_BEFORE="$(openssl dgst -sha256 "$SHALLOW_PATH" | awk '{print $NF}')"
  else
    SHALLOW_STATE=missing
  fi
  GIT_TERMINAL_PROMPT=0 git -c maintenance.auto=false -c fetch.writeCommitGraph=false -c fetch.recurseSubmodules=false fetch \
    --no-auto-maintenance --no-write-commit-graph --no-recurse-submodules --no-prune --no-prune-tags \
    --no-write-fetch-head --no-tags origin "$LIVE_MAIN"
  REFS_AFTER="$(git for-each-ref --format='%(refname) %(objectname)')"
  test "$REFS_AFTER" = "$REFS_BEFORE"
  if [ "$FETCH_HEAD_STATE" = present ]; then
    test "$(openssl dgst -sha256 "$FETCH_HEAD_PATH" | awk '{print $NF}')" = "$FETCH_HEAD_BEFORE"
  else
    test ! -e "$FETCH_HEAD_PATH"
  fi
  if [ "$SHALLOW_STATE" = present ]; then
    test "$(openssl dgst -sha256 "$SHALLOW_PATH" | awk '{print $NF}')" = "$SHALLOW_BEFORE"
  else
    test ! -e "$SHALLOW_PATH"
  fi
fi
GIT_NO_LAZY_FETCH=1 git cat-file -e "$LIVE_MAIN^{commit}"
export REMOTE_BASE="$(GIT_NO_LAZY_FETCH=1 git merge-base "$PHASE_BASE" "$LIVE_MAIN")"
GIT_NO_LAZY_FETCH=1 git diff --quiet "$REMOTE_BASE..$LIVE_MAIN" -- PFI
GIT_NO_LAZY_FETCH=1 git log --left-right --oneline --max-count=12 "$PHASE_BASE...$LIVE_MAIN"
printf 'initial_remote_object_hydration_performed=%s\n' "$INITIAL_HYDRATED"
```

Expected: object hydration is skipped when unnecessary; otherwise only the advertised object graph is added and the before/after complete ref snapshots are identical. `git cat-file`, merge-base, and PFI subtree diff all exit `0`; remote-only commits are unrelated-project changes. Any ref mutation or PFI path on the remote side stops before writing Phase artifacts.

- [ ] **Step 3: Re-hash and integrity-check the pinned sources**

Run:

```bash
openssl dgst -sha256 \
  /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md \
  /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
unzip -t /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip
```

Expected: the two hashes frozen above and ZIP integrity success. Do not require the external Roadmap and ZIP `ROADMAP_COPY.md` byte hashes to match; their only known difference is a leading blank line.

- [ ] **Step 4: Prove the eight core artifacts do not already exist and the twelve companions do**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path

core = [
    "PFI/config/pfi_v025_active_requirements.json",
    "PFI/docs/pfi_v025/stage_0/history_deprecation.md",
    "PFI/docs/pfi_v025/stage_0/scope_boundary.md",
    "PFI/docs/pfi_v025/stage_0/run_contract.md",
    "PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json",
    "PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log",
    "PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt",
    "PFI/reports/pfi_v025/stage_0/phase_0_2/risk_and_rollback.md",
]
companions = [
    "PFI/docs/governance/MODEL_SPEC.md",
    "PFI/docs/governance/model_registry.yaml",
    "PFI/docs/governance/formula_registry.yaml",
    "PFI/docs/governance/parameter_registry.csv",
    "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
    "PFI/docs/governance/development_events.jsonl",
    "PFI/docs/governance/delivery_tasks.yaml",
    "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
    "PFI/docs/governance/VERSION_MATRIX.yaml",
    "PFI/docs/governance/STATUS.md",
    "PFI/docs/governance/OWNER_STATUS.md",
    "PFI/CHANGELOG.md",
]
assert all(not Path(path).exists() for path in core), "core artifact unexpectedly exists"
assert all(Path(path).is_file() for path in companions), "governance companion missing"
print("phase_scope_precondition=pass|core_new=8|companions_existing=12")
PY
```

Expected: exactly `phase_scope_precondition=pass|core_new=8|companions_existing=12`.

- [ ] **Step 5: Capture a metadata-only no-side-effect baseline**

Run before the first Phase artifact write. The fingerprint reads names and metadata only; it never opens financial/App file contents or emits individual paths:

```bash
set -euo pipefail
export RUN_GUARD_ROOT="/private/tmp/pfi-v025-s0p02-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
case "$RUN_GUARD_ROOT" in
  /private/tmp/pfi-v025-s0p02-guard-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) exit 2 ;;
esac
test ! -e "$RUN_GUARD_ROOT"
mkdir -m 700 "$RUN_GUARD_ROOT"
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$RUN_GUARD_ROOT/before.json" <<'PY'
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

output = Path(sys.argv[1])
root = Path.cwd()
targets = {
    "user_pfi": Path.home() / ".pfi",
    "applications_app": Path("/Applications/PFI.app"),
    "desktop_app": Path.home() / "Desktop/PFI.app",
    "downloads_app": Path.home() / "Downloads/PFI.app",
    "repo_data": root / "PFI/data",
    "repo_metadatabase": root / "PFI/MetaDatabase",
}

def fingerprint(path):
    digest = hashlib.sha256()
    count = 0
    if not path.exists() and not path.is_symlink():
        return {"state": "missing", "entry_count": 0, "metadata_sha256": hashlib.sha256(b"missing").hexdigest()}
    pending = [path]
    while pending:
        current = pending.pop()
        st = current.lstat()
        rel = "." if current == path else current.relative_to(path).as_posix()
        payload = [rel, str(stat.S_IFMT(st.st_mode)), str(st.st_mode & 0o7777), str(st.st_size), str(st.st_mtime_ns)]
        if current.is_symlink():
            payload.append(os.readlink(current))
        digest.update("\0".join(payload).encode("utf-8", "surrogateescape"))
        count += 1
        if current.is_dir() and not current.is_symlink():
            pending.extend(sorted(current.iterdir(), reverse=True))
    return {"state": "present", "entry_count": count, "metadata_sha256": digest.hexdigest()}

result = {label: fingerprint(path) for label, path in targets.items()}
output.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
print("no_side_effect_baseline=" + hashlib.sha256(output.read_bytes()).hexdigest())
PY
```

Expected: one aggregate baseline hash and a guarded temporary `before.json`. Keep `RUN_GUARD_ROOT` for the post-commit comparison; never add it to Git or copy its target contents.

---

### Task 2: Create the machine Active Requirements contract

**Files:**

- Create: `PFI/config/pfi_v025_active_requirements.json`

**Interfaces:**

- Consumes: pinned Roadmap/Task Pack, approved design, verified current route module facts.
- Produces: `PFIV025ActiveRequirementsV1`, consumed by the three policies, evidence, governance traceability, and all later v0.2.5 work.

- [ ] **Step 1: Run the failing existence/identity assertion**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import json
from pathlib import Path
p = Path("PFI/config/pfi_v025_active_requirements.json")
assert p.is_file(), "active requirements missing"
d = json.loads(p.read_text(encoding="utf-8"))
assert d["schema"] == "PFIV025ActiveRequirementsV1"
PY
```

Expected before implementation: non-zero with `AssertionError: active requirements missing`.

- [ ] **Step 2: Create the JSON with the exact sixteen-key contract**

Use `apply_patch`. The root key order and values are mandatory:

```json
{
  "schema": "PFIV025ActiveRequirementsV1",
  "contract_id": "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS",
  "version": "v0.2.5",
  "authority_order": [
    "latest_explicit_user_decision",
    "pinned_v025_task_pack_and_roadmap",
    "verified_current_repository_runtime_app_database_test_evidence",
    "non_conflicting_classified_history",
    "historical_completion_claims_have_no_independent_authority"
  ],
  "source_hashes": {
    "roadmap_sha256": "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b",
    "task_pack_sha256": "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
  },
  "official_nav": ["首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与上传", "建议与复盘", "报告与洞察", "市场与研究", "设置"],
  "navigation_policy": {},
  "product_boundaries": {},
  "experience_policy": {},
  "data_policy": {},
  "financial_policy": {},
  "retained_business_rules": {},
  "execution_policy": {},
  "delivery_policy": {},
  "blocking_conflicts": {},
  "policy_overrides": []
}
```

Populate the empty structures with the exact typed values in Steps 3-7; do not add a seventeenth root key.

- [ ] **Step 3: Populate target and verified-current navigation separately**

`navigation_policy` must contain:

```json
{
  "target_primary_routes": {
    "首页总览": "/overview",
    "账户与资产": "/accounts",
    "账本流水": "/ledger",
    "投资管理": "/investment",
    "消费管理": "/consumption",
    "数据源与上传": "/data",
    "建议与复盘": "/review",
    "报告与洞察": "/reports",
    "市场与研究": "/market-research",
    "设置": "/settings"
  },
  "target_compatibility_aliases": {
    "/home": "/overview",
    "/market": "/market-research/market",
    "/research": "/market-research/research",
    "/holdings": "/investment/holdings",
    "/strategy-lab": "/market-research/strategy-lab",
    "/investment/strategy-lab": "/market-research/strategy-lab",
    "/data-system": "/settings/data-system"
  },
  "verified_current_primary_routes": {},
  "verified_current_declared_aliases": {},
  "verified_current_shell_compatibility_inputs": {},
  "verified_current_workspace_bindings": ["home", "accounts", "ledger", "investment", "consumption", "sync", "recommendations", "insights", "market_research", "settings"],
  "current_gap_status": "blocked_pending_S6-P1",
  "resolution_tasks": ["S6-P1-T1", "S6-P1-T2", "S6-P1-T3"]
}
```

Fill the current maps from `routes.js` and `shell.js` exactly as verified by Task 5 Step 6. The current primary map uses `/home` and `/sources-upload`; the six declared aliases and nine explicit shell compatibility inputs retain their current query-based destinations. Never rewrite them as target-complete.

- [ ] **Step 4: Populate product, experience, data, and financial boundaries**

Required invariants:

```text
product_boundaries: pfi_only=true; alpha_read_only=true; no_ralpha=true;
  exclude_serenity_alipay=true; single_active_product=true; single_active_ui=true;
  Alpha Context fields exactly 8; required metadata exactly schema_version/as_of/
  source_or_read_model_hash/privacy_classification; no writeback; no auto trading/payment.
experience_policy: visual_direction exactly bright/high-quality/restrained/zh-CN;
  distinct secondary pages; real URL/history/
  deep-link/refresh/focus/error; Settings-only feedback; motion_user_disable_supported=true;
  haptics_user_disable_supported=true; unsupported_feedback_silently_degrades=true;
  reduced_motion_respected=true.
data_policy: real_financial_data_only=true; no_financial_fallback=true;
  missing_real_input_results=[blocked,not_run]; no_non_ready_financial_zero=true;
  every metric requires source/coverage/as_of/formula/parameter_hash/read_model_hash;
  private_values_in_git_allowed=false; private_values_in_evidence_allowed=false;
  metric states exactly ready/confirmed_zero/partial_coverage/source_missing/not_loaded/
  path_error/parse_failed/outdated_snapshot/permission_denied/calculation_failed/
  reconciliation_failed/valuation_missing/filtered_empty; confirmed_zero requires source,
  record_count, coverage, as_of, formula, read_model_hash and confidence/coverage evidence.
financial_policy: primary_currency=CNY; aud_cny_direction="1 AUD = X CNY";
  example_rate=4.81 with example_only=true and production_hardcode_allowed=false;
  fx_refresh_local_time=06:00; fx_timezone=Australia/Sydney; ordinary_run_network_dependency=false;
  prior valid publication day before 06:00/weekends/NSW holidays; three exact outflow views
  with outflow_views_share_sources=true;
  investment funding/purchases may enter total outflow but are neither living consumption
  nor net-worth loss;
  source dedup + Economic Event lineage + formula rules prevent double counting.
```

- [ ] **Step 5: Populate retained business rules as typed values**

Required values:

```json
{
  "source_account_roles": {"hardcoded": false, "multiple_roles": true, "effective_periods": true},
  "category_limits": {"l1_max": 12, "l2_per_l1_max": 5, "l2_total_max": 50, "exactly_one_primary_category": true},
  "tags": {"default_and_custom": true, "create": true, "update": true, "disable": true, "history": true, "persistence": true, "view_filters": true},
  "classification_confidence": {"field_completeness": 30, "amount_direction": 10, "rule_match": 20, "merchant_counterparty": 15, "interconnection": 15, "historical_consistency": 10, "threshold": 70},
  "cashflow_windows_days": [7, 21, 30, 60, 90, 180, 360],
  "formal_secondary_pages": ["Parameter Center", "Interconnection Map"]
}
```

- [ ] **Step 6: Populate execution and delivery policies**

Use exact types and gates:

```text
execution_policy.max_phases_per_run = integer 1
stage_requires_user_acceptance = true
automatic_phase_advancement = false
automatic_stage_advancement = false
stage_requires_independent_review = true
stage_findings_must_be_remediated_before_acceptance = true
stage_requires_rereview_pass = true
stage_sequence = whole_stage_fresh_review -> findings_remediation -> rereview_pass -> explicit_acceptance -> next_stage
completion_proof_disallowed = [documentation_only, toast_or_marker, string_only_test,
  fake_screenshot, screenshot_path_only, single_number_only]
review_findings_and_evidence_persistence_allowed = true
private_chain_of_thought_or_internal_review_transcript_persistence_allowed = false
delivery_policy.local_phase_commits_allowed = true
per_stage_github_main_upload_allowed = false
per_stage_app_reinstall_allowed = false
stage_1_validation_mode = isolated_candidate_app
stage_1_candidate_source = PFI/macos/PFI.app
stage_1_finder_launch_allowed = true
stage_1_canonical_entry_mutation_allowed = false
stage_1_temp_root_policy = run_created_mktemp_not_canonical_entry
stage_1_candidate_path_template = $STAGE1_TEMP_ROOT/PFI.app
stage_1_isolated_environment = [HOME, PFI_DATA_HOME, browser_profile, runtime_cache, ports]
stage_1_required_binding_hashes = [source_tree_hash, copied_bundle_hash, checkout_binding_hash]
stage_1_required_identity_match = [frontend, backend, manifest, asset, commit]
stage_1_canonical_entry_before_after_hash_required = true
stage_1_launchservices_registration_and_cleanup_recorded = true
stage_1_candidate_disposable_and_never_final_promoted = true
final_delivery_stage = 12
final_candidate_fresh_rebuild_from_release_content_commit = true
final_candidate_hashes_required = [build_hash, asset_hash, commit_hash]
final_commit_identities = [release_content_commit, acceptance_candidate_commit, final_record_commit]
final_app_reinstall_required = true
final_app_reinstall_gate = S12-P2-T1
canonical_app_backup_before_promotion_required = true
failed_promotion_restores_backup = true
automatic_install_retry_allowed = false
final_github_main_upload_required = true
final_github_main_upload_gate = after_S12-P3-T4_explicit_acceptance
expected_remote_main_sha_required = true
final_strict_fast_forward_required = true
post_release_content_freeze_rebase_merge_runtime_content_commit_allowed = false
final_push_count = 1
final_push_from_ref = expected_remote_main_sha
final_push_to_commit_identity = final_record_commit
final_remote_parity_verification_required = true
final_independent_evidence_gates = [remote_parity, installed_app_identity, local_owner_view_consistency]
force_push_allowed = false
pre_push_remote_drift_result = blocked_restore_saved_canonical_app_require_new_explicit_decision
post_push_remote_updated_but_parity_failed_result = freeze_remote_local_app_no_auto_rollback_or_rewrite
```

The three commit identities are not interchangeable: `release_content_commit` freezes runtime content and builds the fresh final candidate; `acceptance_candidate_commit` binds the pending request/evidence without runtime changes; `final_record_commit` appends the accepted record and never claims its own SHA. External attestation binds the last SHA, accepted content hashes, and push/parity result.

- [ ] **Step 7: Populate the seven conflicts and two approved overrides**

Conflict IDs are stable and exhaustive:

```text
PFI-V025-CONFLICT-OWNER-VIEWS
PFI-V025-CONFLICT-RELEASE-IDENTITY
PFI-V025-CONFLICT-APP-IDENTITY
PFI-V025-CONFLICT-RUNTIME-LISTENERS
PFI-V025-CONFLICT-STALE-ROUTE-MARKERS
PFI-V025-CONFLICT-ROUTE-TARGET-GAP
PFI-V025-CONFLICT-GOVERNANCE-SCOPE
```

Each item contains `requirement_disposition`, `fact_level`, optional `owner_evidence_state`, `status`, `evidence_ref`, `affected_surfaces`, `prohibited_claims`, `blocks_phase_0_2_candidate`, and `resolution_tasks`. Items 1-6 remain current blockers but do not fail the contract freeze. Item 7 is `approved_pending_validation` and still blocks until the post-commit attestation resolves the approved override externally.

All seven use `requirement_disposition="BLOCKING_CURRENT_CONFLICT"`. Their exact resolution routes, in the same ordered ID sequence, are:

```json
{
  "PFI-V025-CONFLICT-OWNER-VIEWS": ["S0-P3-T1", "S12-P3-T1"],
  "PFI-V025-CONFLICT-RELEASE-IDENTITY": ["S1-P1-T1", "S12-P3-T1"],
  "PFI-V025-CONFLICT-APP-IDENTITY": ["S12-P2-T1"],
  "PFI-V025-CONFLICT-RUNTIME-LISTENERS": ["S1-P3-T2", "S12-P2-T2"],
  "PFI-V025-CONFLICT-STALE-ROUTE-MARKERS": ["S1-P1-T1", "S6-P1-T1", "S6-P1-T2", "S6-P1-T3", "S12-P3-T1"],
  "PFI-V025-CONFLICT-ROUTE-TARGET-GAP": ["S6-P1-T1", "S6-P1-T2", "S6-P1-T3"],
  "PFI-V025-CONFLICT-GOVERNANCE-SCOPE": ["S0-P3-T1"]
}
```

The override IDs are:

```text
PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE
PFI-V025-S0-GOVERNANCE-COMPANIONS
```

Both records contain `authority="latest_user_decision"`, source contract, original action, status, effective rule, replacement gate, and evidence reference. The Stage 1 record supersedes canonical installation in `S1-P3-T1/T3`; the governance record authorizes only the exact twelve companions.

Use these exact override records; they are part of the typed contract rather than prose-only guidance:

```json
[
  {
    "override_id": "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE",
    "authority": "latest_user_decision",
    "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:S1-P3-T1,S1-P3-T3",
    "original_action": "canonical_app_install_and_entry_replacement_in_stage_1",
    "status": "superseded",
    "effective_rule": "stage_1_uses_isolated_disposable_candidate_without_canonical_entry_mutation",
    "replacement_gate": "canonical_install_only_at_S12-P2-T1_after_stage_12_preconditions",
    "evidence_ref": "PFI/docs/pfi_v025/stage_0/run_contract.md#approved-policy-overrides"
  },
  {
    "override_id": "PFI-V025-S0-GOVERNANCE-COMPANIONS",
    "authority": "latest_user_decision",
    "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:Stage_0_allowed_files",
    "original_action": "stage_0_phase_0_2_writes_limited_to_eight_core_artifacts",
    "status": "superseded",
    "effective_rule": "phase_0_2_allows_exact_eight_core_artifacts_plus_twelve_named_governance_companions",
    "replacement_gate": "exact_twenty_path_ledger_plus_sparse_aware_preflight_and_postcommit_attestation",
    "evidence_ref": "PFI/docs/pfi_v025/stage_0/scope_boundary.md#approved-governance-companion-override"
  }
]
```

---

### Task 3: Create the three human policy artifacts

**Files:**

- Create: `PFI/docs/pfi_v025/stage_0/history_deprecation.md`
- Create: `PFI/docs/pfi_v025/stage_0/scope_boundary.md`
- Create: `PFI/docs/pfi_v025/stage_0/run_contract.md`

**Interfaces:**

- Consumes: the Active Requirements contract and approved design.
- Produces: human-auditable disposition, boundary, and run rules that must agree with the machine contract.

- [ ] **Step 1: Run the failing policy existence assertion**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
from pathlib import Path
paths = [
    Path("PFI/docs/pfi_v025/stage_0/history_deprecation.md"),
    Path("PFI/docs/pfi_v025/stage_0/scope_boundary.md"),
    Path("PFI/docs/pfi_v025/stage_0/run_contract.md"),
]
assert all(path.is_file() for path in paths), "Phase 0.2 human policy missing"
PY
```

Expected before implementation: non-zero with `AssertionError: Phase 0.2 human policy missing`.

- [ ] **Step 2: Create `history_deprecation.md` as a decision table**

Use `apply_patch`. Every row has `item_id`, `historical_rule_or_class`, `requirement_disposition`, `fact_level`, `owner_evidence_state`, `evidence_ref`, `prohibited_use`, `active_replacement_or_retained_principle`, and `resolution_task`.

Required row IDs:

```text
HIST-NAV-COUNT-06
HIST-NAV-COUNT-08
HIST-NAV-COUNT-09
HIST-NAV-COUNT-15
HIST-NAV-COUNT-16
HIST-MARKET-PRIMARY-BAN
HIST-ALIASES-AS-PRIMARY
HIST-DARK-AI-CONSOLE
HIST-TASKPACK-LONGPAGE-PHONE-MOCKUP
HIST-OLD-CLOSEOUT-CLAIMS
HIST-PFI-OS-SECOND-ROOT
HIST-SIDE-REVIEW-HTML
HIST-FAKE-FINANCIAL-ACCEPTANCE
HIST-FAILURE-EVIDENCE
ARCH-SINGLE-UI-AND-REAL-RUNTIME
ARCH-IMMUTABLE-RAW-READMODEL-PROVENANCE
ARCH-DURABLE-OPS-BACKUP-RESTORE
ARCH-DETERMINISTIC-CORE-NO-AUTOTRADE
REF-FAST-DEEP-PATH
REF-APPROVED-HTML-DIRECTION
OVERRIDE-PER-STAGE-DELIVERY
```

The first thirteen rows are `SUPERSEDED`; `HIST-FAILURE-EVIDENCE` is `REFERENCE_ONLY_FAILURE_EVIDENCE`; architecture rows are `REFERENCE_ONLY_ARCHITECTURE`; direction rows are `REFERENCE_ONLY_DIRECTION`; the delivery row is `SUPERSEDED` by the approved Stage 1/12 override. Historical results remain recorded facts but cannot prove current completion.

- [ ] **Step 3: Create `scope_boundary.md` with one-product and integration matrices**

Use `apply_patch`. Start with these invariants:

```text
formal_ui = PFI/web/index.html + route/shell modules + local App/localhost wrapper
active_product_count = 1
active_ui_count = 1
designated_render_implementation_per_acceptance = 1
Finder and localhost = two access surfaces to the same build/runtime
```

Create a matrix with columns `surface`, `owner`, `allowed_reads`, `allowed_writes`, `prohibited_behavior`, `privacy_class`, `release_identity`, and `evidence_gate`. Required rows:

```text
PFI
Alpha
PFI OS / Streamlit internal namespace
Cloudflare public shell
QBVS / QuantLab
Stage 1 isolated candidate PFI.app
```

Alpha is independent and reads only the exact eight-field versioned PFI Context. Cloudflare reads only qualitative redacted public data. PFI OS cannot create a second root/UI. QBVS/QuantLab cannot become primary entries. The candidate App is copied only from `PFI/macos/PFI.app` into `$STAGE1_TEMP_ROOT/PFI.app`, with isolated HOME/data/profile/cache/ports and no canonical-entry mutation.

- [ ] **Step 4: Create `run_contract.md` with exact execution, review, and rollback gates**

Use `apply_patch`. Include these sections in order:

```text
Identity and Acceptance
Authority and source hashes
Exact read set
Exact twenty-file write set
Explicit non-goals and forbidden paths
Preflight and stop conditions
Validation commands and expected evidence
Data/DB/App/migration impact = none
Stage boundary review sequence
Stage 1 isolated-candidate override
Stage 12 single install/upload transaction
Pre-commit rollback
Post-commit append-only-safe compensating rollback
Mandatory stop statement
```

The mandatory stop statement is:

```text
Stage 0 / Phase 0.2 candidate result; do not enter Phase 0.3 in this run.
```

The Stage sequence is exactly `whole-Stage fresh review -> findings remediation -> re-review pass -> explicit acceptance -> next Stage`. A blocked finding cannot be waived into acceptance.

At the end of **each** human policy, add one derived machine-readable projection between the exact markers `<!-- PFI_V025_ACTIVE_PROJECTION_BEGIN -->` and `<!-- PFI_V025_ACTIVE_PROJECTION_END -->`. The JSON payload is generated from the Active Requirements JSON and contains only:

```text
contract_id
blocking_conflicts[]: conflict_id, requirement_disposition, status,
  blocks_phase_0_2_candidate, resolution_tasks
policy_overrides[]: each complete exact override record
```

The three payloads must be semantically identical to the canonical JSON. They are validated derived views, not independent editable fact sources. Store the same object and its canonical SHA-256 in preliminary/final `evidence.json` as `active_contract_projection` and `active_contract_projection_sha256`.

---

### Task 4: Synchronize the twelve governance companions without widening scope

**Files:**

- Modify exactly the twelve companion paths listed in the File Map.

**Interfaces:**

- Consumes: all four Phase contracts and approved override.
- Produces: auditable iteration/evidence/traceability metadata without changing runtime model/formula/parameter values or adding a new canonical delivery task.

- [ ] **Step 1: Prove the core-only diff fails governance companion coverage**

After the four core contracts exist but before companion edits, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_governance_sync.py \
  --changed-only --base-ref "$PHASE_BASE" --enforce-sync
```

Expected: non-zero and a missing-companion set. This is the TDD red state; record it as an expected pre-implementation failure, not a product failure.

- [ ] **Step 2: Add contract-only records to model/formula governance**

Use `apply_patch`:

- Append a `v0.2.5 Stage 0 Phase 0.2 非模型合同` section to `MODEL_SPEC.md`. State `model_ids_changed=[]`, `formula_ids_changed=[]`, `parameter_ids_changed=[]`, existing counts remain `1/1/23/10/10`, and legacy v0.2 values are reference-only for v0.2.5 when the new Active Requirements contract conflicts.
- Add a top-level `phase_contracts` array to `model_registry.yaml` with one record containing iteration ID, contract ID, Acceptance ID, `fact_level: EXTRACTED`, evidence refs, and empty changed-ID arrays. Do not alter `models[]` or `assumptions[]`.
- Add the same top-level audit structure to `formula_registry.yaml`; do not alter `formulas[]`, expressions, variables, or constraints.
- In `parameter_registry.csv`, modify only `PARAM-PFI-003`: set `config_ref` to `PFI/config/pfi_v025_active_requirements.json`, extend `source_or_rationale` to state that Phase 0.2 freezes execution policy without changing the parameter value, and keep default/prior/active value, status, fact level, parameter version, and date unchanged. Do not add a parameter row.

Top-level YAML audit record shape:

```yaml
phase_contracts:
  - iteration_id: "ITER-20260711-PFI-V025-S0-P02"
    contract_id: "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS"
    acceptance_id: "ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT"
    fact_level: "EXTRACTED"
    requirement_disposition: "ACTIVE"
    evidence_refs:
      - "PFI/config/pfi_v025_active_requirements.json"
      - "PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json"
    model_ids_changed: []
    formula_ids_changed: []
    parameter_ids_changed: []
```

- [ ] **Step 3: Prepare the ledger and delivery audit records without a premature result event**

Use `apply_patch`:

- Append `## ITER-20260711-PFI-V025-S0-P02` to `DEVELOPMENT_LEDGER.md`; retain header counts `1/1/23/10/10` and describe evidence assembly, exact four tasks, no runtime/data/App/push work, and the fact that candidate status is unresolved until Task 5 finalization.
- Add a top-level `phase_contracts` array to `delivery_tasks.yaml`; do not append to `tasks[]`, because an eleventh canonical task would require out-of-scope `DELIVERY_PLAN.md` count changes.

Do not append the `development_events.jsonl` line in Task 4. Task 5 Step 3 appends one non-conclusionary line only after base/path/timestamp facts are known; Step 9 updates that same appended line after the actual command ledger and final candidate status are known.

- [ ] **Step 4: Add four traceability rows**

Append one CSV row per `S0-P2-T1..T4` to `TRACEABILITY_MATRIX.csv`. Use `NOT_APPLICABLE` for model/assumption/formula/parameter, the matching core artifact as code/config ref, no invented test file, `terminal.log` as validation evidence, the single Acceptance ID, and status `candidate_pending_postcommit_attestation`.

- [ ] **Step 5: Update version/status/owner/changelog as candidate-only overlays**

Use `apply_patch`:

- `VERSION_MATRIX.yaml`: preserve `product_version: v0.2.4 Repair Pack`, `version_file_value`, model/profile/data snapshot values; add `target_product_version: v0.2.5`, set `current_iteration: ITER-20260711-PFI-V025-S0-P02`, `current_phase: S0-P02`, and gate `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT-CANDIDATE-PENDING-POSTCOMMIT-ATTESTATION`.
- `STATUS.md`: add a Phase 0.2 candidate overlay recording the approved 20-file override, open conflicts, no release/Stage pass, and pending external attestation. Preserve historical snapshot facts rather than rewriting them as v0.2.5 completion.
- `OWNER_STATUS.md`: add the same owner-readable candidate distinction and state that future evidence-based Stage acceptance remains required despite blanket execution authorization.
- `CHANGELOG.md`: insert a top entry `v0.2.5 Stage 0 Phase 0.2 Active Contract Candidate - 2026-07-11`; list the four artifacts, governance companion sync, no runtime/model-value/data/App/push work, and pending external attestation.

- [ ] **Step 6: Prove registry definitions and values did not change**

Run this direct base/current structural comparison instead of relying on the stale owner-document consistency test:

```bash
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$PHASE_BASE" <<'PY'
import csv
import io
import subprocess
import sys
from pathlib import Path

import yaml

base = sys.argv[1]

def before(path):
    return subprocess.check_output(["git", "show", f"{base}:{path}"], text=True)

model_path = "PFI/docs/governance/model_registry.yaml"
formula_path = "PFI/docs/governance/formula_registry.yaml"
parameter_path = "PFI/docs/governance/parameter_registry.csv"

old_models = yaml.safe_load(before(model_path))
new_models = yaml.safe_load(Path(model_path).read_text(encoding="utf-8"))
assert old_models["models"] == new_models["models"]
assert old_models.get("assumptions") == new_models.get("assumptions")

old_formulas = yaml.safe_load(before(formula_path))
new_formulas = yaml.safe_load(Path(formula_path).read_text(encoding="utf-8"))
assert old_formulas["formulas"] == new_formulas["formulas"]

old_rows = {row["parameter_id"]: row for row in csv.DictReader(io.StringIO(before(parameter_path)))}
new_rows = {row["parameter_id"]: row for row in csv.DictReader(Path(parameter_path).read_text(encoding="utf-8").splitlines())}
assert old_rows.keys() == new_rows.keys()
allowed_metadata = {"source_or_rationale", "config_ref"}
for parameter_id in old_rows:
    if parameter_id != "PARAM-PFI-003":
        assert old_rows[parameter_id] == new_rows[parameter_id]
        continue
    for field in old_rows[parameter_id]:
        if field not in allowed_metadata:
            assert old_rows[parameter_id][field] == new_rows[parameter_id][field], field
assert new_rows["PARAM-PFI-003"]["config_ref"] == "PFI/config/pfi_v025_active_requirements.json"
rationale = new_rows["PARAM-PFI-003"]["source_or_rationale"].lower()
assert "phase 0.2" in rationale and "contract" in rationale
assert "no value change" in rationale or "value unchanged" in rationale
print("registry_runtime_definitions_and_values_unchanged=pass")
PY
```

Expected: `registry_runtime_definitions_and_values_unchanged=pass`.

---

### Task 5: Assemble evidence in an executable, non-self-referential order

**Files:**

- Create: the four files under `PFI/reports/pfi_v025/stage_0/phase_0_2/`.
- Append after checks: one final line in `PFI/docs/governance/development_events.jsonl`.

**Interfaces:**

- Consumes: exact candidate contracts and real command outputs.
- Produces: preliminary schema-valid evidence, complete semantic/route/cross-document results, then final candidate evidence and one append-only event. Governance preflight is recorded later in Task 6 and never creates a self-referential final rerun entry.

- [ ] **Step 1: Create the exact sorted changed-file ledger**

Use `apply_patch`. `changed_files.txt` contains exactly these twenty newline-delimited paths, in `LC_ALL=C` sort order:

```text
PFI/CHANGELOG.md
PFI/config/pfi_v025_active_requirements.json
PFI/docs/governance/DEVELOPMENT_LEDGER.md
PFI/docs/governance/MODEL_SPEC.md
PFI/docs/governance/OWNER_STATUS.md
PFI/docs/governance/STATUS.md
PFI/docs/governance/TRACEABILITY_MATRIX.csv
PFI/docs/governance/VERSION_MATRIX.yaml
PFI/docs/governance/delivery_tasks.yaml
PFI/docs/governance/development_events.jsonl
PFI/docs/governance/formula_registry.yaml
PFI/docs/governance/model_registry.yaml
PFI/docs/governance/parameter_registry.csv
PFI/docs/pfi_v025/stage_0/history_deprecation.md
PFI/docs/pfi_v025/stage_0/run_contract.md
PFI/docs/pfi_v025/stage_0/scope_boundary.md
PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt
PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json
PFI/reports/pfi_v025/stage_0/phase_0_2/risk_and_rollback.md
PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log
```

- [ ] **Step 2: Run the safe historical Phase 0.2 regression with guarded cleanup and preserved exit status**

Run this complete block in a fresh zsh process:

```bash
set -u
RUN_TMP="$(mktemp -d /private/tmp/pfi-v025-s0p02.XXXXXX)" || exit 2
case "$RUN_TMP" in /private/tmp/pfi-v025-s0p02.*) ;; *) exit 2 ;; esac
mkdir -p "$RUN_TMP"/{home,pfi-data,tmp,cache,pycache,reports,mpl} || exit 2
set +e
env -i \
  HOME="$RUN_TMP/home" \
  PFI_DATA_HOME="$RUN_TMP/pfi-data" \
  TMPDIR="$RUN_TMP/tmp" \
  XDG_CACHE_HOME="$RUN_TMP/cache" \
  PYTHONPYCACHEPREFIX="$RUN_TMP/pycache" \
  PFI_REPORT_DIR="$RUN_TMP/reports" \
  MPLCONFIGDIR="$RUN_TMP/mpl" \
  PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONPATH="$PWD/PFI/src" \
  PATH="/usr/bin:/bin:/usr/sbin:/sbin:/Users/linzezhang/.local/bin" \
  PFI/.venv/bin/python -B -m pytest -q -p no:cacheprovider \
    PFI/tests/test_v024_stage0_phase02_contract.py
rc=$?
case "$RUN_TMP" in /private/tmp/pfi-v025-s0p02.*) rm -rf -- "$RUN_TMP"; cleanup_rc=$? ;; *) cleanup_rc=2 ;; esac
set -e
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
exit "$cleanup_rc"
```

Expected: exit `0` and exactly `3 passed`. Cleanup cannot mask the pytest status.

Explicitly `not_run`: full PFI suite; `runTests.sh`, `verifyPFI.sh`, `ciSmoke.sh`; real-data/MetaDatabase tests; App/Downloads/browser/Playwright/final-delivery tests; `validateRealData.sh`; validation scripts that write DB/manifests; installers, launchers, start/stop, runtime and App acceptance scripts.

`PFI/tests/test_pfi_parameters_consistency.py` is not a Phase gate. Plan preflight reproduced its existing baseline as `3 passed / 5 failed`: it expects the legacy v0.2.2 catalog in `PFI/模型参数文件.md`, while the current Lean owner view has been generated from canonical governance since `d40e22db`. Record this under `PFI-V025-CONFLICT-OWNER-VIEWS / S0-P3-T1`; do not alter the forbidden owner file/test/renderer or call it a Phase regression.

- [ ] **Step 3: Create a preliminary schema-valid evidence quartet**

Use `apply_patch` before any evidence schema command:

- `evidence.json`: set `status="not_run"`, `allowed_files_obeyed=false`, `git_commit=$PHASE_BASE`, `initial_live_main=$LIVE_MAIN` and boolean `initial_remote_object_hydration_performed` from Task 1 Step 2, exact source/design/plan/Acceptance/task identities, empty `commands`, exact changed/evidence paths, explicit non-goals, current risks, `requires_user_acceptance=true`, and `contains_private_values=false`. Include the exact derived `active_contract_projection` and canonical compact-JSON `active_contract_projection_sha256` required by Task 3 Step 4.
- `terminal.log`: record only Tasks 1-5.2 commands already executed, their real exit codes, and `PHASE_STATUS: semantic_validation_in_progress`.
- `risk_and_rollback.md`: record current conflicts, guarded temp paths, stop conditions, pre-commit rollback, and append-only-safe post-commit compensation.
- Append one preliminary `development_events.jsonl` line with the exact static identities from Task 4, `result="validation_in_progress"`, `binding_status="approved_pending_validation"`, the observed `$PHASE_BASE`, the exact Step 1 path array, the observed Australia/Sydney timestamp, and only command summaries already completed. This line is the sole appended event and may be updated before commit without changing the immutable base prefix.

Do not append a second event and do not claim candidate pass in this step.

- [ ] **Step 4: Validate both streamed Task Pack schemas against the preliminary evidence**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - \
  /Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip \
  PFI/config/pfi_v025_active_requirements.json \
  PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json <<'PY'
import hashlib, json, re, sys, zipfile
from jsonschema import Draft202012Validator
archive, active_path, evidence_path = sys.argv[1:]
with zipfile.ZipFile(archive) as zf:
    for member, path in (
        ("PFI_v0.2.5_TaskPack/schemas/active_requirements.schema.json", active_path),
        ("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json", evidence_path),
    ):
        schema = json.loads(zf.read(member))
        Draft202012Validator.check_schema(schema)
        instance = json.loads(open(path, encoding="utf-8").read())
        Draft202012Validator(schema).validate(instance)
        print(f"schema_valid={path}")
PY
```

Expected: two `schema_valid=` lines and exit `0`.

- [ ] **Step 5: Run the complete strong semantic and type gate**

Run this command without adding assertions at execution time:

```bash
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - <<'PY'
import json
from pathlib import Path

d = json.loads(Path("PFI/config/pfi_v025_active_requirements.json").read_text(encoding="utf-8"))
assert list(d) == ["schema", "contract_id", "version", "authority_order", "source_hashes", "official_nav", "navigation_policy", "product_boundaries", "experience_policy", "data_policy", "financial_policy", "retained_business_rules", "execution_policy", "delivery_policy", "blocking_conflicts", "policy_overrides"]
assert d["schema"] == "PFIV025ActiveRequirementsV1"
assert d["contract_id"] == "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS"
assert d["version"] == "v0.2.5"
assert d["authority_order"] == ["latest_explicit_user_decision", "pinned_v025_task_pack_and_roadmap", "verified_current_repository_runtime_app_database_test_evidence", "non_conflicting_classified_history", "historical_completion_claims_have_no_independent_authority"]
assert d["source_hashes"] == {"roadmap_sha256": "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b", "task_pack_sha256": "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"}
assert d["official_nav"] == ["首页总览", "账户与资产", "账本流水", "投资管理", "消费管理", "数据源与上传", "建议与复盘", "报告与洞察", "市场与研究", "设置"]
nav = d["navigation_policy"]
assert nav["target_primary_routes"] == {"首页总览": "/overview", "账户与资产": "/accounts", "账本流水": "/ledger", "投资管理": "/investment", "消费管理": "/consumption", "数据源与上传": "/data", "建议与复盘": "/review", "报告与洞察": "/reports", "市场与研究": "/market-research", "设置": "/settings"}
assert nav["target_compatibility_aliases"] == {"/home": "/overview", "/market": "/market-research/market", "/research": "/market-research/research", "/holdings": "/investment/holdings", "/strategy-lab": "/market-research/strategy-lab", "/investment/strategy-lab": "/market-research/strategy-lab", "/data-system": "/settings/data-system"}
assert nav["current_gap_status"] == "blocked_pending_S6-P1"
assert nav["resolution_tasks"] == ["S6-P1-T1", "S6-P1-T2", "S6-P1-T3"]
assert nav["verified_current_primary_routes"] != nav["target_primary_routes"]

boundaries = d["product_boundaries"]
for key in ("pfi_only", "alpha_read_only", "no_ralpha", "exclude_serenity_alipay", "single_active_product", "single_active_ui"):
    assert boundaries[key] is True
assert boundaries["alpha_context_fields"] == ["net_worth_state", "investable_cash_state", "cashflow_pressure", "asset_allocation", "risk_budget", "investment_behavior_tags", "consumption_pressure_summary", "data_freshness"]
assert boundaries["alpha_context_metadata_fields"] == ["schema_version", "as_of", "source_or_read_model_hash", "privacy_classification"]
for key in ("alpha_writeback_allowed", "pfi_os_second_product_allowed", "cloudflare_private_financial_reads_allowed", "qbvs_quantlab_primary_navigation_allowed", "live_trading_or_payment_execution_authorized"):
    assert boundaries[key] is False

experience = d["experience_policy"]
assert experience["visual_direction"] == {"brightness": "bright", "quality": "high", "restraint": "restrained", "language": "zh-CN"}
for key in ("distinct_secondary_page_semantics", "real_url_history_deeplink_refresh", "focus_and_error_states", "settings_only_feedback_controls", "motion_user_disable_supported", "haptics_user_disable_supported", "unsupported_feedback_silently_degrades", "reduced_motion_respected"):
    assert experience[key] is True

data = d["data_policy"]
assert data["real_financial_data_only"] is True and data["no_financial_fallback"] is True
assert data["missing_real_input_results"] == ["blocked", "not_run"]
assert data["no_non_ready_financial_zero"] is True
assert data["metric_required_provenance"] == ["source", "coverage", "as_of", "formula", "parameter_hash", "read_model_hash"]
assert data["private_values_in_git_allowed"] is False and data["private_values_in_evidence_allowed"] is False
assert data["metric_states"] == ["ready", "confirmed_zero", "partial_coverage", "source_missing", "not_loaded", "path_error", "parse_failed", "outdated_snapshot", "permission_denied", "calculation_failed", "reconciliation_failed", "valuation_missing", "filtered_empty"]
assert data["confirmed_zero_required_evidence"] == ["source", "record_count", "coverage", "as_of", "formula", "read_model_hash", "confidence_or_coverage_evidence"]

financial = d["financial_policy"]
assert financial["primary_currency"] == "CNY" and financial["aud_cny_direction"] == "1 AUD = X CNY"
assert financial["example_rate"] == 4.81 and financial["example_only"] is True and financial["production_hardcode_allowed"] is False
assert financial["fx_refresh_local_time"] == "06:00" and financial["fx_timezone"] == "Australia/Sydney"
assert financial["ordinary_run_network_dependency"] is False
assert financial["prior_valid_publication_day_conditions"] == ["before_06_00", "weekend", "NSW_holiday"]
assert financial["outflow_views"] == ["消费总流出金额（用户定义活动口径）", "生活消费金额", "投资资金流出/配置金额"]
assert financial["outflow_views_share_sources"] is True
assert financial["investment_funding_and_purchases_may_enter_total_outflow"] is True
assert financial["investment_funding_and_purchases_are_living_consumption"] is False
assert financial["investment_funding_and_purchases_are_net_worth_loss"] is False
assert financial["double_count_controls"] == ["source_record_deduplication", "economic_event_lineage", "formula_rules"]

rules = d["retained_business_rules"]
assert rules["source_account_roles"] == {"hardcoded": False, "multiple_roles": True, "effective_periods": True}
assert rules["category_limits"] == {"l1_max": 12, "l2_per_l1_max": 5, "l2_total_max": 50, "exactly_one_primary_category": True}
assert rules["tags"] == {"default_and_custom": True, "create": True, "update": True, "disable": True, "history": True, "persistence": True, "view_filters": True}
assert rules["classification_confidence"] == {"field_completeness": 30, "amount_direction": 10, "rule_match": 20, "merchant_counterparty": 15, "interconnection": 15, "historical_consistency": 10, "threshold": 70}
assert rules["cashflow_windows_days"] == [7, 21, 30, 60, 90, 180, 360]
assert rules["formal_secondary_pages"] == ["Parameter Center", "Interconnection Map"]

execution = d["execution_policy"]
assert type(execution["max_phases_per_run"]) is int and execution["max_phases_per_run"] == 1
assert execution["stage_requires_user_acceptance"] is True
assert execution["automatic_phase_advancement"] is False and execution["automatic_stage_advancement"] is False
assert execution["stage_requires_independent_review"] is True
assert execution["stage_findings_must_be_remediated_before_acceptance"] is True
assert execution["stage_requires_rereview_pass"] is True
assert execution["stage_sequence"] == ["whole_stage_fresh_review", "findings_remediation", "rereview_pass", "explicit_acceptance", "next_stage"]
assert execution["completion_proof_disallowed"] == ["documentation_only", "toast_or_marker", "string_only_test", "fake_screenshot", "screenshot_path_only", "single_number_only"]
assert execution["review_findings_and_evidence_persistence_allowed"] is True
assert execution["private_chain_of_thought_or_internal_review_transcript_persistence_allowed"] is False

delivery = d["delivery_policy"]
assert delivery["local_phase_commits_allowed"] is True
assert delivery["per_stage_github_main_upload_allowed"] is False and delivery["per_stage_app_reinstall_allowed"] is False
assert delivery["stage_1_validation_mode"] == "isolated_candidate_app"
assert delivery["stage_1_candidate_source"] == "PFI/macos/PFI.app"
assert delivery["stage_1_finder_launch_allowed"] is True and delivery["stage_1_canonical_entry_mutation_allowed"] is False
assert delivery["stage_1_temp_root_policy"] == "run_created_mktemp_not_canonical_entry"
assert delivery["stage_1_candidate_path_template"] == "$STAGE1_TEMP_ROOT/PFI.app"
assert delivery["stage_1_isolated_environment"] == ["HOME", "PFI_DATA_HOME", "browser_profile", "runtime_cache", "ports"]
assert delivery["stage_1_required_binding_hashes"] == ["source_tree_hash", "copied_bundle_hash", "checkout_binding_hash"]
assert delivery["stage_1_required_identity_match"] == ["frontend", "backend", "manifest", "asset", "commit"]
assert delivery["stage_1_canonical_entry_before_after_hash_required"] is True
assert delivery["stage_1_launchservices_registration_and_cleanup_recorded"] is True
assert delivery["stage_1_candidate_disposable_and_never_final_promoted"] is True
assert delivery["final_delivery_stage"] == 12
assert delivery["final_candidate_fresh_rebuild_from_release_content_commit"] is True
assert delivery["final_candidate_hashes_required"] == ["build_hash", "asset_hash", "commit_hash"]
assert delivery["final_commit_identities"] == ["release_content_commit", "acceptance_candidate_commit", "final_record_commit"]
assert delivery["final_app_reinstall_required"] is True and delivery["final_app_reinstall_gate"] == "S12-P2-T1"
assert delivery["canonical_app_backup_before_promotion_required"] is True and delivery["failed_promotion_restores_backup"] is True
assert delivery["automatic_install_retry_allowed"] is False
assert delivery["final_github_main_upload_required"] is True
assert delivery["final_github_main_upload_gate"] == "after_S12-P3-T4_explicit_acceptance"
assert delivery["expected_remote_main_sha_required"] is True and delivery["final_strict_fast_forward_required"] is True
assert delivery["post_release_content_freeze_rebase_merge_runtime_content_commit_allowed"] is False
assert delivery["final_push_count"] == 1 and delivery["final_push_from_ref"] == "expected_remote_main_sha" and delivery["final_push_to_commit_identity"] == "final_record_commit"
assert delivery["final_remote_parity_verification_required"] is True
assert delivery["final_independent_evidence_gates"] == ["remote_parity", "installed_app_identity", "local_owner_view_consistency"]
assert delivery["force_push_allowed"] is False
assert delivery["pre_push_remote_drift_result"] == "blocked_restore_saved_canonical_app_require_new_explicit_decision"
assert delivery["post_push_remote_updated_but_parity_failed_result"] == "freeze_remote_local_app_no_auto_rollback_or_rewrite"

conflicts = d["blocking_conflicts"]
assert conflicts["unresolved_result"] == "blocked" and conflicts["self_declared_unified_allowed"] is False and conflicts["evidence_reference_required"] is True
assert conflicts["blocks_claims"] == ["release_identity_unified", "v0.2.5_accepted", "final_delivery_ready"]
expected_conflict_ids = ["PFI-V025-CONFLICT-OWNER-VIEWS", "PFI-V025-CONFLICT-RELEASE-IDENTITY", "PFI-V025-CONFLICT-APP-IDENTITY", "PFI-V025-CONFLICT-RUNTIME-LISTENERS", "PFI-V025-CONFLICT-STALE-ROUTE-MARKERS", "PFI-V025-CONFLICT-ROUTE-TARGET-GAP", "PFI-V025-CONFLICT-GOVERNANCE-SCOPE"]
assert [item["conflict_id"] for item in conflicts["items"]] == expected_conflict_ids
expected_resolution_tasks = {"PFI-V025-CONFLICT-OWNER-VIEWS": ["S0-P3-T1", "S12-P3-T1"], "PFI-V025-CONFLICT-RELEASE-IDENTITY": ["S1-P1-T1", "S12-P3-T1"], "PFI-V025-CONFLICT-APP-IDENTITY": ["S12-P2-T1"], "PFI-V025-CONFLICT-RUNTIME-LISTENERS": ["S1-P3-T2", "S12-P2-T2"], "PFI-V025-CONFLICT-STALE-ROUTE-MARKERS": ["S1-P1-T1", "S6-P1-T1", "S6-P1-T2", "S6-P1-T3", "S12-P3-T1"], "PFI-V025-CONFLICT-ROUTE-TARGET-GAP": ["S6-P1-T1", "S6-P1-T2", "S6-P1-T3"], "PFI-V025-CONFLICT-GOVERNANCE-SCOPE": ["S0-P3-T1"]}
allowed_dispositions = {"ACTIVE", "SUPERSEDED", "REFERENCE_ONLY_FAILURE_EVIDENCE", "REFERENCE_ONLY_ARCHITECTURE", "REFERENCE_ONLY_DIRECTION", "BLOCKING_CURRENT_CONFLICT"}
allowed_facts = {"EXTRACTED", "RECONSTRUCTED", "PROPOSED", "UNKNOWN", "NOT_APPLICABLE"}
for index, item in enumerate(conflicts["items"]):
    assert item["requirement_disposition"] in allowed_dispositions and item["fact_level"] in allowed_facts
    assert item["evidence_ref"] and item["affected_surfaces"] and item["prohibited_claims"] and item["resolution_tasks"]
    assert item["requirement_disposition"] == "BLOCKING_CURRENT_CONFLICT"
    assert item["resolution_tasks"] == expected_resolution_tasks[item["conflict_id"]]
    assert item["status"] == ("approved_pending_validation" if index == 6 else "blocked")
    assert item["blocks_phase_0_2_candidate"] is (index == 6)

overrides = {item["override_id"]: item for item in d["policy_overrides"]}
assert set(overrides) == {"PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE", "PFI-V025-S0-GOVERNANCE-COMPANIONS"}
assert overrides["PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE"] == {"override_id": "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE", "authority": "latest_user_decision", "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:S1-P3-T1,S1-P3-T3", "original_action": "canonical_app_install_and_entry_replacement_in_stage_1", "status": "superseded", "effective_rule": "stage_1_uses_isolated_disposable_candidate_without_canonical_entry_mutation", "replacement_gate": "canonical_install_only_at_S12-P2-T1_after_stage_12_preconditions", "evidence_ref": "PFI/docs/pfi_v025/stage_0/run_contract.md#approved-policy-overrides"}
assert overrides["PFI-V025-S0-GOVERNANCE-COMPANIONS"] == {"override_id": "PFI-V025-S0-GOVERNANCE-COMPANIONS", "authority": "latest_user_decision", "source_contract": "PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md:Stage_0_allowed_files", "original_action": "stage_0_phase_0_2_writes_limited_to_eight_core_artifacts", "status": "superseded", "effective_rule": "phase_0_2_allows_exact_eight_core_artifacts_plus_twelve_named_governance_companions", "replacement_gate": "exact_twenty_path_ledger_plus_sparse_aware_preflight_and_postcommit_attestation", "evidence_ref": "PFI/docs/pfi_v025/stage_0/scope_boundary.md#approved-governance-companion-override"}
print("active_contract_semantic_gate=pass")
PY
```

Expected: exactly `active_contract_semantic_gate=pass`.

- [ ] **Step 6: Reproduce current route truth and compare it to the JSON current snapshot**

Run:

```bash
node <<'NODE'
const assert = require("node:assert/strict");
const fs = require("node:fs");
const active = JSON.parse(fs.readFileSync("PFI/config/pfi_v025_active_requirements.json", "utf8"));
const nav = require("./PFI/web/app/navigation.js");
const routes = require("./PFI/web/app/routes.js");
assert.deepEqual(nav.officialPrimaryEntries.map(x => [x.label, x.workspace, x.routeAlias]), routes.officialPrimaryEntries.map(x => [x.label, x.workspace, x.routeAlias]));
const primary = Object.fromEntries(routes.officialPrimaryEntries.map(x => [x.label, x.routeAlias]));
const declared = Object.fromEntries(routes.legacyAliasEntries.map(x => [x.routeAlias, x.resolvedRouteAlias]));
assert.deepEqual(primary, active.navigation_policy.verified_current_primary_routes);
assert.deepEqual(declared, active.navigation_policy.verified_current_declared_aliases);
assert.deepEqual(routes.officialPrimaryEntries.map(x => x.workspace), active.navigation_policy.verified_current_workspace_bindings);
const shell = fs.readFileSync("PFI/web/app/shell.js", "utf8");
const body = shell.match(/const LEGACY_ROUTE_ALIAS_TARGETS = Object\.freeze\(\{([\s\S]*?)\n\}\);/);
assert.ok(body, "shell compatibility map missing");
const explicit = Object.fromEntries([...body[1].matchAll(/"([^"]+)":\s*"([^"]+)"/g)].map(m => [m[1], m[2]]));
assert.deepEqual(explicit, active.navigation_policy.verified_current_shell_compatibility_inputs);
assert.notDeepEqual(active.navigation_policy.verified_current_primary_routes, active.navigation_policy.target_primary_routes);
console.log("current_route_snapshot_valid=true");
NODE
```

Expected: `current_route_snapshot_valid=true`.

- [ ] **Step 7: Run a four-document parity gate**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$PHASE_BASE" <<'PY'
import hashlib, json, re, sys
from pathlib import Path
base = sys.argv[1]
active = json.loads(Path("PFI/config/pfi_v025_active_requirements.json").read_text(encoding="utf-8"))
evidence = json.loads(Path("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json").read_text(encoding="utf-8"))
history = Path("PFI/docs/pfi_v025/stage_0/history_deprecation.md").read_text(encoding="utf-8")
scope = Path("PFI/docs/pfi_v025/stage_0/scope_boundary.md").read_text(encoding="utf-8")
run = Path("PFI/docs/pfi_v025/stage_0/run_contract.md").read_text(encoding="utf-8")

projection = {
    "contract_id": active["contract_id"],
    "blocking_conflicts": [
        {key: item[key] for key in ("conflict_id", "requirement_disposition", "status", "blocks_phase_0_2_candidate", "resolution_tasks")}
        for item in active["blocking_conflicts"]["items"]
    ],
    "policy_overrides": active["policy_overrides"],
}
projection_bytes = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
projection_sha256 = hashlib.sha256(projection_bytes).hexdigest()

def embedded_projection(text):
    start = "<!-- PFI_V025_ACTIVE_PROJECTION_BEGIN -->"
    end = "<!-- PFI_V025_ACTIVE_PROJECTION_END -->"
    assert text.count(start) == 1 and text.count(end) == 1
    return json.loads(text.split(start, 1)[1].split(end, 1)[0].strip())

for document in (history, scope, run):
    assert embedded_projection(document) == projection
assert evidence["active_contract_projection"] == projection
assert evidence["active_contract_projection_sha256"] == projection_sha256
for token in ("PFI", "Alpha", "PFI OS", "Cloudflare", "QBVS", "Stage 1 isolated candidate"):
    assert token in scope
for task in ("S0-P2-T1", "S0-P2-T2", "S0-P2-T3", "S0-P2-T4"):
    assert task in run and any(item["task_id"] == task for item in evidence["tasks"])
assert evidence["git_commit"] == base
assert re.fullmatch(r"[0-9a-f]{40}", evidence["initial_live_main"])
assert type(evidence["initial_remote_object_hydration_performed"]) is bool
assert evidence["acceptance_id"] == "ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT"
for digest in active["source_hashes"].values():
    assert digest in history and digest in scope and digest in run
assert "Stage 0 / Phase 0.2 candidate result; do not enter Phase 0.3 in this run." in run
print("cross_document_parity=pass")
PY
```

Expected: `cross_document_parity=pass`.

- [ ] **Step 8: Stage the preliminary candidate and run the recorded sparse-aware governance preflight**

Stage the exact path ledger, then run this complete block in a fresh zsh process:

```bash
set -euo pipefail
git add --pathspec-from-file=PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt
PRE_SHADOW_PARENT="$(mktemp -d /private/tmp/pfi-v025-s0p02-recorded-preflight.XXXXXX)" || exit 2
case "$PRE_SHADOW_PARENT" in /private/tmp/pfi-v025-s0p02-recorded-preflight.*) ;; *) exit 2 ;; esac
PRE_SHADOW="$PRE_SHADOW_PARENT/repo"
registered=0
cleanup_pre_shadow() {
  local cleanup_status=0 remove_status=0 directory_status=0
  if [ "$registered" -eq 1 ]; then
    GIT_NO_LAZY_FETCH=1 git worktree remove --force "$PRE_SHADOW" || remove_status=$?
    if [ "$remove_status" -eq 0 ]; then
      registered=0
    else
      cleanup_status=$remove_status
    fi
  fi
  case "$PRE_SHADOW_PARENT" in
    /private/tmp/pfi-v025-s0p02-recorded-preflight.*) rm -rf -- "$PRE_SHADOW_PARENT" || directory_status=$? ;;
    *) directory_status=2 ;;
  esac
  if [ "$cleanup_status" -eq 0 ] && [ "$directory_status" -ne 0 ]; then cleanup_status=$directory_status; fi
  return "$cleanup_status"
}
trap cleanup_pre_shadow EXIT INT TERM
GIT_NO_LAZY_FETCH=1 git worktree add --detach --no-checkout "$PRE_SHADOW" "$PHASE_BASE" || exit 3
registered=1
git -C "$PRE_SHADOW" sparse-checkout init --no-cone || exit 3
git -C "$PRE_SHADOW" sparse-checkout set --no-cone --stdin <<'SPARSE' || exit 3
/*
!/*/
/PFI/*
!/PFI/*/
/PFI/config/
/PFI/docs/
/PFI/scripts/
/PFI/src/
/PFI/tests/
/PFI/web/
/PFI/reports/
!/PFI/reports/*/
/PFI/reports/pfi_v025/
!/PFI/reports/pfi_v025/*/
/PFI/reports/pfi_v025/stage_0/
!/PFI/reports/pfi_v025/stage_0/*/
/PFI/reports/pfi_v025/stage_0/phase_0_2/
/scripts/
/docs/governance/
/governance/projects.yaml
/governance/schemas/
/tests/governance/
/tests/cloudflare/test_compatibility_envelope.py
/.github/workflows/project-governance.yml
/.agents/skills/project-governance/SKILL.md
/.agents/skills/codex-dex/SKILL.md
/.codex/config.template.toml
/.codex/hooks.json
/.codex/hooks/governance_stop.py
/Alpha/AGENTS.md
/EEI/AGENTS.md
/FIFA/AGENTS.md
/KM_IDSystem/AGENTS.md
/WDA/AGENTS.md
/OpenAIDatabase/AGENTS.md
/MetaDatabase/README.md
/KMFA/AGENTS.md
/QBVS/AGENTS.md
/Serenity-Alipay/AGENTS.md
/whkmSalary/AGENTS.md
/arxiv-daily-push/AGENTS.md
SPARSE
GIT_NO_LAZY_FETCH=1 git -C "$PRE_SHADOW" checkout --detach "$PHASE_BASE" || exit 3
git diff --cached --binary | git -C "$PRE_SHADOW" apply --index - || exit 3
set +e
(
  cd "$PRE_SHADOW" || exit 4
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_project_governance.py --changed-only --base-ref "$PHASE_BASE" --enforce-sync --semantic &&
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_governance_sync.py --changed-only --base-ref "$PHASE_BASE" --enforce-sync --semantic
)
rc=$?
set -e
set +e
cleanup_pre_shadow
cleanup_rc=$?
set -e
trap - EXIT INT TERM
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
exit "$cleanup_rc"
```

Expected: exit `0`, selected scope PFI, no missing companion, valid event/iteration/version parity, and no private/MetaDatabase/App materialization. Record this actual output in Step 9. Do not add an all-project semantic drift report to this selective shadow.

- [ ] **Step 9: Finalize candidate evidence and the single actual event**

Use `apply_patch` only after Steps 2-8 pass:

- Update `evidence.json` to `status="candidate_pass"`, `allowed_files_obeyed=true`, all four task statuses `candidate_pass`, and add every executed command with its integer exit code and factual summary. Keep `git_commit=$PHASE_BASE`, `governance_override_state="approved_pending_postcommit_attestation"`, `requires_user_acceptance=true`, and `contains_private_values=false`.
- Update `terminal.log` with the real Steps 2-8 command blocks and `PHASE_STATUS: candidate_pass_pending_postcommit_attestation`.
- Complete `risk_and_rollback.md` without claiming governance or post-commit success.
- Update the one already-appended `development_events.jsonl` object. Static values are `EVENT-20260711-PFI-V025-S0-P02`, `ITER-20260711-PFI-V025-S0-P02`, phase `S0-P02`, the four exact task IDs, the Acceptance/contract/evidence refs, empty changed-ID arrays, `result="candidate_pass_pending_postcommit_attestation"`, `binding_status="approved_pending_postcommit_attestation"`, `runtime_behavior_changed=false`, and `contains_private_values=false`. Keep its observed timestamp/base/path array and replace `tests_run` with successful Steps 2-8 command summaries. No free-form or future-derived value is permitted.

- [ ] **Step 10: Re-run final schema and evidence parity checks**

Run this self-contained final gate:

```bash
PYTHONDONTWRITEBYTECODE=1 PFI/.venv/bin/python -B - "$PHASE_BASE" <<'PY'
import hashlib, json, re, sys, zipfile
from pathlib import Path
from jsonschema import Draft202012Validator
base = sys.argv[1]
archive = Path("/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip")
active_path = Path("PFI/config/pfi_v025_active_requirements.json")
evidence_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json")
with zipfile.ZipFile(archive) as zf:
    for member, path in (("PFI_v0.2.5_TaskPack/schemas/active_requirements.schema.json", active_path), ("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json", evidence_path)):
        schema = json.loads(zf.read(member))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(json.loads(path.read_text(encoding="utf-8")))
evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
active = json.loads(active_path.read_text(encoding="utf-8"))
projection = {"contract_id": active["contract_id"], "blocking_conflicts": [{key: item[key] for key in ("conflict_id", "requirement_disposition", "status", "blocks_phase_0_2_candidate", "resolution_tasks")} for item in active["blocking_conflicts"]["items"]], "policy_overrides": active["policy_overrides"]}
projection_sha256 = hashlib.sha256(json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
assert evidence["status"] == "candidate_pass"
assert evidence["allowed_files_obeyed"] is True
assert evidence["git_commit"] == base
assert re.fullmatch(r"[0-9a-f]{40}", evidence["initial_live_main"])
assert type(evidence["initial_remote_object_hydration_performed"]) is bool
assert evidence["acceptance_id"] == "ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT"
assert evidence["requires_user_acceptance"] is True and evidence["contains_private_values"] is False
assert [item["task_id"] for item in evidence["tasks"]] == ["S0-P2-T1", "S0-P2-T2", "S0-P2-T3", "S0-P2-T4"]
assert all(item["status"] == "candidate_pass" for item in evidence["tasks"])
assert evidence["commands"] and all(type(item["exit_code"]) is int for item in evidence["commands"])
assert evidence["governance_override_state"] == "approved_pending_postcommit_attestation"
assert evidence["active_contract_projection"] == projection
assert evidence["active_contract_projection_sha256"] == projection_sha256
print("final_schema_and_evidence_parity=pass")
PY
```

Expected: `final_schema_and_evidence_parity=pass`. This final rerun is not appended again, avoiding a logging self-reference.

---

### Task 6: Stage the finalized twenty files and prove privacy/governance readiness

**Files:**

- Stage: exactly the twenty paths in `changed_files.txt`.
- Temporary: one guarded selective detached worktree containing no PFI data, MetaDatabase, macOS App bundle, or historical report tree.

**Interfaces:**

- Consumes: finalized candidate evidence and event.
- Produces: exact staged tree, machine privacy result, append-only result, and a final sparse-aware governance preflight. These final reruns are kept external to the staged content to prevent self-reference.

- [ ] **Step 1: Re-stage only the finalized authorized pathspec and reconcile the index**

Run:

```bash
set -euo pipefail
git add --pathspec-from-file=PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt
git diff --cached --check
test -z "$(git diff --name-only)"
test -z "$(git ls-files --others --exclude-standard)"
diff -u \
  <(LC_ALL=C sort PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt) \
  <(git diff --cached --name-only | LC_ALL=C sort)
test "$(git diff --cached --name-only | wc -l | tr -d ' ')" = 20
test "$(git diff --cached --diff-filter=A --name-only | wc -l | tr -d ' ')" = 8
test -z "$(git diff --cached --diff-filter=DR --name-only)"
```

Expected: exit `0`, twenty staged paths, eight additions, twelve modifications, no unstaged/untracked/delete/rename.

- [ ] **Step 2: Prove the final event is one append-only line**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$PHASE_BASE" <<'PY'
import json, subprocess, sys
from pathlib import Path
base = sys.argv[1]
path = "PFI/docs/governance/development_events.jsonl"
before = subprocess.check_output(["git", "show", f"{base}:{path}"])
after = Path(path).read_bytes()
assert after.startswith(before), "development_events.jsonl prefix changed"
assert after.count(b"\n") == before.count(b"\n") + 1, "expected exactly one appended event"
event = json.loads(after[len(before):].decode("utf-8"))
assert event["event_id"] == "EVENT-20260711-PFI-V025-S0-P02"
assert event["result"] == "candidate_pass_pending_postcommit_attestation"
assert event["binding_status"] == "approved_pending_postcommit_attestation"
print("development_events_append_only=pass")
PY
```

Expected: `development_events_append_only=pass`.

- [ ] **Step 3: Scan the exact staged blobs for private values and forbidden credential material**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import re
import subprocess
from pathlib import Path

ledger = Path("PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt").read_text(encoding="utf-8").splitlines()
staged = subprocess.check_output(["git", "diff", "--cached", "--name-only"], text=True).splitlines()
assert sorted(ledger) == sorted(staged) and len(staged) == 20
forbidden_changed_paths = ("/data/", "/MetaDatabase/", "/macos/", "/.pfi/", "/Applications/", "/Desktop/", "/Downloads/")
assert not [path for path in staged if any(marker in path for marker in forbidden_changed_paths)]
patterns = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "cloud_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "service_token": re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|xox[baprs]-[A-Za-z0-9-]{12,}|sk-[A-Za-z0-9_\-]{12,})\b"),
    "sensitive_assignment": re.compile(r"(?i)\b(?:password|secret|api[_-]?key|account_number|card_number)\b\s*[:=]\s*[\"']?(?!false\b|none\b|not[_ -]?applicable\b)[A-Za-z0-9+/=_\-]{8,}"),
}
findings = []
for path in staged:
    blob = subprocess.check_output(["git", "show", f":{path}"])
    text = blob.decode("utf-8")
    for name, pattern in patterns.items():
        if pattern.search(text):
            findings.append((path, name))
assert not findings, findings
print("staged_privacy_scan=pass|files=20|findings=0")
PY
```

Expected: `staged_privacy_scan=pass|files=20|findings=0`.

- [ ] **Step 4: Run final structural/semantic/sync preflight in a guarded selective shadow**

Run this complete block in a fresh zsh process:

```bash
set -euo pipefail
SHADOW_PARENT="$(mktemp -d /private/tmp/pfi-v025-s0p02-final-preflight.XXXXXX)" || exit 2
case "$SHADOW_PARENT" in /private/tmp/pfi-v025-s0p02-final-preflight.*) ;; *) exit 2 ;; esac
SHADOW="$SHADOW_PARENT/repo"
registered=0
cleanup_shadow() {
  local cleanup_status=0 remove_status=0 directory_status=0
  if [ "$registered" -eq 1 ]; then
    GIT_NO_LAZY_FETCH=1 git worktree remove --force "$SHADOW" || remove_status=$?
    if [ "$remove_status" -eq 0 ]; then
      registered=0
    else
      cleanup_status=$remove_status
    fi
  fi
  case "$SHADOW_PARENT" in
    /private/tmp/pfi-v025-s0p02-final-preflight.*) rm -rf -- "$SHADOW_PARENT" || directory_status=$? ;;
    *) directory_status=2 ;;
  esac
  if [ "$cleanup_status" -eq 0 ] && [ "$directory_status" -ne 0 ]; then cleanup_status=$directory_status; fi
  return "$cleanup_status"
}
trap cleanup_shadow EXIT INT TERM
GIT_NO_LAZY_FETCH=1 git worktree add --detach --no-checkout "$SHADOW" "$PHASE_BASE" || exit 3
registered=1
git -C "$SHADOW" sparse-checkout init --no-cone || exit 3
git -C "$SHADOW" sparse-checkout set --no-cone --stdin <<'SPARSE' || exit 3
/*
!/*/
/PFI/*
!/PFI/*/
/PFI/config/
/PFI/docs/
/PFI/scripts/
/PFI/src/
/PFI/tests/
/PFI/web/
/PFI/reports/
!/PFI/reports/*/
/PFI/reports/pfi_v025/
!/PFI/reports/pfi_v025/*/
/PFI/reports/pfi_v025/stage_0/
!/PFI/reports/pfi_v025/stage_0/*/
/PFI/reports/pfi_v025/stage_0/phase_0_2/
/scripts/
/docs/governance/
/governance/projects.yaml
/governance/schemas/
/tests/governance/
/tests/cloudflare/test_compatibility_envelope.py
/.github/workflows/project-governance.yml
/.agents/skills/project-governance/SKILL.md
/.agents/skills/codex-dex/SKILL.md
/.codex/config.template.toml
/.codex/hooks.json
/.codex/hooks/governance_stop.py
/Alpha/AGENTS.md
/EEI/AGENTS.md
/FIFA/AGENTS.md
/KM_IDSystem/AGENTS.md
/WDA/AGENTS.md
/OpenAIDatabase/AGENTS.md
/MetaDatabase/README.md
/KMFA/AGENTS.md
/QBVS/AGENTS.md
/Serenity-Alipay/AGENTS.md
/whkmSalary/AGENTS.md
/arxiv-daily-push/AGENTS.md
SPARSE
GIT_NO_LAZY_FETCH=1 git -C "$SHADOW" checkout --detach "$PHASE_BASE" || exit 3
git diff --cached --binary | git -C "$SHADOW" apply --index - || exit 3
set +e
(
  cd "$SHADOW" || exit 4
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_project_governance.py --changed-only --base-ref "$PHASE_BASE" --enforce-sync --semantic &&
  PYTHONDONTWRITEBYTECODE=1 python3 -B scripts/validate_governance_sync.py --changed-only --base-ref "$PHASE_BASE" --enforce-sync --semantic
)
rc=$?
set -e
set +e
cleanup_shadow
cleanup_rc=$?
set -e
trap - EXIT INT TERM
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
exit "$cleanup_rc"
```

Expected: exit `0`; selected scope PFI; missing companions `0`; event/iteration/version/append-only checks pass. All-project semantic drift expansion is deliberately absent. This final rerun remains external and is not written back into the staged candidate.

---

### Task 7: Independent review, atomic commit, and external post-commit attestation

**Files:**

- Review/commit: exact staged twenty-file tree.
- External evidence: tool-emitted local `.git/codex-review/lean-governance/` evidence plus one immutable attempt directory under `.git/codex-review/pfi-v025/stage_0/phase_0_2/`; its CI binding, no-side-effect artifact, blocking candidate and final attestation are never overwritten or added to the commit. A mutable pointer is advisory routing to the newest attempt only; every create/publish decision is rechecked under the fixed Phase `flock`, a global final dominates the pointer, and the final never references it. After successful publication the pointer intentionally remains as a non-authoritative breadcrumb to that completed attempt; it is not deleted or used to decide acceptance.

**Interfaces:**

- Consumes: staged candidate and all Phase evidence.
- Produces: one local Phase commit, clean worktree, independently reviewed candidate result, and externally bound governance proof.

- [ ] **Step 1: Run independent specification and evidence reviews before commit**

Use at least two fresh read-only reviewers:

1. Roadmap/Task Pack fidelity and semantic/type coverage.
2. Governance/evidence/privacy/append-only/no-side-effect/remote-drift feasibility.

Each reports Critical/Important/Minor findings with file/line evidence. Fix every finding only inside the same twenty files, rerun Tasks 5.3-6.4, and obtain fresh re-review. No finding may be waived into pass.

- [ ] **Step 2: Create the atomic local Phase commit**

Run:

```bash
set -euo pipefail
git diff --cached --check
git commit -m "docs(PFI): freeze v0.2.5 stage 0 phase 0.2 contract"
export PHASE_COMMIT="$(git rev-parse HEAD)"
git status --porcelain=v1 --untracked-files=all
git diff --name-only "$PHASE_BASE..$PHASE_COMMIT" | LC_ALL=C sort
test -z "$(git status --porcelain=v1 --untracked-files=all)"
diff -u \
  <(LC_ALL=C sort PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt) \
  <(git diff --name-only "$PHASE_BASE..$PHASE_COMMIT" | LC_ALL=C sort)
```

Expected: clean worktree and exact twenty paths. Do not push.

- [ ] **Step 3: Run clean post-commit Lean Governance CI in a guarded selective shadow**

Run this complete block in a fresh zsh process:

```bash
set -euo pipefail
PHASE_COMMIT="$(git rev-parse HEAD)"
PHASE_BASE="$(git rev-parse "$PHASE_COMMIT^")"
COMMON_GIT_DIR="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"
ATTEST_PARENT="$COMMON_GIT_DIR/codex-review/pfi-v025/stage_0/phase_0_2"
mkdir -p "$ATTEST_PARENT"
ATTEST_POINTER="$ATTEST_PARENT/current.path"
ATTEST_DIR="$(PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ATTEST_PARENT" "$ATTEST_POINTER" "$PHASE_COMMIT" <<'PY'
import fcntl, os, sys, tempfile
from pathlib import Path
parent, pointer = (Path(value) for value in sys.argv[1:3])
commit = sys.argv[3]
lock_path = parent / "phase.lock"
with lock_path.open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    assert not list(parent.glob("*.attempt.*/phase_0_2_attestation.json")), "final attestation already exists"
    attempt = Path(tempfile.mkdtemp(prefix=f"{commit}.attempt.", dir=parent))
    temporary = pointer.with_name(f".{pointer.name}.tmp.{os.getpid()}")
    assert not temporary.exists()
    temporary.write_text(str(attempt) + "\n", encoding="utf-8")
    os.replace(temporary, pointer)
    print(attempt)
PY
)"
SHADOW_PARENT="$(mktemp -d /private/tmp/pfi-v025-s0p02-attest.XXXXXX)" || exit 2
case "$SHADOW_PARENT" in /private/tmp/pfi-v025-s0p02-attest.*) ;; *) exit 2 ;; esac
SHADOW="$SHADOW_PARENT/repo"
registered=0
cleanup_attest_shadow() {
  local cleanup_status=0 remove_status=0 directory_status=0
  if [ "$registered" -eq 1 ]; then
    GIT_NO_LAZY_FETCH=1 git worktree remove "$SHADOW" || remove_status=$?
    if [ "$remove_status" -eq 0 ]; then
      registered=0
    else
      cleanup_status=$remove_status
    fi
  fi
  case "$SHADOW_PARENT" in
    /private/tmp/pfi-v025-s0p02-attest.*) rm -rf -- "$SHADOW_PARENT" || directory_status=$? ;;
    *) directory_status=2 ;;
  esac
  if [ "$cleanup_status" -eq 0 ] && [ "$directory_status" -ne 0 ]; then cleanup_status=$directory_status; fi
  return "$cleanup_status"
}
trap cleanup_attest_shadow EXIT INT TERM
GIT_NO_LAZY_FETCH=1 git worktree add --detach --no-checkout "$SHADOW" "$PHASE_COMMIT" || exit 3
registered=1
git -C "$SHADOW" sparse-checkout init --no-cone || exit 3
git -C "$SHADOW" sparse-checkout set --no-cone --stdin <<'SPARSE' || exit 3
/*
!/*/
/PFI/*
!/PFI/*/
/PFI/config/
/PFI/docs/
/PFI/scripts/
/PFI/src/
/PFI/tests/
/PFI/web/
/PFI/reports/
!/PFI/reports/*/
/PFI/reports/pfi_v025/
!/PFI/reports/pfi_v025/*/
/PFI/reports/pfi_v025/stage_0/
!/PFI/reports/pfi_v025/stage_0/*/
/PFI/reports/pfi_v025/stage_0/phase_0_2/
/scripts/
/docs/governance/
/governance/projects.yaml
/governance/schemas/
/tests/governance/
/tests/cloudflare/test_compatibility_envelope.py
/.github/workflows/project-governance.yml
/.agents/skills/project-governance/SKILL.md
/.agents/skills/codex-dex/SKILL.md
/.codex/config.template.toml
/.codex/hooks.json
/.codex/hooks/governance_stop.py
/Alpha/AGENTS.md
/EEI/AGENTS.md
/FIFA/AGENTS.md
/KM_IDSystem/AGENTS.md
/WDA/AGENTS.md
/OpenAIDatabase/AGENTS.md
/MetaDatabase/README.md
/KMFA/AGENTS.md
/QBVS/AGENTS.md
/Serenity-Alipay/AGENTS.md
/whkmSalary/AGENTS.md
/arxiv-daily-push/AGENTS.md
SPARSE
GIT_NO_LAZY_FETCH=1 git -C "$SHADOW" checkout --detach "$PHASE_COMMIT" || exit 3
set +e
CI=1 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 \
  python3 -B "$SHADOW/scripts/lean_governance.py" ci \
  --changed-only --base-ref "$PHASE_BASE" 2>&1 | tee "$ATTEST_DIR/lean_governance.log"
rc=$?
set -e
set +e
cleanup_attest_shadow
cleanup_rc=$?
set -e
trap - EXIT INT TERM
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
if [ "$cleanup_rc" -ne 0 ]; then exit "$cleanup_rc"; fi
PYTHONDONTWRITEBYTECODE=1 python3 -B - \
  "$ATTEST_DIR/lean_governance.log" \
  "$ATTEST_DIR/phase_0_2_ci_attestation.json" \
  "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import fcntl, hashlib, json, os, re, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

log_path, output_path = map(Path, sys.argv[1:3])
base, commit = sys.argv[3:5]
lines = [line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
compact = json.loads(lines[-1])
assert compact["decision"] == "SHIP"
assert compact["process_exit_code"] == 0 and compact["legacy_exit_code"] == 0
assert compact["selected_project_count"] == 1
assert compact["validation_checked_project_count"] == 1
assert compact["zero_tracked_write"] is True
full_ref = compact["full_evidence_ref"]
full_path = Path(full_ref["path_or_artifact_ref"])
raw = full_path.read_bytes()
payload = raw[:-1] if raw.endswith(b"\n") else raw
assert "sha256:" + hashlib.sha256(payload).hexdigest() == full_ref["sha256"]
full = json.loads(payload)
assert [item["project_id"] for item in full["changed_scope"]["selected_projects"]] == ["PFI"]
assert full["validation"]["exit_code"] == 0
assert full["selector_parity"]["matches"] is True
assert full["zero_write_delta"]["clean"] is True
assert full["candidate_shadow_comparison"]["legacy_exit_code"] == 0
assert compact["stable_summary_hash"] == full["stable_summary_hash"]
changed_files = subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines()
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
assert len(ledger) == 20 and ledger == sorted(ledger)
assert changed_files == ledger
changed_files_bytes = ledger_path.read_bytes()
attestation = {
    "schema": "PFIV025PhaseCIAttestationV1",
    "contract_id": "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS",
    "acceptance_id": "ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT",
    "conflict_id": "PFI-V025-CONFLICT-GOVERNANCE-SCOPE",
    "override_id": "PFI-V025-S0-GOVERNANCE-COMPANIONS",
    "phase_base": base,
    "phase_commit": commit,
    "ci_evidence_ref": str(full_path),
    "ci_evidence_sha256": full_ref["sha256"],
    "ci_stable_summary_hash": compact["stable_summary_hash"],
    "ci_exit_code": 0,
    "selected_projects": ["PFI"],
    "changed_files": ledger,
    "changed_files_sha256": "sha256:" + hashlib.sha256(changed_files_bytes).hexdigest(),
    "status": "ci_pass_pending_final_stop_checks",
    "blocks_phase_0_2_candidate": True,
    "attested_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
    "contains_private_values": False,
}
with output_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(attestation, ensure_ascii=False, indent=2) + "\n")
PY
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ATTEST_DIR/phase_0_2_ci_attestation.json" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import hashlib, json, subprocess, sys
from pathlib import Path
path = Path(sys.argv[1])
base, commit = sys.argv[2:4]
d = json.loads(path.read_text(encoding="utf-8"))
assert d["schema"] == "PFIV025PhaseCIAttestationV1"
assert d["contract_id"] == "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS"
assert d["acceptance_id"] == "ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT"
assert d["conflict_id"] == "PFI-V025-CONFLICT-GOVERNANCE-SCOPE"
assert d["override_id"] == "PFI-V025-S0-GOVERNANCE-COMPANIONS"
assert d["phase_base"] == base and d["phase_commit"] == commit
assert d["ci_exit_code"] == 0 and d["selected_projects"] == ["PFI"]
assert d["status"] == "ci_pass_pending_final_stop_checks"
assert d["blocks_phase_0_2_candidate"] is True
assert d["contains_private_values"] is False
evidence_path = Path(d["ci_evidence_ref"])
raw = evidence_path.read_bytes()
payload = raw[:-1] if raw.endswith(b"\n") else raw
assert "sha256:" + hashlib.sha256(payload).hexdigest() == d["ci_evidence_sha256"]
full = json.loads(payload)
assert d["ci_stable_summary_hash"] == full["stable_summary_hash"]
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
actual = subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines()
assert len(ledger) == 20 and ledger == sorted(ledger)
assert d["changed_files"] == ledger == actual
assert d["changed_files_sha256"] == "sha256:" + hashlib.sha256(ledger_path.read_bytes()).hexdigest()
print(f"external_ci_attestation_path={path}")
print("external_ci_attestation_sha256=" + hashlib.sha256(path.read_bytes()).hexdigest())
PY
```

Required authoritative results:

```text
exit_code = 0
selected_project_count = 1 and selected project = PFI
legacy validation exit_code = 0
selector parity = true
zero_write_delta.clean = true
missing governance companions = 0
external CI binding status = ci_pass_pending_final_stop_checks
external CI binding blocks_phase_0_2_candidate = true
```

`check-render` drift is report-only in Lean v2 (`blocking_required_exit=false`) and must be disclosed if the unchanged canonical owner entries diverge. It is not flattened into either a pass or a failure. This Step creates only a structured **CI binding** for the tool-emitted full evidence path and SHA-256, stable summary hash, override/conflict IDs, Phase base/commit, and exact twenty paths. It deliberately remains blocking until Step 4 binds clean-worktree, final remote, commit-content and no-side-effect facts into the final attestation. Do not back-write either artifact into `terminal.log` or `evidence.json`.

- [ ] **Step 4: Recheck remote and all no-side-effect stop facts**

Run the following single complete block. It reconstructs the deterministic guard path, proves the post-run metadata fingerprint first, then performs the only Task 7 object hydration/final-remote/content proof and writes the final attestation. There is no separate preliminary Task 7 hydration whose fact could be lost. The pre-write `before.json` is retained on every failure and each attempt writes a unique `after-<attempt>.json`; any Step 4 failure therefore requires a full rerun from Step 3, which creates a new immutable attempt and repoints only the advisory pointer. Never rerun Step 4 against an existing attempt.

```bash
set -euo pipefail
export PHASE_COMMIT="$(git rev-parse HEAD)"
export PHASE_BASE="$(git rev-parse "$PHASE_COMMIT^")"
COMMON_GIT_DIR="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"
ATTEST_PARENT="$COMMON_GIT_DIR/codex-review/pfi-v025/stage_0/phase_0_2"
ATTEST_POINTER="$ATTEST_PARENT/current.path"
test -f "$ATTEST_POINTER"
ATTEST_DIR="$(PYTHONDONTWRITEBYTECODE=1 python3 -B - "$ATTEST_POINTER" <<'PY'
import sys
from pathlib import Path
print(Path(sys.argv[1]).read_text(encoding="utf-8").strip())
PY
)"
case "$ATTEST_DIR" in "$ATTEST_PARENT/${PHASE_COMMIT}.attempt."*) ;; *) exit 2 ;; esac
test -d "$ATTEST_DIR" && test ! -L "$ATTEST_DIR"
test ! -e "$ATTEST_DIR/phase_0_2_attestation.json"
export RUN_GUARD_ROOT="/private/tmp/pfi-v025-s0p02-guard-$(printf '%s' "$PHASE_BASE" | cut -c1-12)"
case "$RUN_GUARD_ROOT" in
  /private/tmp/pfi-v025-s0p02-guard-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f]) ;;
  *) exit 2 ;;
esac
test -f "$RUN_GUARD_ROOT/before.json"
AFTER_FINGERPRINT="$RUN_GUARD_ROOT/after-$(basename "$ATTEST_DIR").json"
test ! -e "$AFTER_FINGERPRINT"
set +e
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$AFTER_FINGERPRINT" <<'PY'
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

output = Path(sys.argv[1])
root = Path.cwd()
targets = {
    "user_pfi": Path.home() / ".pfi",
    "applications_app": Path("/Applications/PFI.app"),
    "desktop_app": Path.home() / "Desktop/PFI.app",
    "downloads_app": Path.home() / "Downloads/PFI.app",
    "repo_data": root / "PFI/data",
    "repo_metadatabase": root / "PFI/MetaDatabase",
}

def fingerprint(path):
    digest = hashlib.sha256()
    count = 0
    if not path.exists() and not path.is_symlink():
        return {"state": "missing", "entry_count": 0, "metadata_sha256": hashlib.sha256(b"missing").hexdigest()}
    pending = [path]
    while pending:
        current = pending.pop()
        st = current.lstat()
        rel = "." if current == path else current.relative_to(path).as_posix()
        payload = [rel, str(stat.S_IFMT(st.st_mode)), str(st.st_mode & 0o7777), str(st.st_size), str(st.st_mtime_ns)]
        if current.is_symlink():
            payload.append(os.readlink(current))
        digest.update("\0".join(payload).encode("utf-8", "surrogateescape"))
        count += 1
        if current.is_dir() and not current.is_symlink():
            pending.extend(sorted(current.iterdir(), reverse=True))
    return {"state": "present", "entry_count": count, "metadata_sha256": digest.hexdigest()}

result = {label: fingerprint(path) for label, path in targets.items()}
output.write_text(json.dumps(result, sort_keys=True) + "\n", encoding="utf-8")
print("no_side_effect_after=" + hashlib.sha256(output.read_bytes()).hexdigest())
PY
fingerprint_rc=$?
if [ "$fingerprint_rc" -eq 0 ]; then
  PYTHONDONTWRITEBYTECODE=1 python3 -B - "$RUN_GUARD_ROOT/before.json" "$AFTER_FINGERPRINT" <<'PY'
import hashlib, json, sys
from pathlib import Path
before, after = (Path(value) for value in sys.argv[1:])
assert json.loads(before.read_text(encoding="utf-8")) == json.loads(after.read_text(encoding="utf-8")), "protected metadata changed"
print("no_side_effect_postcheck=" + hashlib.sha256(after.read_bytes()).hexdigest())
PY
  rc=$?
  if [ "$rc" -eq 0 ]; then
    NO_SIDE_EFFECT_ARTIFACT="$ATTEST_DIR/no_side_effect_fingerprints.json"
    PYTHONDONTWRITEBYTECODE=1 python3 -B - "$RUN_GUARD_ROOT/before.json" "$AFTER_FINGERPRINT" "$NO_SIDE_EFFECT_ARTIFACT" <<'PY'
import json, sys
from pathlib import Path
before, after, output = (Path(value) for value in sys.argv[1:])
before_value = json.loads(before.read_text(encoding="utf-8"))
after_value = json.loads(after.read_text(encoding="utf-8"))
assert before_value == after_value
with output.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps({"before": before_value, "after": after_value}, sort_keys=True) + "\n")
PY
    rc=$?
    if [ "$rc" -eq 0 ]; then
      NO_SIDE_EFFECT_ARTIFACT_SHA="$(openssl dgst -sha256 "$NO_SIDE_EFFECT_ARTIFACT" | awk '{print $NF}')"
    fi
  fi
else
  rc=$fingerprint_rc
fi
if [ "$rc" -ne 0 ]; then exit "$rc"; fi

# Authoritative final remote/content proof: this is intentionally after the
# no-side-effect comparison, and its result is bound into one final attestation.
set -euo pipefail
test -z "$(git status --porcelain=v1 --untracked-files=all)"
INITIAL_LIVE_MAIN="$(PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import json
from pathlib import Path
print(json.loads(Path("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json").read_text(encoding="utf-8"))["initial_live_main"])
PY
)"
INITIAL_HYDRATED="$(PYTHONDONTWRITEBYTECODE=1 python3 -B - <<'PY'
import json
from pathlib import Path
value = json.loads(Path("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json").read_text(encoding="utf-8"))["initial_remote_object_hydration_performed"]
assert type(value) is bool
print(str(value).lower())
PY
)"
FINAL_LIVE_MAIN="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
test -n "$FINAL_LIVE_MAIN"
FINAL_REFS_BEFORE="$(git for-each-ref --format='%(refname) %(objectname)')"
FINAL_REFS_BEFORE_SHA="$(printf '%s' "$FINAL_REFS_BEFORE" | openssl dgst -sha256 | awk '{print $NF}')"
FINAL_FETCH_HEAD_PATH="$(git rev-parse --git-path FETCH_HEAD)"
if [ -e "$FINAL_FETCH_HEAD_PATH" ]; then
  FINAL_FETCH_HEAD_BEFORE_STATE=present
  FINAL_FETCH_HEAD_BEFORE_HASH="$(openssl dgst -sha256 "$FINAL_FETCH_HEAD_PATH" | awk '{print $NF}')"
else
  FINAL_FETCH_HEAD_BEFORE_STATE=missing
  FINAL_FETCH_HEAD_BEFORE_HASH=missing
fi
FINAL_SHALLOW_PATH="$(git rev-parse --git-path shallow)"
if [ -e "$FINAL_SHALLOW_PATH" ]; then
  FINAL_SHALLOW_BEFORE_STATE=present
  FINAL_SHALLOW_BEFORE_HASH="$(openssl dgst -sha256 "$FINAL_SHALLOW_PATH" | awk '{print $NF}')"
else
  FINAL_SHALLOW_BEFORE_STATE=missing
  FINAL_SHALLOW_BEFORE_HASH=missing
fi
FINAL_HYDRATED=false
if ! GIT_NO_LAZY_FETCH=1 git cat-file -e "$FINAL_LIVE_MAIN^{commit}" 2>/dev/null; then
  FINAL_HYDRATED=true
  GIT_TERMINAL_PROMPT=0 git -c maintenance.auto=false -c fetch.writeCommitGraph=false -c fetch.recurseSubmodules=false fetch \
    --no-auto-maintenance --no-write-commit-graph --no-recurse-submodules --no-prune --no-prune-tags \
    --no-write-fetch-head --no-tags origin "$FINAL_LIVE_MAIN"
fi
FINAL_REFS_AFTER="$(git for-each-ref --format='%(refname) %(objectname)')"
FINAL_REFS_AFTER_SHA="$(printf '%s' "$FINAL_REFS_AFTER" | openssl dgst -sha256 | awk '{print $NF}')"
test "$FINAL_REFS_AFTER" = "$FINAL_REFS_BEFORE"
if [ -e "$FINAL_FETCH_HEAD_PATH" ]; then
  FINAL_FETCH_HEAD_AFTER_STATE=present
  FINAL_FETCH_HEAD_AFTER_HASH="$(openssl dgst -sha256 "$FINAL_FETCH_HEAD_PATH" | awk '{print $NF}')"
else
  FINAL_FETCH_HEAD_AFTER_STATE=missing
  FINAL_FETCH_HEAD_AFTER_HASH=missing
fi
test "$FINAL_FETCH_HEAD_AFTER_STATE" = "$FINAL_FETCH_HEAD_BEFORE_STATE"
test "$FINAL_FETCH_HEAD_AFTER_HASH" = "$FINAL_FETCH_HEAD_BEFORE_HASH"
if [ -e "$FINAL_SHALLOW_PATH" ]; then
  FINAL_SHALLOW_AFTER_STATE=present
  FINAL_SHALLOW_AFTER_HASH="$(openssl dgst -sha256 "$FINAL_SHALLOW_PATH" | awk '{print $NF}')"
else
  FINAL_SHALLOW_AFTER_STATE=missing
  FINAL_SHALLOW_AFTER_HASH=missing
fi
test "$FINAL_SHALLOW_AFTER_STATE" = "$FINAL_SHALLOW_BEFORE_STATE"
test "$FINAL_SHALLOW_AFTER_HASH" = "$FINAL_SHALLOW_BEFORE_HASH"
GIT_NO_LAZY_FETCH=1 git cat-file -e "$FINAL_LIVE_MAIN^{commit}"
FINAL_REMOTE_BASE="$(GIT_NO_LAZY_FETCH=1 git merge-base "$PHASE_COMMIT" "$FINAL_LIVE_MAIN")"
GIT_NO_LAZY_FETCH=1 git diff --quiet "$FINAL_REMOTE_BASE..$FINAL_LIVE_MAIN" -- PFI
test -z "$(git status --porcelain=v1 --untracked-files=all)"
diff -u \
  <(LC_ALL=C sort PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt) \
  <(git diff --name-only "$PHASE_BASE..$PHASE_COMMIT" | LC_ALL=C sort)

CI_ATTESTATION="$ATTEST_DIR/phase_0_2_ci_attestation.json"
FINAL_ATTESTATION="$ATTEST_DIR/phase_0_2_attestation.json"
test -f "$CI_ATTESTATION"
test ! -e "$FINAL_ATTESTATION"
CANDIDATE_ATTESTATION="$(mktemp "$ATTEST_DIR/phase_0_2_attestation.candidate.XXXXXX")"
PYTHONDONTWRITEBYTECODE=1 python3 -B - \
  "$CI_ATTESTATION" "$CANDIDATE_ATTESTATION" "$PHASE_BASE" "$PHASE_COMMIT" \
  "$INITIAL_LIVE_MAIN" "$INITIAL_HYDRATED" "$FINAL_LIVE_MAIN" "$FINAL_REMOTE_BASE" "$FINAL_HYDRATED" \
  "$FINAL_REFS_BEFORE_SHA" "$FINAL_REFS_AFTER_SHA" \
  "$FINAL_FETCH_HEAD_BEFORE_STATE" "$FINAL_FETCH_HEAD_BEFORE_HASH" \
  "$FINAL_FETCH_HEAD_AFTER_STATE" "$FINAL_FETCH_HEAD_AFTER_HASH" \
  "$FINAL_SHALLOW_BEFORE_STATE" "$FINAL_SHALLOW_BEFORE_HASH" \
  "$FINAL_SHALLOW_AFTER_STATE" "$FINAL_SHALLOW_AFTER_HASH" \
  "$NO_SIDE_EFFECT_ARTIFACT" "$NO_SIDE_EFFECT_ARTIFACT_SHA" <<'PY'
import hashlib, json, re, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

(
    ci_path_s, output_path_s, base, commit, initial_live, initial_hydrated_s,
    final_live, remote_base, final_hydrated_s, refs_before_sha, refs_after_sha,
    fetch_before_state, fetch_before_hash, fetch_after_state, fetch_after_hash,
    shallow_before_state, shallow_before_hash, shallow_after_state, shallow_after_hash,
    no_side_effect_ref, no_side_effect_sha,
) = sys.argv[1:]
ci_path, output_path = Path(ci_path_s), Path(output_path_s)
ci_raw = ci_path.read_bytes()
ci = json.loads(ci_raw)
assert ci["schema"] == "PFIV025PhaseCIAttestationV1"
assert ci["phase_base"] == base and ci["phase_commit"] == commit
assert ci["status"] == "ci_pass_pending_final_stop_checks"
assert ci["blocks_phase_0_2_candidate"] is True
assert re.fullmatch(r"[0-9a-f]{40}", initial_live)
assert re.fullmatch(r"[0-9a-f]{40}", final_live)
assert re.fullmatch(r"[0-9a-f]{40}", remote_base)
assert initial_hydrated_s in ("true", "false") and final_hydrated_s in ("true", "false")
assert refs_before_sha == refs_after_sha
assert (fetch_before_state, fetch_before_hash) == (fetch_after_state, fetch_after_hash)
assert (shallow_before_state, shallow_before_hash) == (shallow_after_state, shallow_after_hash)
assert re.fullmatch(r"[0-9a-f]{64}", no_side_effect_sha)
no_side_effect_path = Path(no_side_effect_ref)
assert hashlib.sha256(no_side_effect_path.read_bytes()).hexdigest() == no_side_effect_sha
no_side_effect = json.loads(no_side_effect_path.read_text(encoding="utf-8"))
assert no_side_effect["before"] == no_side_effect["after"]
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
actual = subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines()
assert len(ledger) == 20 and ledger == sorted(ledger) and ledger == actual
attestation = {
    "schema": "PFIV025PhaseAttestationCandidateV1",
    "contract_id": ci["contract_id"],
    "acceptance_id": ci["acceptance_id"],
    "conflict_id": ci["conflict_id"],
    "override_id": ci["override_id"],
    "phase_base": base,
    "phase_commit": commit,
    "ci_attestation_ref": str(ci_path),
    "ci_attestation_sha256": "sha256:" + hashlib.sha256(ci_raw).hexdigest(),
    "ci_evidence_ref": ci["ci_evidence_ref"],
    "ci_evidence_sha256": ci["ci_evidence_sha256"],
    "ci_stable_summary_hash": ci["ci_stable_summary_hash"],
    "ci_exit_code": ci["ci_exit_code"],
    "selected_projects": ci["selected_projects"],
    "changed_files": ledger,
    "changed_files_sha256": "sha256:" + hashlib.sha256(ledger_path.read_bytes()).hexdigest(),
    "initial_live_main": initial_live,
    "final_live_main": final_live,
    "final_remote_base": remote_base,
    "initial_remote_object_hydration_performed": initial_hydrated_s == "true",
    "final_remote_object_hydration_performed": final_hydrated_s == "true",
    "ref_snapshot_sha256_before": "sha256:" + refs_before_sha,
    "ref_snapshot_sha256_after": "sha256:" + refs_after_sha,
    "fetch_head_before": {"state": fetch_before_state, "sha256": fetch_before_hash},
    "fetch_head_after": {"state": fetch_after_state, "sha256": fetch_after_hash},
    "shallow_before": {"state": shallow_before_state, "sha256": shallow_before_hash},
    "shallow_after": {"state": shallow_after_state, "sha256": shallow_after_hash},
    "remote_pfi_drift": False,
    "clean_worktree": True,
    "commit_content_verified": True,
    "no_side_effect_artifact_ref": str(no_side_effect_path),
    "no_side_effect_artifact_sha256": "sha256:" + no_side_effect_sha,
    "no_side_effect_postcheck": True,
    "status": "candidate_pending_independent_validation",
    "blocks_phase_0_2_candidate": True,
    "attested_at": datetime.now(ZoneInfo("Australia/Sydney")).isoformat(),
    "contains_private_values": False,
}
output_path.write_text(json.dumps(attestation, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY
PYTHONDONTWRITEBYTECODE=1 python3 -B - "$CANDIDATE_ATTESTATION" "$FINAL_ATTESTATION" "$PHASE_BASE" "$PHASE_COMMIT" <<'PY'
import fcntl, hashlib, json, os, re, subprocess, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
candidate_path, path = (Path(value) for value in sys.argv[1:3])
base, commit = sys.argv[3:5]
assert not path.exists(), "stale final attestation exists"
assert candidate_path.parent == path.parent
assert candidate_path.name.startswith("phase_0_2_attestation.candidate.")
assert candidate_path.is_file() and not candidate_path.is_symlink()
d = json.loads(candidate_path.read_text(encoding="utf-8"))
assert d["schema"] == "PFIV025PhaseAttestationCandidateV1"
assert d["contract_id"] == "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS"
assert d["acceptance_id"] == "ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT"
assert d["conflict_id"] == "PFI-V025-CONFLICT-GOVERNANCE-SCOPE"
assert d["override_id"] == "PFI-V025-S0-GOVERNANCE-COMPANIONS"
assert d["phase_base"] == base and d["phase_commit"] == commit
assert d["status"] == "candidate_pending_independent_validation"
assert d["blocks_phase_0_2_candidate"] is True
assert d["remote_pfi_drift"] is False
assert d["clean_worktree"] is True and d["commit_content_verified"] is True
assert d["ref_snapshot_sha256_before"] == d["ref_snapshot_sha256_after"]
assert d["fetch_head_before"] == d["fetch_head_after"]
assert d["shallow_before"] == d["shallow_after"]
assert re.fullmatch(r"[0-9a-f]{40}", d["initial_live_main"])
assert re.fullmatch(r"[0-9a-f]{40}", d["final_live_main"])
assert re.fullmatch(r"[0-9a-f]{40}", d["final_remote_base"])
assert type(d["initial_remote_object_hydration_performed"]) is bool
assert type(d["final_remote_object_hydration_performed"]) is bool
assert subprocess.check_output(["git", "status", "--porcelain=v1", "--untracked-files=all"], text=True) == ""
live_line = subprocess.check_output(["git", "ls-remote", "origin", "refs/heads/main"], text=True).strip()
assert live_line and live_line.split()[0] == d["final_live_main"]
no_lazy_env = dict(os.environ, GIT_NO_LAZY_FETCH="1")
subprocess.run(["git", "cat-file", "-e", f'{d["final_live_main"]}^{{commit}}'], check=True, env=no_lazy_env)
verified_remote_base = subprocess.check_output(["git", "merge-base", commit, d["final_live_main"]], text=True, env=no_lazy_env).strip()
assert verified_remote_base == d["final_remote_base"]
assert subprocess.run(["git", "diff", "--quiet", f'{verified_remote_base}..{d["final_live_main"]}', "--", "PFI"], env=no_lazy_env).returncode == 0
committed_evidence = json.loads(Path("PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json").read_text(encoding="utf-8"))
assert committed_evidence["initial_live_main"] == d["initial_live_main"]
assert committed_evidence["initial_remote_object_hydration_performed"] is d["initial_remote_object_hydration_performed"]
assert d["no_side_effect_postcheck"] is True
no_side_effect_path = Path(d["no_side_effect_artifact_ref"])
assert no_side_effect_path == path.parent / "no_side_effect_fingerprints.json"
assert d["no_side_effect_artifact_sha256"] == "sha256:" + hashlib.sha256(no_side_effect_path.read_bytes()).hexdigest()
no_side_effect = json.loads(no_side_effect_path.read_text(encoding="utf-8"))
assert no_side_effect["before"] == no_side_effect["after"]
ci_path = Path(d["ci_attestation_ref"])
assert ci_path == path.parent / "phase_0_2_ci_attestation.json"
assert d["ci_attestation_sha256"] == "sha256:" + hashlib.sha256(ci_path.read_bytes()).hexdigest()
ci = json.loads(ci_path.read_text(encoding="utf-8"))
assert ci["ci_evidence_ref"] == d["ci_evidence_ref"]
evidence_path = Path(d["ci_evidence_ref"])
raw = evidence_path.read_bytes()
payload = raw[:-1] if raw.endswith(b"\n") else raw
assert d["ci_evidence_sha256"] == "sha256:" + hashlib.sha256(payload).hexdigest()
assert d["ci_stable_summary_hash"] == json.loads(payload)["stable_summary_hash"]
ledger_path = Path("PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt")
ledger = ledger_path.read_text(encoding="utf-8").splitlines()
actual = subprocess.check_output(["git", "diff", "--name-only", f"{base}..{commit}"], text=True).splitlines()
assert d["changed_files"] == ledger == actual
assert d["changed_files_sha256"] == "sha256:" + hashlib.sha256(ledger_path.read_bytes()).hexdigest()
assert d["contains_private_values"] is False
final = dict(d)
final["schema"] = "PFIV025PhaseAttestationV1"
final["status"] = "resolved_by_approved_override"
final["blocks_phase_0_2_candidate"] = False
final["independently_validated_at"] = datetime.now(ZoneInfo("Australia/Sydney")).isoformat()
publication_source_path = path.with_name(f"{path.name}.published-source.{os.getpid()}")
assert not publication_source_path.exists()
final["publication_source_ref"] = str(publication_source_path)
with publication_source_path.open("x", encoding="utf-8") as stream:
    stream.write(json.dumps(final, ensure_ascii=False, indent=2) + "\n")
verified_final = json.loads(publication_source_path.read_text(encoding="utf-8"))
assert verified_final["schema"] == "PFIV025PhaseAttestationV1"
assert verified_final["status"] == "resolved_by_approved_override"
assert verified_final["blocks_phase_0_2_candidate"] is False
assert verified_final["phase_base"] == base and verified_final["phase_commit"] == commit
assert verified_final["publication_source_ref"] == str(publication_source_path)
final_sha256 = hashlib.sha256(publication_source_path.read_bytes()).hexdigest()
phase_parent = path.parent.parent
lock_path = phase_parent / "phase.lock"
pointer_path = phase_parent / "current.path"
with lock_path.open("a+", encoding="utf-8") as lock_stream:
    fcntl.flock(lock_stream.fileno(), fcntl.LOCK_EX)
    assert not list(phase_parent.glob("*.attempt.*/phase_0_2_attestation.json")), "concurrent final attestation exists"
    assert pointer_path.read_text(encoding="utf-8").strip() == str(path.parent)
    os.link(publication_source_path, path)
d = verified_final
assert d["schema"] == "PFIV025PhaseAttestationV1"
assert d["status"] == "resolved_by_approved_override"
assert d["blocks_phase_0_2_candidate"] is False
assert d["phase_base"] == base and d["phase_commit"] == commit
print(f"external_attestation_path={path}")
print("external_attestation_sha256=" + final_sha256)
PY
case "$RUN_GUARD_ROOT" in
  /private/tmp/pfi-v025-s0p02-guard-[0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f][0-9a-f])
    if rm -rf -- "$RUN_GUARD_ROOT"; then
      printf 'post_attestation_guard_cleanup=pass\n'
    else
      printf 'post_attestation_guard_cleanup=warning_retained_for_manual_cleanup\n' >&2
    fi
    ;;
  *) printf 'post_attestation_guard_cleanup=warning_invalid_path\n' >&2 ;;
esac
```

Expected: identical aggregate fingerprints and an unchanged postcheck hash; a second authoritative final-remote proof with unchanged refs, `FETCH_HEAD` and shallow boundary; exact commit/ledger parity; and a validated `phase_0_2_attestation.json` whose lifecycle is `resolved_by_approved_override` with `blocks_phase_0_2_candidate=false`. The generator writes only a uniquely named blocking candidate; all independent checks run against that candidate, then the fixed Phase `flock` serializes a global-final recheck, pointer check and no-clobber hard-link of the fully verified immutable publication source to the previously absent final path. The OS releases the lock on process exit; a failed publish leaves the pointer and baseline reusable from a new Step 3 attempt, with no resolved final artifact. No protected file content is read or emitted. Pre-final failures preserve the guard root for retry; post-final cleanup success or warning is reported separately and cannot change the accepted attestation.

- [ ] **Step 5: Apply the candidate result and stop before Phase 0.3**

Only after all pre-commit checks, independent re-review, commit verification, and external CI pass may the authoritative result be:

```text
Stage 0 / Phase 0.2 candidate_pass accepted by Codex; Phase 0.3 remains not_started.
```

This is not Stage 0 acceptance and not v0.2.5 completion. The user has authorized continued goal execution, but the one-Phase-per-run rule requires this run to stop here.

---

## Completion Evidence Map

| Requirement | Authoritative evidence |
|---|---|
| `S0-P2-T1` active requirements | JSON schema + strong semantic gate + route snapshot |
| `S0-P2-T2` history no longer drives | decision table with stable IDs/dispositions and governance applicability notes |
| `S0-P2-T3` one product/UI boundary | boundary matrix and exact Alpha/Cloudflare/PFI OS/candidate constraints |
| `S0-P2-T4` no auto-advance | JSON execution policy + run contract + mandatory stop statement |
| Approved 20-file override | policy override record, exact changed ledger, staged-name parity, sync validator |
| No model/formula/parameter value drift | empty changed-ID arrays and direct base/current registry structural comparison |
| Task Pack schemas | streamed ZIP schema validation with `check_schema` and instance validation |
| Current-vs-target routes | executable Node snapshot + JSON blockers/resolution tasks |
| Privacy and no side effects | staged-blob machine privacy scan, isolated test environment, and protected metadata before/after fingerprints |
| Append-only history | exact base-prefix assertion + one appended event |
| Governance acceptance | clean selective-shadow Lean CI exit `0`, pending CI binding, and final structured attestation binding clean worktree, commit content, final remote, no-side-effect hash and resolved override lifecycle |
| Phase candidate acceptance | independent reviews, remediation/re-review, exact Phase commit, Codex explicit result |

Phase 0.2 completion does not complete Stage 0. Phase 0.3, whole-Stage independent review, finding remediation, re-review, explicit Stage acceptance, Stages 1-12, final GitHub main upload, and the single canonical App reinstall remain required by the full goal.
