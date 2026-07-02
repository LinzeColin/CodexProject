# S2PMT07 Final Bundle Artifact Templates

These files are templates only. They do not override the current live artifact
state, and they must not be copied into live artifact paths unless the named
external evidence is real, independently reviewed, hash-bound, and validated.

Stage 2 final-bundle live artifacts already exist and have been consumed by
the current Stage 2 integrated acceptance evidence. Historical final-bundle
templates remain useful only as schema examples; they must not be used to
roll current acceptance state backward.

The only current blocked live artifact path is `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`.

`manifest.template.json` is a final-bundle manifest skeleton only. It must not
be copied to `FINAL_ACCEPTANCE_BUNDLE/manifest.json` unless every required
bundle item is real, independently reviewed, validated, and ready for manifest
binding.

`s2plt02_real_proof_capture_authorization.template.json` is an owner-editable
template only. It must not be copied to
`FINAL_ACCEPTANCE_BUNDLE/s2plt02_real_proof_capture_authorization.json` unless
the owner explicitly approves real SMTP/scheduler proof capture and recomputes
the authorization hash against the current readiness state hash.

`daily_operation_persistent_enablement_authorization.template.json` is an
owner-editable DAILY_OPERATION authorization template only. It deliberately sets
`template_only=true` and `explicit_persistent_daily_operation_authorization=false`,
so copying it unchanged to
`FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`
must remain invalid. A partially edited copy is still invalid if it preserves
placeholder `generated_at` or `authorization_text` values. It may only be
converted into a live authorization artifact after the owner explicitly
authorizes persistent DAILY_OPERATION in the current thread, the timestamp and
authorization text are replaced with current owner evidence, all runtime
prechecks are still disabled, and the separate DAILY_OPERATION readiness /
enablement gates are rerun.

Current S3/DAILY_OPERATION remains blocked until the explicit persistent
authorization artifact exists and the separate readiness / enablement gates
pass. These templates do not enable SMTP, scheduler, Release, restore, or
DAILY_OPERATION. These templates do not change Stage 2 integrated acceptance.
