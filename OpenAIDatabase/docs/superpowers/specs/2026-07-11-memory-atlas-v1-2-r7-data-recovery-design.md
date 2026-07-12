# Memory Atlas v1.2 R7 Data Parity And Recovery Design

## Decision Status

This design implements only `R7_DATA_PARITY_RAW_EVIDENCE_AND_RECOVERY` from the
user-approved R0-R8 remediation plan. Approval is inherited from that bounded plan and
the restored TaskPack's explicit plaintext-public transcript policy. It does not perform
R8 overall acceptance, remote-history reconciliation, GitHub push, app reinstall or
Cloudflare deployment.

R6 closed the rendered visual-workflow gaps, but the current repository still has an
empty public raw archive and empty hash ledger. The installed app snapshot contains 79
Codex sessions and 403 nodes while the tracked web candidate contains 16 Codex sessions
and 340 nodes. A real 2026-07-07 ChatGPT official export exists in the authorized private
OneDrive source layer; it is about 1.4 GB and contains four conversation JSON chunks with
379 conversations. Local Codex session and archived-session logs total about 408 MB.

R7 must turn those real inputs into credential-free, append-only, GitHub-portable
transcripts; rebuild one data candidate; freeze one immutable release snapshot; and
prove a clean tracked-files-only recovery. Source markers, empty ledgers and derived-only
summaries cannot satisfy this phase.

## Authoritative Requirement Impact

R7 may promote only these five rows:

- `S03-AC01`: FAILED -> VERIFIED;
- `S03-AC02`: PARTIAL -> VERIFIED;
- `S04-AC02`: NOT_VERIFIED -> VERIFIED;
- `S04-AC03`: PARTIAL -> VERIFIED;
- `S05-AC01`: PARTIAL -> VERIFIED.

Expected aggregate after R7:

```text
VERIFIED 53 / PARTIAL 2 / FAILED 3 / NOT_VERIFIED 0
```

The remaining two PARTIAL and three FAILED rows belong to R8. Release status remains
`FAIL_REMEDIATION_REQUIRED`.

## Considered Approaches

### Track The Original Archives Or Use Git LFS

Rejected. The ChatGPT export includes binary assets and may contain credentials; the
Codex source logs include local paths, tool payloads and binary screenshots. The original
ChatGPT ZIP is larger than a normal GitHub file and Git LFS would make clean recovery
depend on a second storage/control plane. This conflicts with credential exclusion and
ordinary tracked-file recovery.

### Keep Only Existing Manifests And Derived Summaries

Rejected. This is the current state that produced the false PASS: zero public raw files,
zero ledger rows and no official-export execution evidence. It cannot recover transcript
content or prove the fallback path.

### Versioned Sanitized Public Transcripts And Immutable Release Artifacts

Selected. It keeps all ordinary textual transcript/event content after explicit privacy
redaction, preserves source and output hashes, records intentional binary omissions, and
uses normal tracked files. It is compatible with the TaskPack's rule that transcript is
memory while credentials are not memory.

## Public Raw Boundary

### Included

- ChatGPT conversation title, IDs, timestamps, roles and full textual messages from the
  official export;
- Codex JSONL event structure and all textual event fields, including user/assistant
  messages and textual tool-call/result fields;
- one real reviewer-agent report imported through the future-agent adapter;
- portable source provenance, source hashes, redaction counts, output hashes and
  explicit omission reasons.

### Excluded Or Replaced

- cookies, session/auth/OAuth tokens, passwords, API keys and private keys;
- email, phone and machine-local absolute path values;
- binary attachments, data URLs and base64-like non-text blobs.

Excluded binary values are replaced by a deterministic marker containing SHA-256,
original byte count and `reason=non_text_binary_not_transcript`. Ordinary text is not
length-truncated. If a sanitized single event still exceeds the configured chunk limit,
the export fails instead of silently truncating it.

The original 1.4 GB ZIP and original Codex logs remain private source inputs and are not
copied into Git. GitHub recovery covers the complete public transcript contract, code,
derived data, manifests and operational evidence; it intentionally cannot reconstruct
credentials or excluded binary attachment bodies.

## Versioning And Append-Only Rules

ChatGPT filenames use the conversation ID and normalized-content hash:

```text
data/public_raw/chatgpt/<conversation_id>.<content_sha12>.json
```

Codex filenames use session ID, source-content hash and a 1-based chunk suffix:

```text
data/public_raw/codex/sessions/<session_id>.<source_sha12>.part-0001.jsonl
```

Future-agent filenames use agent ID, event ID and normalized-content hash. Existing
files may be reused only when bytes are identical. A newer version is appended under a
new hash; no existing raw file is overwritten or deleted.

Codex chunks target at most 40 MiB, below GitHub's single-file hard limit. Chunking occurs
only between complete JSONL events. ChatGPT conversations are one JSON document each;
the exporter fails if one sanitized conversation exceeds 40 MiB.

## Shared Sanitizer

`scripts/public_raw_sanitizer.py` provides one implementation for all connectors:

```python
sanitize_public_value(value: Any) -> tuple[Any, dict[str, int]]
sanitize_jsonl_event(event: dict[str, Any]) -> tuple[dict[str, Any], dict[str, int]]
binary_omission_marker(value: str) -> str
```

It delegates credential/PII/path redaction to `privacy_guard`, recursively handles lists
and dictionaries, detects data URLs and strongly base64-like long strings, and returns
aggregate redaction counts without retaining the removed values.

`audit_memory_atlas_public_raw.py` scans every public raw file regardless of size. It
parses JSON/JSONL, checks all strings for credential patterns and absolute paths, rejects
unmarked binary data, enforces the 40 MiB file limit and reports exact source/file counts.
The existing privacy guard remains a broad repository regression but is not sufficient
on its own because it skips files larger than 1 MB.

## Connector Changes

### ChatGPT

The existing default remains strict: credential-bearing input fails before write.
R7 adds an explicit `--redact-for-public-backup` mode. In that mode, the connector:

1. hashes the official export without recording its absolute path;
2. normalizes and sanitizes all 379 current conversations;
3. writes versioned append-only public transcript files;
4. writes the current processed conversation manifest from those files;
5. records conversation/message counts, source archive SHA and redaction counts.

Browser state remains untouched. Login/password/verification states still fail closed.

### Codex

R7 adds `--public-transcripts`. The connector keeps its current derived session model and
also streams every local session/archived-session JSONL file through the shared sanitizer.
It writes versioned chunks and records their relative refs in the aggregate Codex public
snapshot. Source paths are relative to the supplied Codex home and never include the user
home path.

### Real Reviewer Agent

The future-agent adapter adds an explicit Markdown-report input mode. R7 imports the real
R6 independent reviewer report as `codex-reviewer`, writes one versioned public event and
registers the concrete source beside the reusable future-agent template. This is actual
agent output, not a synthetic placeholder.

## Immutable Manifest And Ledger

`raw_archive_manifest.py` retains the historical empty S03 baseline for audit history but
hardens all new runs:

- a manifest run ID is immutable; same bytes are idempotent, different bytes fail;
- `raw_hash_ledger.jsonl` is a union ledger and never drops old entries;
- the same relative path may never map to a different SHA;
- `--require-non-empty` fails zero-file or zero-source evidence;
- audit fails deleted ledger entries or hash drift and reports newly appended files;
- every row carries source ID, relative path, SHA-256, size and imported timestamp.

The R7 manifest must contain non-zero ChatGPT, Codex and reviewer-agent files. It is a
machine artifact and remains outside the human first screen.

## Facet And Derived Rebuild

The facet extractor selects the newest version of each ChatGPT conversation and uses the
exact public transcript ref. Codex session rows reference their exported transcript
chunks. The real reviewer-agent event produces at least one `future_agent` canonical
event with a raw evidence ref.

After all three sources are materialized, R7 reruns facets and dependent behavior models,
then rebuilds `data/derived/visualization/memory_atlas.json`. No fake record may be created
when a source fails. Raw files are never modified by analysis.

## Immutable Release Snapshot

`materialize_memory_atlas_release.py` creates:

```text
data/releases/memory_atlas/v1_2/<release_id>/memory_atlas.json
data/releases/memory_atlas/v1_2/<release_id>/release_manifest.json
机器治理/发布快照/memory_atlas_current_release.json
```

The release manifest contains the snapshot SHA-256, counts, raw manifest SHA-256,
source-package hashes and relative paths only. A release ID is immutable. Re-creating the
same ID with different bytes fails.

`audit_memory_atlas_snapshot_parity.py` requires exact hash equality among:

- current release manifest and immutable release snapshot;
- tracked derived candidate;
- local-runtime candidate;
- Pages `dist/memory_atlas.json` candidate.

R7 prepares temporary candidates only. It does not modify the installed app or online
site. Installer and deployer gain release-manifest verification so R8 cannot silently
rebuild and deploy a different snapshot. A newly installed launcher serves the pinned
release by default; an explicit local sync action may later create a newer local-only
runtime snapshot without changing the immutable release record.

## Tracked-Files-Only Recovery

`audit_memory_atlas_github_recovery.py` archives a specified local candidate commit into
a temporary directory using Git tracked files only. It then:

1. restores and re-hashes the original Roadmap and TaskPack from tracked source-package
   parts;
2. validates the non-empty raw manifest, append-only ledger and full public-raw privacy
   audit;
3. verifies the immutable release manifest and snapshot hash;
4. performs fresh `npm ci` and frontend build;
5. verifies the built Pages candidate matches the release hash;
6. records commands, file counts and hashes without absolute machine paths.

This proves the candidate commit is recovery-complete before upload. R8 must repeat the
same audit from an actual GitHub clone after the single final push; R7 alone cannot claim
remote GitHub recovery.

## Acceptance

R7 passes only when all of the following are true:

- real ChatGPT official export fallback materializes non-empty sanitized transcripts;
- real Codex sessions materialize non-empty versioned public transcript chunks;
- a real reviewer-agent record produces a future-agent canonical event;
- full public raw audit reports zero credential/path/unmarked-binary/file-size failures;
- non-empty immutable manifest contains all three source families;
- changing or deleting an existing raw file fails append-only audit in regression tests;
- release, derived, local candidate and Pages candidate hashes are identical;
- tracked-files-only recovery completes from a clean temporary directory;
- R1-R6 product workflows and privacy regressions continue to pass;
- independent final review has zero High and zero Medium findings.

## Rollback And Stop

Revert only R7 commits after R6 closeout `7412a5c2b`. Scripts, derived/release data and R7
evidence may be reverted. Newly appended raw files are not automatically deleted; the
TaskPack reserves raw deletion decisions to the human owner.

Stop after the R7 local closeout commit and cache cleanup. Do not merge/rebase remote
history, push, reinstall, deploy or start R8 in this run.
