# Tests

Run:

```bash
python3 tests/test_stage2_consensus.py
python3 tests/test_database_dry_run.py
python3 tests/test_database_landing_bundle.py
```

The test suite verifies:

1. Five identical canonical hashes are accepted.
2. One divergent day-5 hash fails stage-2.
3. Volatile `generated_at` is excluded from canonical hash.
4. PostgreSQL schema/view contract supports the stage-2 -> payroll baseline path.
5. Accepted stage-2 artifacts can generate an offline private DB landing bundle without database mutation or live DWS.
6. The private DB landing bundle is FK-complete and can generate a PostgreSQL JSONB/COPY load plan without opening PostgreSQL.
7. The generated PostgreSQL load plan is statically validated against schema columns, load order, payload files, and schema-backed `ON CONFLICT` targets.
