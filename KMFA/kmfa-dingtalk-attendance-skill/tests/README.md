# Tests

Run:

```bash
python3 tests/test_stage2_consensus.py
python3 tests/test_database_dry_run.py
python3 tests/test_database_landing_bundle.py
python3 tests/test_raw_archive_replay.py
python3 tests/test_stage2_source_from_raw_replay.py
PYTHONPATH=tests:scripts:. python3 tests/test_preconsensus_database_proof.py
```

The test suite verifies:

1. Five identical canonical hashes are accepted only when required quality gates also pass.
2. One divergent day-5 hash fails stage-2.
3. Volatile `generated_at` is excluded from canonical hash.
4. PostgreSQL schema/view contract supports the stage-2 -> payroll baseline path.
5. Accepted stage-2 artifacts can generate an offline private DB landing bundle without database mutation or live DWS.
6. The private DB landing bundle is FK-complete and can generate a PostgreSQL JSONB/COPY load plan without opening PostgreSQL.
7. The generated PostgreSQL load plan is statically validated against schema columns, load order, payload files, and schema-backed `ON CONFLICT` targets.
8. The PostgreSQL load plan executor fail-closes unless non-production execution is explicitly authorized and acknowledged.
9. Private raw archive month replay inspection validates manifest/raw parity, seed raw isolation, location coverage thresholds, and stable replay hashes without exposing names, DingTalk IDs, raw rows, or local paths.
10. Offline replay stage-2 artifacts fail closed on day 5 until database transaction commit and verification gates are explicitly true.
11. Private raw archive replay can materialize day facts with raw detail linkage and a stable canonical replay hash without exposing names, DingTalk IDs, raw rows, or local paths in summary output.
12. A private raw replay day-fact/linkage bundle can materialize a Stage-2 source snapshot and resolver source adapter without live DWS, database mutation, employee plaintext, or raw DingTalk IDs.
13. Pre-consensus Stage-2 sources can generate a PostgreSQL landing bundle before payroll acceptance, and fail-closed non-production execution plus read-only state verification proofs can promote only the database gates used by Stage-2 consensus.
