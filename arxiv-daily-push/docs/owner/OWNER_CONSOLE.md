# Owner Console

- generated_at: 2026-06-22T16:30:00+10:00
- generated_from: `config/owner_controls.yaml`
- config_version: `owner-controls-v1`
- task_id: `S1-03-OWNER-CONTROLS-001`
- model_id: `adp-owner-controls-v1`
- validation_status: `pass`
- production_enabled: `false`
- production_acceptance_claimed: `false`

## Current Conclusion

Owner controls are installed for Stage 1 Window A. Production remains disabled; this run does not prove scheduled production, 30-day trial evidence, or live two-day operation.

## Today Mail Plan

- email_enabled: `true`
- split_mode: `five_independent_messages`
- send_order: `B1`, `B2`, `B3`, `B4`, `B5`
- recipients: `linzezhang35@gmail.com`

## Queue And Resource Pressure

- max_active_items: `10000`
- max_temp_cache_gb: `2`
- window_a_max_online_arxiv_metadata: `10`
- ranking_change_preview: `NOT_RUN_UNTIL_S1_06_REPLAY_DATA_EXISTS`

## Required Human Decisions

- No production enablement decision is accepted by this file alone.
- S1-04 must add the unified local SQLite model before broad source ingestion or queue replay can be trusted.

## Commands

- `adp owner validate`
- `adp owner preview-impact --days 30`
- `adp owner render-docs --write`
