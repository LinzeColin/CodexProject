# Memory Atlas v1.2 R7 Data Parity And Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task.
> Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize real credential-free public transcripts from all three source
families, freeze one immutable Memory Atlas release snapshot, prove local/Pages candidate
parity and rehearse tracked-files-only recovery without performing the R8 delivery.

**Architecture:** Existing sync connectors gain one shared recursive public sanitizer and
versioned append-only transcript outputs. A hardened manifest/ledger and full-size privacy
audit protect those outputs. Separate release/parity/recovery scripts freeze the rebuilt
snapshot and verify a clean archive of the candidate commit.

**Tech Stack:** Python 3 standard library, React/Vite build, Git archive, JSON/JSONL,
`unittest`, existing npm/Playwright regressions.

## Global Constraints

- Complete only `R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY` in this run.
- Work on the canonical local `main`; create no branch, PR, merge or rebase.
- No GitHub push, app reinstall or Cloudflare deployment before R8.
- Original ChatGPT ZIP, original Codex logs, credentials and binary attachment bodies are
  private inputs and must not enter Git.
- Keep every ordinary text field after redaction; do not truncate ordinary transcript
  text.
- Redact credentials, email, phone and machine-local absolute paths; replace only
  non-text binary/data blobs with deterministic SHA/byte-count markers.
- Public raw outputs are append-only, content-versioned and at most 40 MiB per file.
- A manifest run ID and release ID are immutable.
- R7 recovery uses tracked files from a local candidate commit; actual GitHub clone proof
  remains mandatory in R8.
- Expected requirement aggregate is `VERIFIED 53 / PARTIAL 2 / FAILED 3 /
  NOT_VERIFIED 0`; release remains `FAIL_REMEDIATION_REQUIRED`.

---

### Task 1: Shared Sanitizer And Real Public Transcript Connectors

**Files:**

- Create: `scripts/public_raw_sanitizer.py`
- Modify: `scripts/sync_chatgpt_memory_data.py`
- Modify: `scripts/sync_codex_memory_data.py`
- Modify: `scripts/sync_future_agent_data.py`
- Modify: `scripts/atlasctl.py`
- Modify: `机器治理/同步与备份/sync_source_registry.json`
- Test: `tests/test_memory_atlas_r7_public_raw.py`
- Regression: `tests/test_s04p1_chatgpt_sync.py`
- Regression: `tests/test_s04p2_codex_agent_sync.py`

**Interfaces:**

```python
MAX_PUBLIC_RAW_FILE_BYTES = 40 * 1024 * 1024
BINARY_STRING_MIN_BYTES = 256 * 1024

def sanitize_public_value(value: Any) -> tuple[Any, dict[str, int]]: ...
def binary_omission_marker(value: str) -> str: ...
def export_codex_session_jsonl(source: Path, codex_home: Path,
                              output_root: Path) -> dict[str, Any]: ...
```

ChatGPT CLI adds `--redact-for-public-backup`. Codex CLI adds
`--public-transcripts`. Future-agent CLI adds `--markdown-report`, `--event-id` and
versioned output names. Existing strict/default behavior remains compatible.

- [ ] Write RED sanitizer tests that require credential/email/phone/absolute-path
  replacement, deterministic binary markers, unchanged ordinary long text and recursive
  count aggregation.
- [ ] Write a RED ChatGPT test whose credential-bearing official export fails in default
  mode but passes only with `--redact-for-public-backup`, writes a versioned transcript,
  processed manifest, export SHA and no source absolute path.
- [ ] Write a RED Codex test using a real-shaped JSONL session with message, tool result,
  secret, local path and data URL. Require versioned chunk output, every JSON event,
  redaction markers, source-relative provenance and no file over 40 MiB.
- [ ] Write a RED future-agent Markdown test that produces one versioned real report event
  and a registry entry with `source_type=other_agent`.
- [ ] Run:

  ```bash
  PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
    tests.test_memory_atlas_r7_public_raw -q
  ```

  Expected: FAIL because the sanitizer and new CLI contracts do not exist.
- [ ] Implement `public_raw_sanitizer.py` with `privacy_guard.redact_text`, recursive
  traversal, data-URL/base64 detection, SHA/byte markers and hard event/file limits.
- [ ] Implement content-hash-versioned ChatGPT outputs and current processed conversation
  manifest. Keep default credential failure; enable sanitization only through the exact
  R7 flag.
- [ ] Implement streaming Codex JSONL export with event-boundary chunking. Record chunk
  refs in the aggregate public snapshot and never expose an absolute source path.
- [ ] Implement Markdown future-agent import and add the concrete `codex-reviewer` source
  without removing `future_agent_template`.
- [ ] Wire the new exact flags through `atlasctl sync` without changing hosted/browser
  mutation boundaries.
- [ ] Run the focused and S04 connector regressions until green.
- [ ] Run `git diff --check`, review output schemas and commit the connector task locally.

### Task 2: Immutable Non-Empty Raw Manifest And Canonical Events

**Files:**

- Modify: `scripts/raw_archive_manifest.py`
- Create: `scripts/audit_memory_atlas_public_raw.py`
- Modify: `scripts/extract_memory_atlas_facets.py`
- Modify: `机器治理/同步与备份/raw_manifest_ledger_policy.v1_2_s03_p3.json`
- Test: `tests/test_memory_atlas_r7_raw_integrity.py`
- Regression: `tests/test_s03p3_raw_manifest.py`
- Regression: `tests/test_memory_atlas_facets.py`

**Interfaces:**

```python
class ManifestConflict(ValueError): ...

def update_hash_ledger(existing: list[dict[str, Any]],
                       current: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
def generate_raw_manifest(database_dir: Path, run_id: str,
                          imported_at: str | None = None,
                          require_non_empty: bool = False) -> dict[str, Any]: ...
def audit_public_raw(database_dir: Path,
                     max_file_bytes: int = 40 * 1024 * 1024) -> dict[str, Any]: ...
```

- [ ] Write a RED test proving an existing manifest run ID cannot be rewritten with
  different rows/imported time, while byte-identical regeneration is idempotent.
- [ ] Write a RED union-ledger test: adding a new version preserves old rows; same path
  with a changed SHA, deleted raw, or changed raw fails.
- [ ] Write a RED `require_non_empty` test that rejects zero raw rows and requires
  ChatGPT, Codex and at least one `agent:*` source.
- [ ] Write a RED full-size public-raw audit test that finds secrets/absolute paths in a
  file larger than 1 MB, rejects raw data URLs and accepts deterministic binary markers.
- [ ] Write RED facet tests that select one newest ChatGPT version, use Codex transcript
  refs and emit at least one real future-agent event with raw evidence.
- [ ] Run the focused tests and confirm the expected feature-missing failures.
- [ ] Implement immutable manifests, union-ledger updates, non-empty/source-family gates
  and unchanged append-only audit behavior.
- [ ] Implement streaming JSON/JSONL public-raw validation independent of Git tracking or
  file size.
- [ ] Implement version-aware facet selection and exact public transcript evidence refs.
- [ ] Re-run focused tests and the historical S03/S05 regressions until green.
- [ ] Commit the integrity/extractor task locally.

### Task 3: Materialize Authorized Sources And Rebuild The Candidate

**Files generated or modified by existing/new commands:**

- Add: `data/public_raw/chatgpt/*.json`
- Add: `data/public_raw/codex/*.json`
- Add: `data/public_raw/codex/sessions/*.jsonl`
- Add: `data/public_raw/agents/codex-reviewer/*.json`
- Modify: `data/processed/conversations/conversation_manifest.jsonl`
- Modify: `data/processed/codex/*`
- Modify: `data/derived/chatgpt/*`
- Modify: `data/derived/codex/*`
- Modify: `data/derived/agents/*`
- Modify: `data/derived/behavior_intelligence/*`
- Modify: `data/derived/visualization/memory_atlas.json`
- Add: `机器治理/证据与日志/raw_archive_manifests/raw_manifest.v1_2_r7.jsonl`
- Modify: `机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl`
- Add: `机器治理/证据与日志/remediation/v1_2_r7/source_provenance.json`

- [ ] Record source hashes/counts in `/tmp` without writing source paths to tracked
  evidence. Require the ChatGPT ZIP to contain four `conversations-*.json` chunks and at
  least one conversation.
- [ ] Run ChatGPT apply with `--redact-for-public-backup`; require 379 current
  conversations, non-zero messages/redactions and no browser mutation.
- [ ] Run Codex apply with `--public-transcripts`; capture a stable point-in-time source
  inventory, non-zero session/chunk counts and append-only outputs.
- [ ] Import the actual R6 reviewer report through the Markdown future-agent adapter.
- [ ] Run `audit_memory_atlas_public_raw.py` before staging; require zero credentials,
  absolute paths, unmarked binary and oversize files.
- [ ] Generate `raw_manifest.v1_2_r7.jsonl` with `--require-non-empty`; require all three
  source families, then run append-only audit.
- [ ] Run facets, clusters, low-value loops, opportunities, economic proxy, information
  ROI, Formula, latent, self-iteration and decision-debt builders in dependency order.
- [ ] Rebuild `memory_atlas.json`; require current ChatGPT/Codex/future-agent counts and
  raw evidence refs rather than processed-manifest missing reasons.
- [ ] Run privacy audit and stage the new raw files. Re-run privacy/public-raw audits so
  staged files, including files over 1 MB, are covered.
- [ ] Commit the immutable raw/derived candidate locally. Do not push.

### Task 4: Immutable Release Snapshot And Candidate Parity

**Files:**

- Create: `scripts/materialize_memory_atlas_release.py`
- Create: `scripts/audit_memory_atlas_snapshot_parity.py`
- Modify: `scripts/install_memory_atlas_app.py`
- Modify: `scripts/deploy_memory_atlas_cloudflare.py`
- Test: `tests/test_memory_atlas_r7_release_parity.py`
- Regression: `tests/test_memory_atlas_deployment.py`
- Regression: `tests/test_memory_atlas_cloudflare_deploy.py`
- Add generated: `data/releases/memory_atlas/v1_2/<release_id>/memory_atlas.json`
- Add generated: `data/releases/memory_atlas/v1_2/<release_id>/release_manifest.json`
- Add generated: `机器治理/发布快照/memory_atlas_current_release.json`

**Interfaces:**

```python
def materialize_release(database_dir: Path, release_id: str,
                        snapshot_path: Path, raw_manifest_path: Path) -> dict[str, Any]: ...
def verify_current_release(database_dir: Path) -> dict[str, Any]: ...
def audit_snapshot_parity(database_dir: Path, local_runtime: Path,
                          pages_candidate: Path) -> dict[str, Any]: ...
```

- [ ] Write RED tests for immutable release ID, relative-only manifest paths, snapshot
  counts/SHA, raw-manifest SHA and source-package hashes.
- [ ] Write RED parity tests requiring exact release/derived/local/Pages hashes and a
  clear FAIL result for any one-byte mismatch or missing candidate.
- [ ] Add RED installer/deployer tests requiring current-release verification. The
  deploy plan must not rebuild a mutable snapshot after release creation; a newly
  installed launcher must keep the pinned release unless an explicit refresh/sync occurs.
- [ ] Run focused tests and confirm missing-script/legacy-command failures.
- [ ] Implement immutable release creation/verification and exact parity audit.
- [ ] Integrate release resolution into static runtime preparation, build metadata and
  launcher default behavior while preserving explicit local sync refresh.
- [ ] Replace deploy-time snapshot rebuild with current-release verification and post-build
  parity audit; retain authorization and live verification gates.
- [ ] Re-run focused installer/deployer tests, lint and production build until green.
- [ ] Materialize one R7 release ID, build Pages candidate, create a temporary local
  runtime candidate and run exact parity audit.
- [ ] Commit release scripts, manifests and candidate evidence locally.

### Task 5: Tracked-Files-Only Recovery Rehearsal

**Files:**

- Create: `scripts/audit_memory_atlas_github_recovery.py`
- Test: `tests/test_memory_atlas_r7_recovery.py`
- Add evidence: `机器治理/证据与日志/remediation/v1_2_r7/recovery/status.json`

**Interfaces:**

```python
def build_recovery_plan(repo_root: Path, commit: str) -> list[list[str]]: ...
def audit_recovered_tree(database_dir: Path) -> dict[str, Any]: ...
def rehearse_recovery(repo_root: Path, commit: str,
                      output_dir: Path) -> dict[str, Any]: ...
```

- [ ] Write RED tests requiring an exact commit, `git archive`, no untracked inputs,
  source-package hash restoration, raw/ledger/release validation and relative-only
  evidence paths.
- [ ] Write a RED failure test for missing source package, empty ledger, snapshot mismatch
  and build command failure.
- [ ] Implement temporary archive extraction, command execution with bounded output tails,
  cleanup and machine-portable status evidence.
- [ ] Run focused recovery tests until green.
- [ ] Commit the recovery script/tests locally.
- [ ] Rehearse recovery from the new committed candidate, run fresh `npm ci` and build in
  the recovered tree, and require Pages snapshot hash equality.
- [ ] Confirm the recovery temp directory and npm/build caches are removed after evidence
  capture.

### Task 6: Full Regression, Independent Review And R7 Closeout

**Files:**

- Create: `docs/remediation/memory_atlas_v1_2/R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY.md`
- Create: `机器治理/证据与日志/remediation/v1_2_r7/status.json`
- Create: `机器治理/证据与日志/remediation/v1_2_r7/requirements_gap_delta.csv`
- Modify: `docs/remediation/memory_atlas_v1_2/HANDOFF.md`
- Modify: `docs/superpowers/plans/2026-07-10-memory-atlas-v1-2-remediation.md`
- Modify: `功能清单.md`
- Modify: `模型参数文件.md`
- Modify: `开发记录.md`
- Modify: `docs/MEMORY_ATLAS_DELIVERY_RECORD.md`
- Modify: `docs/MEMORY_ATLAS_PROJECT_MODEL_PARAMETERS.md`
- Modify: `CHANGELOG.md`

- [ ] Run all R7 focused tests, manifest/public-raw audits, release verification, parity
  audit and recovery rehearsal from the final implementation/data commit.
- [ ] Re-run R1 Home, R3 command, R4 proposal, R5 Owner Daily, R6 visual workflows,
  Stage 7 full acceptance, lint, build and broad privacy gates.
- [ ] Inspect candidate screenshots only for regressions caused by new data counts; R7 does
  not redesign UI.
- [ ] Obtain independent correctness/security/recovery review. Reproduce and fix every
  High/Medium finding, then re-review until both are zero.
- [ ] Promote only the five R7 rows and record aggregate `53/2/3/0`.
- [ ] Record installed app/online site unchanged and remote reconciliation deferred to R8.
- [ ] Commit R7 records locally, remove reproducible caches and temporary source restores,
  verify clean worktree, only `main`, zero stash and ports 4177-4187 released.
- [ ] Stop before R8. Do not merge/rebase, push, reinstall or deploy.
