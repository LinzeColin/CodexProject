# KMFA v0.1.4 S05-P3 Risk Register

- risk: public evidence accidentally includes raw filenames, source headers, sheet names, values, or business values
  mitigation: validator scans manifest, records and human evidence for forbidden public keys/text; raw inbox is not accessed.
- risk: calculation baseline is mistaken for formal report readiness
  mitigation: full Q5 quality, zero-delta, lineage, formal report and business execution flags remain false.
- risk: Excel owner-downgraded fields enter the locked calculation baseline
  mitigation: validator requires all 5 Excel fields to remain excluded_cross_source_support_only.

- baseline_content_hash: `sha256:1d9e663870917d82add8342fd8f06e60d18e192d1205e023c41a90561dcd88b8`
