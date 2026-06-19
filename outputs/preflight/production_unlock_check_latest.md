# Production Unlock Check

- Generated: 2026-06-13T06:47:18+08:00
- Status: blocked
- Apply requested: False
- Apply performed: False
- Full diagnostics: True
- Pack ready to apply: False
- Production ready: False
- Stop reason: pack source evidence audit failed

## Stages

| Stage | Status | Summary |
|---|---|---|
| source_evidence_audit_pack | block | `{"files": {"csv": "<workspace>/outputs/preflight/source_evidence_audit_latest.csv", "json": "<workspace>/outputs/preflight/source_evidence_audit_latest.json", "markdown": "<workspace>/outputs/preflight/source_evidence_audit_latest.md"}, "invalid_count": 15, "local_hashed_count": 0, "pack_dir": "<workspace>/outputs/intake_pack", "row_count": 17, "status": "blocked", "url_count": 2, "valid_count": 2}` |
| promote_intake_pack_dry_run | block | `{"applied": false, "apply_requested": false, "backup_dir": null, "evidence_copied_count": 0, "issue_count": 39, "json_path": "<workspace>/outputs/intake_pack/promotion_latest.json", "markdown_path": "<workspace>/outputs/intake_pack/promotion_latest.md", "placeholder_blocked": true, "production_ready": false, "validation_block_count": null, "validation_warn_count": null}` |
| preflight | pass | `{"blockers": [], "json_path": "<workspace>/outputs/preflight/preflight_latest.json", "markdown_path": "<workspace>/outputs/preflight/preflight_latest.md", "production_ready": true, "shadow_ready": true, "status": "pass", "warnings": ["alipay_positions"]}` |
| completion_audit | block | `{"block_count": 1, "completion_percent": 91.94, "csv_path": "<workspace>/outputs/completion_audit/completion_audit_latest.csv", "json_path": "<workspace>/outputs/completion_audit/completion_audit_latest.json", "markdown_path": "<workspace>/outputs/completion_audit/completion_audit_latest.md", "overall_status": "blocked", "pass_count": 57, "total_count": 62, "warn_count": 4}` |

## Boundary

- This command does not send mail.
- This command does not place trades.
- `--apply` only promotes the intake pack after evidence and dry-run promotion checks pass.
- `--full-diagnostics` only continues read-only checks after a pack blocker; it does not apply files.
- Production remains locked unless preflight and completion audit both pass.
