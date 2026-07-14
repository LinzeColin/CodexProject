# KMFA v0.1.4 S05-P1 Risk Register

| Risk | Mitigation | Status |
|---|---|---|
| Raw package names, member names or hashes could leak into public evidence. | Public files store only aggregate counts, redacted refs and status flags; private diagnostics remain under ignored runtime. | controlled |
| A0 file registration could be mistaken for field-level golden baseline. | Manifest keeps S05-P2, S05-P3, formal report, raw value matching and business execution false. | controlled |
| Local raw package may differ from the registered legacy source package. | Public evidence records only match status and blocks public hash backfill; private diagnostic preserves details locally. | controlled |
