# MooMoo/OpenD Smoke Report

- Generated at: 2026-06-14T10:06:53+08:00
- Status: pass
- Socket: OpenD socket reachable at 127.0.0.1:11111
- SDK: Python import `moomoo` is available; installed distribution version=10.6.6608

## Workbenches

- external:moomoo-api-workbench
  - start: `external:start_opend.sh`
  - SDK vendor: `external:MMAPI4Python_10.6.6608`

## Recommended Actions

- Moomoo/OpenD smoke is ready for read-only market data collection
- Optional independent quote smoke: python external:quote_smoke_test.py
- Keep OpenD running and logged in before scheduled collection windows
