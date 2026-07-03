# WDA Handoff

## Current Goal

Execute WDA Stage 2 Sprint 2N import-readiness and Data Core boundary planning.

## Current Status

- Local worktree: `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA`
- Project directory: `WDA/`
- Branch: `codex/wda`
- Product scope: WDA Control Plane for WeChat data analysis feasibility; current scope is import-readiness and Data Core boundary planning, not database implementation or RAG/Web/Matrix buildout
- Implementation status: Sprint 2B-A/2B-B/2B-C, Sprint 2C contract, Sprint 2D discovery, Sprint 2E route decision, Sprint 2F acquisition contract, Sprint 2G automated route feasibility, Sprint 2I report validation, Sprint 2J-B raw import validation, Sprint 2K-B bounded raw import validation, Sprint 2L subject coverage plan, Sprint 2M-B subject coverage import validation, and Sprint 2N import-readiness/Data Core boundary artifacts generated; no runtime code yet
- Latest Sprint 1C outputs: `WDA/docs/stage2_sprint1c/`
- Latest Sprint 2 outputs: `WDA/docs/stage2_sprint2_safe_readability/`
- Latest Sprint 2B-A outputs: `WDA/docs/stage2_sprint2b_candidate_bundle/`
- Latest Sprint 2B-B outputs: `WDA/docs/stage2_sprint2b_schema_probe/`
- Latest Sprint 2B-C outputs: `WDA/docs/stage2_sprint2b_route_decision/`
- Latest Sprint 2C outputs: `WDA/docs/stage2_sprint2c_readable_artifact_contract/`
- Latest Sprint 2D outputs: `WDA/docs/stage2_sprint2d_real_artifact_discovery/`
- Latest Sprint 2E outputs: `WDA/docs/stage2_sprint2e_message_data_route_decision/`
- Latest Sprint 2F outputs: `WDA/docs/stage2_sprint2f_artifact_acquisition_contract/`
- Latest Sprint 2G outputs: `WDA/docs/stage2_sprint2g_automated_acquisition_feasibility/`
- Latest Sprint 2I outputs: `WDA/docs/stage2_sprint2i_2h_report_validation/`
- Latest Sprint 2J-B outputs: `WDA/docs/stage2_sprint2j_wda_raw_import_validation/`
- Latest Sprint 2K-B outputs: `WDA/docs/stage2_sprint2k_b_bounded_raw_import_validation/`
- Latest Sprint 2L outputs: `WDA/docs/stage2_sprint2l_subject_coverage_plan/`
- Latest Sprint 2M-B outputs: `WDA/docs/stage2_sprint2m_b_subject_coverage_import_validation/`
- Latest Sprint 2N outputs: `WDA/docs/stage2_sprint2n_import_readiness_data_core_boundary/`
- Local Sprint 2B copied bundle: `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`
- Latest Sprint 2M-B local Raw Import Pack: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2m_b_subject_coverage_import_validation/`
- Raw Gate: `First-Batch Subject Coverage Proven`; full Raw Gate Go is not proven

## Key Decisions

- Keep WDA as one long-lived project worktree.
- Do not create a full CodexProject copy for each chat.
- Do not expand unrelated project directories into this worktree.
- Treat current WDA files as governance/bootstrap only, not product implementation.
- Treat old computer as the highest-value data source candidate.
- Treat new computer as WDA Control Plane / WDA_HOME / database / RAG / Web host.
- Do not copy the full old WeChat cache; Sprint 2 should use a copied candidate DB bundle if approved.
- Treat `/Volumes/My Passport/WDA_MetaData/raw_ferry/old_mac_wechat_full_export_20260702_apfs.sparseimage` as the authoritative old-computer export.
- Do not use the abandoned direct ExFAT partial copy as authoritative.
- Keep `key_info`, login paths, and MMKV/key-value stores as skip/no-open.
- Sprint 2B-A bundle must exclude `key_info`, login paths, MMKV, KVDB/key-value stores, sensitive skip paths, and raw `msg/file`, `msg/attach`, `msg/video` cache paths.
- Sprint 2B-B must run from the local copied bundle only; no external drive or APFS source is required after bundle validation.
- Sprint 2B-B read-only SQLite probe found 0 plain SQLite schema-open successes across 91 main candidates; all 91 remained `not_plain_sqlite_or_encrypted_unknown` under the approved safe path.
- Sprint 2B-C route decision recommends an owner-authorized readable artifact intake contract as the next route; it does not execute that route.
- WDA RAG/Web/Matrix data-dependent implementation remains blocked until a safe, authorized message-level import path exists.
- Sprint 2C defines the readable artifact contract only; it does not create `messages.jsonl`, validate a real artifact, or implement RAG/Web/Matrix.
- Sprint 2D searched real data sources metadata-only and found no validated message-level readable artifact; APFS was mounted read-only for discovery and detached after search.
- WDA still lacks message-level readable input; future conversion requires a separate approved sprint and a selected readable candidate.
- Sprint 2E chooses the next direction as official/user-readable artifact route selection and acquisition contract; it does not execute acquisition or import.
- Third-party adapter work is research-only backup; high-risk raw adapter work remains rejected under the current boundary.
- Sprint 2F approves the official/user-readable artifact acquisition route and fixes the future intake storage root at `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/owner_authorized_readable_artifacts/`.
- Sprint 2F does not create `messages.jsonl`, import real message data, or implement RAG/Web/Matrix.
- Sprint 2G deprecates the manual owner-prepared artifact route for WDA core viability.
- WDA requires automated message-level acquisition; if no automated acquisition route is accepted, WDA core is not viable as a fully automatic system.
- Low-risk read-only/APFS/schema-only routes have not produced message-level data.
- Recommended next sprint is Sprint 2H controlled automated acquisition trial using one local CLI exporter route in the `wechat-cli` / `wx-cli` family, only after explicit user approval.
- Sprint 2H should run on the old computer if the target data is the old-computer WeChat source; the new computer remains WDA Control Plane and future RAG/Web/database host.
- Sprint 2H partially succeeded: `r266-tech/wechat-cli` / `wxkey` was installed/pinned, `wxkey bootstrap` succeeded under approved high-permission trial, and key coverage reached `25/26`.
- Sprint 2H did not produce `messages.jsonl` or a minimal message-level sample.
- Sprint 2H post-bootstrap `wechat-cli status`, strict status, and `wxkey doctor` live-read paths hung with no usable JSON output.
- Sprint 2I validated only the non-sensitive report pack; it did not transfer `sensitive_local_state/`, `raw_trial_outputs/`, raw logs, key configs, decrypted DBs, or message outputs.
- Recommended next executable step is Sprint 2I-B bounded old-computer remediation on the existing pinned primary route, only after explicit approval.
- Sprint 2I-B produced a minimal full-sensitive message-level JSONL proof after bounded remediation.
- Sprint 2J-B validated the transferred minimal artifact on the new computer and generated a local WDA Raw Import Pack under `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2j_wda_raw_import_validation/`.
- Sprint 2J-B generated local `messages.jsonl` with `1` row, `conversations.jsonl` with `1` row, `contacts.jsonl` with `2` rows, and empty `media_index.csv`.
- Sprint 2J-B advances Raw Gate to `Sample Message-Level Proven`, not full Go.
- Sprint 2K-A produced a bounded repeatability export: 5 conversations, 20 rows per conversation, 100 total message rows, `include_media_paths=false`, and no keys/configs/DBs/logs/tool_work/sensitive_local_state in the transfer bundle.
- Sprint 2K-B validated the bounded transfer bundle on the new computer and generated a local WDA Raw Import Pack under `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2k_b_bounded_raw_import_validation/`.
- Sprint 2K-B generated local `messages.jsonl` with `100` rows, `conversations.jsonl` with `5` rows, `contacts.jsonl` with `21` rows, and empty `media_index.csv`.
- Sprint 2K-B advances Raw Gate to `Bounded Multi-Message Proven`, not full Go.
- Sprint 2L is planning-only: it does not run exporter tools, does not access the external hard drive, and does not create or modify `messages.jsonl`.
- Sprint 2L defines Sprint 2M-A as an old-computer bounded first-batch subject coverage export with max 5 subject targets, max 100 messages per subject/conversation, max 500 total messages, and `include_media_paths=false`.
- Sprint 2L explicitly excludes `李晶工作交接` as a pollution/noise source, not a subject sample.
- Sprint 2M-A produced a bounded first-batch subject coverage transfer bundle: 5 subject exports, 100 rows each, 500 total rows, `include_media_paths=false`, no external hard drive, and `李晶工作交接` excluded as pollution/noise.
- Sprint 2M-B validated the transfer bundle on the new computer and generated a local WDA Raw Import Pack under `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2m_b_subject_coverage_import_validation/`.
- Sprint 2M-B generated local `messages.jsonl` with `500` rows, `conversations.jsonl` with `5` rows, `contacts.jsonl` with `23` rows, and empty `media_index.csv`.
- Sprint 2M-B advances Raw Gate to `First-Batch Subject Coverage Proven`, not full Go.
- Sprint 2N validated import readiness for a minimal local Data Core seed and did not modify/regenerate `messages.jsonl`.
- Sprint 2N does not create a database. It defines Sprint 2O as the first allowed minimal local Data Core seed sprint.
- Sprint 2O must use only the bounded Sprint 2M-B 500-row Raw Import Pack and store local DB files under `/Users/linzezhang/Downloads/WDA_MetaData/data_core/sprint2o_minimal_seed/`.
- RAG/Web/Matrix remain blocked until repeatable broader import-readiness and Data Core readiness are proven.

## Files To Read First

- `AGENTS.md`
- `WDA/AGENTS.md`
- `WDA/README.md`
- `WDA/docs/HANDOFF.md`
- `WDA/功能清单.md`
- `WDA/开发记录.md`
- `WDA/模型参数文件.md`
- `WDA/docs/governance/project.yaml`
- `WDA/docs/governance/roadmap.yaml`
- `WDA/docs/stage2_sprint1c/multi_device_topline_comparison.md`
- `WDA/docs/stage2_sprint1c/multi_device_raw_gate_summary.md`
- `WDA/docs/stage2_sprint1c/next_sprint2_safe_readability_plan.md`
- `WDA/docs/stage2_sprint2_safe_readability/README.md`
- `WDA/docs/stage2_sprint2_safe_readability/safe_readability_decision.md`
- `WDA/docs/stage2_sprint2_safe_readability/sprint2_validation_report.md`
- `WDA/docs/stage2_sprint2b_candidate_bundle/README.md`
- `WDA/docs/stage2_sprint2b_candidate_bundle/bundle_validation_report.md`
- `WDA/docs/stage2_sprint2b_schema_probe/README.md`
- `WDA/docs/stage2_sprint2b_schema_probe/sprint2b_safe_readability_decision.md`
- `WDA/docs/stage2_sprint2b_route_decision/README.md`
- `WDA/docs/stage2_sprint2b_route_decision/raw_gate_decision.md`
- `WDA/docs/stage2_sprint2b_route_decision/recommended_next_route.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/README.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/readable_artifact_contract.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/import_manifest_schema.md`
- `WDA/docs/stage2_sprint2c_readable_artifact_contract/next_sprint2d_validation_plan.md`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/README.md`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/sprint2d_decision.md`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/readable_artifact_candidates.csv`
- `WDA/docs/stage2_sprint2d_real_artifact_discovery/privacy_and_safety_validation.md`
- `WDA/docs/stage2_sprint2e_message_data_route_decision/README.md`
- `WDA/docs/stage2_sprint2e_message_data_route_decision/route_options_matrix.md`
- `WDA/docs/stage2_sprint2e_message_data_route_decision/recommended_next_step.md`
- `WDA/docs/stage2_sprint2f_artifact_acquisition_contract/README.md`
- `WDA/docs/stage2_sprint2f_artifact_acquisition_contract/artifact_storage_contract.md`
- `WDA/docs/stage2_sprint2f_artifact_acquisition_contract/artifact_validation_gate.md`
- `WDA/docs/stage2_sprint2f_artifact_acquisition_contract/next_sprint2g_sample_intake_validation_plan.md`
- `WDA/docs/stage2_sprint2g_automated_acquisition_feasibility/README.md`
- `WDA/docs/stage2_sprint2g_automated_acquisition_feasibility/current_blocker_summary.md`
- `WDA/docs/stage2_sprint2g_automated_acquisition_feasibility/candidate_tool_matrix.md`
- `WDA/docs/stage2_sprint2g_automated_acquisition_feasibility/controlled_trial_plan.md`
- `WDA/docs/stage2_sprint2g_automated_acquisition_feasibility/recommended_next_sprint.md`
- `WDA/docs/stage2_sprint2i_2h_report_validation/README.md`
- `WDA/docs/stage2_sprint2i_2h_report_validation/sprint2h_result_validation.md`
- `WDA/docs/stage2_sprint2i_2h_report_validation/sensitive_material_exclusion_check.md`
- `WDA/docs/stage2_sprint2i_2h_report_validation/blocker_analysis.md`
- `WDA/docs/stage2_sprint2i_2h_report_validation/recommended_sprint2i_b_plan.md`
- `WDA/docs/stage2_sprint2j_wda_raw_import_validation/README.md`
- `WDA/docs/stage2_sprint2j_wda_raw_import_validation/raw_artifact_shape_report.md`
- `WDA/docs/stage2_sprint2j_wda_raw_import_validation/wda_contract_mapping_report.md`
- `WDA/docs/stage2_sprint2j_wda_raw_import_validation/raw_gate_decision.md`
- `WDA/docs/stage2_sprint2j_wda_raw_import_validation/next_sprint2k_plan.md`
- `WDA/docs/stage2_sprint2k_b_bounded_raw_import_validation/README.md`
- `WDA/docs/stage2_sprint2k_b_bounded_raw_import_validation/raw_artifact_shape_report.md`
- `WDA/docs/stage2_sprint2k_b_bounded_raw_import_validation/wda_contract_mapping_report.md`
- `WDA/docs/stage2_sprint2k_b_bounded_raw_import_validation/raw_gate_decision.md`
- `WDA/docs/stage2_sprint2k_b_bounded_raw_import_validation/next_sprint2l_plan.md`
- `WDA/docs/stage2_sprint2l_subject_coverage_plan/README.md`
- `WDA/docs/stage2_sprint2l_subject_coverage_plan/first_batch_subject_matrix.md`
- `WDA/docs/stage2_sprint2l_subject_coverage_plan/export_scope_policy.md`
- `WDA/docs/stage2_sprint2l_subject_coverage_plan/sprint2m_old_computer_export_plan.md`
- `WDA/docs/stage2_sprint2l_subject_coverage_plan/import_readiness_criteria.md`
- `WDA/docs/stage2_sprint2m_b_subject_coverage_import_validation/README.md`
- `WDA/docs/stage2_sprint2m_b_subject_coverage_import_validation/transfer_bundle_validation.md`
- `WDA/docs/stage2_sprint2m_b_subject_coverage_import_validation/wda_contract_mapping_report.md`
- `WDA/docs/stage2_sprint2m_b_subject_coverage_import_validation/raw_gate_decision.md`
- `WDA/docs/stage2_sprint2m_b_subject_coverage_import_validation/next_sprint2n_plan.md`
- `WDA/docs/stage2_sprint2n_import_readiness_data_core_boundary/README.md`
- `WDA/docs/stage2_sprint2n_import_readiness_data_core_boundary/data_core_minimum_table_plan.md`
- `WDA/docs/stage2_sprint2n_import_readiness_data_core_boundary/data_core_storage_boundary.md`
- `WDA/docs/stage2_sprint2n_import_readiness_data_core_boundary/sprint2o_minimal_data_core_seed_plan.md`
- `WDA/docs/stage2_sprint2n_import_readiness_data_core_boundary/risk_and_stop_conditions.md`

## Validation

Lightweight project check:

```bash
/usr/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

Do not expand unrelated projects to satisfy full monorepo validation unless the user explicitly asks for a root-governance run.

Latest verified command:

```bash
/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/lean_governance.py check-render --project WDA
```

Result: passed with `drift_count=0` and `reference_issue_count=0` after Sprint 2B output generation.

Latest Sprint 2B local validation:

- Required Sprint 2B-A/B outputs present: true
- Candidate bundle manifest/checksum/local file count: 169/169/169
- Deny-marker violations in selected bundle: 0
- Probe main candidates: 91
- Plain SQLite schema-open successes: 0
- Read-only open failures: 91
- Message/contact row access violations: 0
- External/APFS mounts visible before Sprint 2B-B validation: 0

Latest Sprint 2B-C decision:

- Required route-decision outputs present: true
- Hard drive required: false
- `messages.jsonl` present under WDA repo stage docs: false
- Recommended next route: owner-authorized readable artifact intake contract
- Raw Gate: `Conditional Investigation`

Latest Sprint 2C contract:

- Required contract outputs present: true
- Hard drive required: false
- `messages.jsonl` produced: false
- Contract files defined: `import_manifest.json`, `messages.jsonl`, `conversations.jsonl`, `contacts.jsonl`, `media_index.csv`
- Next executable step: validate a small owner-authorized sample artifact only if the user provides or approves one
- Raw Gate: `Conditional Investigation`

Latest Sprint 2D discovery:

- Required discovery outputs present: true
- Discovery mode: real-data, metadata-only
- APFS source scanned: true, mounted read-only
- APFS detached after search: true
- Candidate rows reported: 12, all local generated report/metadata-like rows
- APFS message/chat-like readable artifact candidates: 0
- Protected DB/key/MMKV/login opened: 0
- Message content parsed: 0
- `messages.jsonl` produced: false
- Raw Gate: `Conditional Investigation`

Latest Sprint 2E route decision:

- Required decision outputs present: true
- Hard drive required: false
- `messages.jsonl` exists: false
- Recommended next sprint: Sprint 2F official/user-readable artifact route selection and acquisition contract
- Third-party adapter route: research-only backup, not execution
- High-risk raw adapter route: rejected under current boundary
- RAG/Web/Matrix: blocked
- Raw Gate: `Conditional Investigation`

Latest Sprint 2F acquisition contract:

- Required acquisition-contract outputs present: true
- Hard drive required: false
- `messages.jsonl` created: false
- Real message data imported: false
- Approved future storage root: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/owner_authorized_readable_artifacts/`
- Accepted future file types: `.jsonl`, `.json`, `.csv`, `.txt`, `.md`, `.html`, `.zip`
- Next executable step: Sprint 2G sample intake validation, only if user provides or approves a real owner-authorized readable artifact
- Raw Gate: `Conditional Investigation`

Latest Sprint 2G automated acquisition feasibility:

- Required feasibility outputs present: true
- Hard drive required: false
- WeChat export/decrypt tools executed: false
- Manual user-prepared artifact route: deprecated for WDA core viability
- Automated message-level acquisition: required
- Recommended controlled-trial route: one local CLI exporter in the `wechat-cli` / `wx-cli` family
- Recommended trial host: old computer, with new computer as WDA Control Plane and validation/RAG/Web host
- Required before trial: explicit user approval of exact route/tool/repo/commit, host, live WeChat requirement, admin/sudo, process-memory access, key extraction, DB decryption, output path, trial scope, and stop conditions
- `messages.jsonl` created: false
- RAG/Web/Matrix: blocked
- Raw Gate: `Conditional Investigation`

Latest Sprint 2I report validation:

- Required Sprint 2I outputs present: true
- Hard drive required: false
- Input pack: `/Users/linzezhang/Downloads/WDA_sprint2h_non_sensitive_report_pack_for_2I.zip`
- Input pack SHA-256: `a7c913deee0a2723806ec3ce9bb03c63f4d28f91839eaac8940f6fa111c12084`
- Non-sensitive transferred files: 15
- Actual transferred `sensitive_local_state/`, `raw_trial_outputs/`, raw logs, key configs, decrypted DBs, message outputs: 0
- Sprint 2H result: partial success, no minimal message-level sample
- Sprint 2H key coverage: `25/26`
- `messages.jsonl` created: false
- Recommended next step: Sprint 2I-B bounded old-computer remediation on the existing pinned primary route, only after explicit approval
- RAG/Web/Matrix: blocked
- Raw Gate: `Conditional Investigation`

Latest Sprint 2J-B raw import validation:

- Required Sprint 2J-B repo-safe outputs present: true
- Expected input path exists: false
- Actual validated transfer bundle: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2j_transfer_bundle/sprint2j_transfer_bundle.zip`
- Transfer bundle SHA-256: `10dbe9b40c13f5a8d09ded87c6f23fa340f4f4edbec8e25da6ff52d21ab76be4`
- Key material / decrypted DB / `sensitive_local_state/` included in bundle: false
- Minimal raw artifact: `raw_sensitive_minimal/minimal_export_limit1_raw.jsonl`
- Local Raw Import Pack output root: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2j_wda_raw_import_validation/`
- Local `messages.jsonl` rows: `1`
- Local `conversations.jsonl` rows: `1`
- Local `contacts.jsonl` rows: `2`
- Local `media_index.csv` rows: `0`
- Missing required fields: none
- Validation errors: none
- Repo raw content committed: false
- RAG/Web/Matrix: blocked
- Raw Gate: `Sample Message-Level Proven`, not full Go

Latest Sprint 2K-B bounded raw import validation:

- Required Sprint 2K-B repo-safe outputs present: true
- Expected input path exists: false
- Actual validated transfer bundle: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/sprint2k_transfer_bundle/sprint2k_a_bounded_repeatability_export/sprint2k_transfer_bundle.zip`
- Transfer bundle SHA-256: `e97cf341fc5905372b2d76546a4270bb54b515d1f1b6850b2ab7815089123b56`
- Payload checksum manifest status: pass
- Transfer bundle file count: `18`
- Raw bounded export files: `5`
- Key material / DBs / broad logs / `tool_work/` / `sensitive_local_state/` included in bundle: false
- Local Raw Import Pack output root: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2k_b_bounded_raw_import_validation/`
- Local `messages.jsonl` rows: `100`
- Local `conversations.jsonl` rows: `5`
- Local `contacts.jsonl` rows: `21`
- Local `media_index.csv` rows: `0`
- Missing required fields: none
- Conversion errors: `0`
- Validation errors: none
- Repo raw content committed: false
- RAG/Web/Matrix: blocked
- Raw Gate: `Bounded Multi-Message Proven`, not full Go

Latest Sprint 2L subject coverage plan:

- Required Sprint 2L outputs present: true
- Hard drive required: false
- Exporter tools run: false
- Local `messages.jsonl` created or modified: false
- Sprint 2M host recommendation: old computer for export, new computer for validation
- Sprint 2M subject target cap: `5`
- Sprint 2M per-subject/conversation cap: `100` messages
- Sprint 2M total cap: `500` messages
- Sprint 2M media policy: `include_media_paths=false`
- Full-contact export: forbidden
- All-history export: forbidden
- Media DB enhancement: forbidden
- Explicit exclusion: `李晶工作交接`
- RAG/Web/Matrix: blocked
- Raw Gate: `Bounded Multi-Message Proven`, not full Go

Latest Sprint 2M-B subject coverage import validation:

- Required Sprint 2M-B repo-safe outputs present: true
- Input transfer bundle: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/sprint2m_a_subject_coverage_export/sprint2m_transfer_bundle.zip`
- Transfer bundle SHA-256: `ba8ff637714711e444d6072f4e50a59452e1a286a51b7b49038cc11bfd285d0b`
- External bundle checksum status: `pass`
- Internal payload checksum status: `pass`
- Transfer bundle file count: `20`
- Forbidden key/config/DB/log/tool/state/full-export paths in bundle: `0`
- Raw subject export files parsed: `5`
- Expected rows per subject: `100`
- Local `messages.jsonl` rows: `500`
- Local `conversations.jsonl` rows: `5`
- Local `contacts.jsonl` rows: `23`
- Local `media_index.csv` rows: `0`
- Conversion errors: `0`
- Explicit noise source `李晶工作交接` raw export hits: `0`
- Repo raw content committed: false
- RAG/Web/Matrix: blocked
- Raw Gate: `First-Batch Subject Coverage Proven`, not full Go

Latest Sprint 2N import-readiness and Data Core boundary:

- Required Sprint 2N repo-safe outputs present: true
- Input local Raw Import Pack exists: true
- Required local files present: true
- Local `messages.jsonl` modified or regenerated: false
- Database created: false
- Local checksum entries checked: `12`
- Local checksum mismatches: `0`
- Local row counts: `500` messages, `5` conversations, `23` contacts, `0` media rows
- Minimum Sprint 2O tables: `import_batches`, `import_files`, `conversations`, `contacts`, `conversation_participants`, `messages`, `message_media_refs`, `media_index`, `import_validation_events`
- Sprint 2O allowed storage root: `/Users/linzezhang/Downloads/WDA_MetaData/data_core/sprint2o_minimal_seed/`
- Sprint 2O may start: yes, bounded to the Sprint 2M-B 500-row pack only
- RAG/Web/Matrix: blocked
- Raw Gate: `First-Batch Subject Coverage Proven`, not full Go

## Next Step

Run Sprint 2O on the new computer as a minimal local Data Core seed sprint if approved. Sprint 2O must ingest only the bounded 500-row Sprint 2M-B Raw Import Pack, write local database files only under `/Users/linzezhang/Downloads/WDA_MetaData/data_core/sprint2o_minimal_seed/`, and keep RAG/Web/Matrix, full export, media paths, and ChatGPT Pack using raw messages blocked.
