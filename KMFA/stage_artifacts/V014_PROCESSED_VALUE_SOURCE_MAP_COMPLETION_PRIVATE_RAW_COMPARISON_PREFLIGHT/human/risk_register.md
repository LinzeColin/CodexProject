# Risk Register

- Risk: treating file-level inventory as value reconciliation.
  Mitigation: parsing, field/header read, raw value extraction and value matching remain blocked.
- Risk: leaking raw filenames or hashes.
  Mitigation: public artifacts contain only aggregate counts and type buckets; exact records stay in ignored private runtime.
