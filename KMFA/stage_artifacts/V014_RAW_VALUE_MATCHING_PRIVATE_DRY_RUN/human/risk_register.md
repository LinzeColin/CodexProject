# KMFA v0.1.4 Raw Value Matching Private Dry Run Risk Register

- risk: approved private processed value targets are missing.
  mitigation: keep NO_GO and create a separate private processed staging phase.
- risk: private fingerprints could be mistaken for public consistency evidence.
  mitigation: validator requires business_value_consistency_verified=false and public-safe aggregate-only evidence.
- risk: raw inbox mutation.
  mitigation: before/after stat guard and no writes to raw inbox.
