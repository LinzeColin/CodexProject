# Tests

Run:

```bash
python3 tests/test_stage2_consensus.py
```

The test suite verifies:

1. Five identical canonical hashes are accepted.
2. One divergent day-5 hash fails stage-2.
3. Volatile `generated_at` is excluded from canonical hash.
