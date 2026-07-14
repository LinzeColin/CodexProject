# Risk Register

- Risk: final threshold recheck is mistaken for a value comparison retry.
- Control: public evidence keeps retry-ready count at zero and value comparison false.
- Risk: private threshold records leak handles.
- Control: private outputs remain git-ignored and public evidence is aggregate-only.
- Risk: raw data is modified during recheck.
- Control: this phase reads existing ignored private audit artifacts only and does not touch the raw inbox.
