# Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| RPD-001 | Raw numeric fingerprints could be mistaken for business consistency proof | Keep comparable pairs at zero until authorized processed source-map exists | controlled |
| RPD-002 | Processed private refs are path/ref-only | Require owner-authorized target-slot source mapping before materialization | active |
| RPD-003 | Raw files must remain immutable | Write all diagnostics only to ignored private runtime and verify raw mutation flag is false | controlled |
