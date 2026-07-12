# KMFA v0.1.4 S17-P3 Operations SOP Risk Register

- risk: Public-safe SOP metadata could be mistaken for production execution.
  mitigation: All runbooks use manual_sop_only and all drills use metadata_drill_only; restore and business execution counts remain zero.
- risk: Knowledge-index refs could be mistaken for private SOP documents.
  mitigation: Storage mode is public_safe_index_only and private documents are blocked from public evidence.
