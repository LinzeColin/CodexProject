# Policy Intelligence System

This directory contains the migrated source package for the PFI_OS policy intelligence and government document interpretation system.

## Status

- Migration phase: source/tests/docs migrated.
- Runtime databases, report archives, platform auth, cookies, API keys, Chrome profiles, raw HTML snapshots, and local logs are intentionally excluded.
- The legacy local source remains the private runtime source of historical data:

```text
systems/policy_intelligence/source
```

## Included

```text
source/src/source_registry/
source/tests/
source/scripts/
source/config/
source/rules/
source/docs/
source/data/sample/
source/README.md
source/HANDOFF.md
source/pyproject.toml
```

## Excluded

```text
source/data/*.sqlite
source/data/automation/
source/data/monitor/
source/data/run_logs/
source/data/snapshots/
source/reports/
source/work/
~/.policy-intelligence/
Chrome profile data
cookies, sessions, API keys, platform auth files
raw HTML dumps and local debug logs
```

## Smoke Verification

From the PFI_OS repo root:

```bash
python3 -m compileall -q systems/policy_intelligence/source/src
bash -n systems/policy_intelligence/source/scripts/run_policy_report.sh
PYTHONPATH=systems/policy_intelligence/source/src python3 -m pytest \
  systems/policy_intelligence/source/tests/test_registry.py \
  systems/policy_intelligence/source/tests/test_quality_gates.py \
  systems/policy_intelligence/source/tests/test_readiness.py \
  systems/policy_intelligence/source/tests/test_automation_readiness.py \
  -q
PYTHONPATH=systems/policy_intelligence/source/src python3 -m source_registry --help >/dev/null
```

Or run the consolidated PFI_OS smoke:

```bash
./scripts/ciSmoke.sh
```

## Next Integration Step

Build a read-only PFI_OS adapter that publishes policy queue readiness, external-reference gaps, quality-gate status, and source authority summaries to ResearchBus. Do not publish raw document text, cookies, API keys, or local platform-auth paths.
