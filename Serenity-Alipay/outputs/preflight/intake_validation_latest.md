# Intake Validation

- Generated at: 2026-06-13T08:03:29+08:00
- Production ready: True
- Block gaps: 0
- Warn gaps: 6

## Gaps

- **alipay_positions / FUND001 / source_note** [warn]: optional source_note contains sample/demo marker
  - Action: Replace only if you want optional real-holding overlay
- **alipay_positions / FUND003 / source_note** [warn]: optional source_note contains sample/demo marker
  - Action: Replace only if you want optional real-holding overlay
- **alipay_positions / FUND004 / source_note** [warn]: optional source_note contains sample/demo marker
  - Action: Replace only if you want optional real-holding overlay
- **alipay_positions / FUND005 / source_note** [warn]: optional source_note contains sample/demo marker
  - Action: Replace only if you want optional real-holding overlay
- **benchmark_history / 000001.SH / source_type** [warn]: Shanghai Composite uses public aggregation fallback
  - Action: Prefer moomoo or official source when available
- **benchmark_history / SPX / source_type** [warn]: S&P 500 uses public aggregation fallback
  - Action: Prefer moomoo or official source when available

## Candidate Files Found

- None
