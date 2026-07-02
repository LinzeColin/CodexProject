# Next Raw Import Or Adapter Plan

Generated: 2026-07-03T08:15:45+10:00

Recommended next step: Sprint 2B-C decision point, not raw import.

If schema-readable candidates exist:
- Review only schema names and column metadata.
- Decide whether a content-safe adapter can be specified without decryption, key extraction, or protected-store bypass.
- Stop before selecting business rows unless an explicit approved run contract exists.

If no schema-readable candidates exist:
- Do not attempt SQLCipher keys or protected-store bypass.
- Consider a safe readability classification summary and decide whether WDA should rely on officially exported or user-provided readable artifacts instead.

Stop conditions for any later raw/import step:
- Any operation requires decryption/key extraction/protected-store bypass.
- Any step would open `key_info`, `login`, MMKV, KVDB, or key-value stores.
- Any step would select message/contact rows before a dedicated approved content-read contract.
- Any step would upload raw data.

Raw Gate remains Conditional Investigation until a later approved safe process produces explicit readable-message evidence.
