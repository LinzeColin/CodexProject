# KMFA v1.4 S01-P1 Stop Conditions

Stop immediately if any of the following occurs:

- Any command attempts to write inside `/Users/linzezhang/Downloads/KMFA_MetaData`.
- Any raw/private payload file, ZIP, Excel, PDF, video, private CSV, raw filename, field/header plaintext, row value, or business value appears in a commit candidate.
- Any implementation starts outside `V014_S01_P1_READ_ONLY_SCOPE_LOCK`.
- Any report or UI output claims production readiness, formal report readiness, business decision basis, or delivery readiness.
- Any business amount code uses `float`.
- Any same-source inconsistency is found in later phases without invalidation, rerun, mismatch reporting, and report-grade downgrade.
