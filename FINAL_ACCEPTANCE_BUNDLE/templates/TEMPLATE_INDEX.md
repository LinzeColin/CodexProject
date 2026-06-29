# S2PMT07 Final Bundle Artifact Templates

These files are templates only. They do not satisfy S2PMT07 readiness and must
not be copied into the live artifact paths until the named external evidence is
real, independently reviewed, hash-bound, and validated.

Live artifact paths remain blocked:

- `FINAL_ACCEPTANCE_BUNDLE/manifest.json`
- `FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json`
- `FINAL_ACCEPTANCE_BUNDLE/independent_final_reviewer_assignment.json`
- `FINAL_ACCEPTANCE_BUNDLE/p0_p1_zero_proof.json`
- `FINAL_ACCEPTANCE_BUNDLE/s2plt04_completion_report.json`
- `FINAL_ACCEPTANCE_BUNDLE/independent_review_signoff.yaml`
- `FINAL_ACCEPTANCE_BUNDLE/final_command_execution.json`
- `HANDOFF/00_下一Agent先读.md`

`manifest.template.json` is a final-bundle manifest skeleton only. It must not
be copied to `FINAL_ACCEPTANCE_BUNDLE/manifest.json` unless every required
bundle item is real, independently reviewed, validated, and ready for manifest
binding.

`s2plt02_real_proof_capture_authorization.template.json` is an owner-editable
template only. It must not be copied to
`FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json` unless
the owner explicitly approves real SMTP/scheduler proof capture and recomputes
the authorization hash against the current readiness state hash.

Current S2PLT02/S2PLT03/S2PLT04/S2PMT07 gates remain blocked. These templates
do not enable SMTP, scheduler, Release, restore, DAILY_OPERATION, or
INTEGRATED_PRODUCTION_ACCEPTED.
