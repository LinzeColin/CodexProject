# KMFA v0.1.4 Value Consistency Scope Risk Register

| risk_id | risk | control | status |
|---|---|---|---|
| VC-SCOPE-001 | Scope lock could be mistaken for successful value matching | Keep raw value matching and business value consistency flags false | blocked |
| VC-SCOPE-002 | Difference report could leak values | Public contract requires sanitized report; detailed values stay private-runtime only if needed | controlled |
| VC-SCOPE-003 | Raw source could be polluted during analysis | Before/after stat guard and explicit mutation flags remain required | controlled |
