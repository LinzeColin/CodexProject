# Risk Register

| Risk | Control | Status |
|---|---|---|
| Metadata/quality output is mistaken for actual business zero-delta | Manifest keeps actual raw value matching false and Go/No-Go blocked | controlled |
| Sanitized report leaks source field/value plaintext | Validator blocks forbidden public output keys and source amount literals | controlled |
| S06-P3 is used to close unresolved difference | Manifest keeps difference_closed false and report grade A count zero | controlled |
