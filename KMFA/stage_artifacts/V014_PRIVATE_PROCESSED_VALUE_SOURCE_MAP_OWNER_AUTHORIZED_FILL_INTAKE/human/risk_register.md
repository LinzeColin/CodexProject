# Risk Register

| Risk | Status | Control |
| --- | --- | --- |
| 113 gaps still require owner/authorized action | open | private intake request prepared; NO_GO preserved |
| Private refs leak to public artifacts | controlled | public artifacts contain aggregate counts and action-code schema only |
| Raw inbox mutation | controlled | this phase performs no raw inbox access or mutation |
| Premature materialization/comparison | blocked | Go/No-Go keeps replay and comparison false |
