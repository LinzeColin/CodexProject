# PFI-004 Golden/PIT Truth Proof

Last updated: 2026-06-20 Australia/Sydney

## Objective

PFI-004 closes the local data-truth gap for Gate 1 by proving:

- Operational Store is the active authoritative store.
- `source_versions` supports point-in-time replay.
- Active `source_records` rejects retrograde writes.
- A deterministic financial Golden fixture produces stable metrics.
- Active truth and PIT replay reconcile through a dual-read check.

## Implemented Surfaces

- `src/pfi_os/application/operational_store.py`
  - rejects older active writes for the same `source_id` with
    `PIT_INVALID_WRITE`.
  - replays PIT sources by parsed `as_of` timestamps instead of relying only
    on string ordering.
- `src/pfi_os/application/pfi004_truth_golden.py`
  - declares `PFI004TruthContractV1`.
  - declares `PFI004GoldenPITAcceptanceV1`.
  - records a synthetic public Golden fixture into Operational Store.
  - computes deterministic financial metrics.
  - reconciles active truth against PIT replay.
  - verifies invalid-write rejection without provider, broker, order, payment,
    betting, or private-account mutation.
- `tests/contract/test_pfi004_truth_golden.py`
  - covers contract boundaries, Golden metrics, PIT replay, dual-read
    reconciliation, invalid-write rejection, and no-execution boundary.

## Golden Fixture

Fixture id: `pfi004-golden-market-bars`

| Version | as_of | URI |
|---|---|---|
| v1 | `2026-06-18T00:00:00+00:00` | `shared/canonical/golden/pfi004-bars-v1.json` |
| v2 | `2026-06-19T00:00:00+00:00` | `shared/canonical/golden/pfi004-bars-v2.json` |

Expected metrics from v2:

| Metric | Value |
|---|---:|
| observation_count | 4 |
| start_close | 100.00 |
| end_close | 105.00 |
| total_return_pct | 5.00 |
| max_drawdown_pct | -0.98 |

## Acceptance

Target command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' /opt/anaconda3/bin/python3.12 -m pytest tests/contract/test_pfi004_truth_golden.py tests/contract/test_phase_a_operational_store.py tests/contract/test_phase_a_source_registry_homepage.py -q
```

Observed local result:

```text
15 passed
```

Programmatic acceptance:

```python
from pfi_os.application import run_pfi004_truth_golden_acceptance

payload = run_pfi004_truth_golden_acceptance()
assert payload["schema"] == "PFI004GoldenPITAcceptanceV1"
assert payload["status"] == "Pass"
```

## Boundaries

PFI-004 proof uses synthetic public fixtures and the local Operational Store
only. It does not call market providers, brokers, order APIs, payment systems,
betting systems, LLM providers, or private account data.

## Remaining Gate Context

PFI-004 now has strong local proof. Gate 1 still needs PFI-001 PR/CI
injected-failure evidence before it can be closed.
