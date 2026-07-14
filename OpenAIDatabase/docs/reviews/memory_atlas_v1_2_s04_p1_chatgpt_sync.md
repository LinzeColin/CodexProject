# Memory Atlas v1.2 S04 P1 ChatGPT Sync

Task ID: `MA-V12-S04P1`.

Acceptance ID: `ACC-MA-V12-S04P1`.

Status: `phase_s04_p1_chatgpt_sync_completed_pending_s04_p2`.

Validator: `validate:v1.2-s04-p1`.

## Result

S04 P1 adds the ChatGPT sync surface for Memory Atlas v1.2.

The browser connector is a read-only contract for an already logged-in browser
state. It stops on password or verification states and contains no send,
delete, archive or rename behavior.

The executable path is `scripts/sync_chatgpt_memory_data.py`, which supports
official export ZIP/conversations.json fallback. `scripts/atlasctl.py sync
--source chatgpt --dry-run` exposes the low-friction CLI contract without
writing files.

## Files

- `机器治理/同步与备份/chatgpt_readonly_sync_policy.v1_2_s04_p1.json`
- `scripts/sync_chatgpt_memory_data.py`
- `scripts/atlasctl.py`
- `人类可读/09_ChatGPT只读同步与官方导出Fallback.md`
- `tests/test_s04p1_chatgpt_sync.py`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s04_p1.cjs`

## Acceptance Coverage

- Browser connector boundary is read-only.
- Password or verification states fail closed.
- Official export ZIP/conversations.json fallback is executable.
- Dry-run writes no files.
- Apply mode requires an official export input and writes append-only public raw.
- Credential content fails before public raw write.

## Boundaries

- No Codex local sync in this phase.
- No future-agent adapter in this phase.
- No GitHub backup apply in this phase.
- No browser mutation.
- No GitHub main upload in this phase.

Next gate: pending S04 P2.
