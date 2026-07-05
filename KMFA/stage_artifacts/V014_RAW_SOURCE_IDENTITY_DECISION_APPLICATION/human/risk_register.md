# Risk Register

| id | risk | mitigation | status |
|---|---|---|---|
| RAW-APP-001 | Missing owner decision could be mistaken for source identity closure | Application status remains blocked and Go/No-Go remains NO_GO | blocked |
| RAW-APP-002 | A pending decision could unlock downstream gates too early | keep_pending keeps decision_applied=false and every downstream gate false | controlled |
| RAW-APP-003 | Private source details could leak into public evidence | Validator scans public evidence for forbidden local markers, suffixes, hashes and secret-like tokens | controlled |
