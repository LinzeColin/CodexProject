## FORM-KMFA-V014-RESIDUAL-DIFFERENCE-RAW-CANDIDATE-ALIGNMENT-AFTER-PRECHECK-001

- version: `0.1.4-residual-difference-raw-candidate-alignment-after-precheck`
- model_id: `MOD-KMFA-GOV-001`
- scope: Build private residual-difference raw candidate anchor draft after precheck using read-only raw inbox access, without owner-authorizing anchors, running formal raw-to-processed comparison, reconciling values, uploading, reinstalling or executing business steps.
- rule: alignment is valid only when source blockers=72, raw-comparison input records=72, raw numeric candidates=351453, raw unique numeric fingerprints=22453, owner-authorized anchors=0, owner review required=72, alignment ready=0, and comparison/reconciliation/release/execution gates remain false.
- public_safety: public artifacts contain aggregate counts, status flags and evidence refs only; private alignment, anchor draft, question list and raw scan runtime remain ignored and untracked.
- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_candidate_alignment_after_precheck.py --require-private-alignment`
- evidence: `KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_RAW_CANDIDATE_ALIGNMENT_AFTER_PRECHECK/machine/residual_difference_raw_candidate_alignment_after_precheck_manifest.json`

## FORM-KMFA-V014-RESIDUAL-DIFFERENCE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-001

- version: `0.1.4-residual-difference-raw-to-processed-comparison-precheck`
- model_id: `MOD-KMFA-GOV-001`
- scope: Precheck residual-difference raw-to-processed comparison readiness without reading raw inbox, running formal raw-to-processed comparison, reconciling values, uploading, reinstalling or executing business steps.
- rule: precheck is valid only when source materialized records=72, source raw-comparison input records=72, comparison-ready records=0, comparison blockers=72, missing private comparison anchors=72, and raw-comparison/reconciliation/release/execution gates remain false.
- public_safety: public artifacts contain aggregate counts, status flags and evidence refs only; private precheck outputs remain ignored and untracked.
- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_raw_to_processed_comparison_precheck.py --require-private-precheck`
- evidence: `KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_RAW_TO_PROCESSED_COMPARISON_PRECHECK/machine/residual_difference_raw_to_processed_comparison_precheck_manifest.json`

## FORM-KMFA-V014-RESIDUAL-DIFFERENCE-PRIVATE-RESOLUTION-MATERIALIZATION-REPLAY-001

- version: `0.1.4-residual-difference-private-resolution-materialization-replay`
- model_id: `MOD-KMFA-GOV-001`
- scope: Materialize residual-difference private resolution records without reading raw inbox, running formal raw-to-processed comparison, reconciling values, uploading, reinstalling or executing business steps.
- rule: materialization replay is valid only when source application records=72, source application blockers=0, source materialization input records=72, private materialized records=72, materialization blockers=0, raw-to-processed comparison ready=true, and raw-comparison/reconciliation/release/execution gates remain false.
- public_safety: public artifacts contain aggregate counts, status flags and evidence refs only; private materialization outputs remain ignored and untracked.
- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_residual_difference_private_resolution_materialization_replay.py --require-private-replay`
- evidence: `KMFA/stage_artifacts/V014_RESIDUAL_DIFFERENCE_PRIVATE_RESOLUTION_MATERIALIZATION_REPLAY/machine/residual_difference_private_resolution_materialization_replay_manifest.json`

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-APPLICATION-001

- version: `0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-application`
- model_id: `MOD-KMFA-GOV-001`
- scope: Apply residual-difference private source-map correction / authoritative value resolution records without reading raw inbox, running materialization replay, comparing values, uploading, reinstalling or executing business steps.
- rule: application is valid only when source ready queue count=72, source blocker queue count=0, private application records applied=72, application blockers=0, private materialization input records=72, materialization replay ready=true, and materialization/raw-comparison/reconciliation/release/execution gates remain false.
- public_safety: public artifacts contain aggregate counts, status flags and evidence refs only; private application outputs remain ignored and untracked.
- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application.py --require-private-application`
- evidence: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION/machine/outside_scope_candidate_review_residual_difference_source_map_correction_application_manifest.json`

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-APPLICATION-READINESS-001

- version: `0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-application-readiness`
- model_id: `MOD-KMFA-GOV-001`
- scope: Validate private application readiness for residual-difference source-map correction / authoritative value resolution without applying corrections, closing discrepancies, reading raw inbox, comparing values, uploading, reinstalling or executing business steps.
- rule: readiness is valid only when source authorization count=72, private authorization queue count=72, application ready records=72, application blockers=0, private resolution application ready=true, next-phase application flags=true, and all write/comparison/reconciliation/release/execution gates remain false.
- public_safety: public artifacts contain aggregate counts, status flags and evidence refs only; private readiness outputs remain ignored and untracked.
- validator: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_v014_outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness.py --require-private-readiness`
- evidence: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_APPLICATION_READINESS/machine/outside_scope_candidate_review_residual_difference_source_map_correction_application_readiness_manifest.json`

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-AUTHORIZATION-INTAKE-001

- version: `0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-authorization-intake`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for recording owner authorization to prepare private residual-difference source-map correction or authoritative value resolution while keeping all application and value-consistency gates closed.
- expression: `source_map_correction_authorization_intake_valid = source_final_threshold_met == true AND authorization_item_count == 72 AND owner_authorization_intaken == true AND private_resolution_preparation_allowed_next_phase == true AND source_map_correction_written == false AND authoritative_value_resolution_written == false AND raw_to_processed_value_comparison_performed == false AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND decision == NO_GO`.
- inputs: prior public-safe final threshold summary/manifest/Go-No-Go/matrix, ignored private final threshold diagnostic/queue/report and raw immutable boundary.
- missing_policy: missing authorization intake manifest, Go/No-Go report, summary, matrix, private authorization active record, private authorization queue/diagnostic/report, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_AUTHORIZATION_INTAKE/machine/outside_scope_candidate_review_residual_difference_source_map_correction_authorization_intake_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private final threshold queue mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, source-map correction claim, authoritative value resolution claim, discrepancy closure claim, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-FINAL-THRESHOLD-RECHECK-001

- version: `0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-blocker-final-threshold-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for confirming the residual-difference source-map correction blocker has reached the strict blocked-goal threshold while keeping all value-consistency gates closed.
- expression: `source_map_correction_blocker_final_threshold_recheck_valid = valid_diagnostic_response_count == 72 AND missing_response_blocker_cleared == true AND non_actionable_diagnostic_response_count == 72 AND source_map_correction_blocker_count == 72 AND prior_source_map_correction_blocker_observation_count == 2 AND source_map_correction_blocker_observation_count == 3 AND source_map_correction_blocked_audit_threshold_met == true AND goal_status_recommendation == blocked AND source_map_actionable_response_count == 0 AND open_residual_difference_count == 72 AND closed_discrepancy_count == 0 AND source_map_correction_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public-safe source-map correction blocker threshold recheck summary/manifest/Go-No-Go/matrix, ignored private threshold diagnostic/queue/report and raw immutable boundary.
- missing_policy: missing final threshold recheck manifest, Go/No-Go report, summary, matrix, private final threshold diagnostic, private final threshold queue/report, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_FINAL_THRESHOLD_RECHECK/machine/outside_scope_candidate_review_residual_difference_source_map_correction_blocker_final_threshold_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private threshold output mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, discrepancy closure claim, source-map correction claim, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-THRESHOLD-RECHECK-001

- version: `0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-blocker-threshold-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for rechecking whether the residual-difference source-map correction blocker has reached the strict blocked-goal threshold while keeping all value-consistency gates closed.
- expression: `source_map_correction_blocker_threshold_recheck_valid = valid_diagnostic_response_count == 72 AND missing_response_blocker_cleared == true AND non_actionable_diagnostic_response_count == 72 AND source_map_correction_blocker_count == 72 AND prior_source_map_correction_blocker_observation_count == 1 AND source_map_correction_blocker_observation_count == 2 AND source_map_correction_blocked_audit_threshold_met == false AND source_map_actionable_response_count == 0 AND open_residual_difference_count == 72 AND closed_discrepancy_count == 0 AND source_map_correction_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public-safe source-map correction blocker audit summary/manifest/Go-No-Go/matrix, ignored private blocker audit diagnostic/queue/report and raw immutable boundary.
- missing_policy: missing threshold recheck manifest, Go/No-Go report, summary, matrix, private threshold diagnostic, private threshold queue/report, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_THRESHOLD_RECHECK/machine/outside_scope_candidate_review_residual_difference_source_map_correction_blocker_threshold_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private blocker audit mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, discrepancy closure claim, source-map correction claim, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-DISCREPANCY-CLOSURE-BLOCKER-AUDIT-001

- version: `0.1.4-outside-scope-candidate-review-discrepancy-closure-blocker-audit`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for auditing unresolved private discrepancy closure blockers without mutating raw data, closing differences, or inventing value matches.
- expression: `discrepancy_closure_blocker_audit_valid = source_private_blocking_queue_item_count == 72 AND residual_blocker_queue_item_count == 72 AND open_closure_blocker_count == 72 AND closed_discrepancy_count == 0 AND safe_auto_closure_count == 0 AND newly_actionable_closure_count == 0 AND ambiguous_selection_required_count == 24 AND authoritative_source_reference_required_count == 40 AND formula_or_non_numeric_mapping_required_count == 8 AND discrepancy_closure_complete == false AND source_map_correction_ready == false AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public-safe closure readiness summary/manifest, ignored private closure blocker queue/workpack and raw immutable boundary.
- missing_policy: missing blocker audit manifest, Go/No-Go report, summary, matrix, private blocker audit diagnostic, private residual blocker queue, private residual report, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_BLOCKER_AUDIT/machine/outside_scope_candidate_review_discrepancy_closure_blocker_audit_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private closure blocker queue/workpack mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, difference closure claim, source-map correction claim, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-DISCREPANCY-CLOSURE-READINESS-001

- version: `0.1.4-outside-scope-candidate-review-discrepancy-closure-readiness`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for classifying private discrepancy queue items into closure blockers without mutating raw data, closing differences, or inventing value matches.
- expression: `discrepancy_closure_readiness_valid = source_discrepancy_queue_item_count == 72 AND closure_plan_item_count == 72 AND closure_ready_item_count == 0 AND closure_blocked_item_count == 72 AND safe_auto_closure_count == 0 AND ambiguous_tie_closure_blocker_count == 24 AND no_context_candidate_closure_blocker_count == 40 AND non_numeric_or_calculation_closure_blocker_count == 8 AND source_map_correction_ready == false AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public-safe discrepancy summary, ignored private discrepancy queue and raw immutable boundary.
- missing_policy: missing closure readiness manifest, Go/No-Go report, summary, matrix, private closure readiness record, private closure blocking queue, private closure workpack, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_DISCREPANCY_CLOSURE_READINESS/machine/outside_scope_candidate_review_discrepancy_closure_readiness_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private discrepancy queue mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, difference closure claim, source-map correction claim, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-OWNER-AUTHORIZED-DISCREPANCY-REPORT-001

- version: `0.1.4-outside-scope-candidate-review-owner-authorized-discrepancy-report`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for recording an owner-authorized automatic conservative resolution attempt and reporting unresolved private discrepancies without mutating raw data or inventing value matches.
- expression: `owner_authorized_discrepancy_report_valid = source_review_item_count == 72 AND direct_exact_private_match_count == 0 AND safe_auto_resolution_count == 0 AND discrepancy_queue_item_count == 72 AND ambiguous_tied_candidate_item_count == 24 AND auto_unmatched_item_count == 40 AND non_numeric_or_calculation_item_count == 8 AND source_map_correction_ready == false AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: owner latest authorization, prior threshold recheck public-safe summary, ignored private review packet items, ignored private alignment items and raw immutable boundary.
- missing_policy: missing discrepancy report manifest, Go/No-Go report, summary, matrix, private discrepancy queue, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_OWNER_AUTHORIZED_DISCREPANCY_REPORT/machine/outside_scope_candidate_review_owner_authorized_discrepancy_report_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private review/alignment mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, private candidate selection claim, source-map correction claim, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-BLOCKER-THRESHOLD-RECHECK-001

- version: `0.1.4-outside-scope-candidate-review-intake-blocker-threshold-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for rechecking whether the same candidate-review keep-pending blocker has reached the strict blocked-goal threshold while keeping all value-consistency gates closed.
- expression: `candidate_review_intake_blocker_threshold_recheck_valid = prior_review_intake_blocker_observation_count == 2 AND review_intake_blocker_observation_count == 3 AND review_intake_blocked_audit_threshold_met == true AND goal_status_recommendation == blocked AND delegated_decision_record_count == 72 AND delegated_keep_pending_response_count == 72 AND selected_private_candidate_count == 0 AND corrected_source_map_reference_count == 0 AND authoritative_non_numeric_or_calculation_mapping_count == 0 AND source_map_actionable_response_count == 0 AND source_map_correction_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior blocker audit public-safe summary, prior blocker audit public-safe manifest, ignored prior private blocker audit diagnostic and raw immutable boundary.
- missing_policy: missing threshold recheck manifest, Go/No-Go report, summary, matrix, private threshold recheck diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_THRESHOLD_RECHECK/machine/outside_scope_candidate_review_intake_blocker_threshold_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private blocker audit diagnostic mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, private candidate selection, source-map correction, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-BLOCKER-AUDIT-001

- version: `0.1.4-outside-scope-candidate-review-intake-blocker-audit`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for recording the second keep-pending outside-scope candidate review blocker observation while keeping all value-consistency gates closed.
- expression: `candidate_review_intake_blocker_audit_valid = delegated_decision_record_count == 72 AND delegated_keep_pending_response_count == 72 AND selected_private_candidate_count == 0 AND corrected_source_map_reference_count == 0 AND authoritative_non_numeric_or_calculation_mapping_count == 0 AND source_map_actionable_response_count == 0 AND review_intake_blocker_observation_count == 2 AND review_intake_blocked_audit_threshold_met == false AND source_map_correction_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public readiness summary, prior public readiness manifest, ignored private readiness diagnostic and raw immutable boundary.
- missing_policy: missing blocker audit manifest, Go/No-Go report, summary, matrix, private blocker audit diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_BLOCKER_AUDIT/machine/outside_scope_candidate_review_intake_blocker_audit_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private readiness diagnostic mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, private candidate selection, source-map correction, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-READINESS-RECHECK-001

- version: `0.1.4-outside-scope-candidate-review-intake-readiness-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for rechecking whether a delegated keep-pending outside-scope candidate review intake can unlock source-map correction while keeping all value-consistency gates closed.
- expression: `candidate_review_intake_readiness_valid = delegated_decision_record_count == 72 AND delegated_keep_pending_response_count == 72 AND selected_private_candidate_count == 0 AND corrected_source_map_reference_count == 0 AND authoritative_non_numeric_or_calculation_mapping_count == 0 AND source_map_actionable_response_count == 0 AND review_intake_blocker_observation_count == 1 AND review_intake_blocked_audit_threshold_met == false AND source_map_correction_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public intake summary, ignored private delegated response record, ignored private delegated response items, ignored private delegated response diagnostic and raw immutable boundary.
- missing_policy: missing readiness recheck manifest, Go/No-Go report, summary, matrix, private readiness diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_READINESS_RECHECK/machine/outside_scope_candidate_review_intake_readiness_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source private response mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, private candidate selection, source-map correction, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-INTAKE-AFTER-PACKET-001

- version: `0.1.4-outside-scope-candidate-review-intake-after-packet`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for intaking a delegated conservative response to the 72-item private outside-scope candidate review packet while keeping all source-map correction and value-consistency gates closed.
- expression: `review_intake_valid = source_review_packet_item_count == 72 AND intake_response_item_count == 72 AND delegated_decision_record_count == 72 AND delegated_keep_pending_response_count == 72 AND selected_private_candidate_count == 0 AND corrected_source_map_reference_count == 0 AND authoritative_non_numeric_or_calculation_mapping_count == 0 AND source_map_actionable_response_count == 0 AND source_map_correction_ready == false AND raw_to_processed_value_comparison_performed == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public review-packet summary, ignored private review packet, ignored private review packet items and raw immutable boundary.
- missing_policy: missing intake manifest, Go/No-Go report, summary, matrix, private delegated response record, private delegated response items, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_INTAKE_AFTER_PACKET/machine/outside_scope_candidate_review_intake_after_packet_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source private review packet mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, private candidate selection, source-map correction, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-PACKET-AFTER-ALIGNMENT-001

- version: `0.1.4-outside-scope-candidate-review-packet-after-alignment`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for preparing owner/authorized-delegate review of 72 outside-scope alignment items while keeping all downstream value-consistency gates closed.
- expression: `outside_scope_candidate_review_packet_valid = source_alignment_item_count == 72 AND review_packet_item_count == 72 AND review_group_count == 10 AND ambiguous_review_item_count == 24 AND unmatched_review_item_count == 40 AND non_numeric_or_calculation_review_item_count == 8 AND private_candidate_option_excerpt_count == 240 AND candidate_record_observation_count == 56748 AND candidate_unique_fingerprint_observation_count == 19292 AND owner_review_required_item_count == 72 AND owner_review_response_supplied == false AND source_map_correction_ready == false AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: previous public alignment summary, previous ignored private alignment packet/items and raw immutable boundary.
- missing_policy: missing review packet manifest, Go/No-Go report, summary, matrix, private packet, private packet items, private markdown, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_PACKET_AFTER_ALIGNMENT/machine/outside_scope_candidate_review_packet_after_alignment_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source private alignment mutation, candidate selection, source-map correction, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-RAW-CANDIDATE-ALIGNMENT-AFTER-FULL-PRECHECK-001
- version: `0.1.4-outside-scope-raw-candidate-alignment-after-full-precheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for diagnosing the 72 outside-scope full-comparison precheck blockers against authorized raw candidates while keeping all downstream value-consistency gates closed.
- expression: `outside_scope_raw_candidate_alignment_valid = outside_scope_blocker_count == 72 AND raw_numeric_candidate_count == 351453 AND raw_unique_numeric_fingerprint_count == 22453 AND outside_scope_context_group_count == 10 AND auto_ambiguous_candidate_item_count == 24 AND auto_unmatched_item_count == 40 AND non_numeric_or_calculation_context_item_count == 8 AND direct_source_record_ref_match_count == 0 AND direct_processed_fingerprint_match_count == 0 AND owner_review_required_item_count == 72 AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: previous full comparison precheck public summary, ignored private blocker records, ignored private full materialized records, ignored private processed staging and current authorized read-only raw scan.
- missing_policy: missing alignment manifest, Go/No-Go report, summary, matrix, private alignment, private diagnostic, private items, private review question list, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_RAW_CANDIDATE_ALIGNMENT_AFTER_FULL_PRECHECK/machine/outside_scope_raw_candidate_alignment_after_full_precheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox write/delete/move/copy/normalize/overwrite, source-map correction, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-FULL-RAW-TO-PROCESSED-COMPARISON-PRECHECK-AFTER-FULL-MATERIALIZATION-001
- version: `0.1.4-full-raw-to-processed-comparison-precheck-after-full-materialization`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for prechecking all 149 full materialized processed-value records against ignored private raw-derived candidate fingerprints while keeping formal raw-to-processed comparison and downstream value-consistency gates closed.
- expression: `full_comparison_precheck_valid = processed_target_slot_count == 149 AND full_materialized_record_count == 149 AND candidate_catalog_record_count == 366 AND full_scope_exact_fingerprint_match_count == 77 AND full_scope_fingerprint_mismatch_count == 0 AND full_scope_missing_candidate_count == 72 AND outside_scope_missing_candidate_count == 72 AND full_unique_processed_value_fingerprint_count == 84 AND full_raw_to_processed_value_comparison_precheck_passed == false AND raw_to_processed_value_comparison_performed == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior full materialization public summary, ignored private full replay, ignored private full materialized records, ignored private candidate catalog and raw immutable boundary.
- missing_policy: missing full comparison precheck manifest, Go/No-Go report, summary, matrix, private precheck, private comparison records, private blocker records, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_FULL_RAW_TO_PROCESSED_COMPARISON_PRECHECK_AFTER_FULL_MATERIALIZATION/machine/full_raw_to_processed_comparison_precheck_after_full_materialization_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source private replay mutation, source private materialized records mutation, source private candidate catalog mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, formal raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-FULL-MATERIALIZATION-REPLAY-AFTER-OUTSIDE-SCOPE-APPLICATION-001
- version: `0.1.4-full-materialization-replay-after-outside-scope-application`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for materializing all 149 processed-value source-map records in ignored private runtime while keeping raw-to-processed comparison and downstream value-consistency gates closed.
- expression: `full_materialization_replay_valid = processed_target_slot_count == 149 AND full_materialization_source_map_record_count == 149 AND full_materialized_record_count == 149 AND full_materialization_blocked_record_count == 0 AND linked_materialized_record_count == 77 AND outside_scope_materialized_record_count == 72 AND full_unique_private_value_source_count == 84 AND full_processed_value_materialization_complete == true AND raw_to_processed_value_comparison_ready == true AND raw_to_processed_value_comparison_performed == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior outside-scope application public summary, ignored private full source-map input, ignored private processed target staging and raw immutable boundary.
- missing_policy: missing full materialization replay manifest, Go/No-Go report, summary, matrix, private replay, private materialized records, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_FULL_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_OUTSIDE_SCOPE_APPLICATION/machine/full_processed_value_materialization_replay_after_outside_scope_application_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source private source-map mutation, source private staging mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-APPLICATION-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-application`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for applying 72 owner-authorized outside-scope source-map extension records in ignored private runtime and preparing a 149-record private materialization input while keeping materialization and downstream value-consistency gates closed.
- expression: `application_valid = source_ready_queue_record_count == 72 AND outside_scope_source_map_extension_applied_record_count == 72 AND outside_scope_source_map_extension_blocker_count == 0 AND outside_scope_source_map_extension_duplicate_target_slot_count == 0 AND existing_linked_source_map_record_count == 77 AND private_full_materialization_source_map_record_count == 149 AND full_processed_value_materialization_ready == true AND full_processed_value_materialization_performed_by_this_phase == false AND raw_to_processed_value_comparison_performed == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public application-readiness summary, ignored private application-ready queue, ignored private readiness diagnostic, ignored linked private source-map and raw immutable boundary.
- missing_policy: missing application manifest, Go/No-Go report, summary, matrix, private application diagnostic/result/applied records/source-map/full materialization source-map, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION/machine/outside_scope_authorized_source_map_extension_application_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source ready queue mutation, linked private source-map mutation, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, materialization replay, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-APPLICATION-READINESS-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-application-readiness`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for checking whether 72 owner-authorized outside-scope source-map extension records are ready for a later application phase while keeping application and downstream value-consistency gates closed.
- expression: `application_readiness_valid = source_valid_authorized_extension_record_count == 72 AND private_active_authorization_record_count == 72 AND private_authorization_queue_count == 72 AND application_ready_record_count == 72 AND application_blocker_count == 0 AND duplicate_target_slot_count == 0 AND source_map_extension_application_ready == true AND source_map_extension_application_performed_by_this_phase == false AND source_map_extension_written_by_this_phase == false AND raw_to_processed_value_comparison_performed == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior public owner authorization intake summary, ignored private owner authorization active record, ignored private owner authorization queue, ignored private owner authorization diagnostic and raw immutable boundary.
- missing_policy: missing application readiness manifest, Go/No-Go report, summary, matrix, private readiness diagnostic, private ready queue, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_APPLICATION_READINESS/machine/outside_scope_authorized_source_map_extension_application_readiness_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private authorization mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-OWNER-AUTHORIZATION-INTAKE-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-owner-authorization-intake`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for intaking owner direct authorization for the 72 outside-scope source-map extension records into ignored private runtime while keeping all downstream value-consistency gates closed.
- expression: `owner_authorization_intake_valid = source_private_template_item_count == 72 AND source_private_pending_queue_count == 72 AND owner_direct_authorization_present == true AND owner_authorized_extension_record_count == 72 AND valid_authorized_extension_record_count == 72 AND invalid_authorized_extension_record_count == 0 AND missing_authorized_extension_record_count == 0 AND source_map_extension_ready_count == 72 AND source_map_extension_blocker_count == 0 AND source_map_extension_application_ready == true AND source_map_extension_written_by_this_phase == false AND raw_to_processed_value_comparison_performed == false AND processed_consistency_verified == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: user direct authorization statement, ignored private authorized extension template, ignored private pending queue, prior public blocker threshold summary and raw immutable boundary.
- missing_policy: missing owner authorization manifest, Go/No-Go report, summary, matrix, private active authorization record, private authorization queue, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_OWNER_AUTHORIZATION_INTAKE/machine/outside_scope_authorized_source_map_extension_owner_authorization_intake_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-POST-DELEGATION-BLOCKER-THRESHOLD-RECHECK-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-post-delegation-blocker-threshold-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for rechecking whether the same delegated keep-pending blocker has reached the strict post-delegation blocked-goal threshold.
- expression: `post_delegation_blocker_threshold_recheck_valid = prior_post_delegation_blocker_observation_count == 2 AND post_delegation_blocker_observation_count == 3 AND post_delegation_blocked_audit_threshold_met == true AND goal_status_recommendation == blocked AND delegated_decision_record_count == 72 AND delegated_keep_pending_decision_count == 72 AND delegated_authorize_source_map_extension_count == 0 AND valid_authorized_extension_record_count == 0 AND source_map_extension_application_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: prior post-delegation blocker audit public-safe summary, ignored prior private diagnostic, raw immutable boundary.
- missing_policy: missing threshold recheck manifest, Go/No-Go report, summary, matrix, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_POST_DELEGATION_BLOCKER_THRESHOLD_RECHECK/machine/outside_scope_authorized_source_map_extension_post_delegation_blocker_threshold_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private diagnostic mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-POST-DELEGATION-BLOCKER-AUDIT-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-post-delegation-blocker-audit`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for auditing whether the same delegated keep-pending blocker has repeated after delegated decision readiness recheck.
- expression: `post_delegation_blocker_audit_valid = prior_post_delegation_blocker_observation_count == 1 AND post_delegation_blocker_observation_count == 2 AND post_delegation_blocked_audit_threshold_met == false AND delegated_decision_record_count == 72 AND delegated_keep_pending_decision_count == 72 AND delegated_authorize_source_map_extension_count == 0 AND valid_authorized_extension_record_count == 0 AND source_map_extension_application_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: delegated decision readiness recheck public-safe summary, ignored prior private diagnostic, raw immutable boundary.
- missing_policy: missing post-delegation blocker audit manifest, Go/No-Go report, summary, matrix, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_POST_DELEGATION_BLOCKER_AUDIT/machine/outside_scope_authorized_source_map_extension_post_delegation_blocker_audit_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private diagnostic mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-DELEGATED-DECISION-READINESS-RECHECK-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-delegated-decision-readiness-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for rechecking whether delegated outside-scope decisions authorize source-map extension application.
- expression: `delegated_decision_readiness_valid = delegated_decision_record_count == 72 AND delegated_keep_pending_decision_count == 72 AND delegated_authorize_source_map_extension_count == 0 AND delegated_application_allowed_count == 0 AND valid_authorized_extension_record_count == 0 AND source_map_extension_application_ready == false AND post_delegation_blocked_audit_threshold_met == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: ignored prior private delegated decision record, ignored prior private delegated decision queue, prior public delegated keep-pending summary, raw immutable boundary.
- missing_policy: missing readiness recheck manifest, Go/No-Go report, summary, matrix, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_DELEGATED_DECISION_READINESS_RECHECK/machine/outside_scope_authorized_source_map_extension_delegated_decision_readiness_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, prior private decision mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business content, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-DELEGATED-KEEP-PENDING-DECISION-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-delegated-keep-pending-decision`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for recording delegated conservative outside-scope source-map extension decisions.
- expression: `delegated_keep_pending_valid = delegated_decision_record_count == 72 AND delegated_keep_pending_decision_count == 72 AND exact_source_record_ref_match_count == 0 AND exact_processed_ref_match_count == 0 AND valid_authorized_extension_record_count == 0 AND source_map_extension_application_ready == false AND downstream_allowed == false AND decision == NO_GO`.
- inputs: ignored private authorized extension template, ignored private outside-scope resolution evidence, ignored private candidate catalog, raw immutable boundary.
- missing_policy: missing delegated decision manifest, Go/No-Go report, summary, matrix, private decision record, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_DELEGATED_KEEP_PENDING_DECISION/machine/outside_scope_authorized_source_map_extension_delegated_keep_pending_decision_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, original private template mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business value, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-RESUMED-READINESS-RECHECK-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-resumed-readiness-recheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for rechecking outside-scope authorized source-map extension readiness after goal resume.
- expression: `outside_scope_extension_resumed_readiness_valid = resumed_goal_turn_blocker_count == 1 AND resumed_blocked_audit_threshold_met == false AND valid_authorized_extension_record_count == 0 AND missing_authorized_extension_record_count == 72 AND source_map_extension_application_ready == false AND goal_status_recommendation == continue_waiting_for_owner_input AND downstream_allowed == false`.
- inputs: ignored private authorized extension template, prior public blocker audit summary, raw immutable boundary.
- missing_policy: missing resumed readiness manifest, Go/No-Go report, summary, matrix, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_RESUMED_READINESS_RECHECK/machine/outside_scope_authorized_source_map_extension_resumed_readiness_recheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, private template mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business value, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-BLOCKER-AUDIT-001
- version: `0.1.4-outside-scope-authorized-source-map-extension-blocker-audit`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for auditing repeated owner/authorized source-map extension input blockers.
- expression: `outside_scope_extension_blocker_audit_valid = consecutive_goal_turn_blocker_count == 3 AND blocked_audit_threshold_met == true AND valid_authorized_extension_record_count == 0 AND missing_authorized_extension_record_count == 72 AND source_map_extension_application_ready == false AND goal_status_recommendation == blocked AND downstream_allowed == false`.
- inputs: prior outside-scope extension public summary, prior readiness public summary, git-ignored private blocker diagnostic, raw immutable boundary.
- missing_policy: missing blocker audit manifest, Go/No-Go report, summary, matrix, private diagnostic, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_BLOCKER_AUDIT/machine/outside_scope_authorized_source_map_extension_blocker_audit_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, private template mutation, source-map extension application, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, target-slot detail, business value, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-LINKED-SCOPE-RAW-TO-PROCESSED-COMPARISON-PRECHECK-001
- version: `0.1.4-linked-scope-raw-to-processed-comparison-precheck`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for prechecking linked-scope private raw-derived fingerprints against processed replay fingerprints.
- expression: `linked_scope_precheck_valid = linked_materialized_record_count == 77 AND linked_scope_private_fingerprint_precheck_pair_count == 77 AND linked_scope_exact_fingerprint_match_count == 77 AND linked_scope_fingerprint_mismatch_count == 0 AND linked_scope_missing_candidate_count == 0 AND linked_scope_invalid_materialized_record_count == 0 AND full_raw_to_processed_value_comparison_complete == false AND business_value_consistency_verified == false AND downstream_allowed == false`.
- inputs: linked materialization replay public summary, git-ignored private linked materialized records, git-ignored private candidate catalog, raw immutable boundary.
- missing_policy: missing linked-scope precheck manifest, Go/No-Go report, summary, matrix, private precheck, private diagnostic, private comparison records, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_LINKED_SCOPE_RAW_TO_PROCESSED_COMPARISON_PRECHECK/machine/linked_scope_raw_to_processed_comparison_precheck_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, public raw source name, field/header plaintext, row/cell coordinate, private fingerprint, business value, full raw-to-processed comparison claim, processed-data reconciliation, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-PROCESSED-VALUE-MATERIALIZATION-REPLAY-AFTER-LINKED-REAPPLICATION-001
- version: `0.1.4-linked-materialization-replay`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe gate for replaying linked-scope processed value materialization after linked source-map reapplication.
- expression: `linked_materialization_replay_valid = processed_target_slot_count == 149 AND linked_materialization_source_map_record_count == 77 AND linked_materialized_record_count == 77 AND linked_materialization_blocked_record_count == 0 AND processed_target_slot_outside_linked_replay_scope_count == 72 AND linked_scope_raw_to_processed_value_comparison_ready == true AND raw_to_processed_value_comparison_performed == false AND business_value_consistency_verified == false AND downstream_allowed == false`.
- inputs: linked source-map reapplication public summary, git-ignored private materialization source-map input, git-ignored private processed target staging, raw immutable boundary.
- missing_policy: missing linked replay manifest, Go/No-Go report, summary, matrix, private replay, private materialized records, private unmaterialized scope records, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_MATERIALIZATION_REPLAY_AFTER_LINKED_REAPPLICATION/machine/processed_value_materialization_replay_after_linked_reapplication_manifest.json` and paired public-safe summary/Go-No-Go/matrix evidence.
- forbidden_scope: raw inbox read/list/stat/fingerprint/parse/write/delete/move/copy/normalize/overwrite, public raw source name, field/header plaintext, row/cell coordinate, business value, full processed value materialization claim, raw-to-processed comparison, lineage full check, formal report, GitHub upload, app reinstall and business execution.

## FORM-KMFA-V014-PRIVATE-PROCESSED-VALUE-SOURCE-MAP-OWNER-AUTHORIZED-FILL-RECORD-DRAFT-001
- version: `0.1.4-private-processed-value-source-map-owner-authorized-fill-record-draft`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe draft gate for owner-authorized private processed value source-map fill records.
- expression: `draft_ready = private_intake_request_item_count == 113 AND draft_fill_item_count == 113 AND draft_keep_pending_item_count == 113 AND active_authorized_fill_record_created == false AND fill_application_performed == false AND source_map_records_applied_count == 0 AND new_authorized_fingerprint_count == 0 AND raw_inbox_access == false AND downstream_allowed == false`.
- inputs: owner-authorized fill intake contract, public-safe intake packet, git-ignored private intake request, raw immutable boundary.
- missing_policy: missing draft manifest, Go/No-Go report, summary, preview, private draft, validator, focused test, governance row or raw-boundary flag fails validation.
- outputs: `KMFA/stage_artifacts/V014_PRIVATE_PROCESSED_VALUE_SOURCE_MAP_OWNER_AUTHORIZED_FILL_RECORD_DRAFT/machine/private_processed_value_source_map_owner_authorized_fill_record_draft_manifest.json` and paired public-safe summary/Go-No-Go evidence.
- forbidden_scope: active owner authorization creation, source-map application, processed value materialization replay, raw-to-processed comparison, lineage full check, formal report, GitHub upload, app reinstall, raw inbox access, raw inbox mutation and business execution.

## FORM-KMFA-V014-S17P1-ACCESS-SECURITY-001
- version: `0.1.4-s17p1-access-security`
- model_id: `MOD-KMFA-GOV-001`
- purpose: deterministic public-safe S17-P1 access/security gate.
- expression: `s17p1_valid = s16_stage_review_dependency_PASS AND legacy_s17p1_baseline_PASS AND role_count == 4 AND sensitive_policy_category_count == 15 AND audit_action_type_count == 5 AND notification_delivery_count == 0 AND full_report_email_body_count == 0 AND external_connector_count == 0 AND formal_report_count == 0 AND business_execution_count == 0 AND raw_inbox_access_count == 0 AND s17_p2_performed == false AND s17_p3_performed == false AND stage17_review_performed == false AND github_upload_performed == false`.
- inputs: role permission matrix, sensitive public repository policy lock, audit-log policy lock, v1.4 S17-P1 taskpack/roadmap anchors and S16 review manifest.
- missing_policy: missing dependency, role coverage, sensitive-data policy, audit action coverage, public-safe boundaries, focused test, validator or evidence fails S17-P1 validation.
- outputs: `KMFA/stage_artifacts/V014_S17_P1_ACCESS_SECURITY/machine/access_security_manifest.json` and paired JSONL locks.
- forbidden_scope: S17-P2, S17-P3, Stage17 review, GitHub upload, protected source matching, lineage full check, notification delivery, full report body, formal report, external connector, app reinstall, raw inbox access and business execution.

# KMFA Model Spec

product_version: 0.1.4-s16p3-customer-business-analysis

## Scope

当前 v0.1.4 scope lock：S16-P3 客户经营分析已本地通过，验证 S16-P2 dependency、S08/S09/S13 public-safe fact manifests、v1.4 taskpack/roadmap requirements、v0.1.4 S16-P3 validator 和 focused unit test；source lanes=7、customer value dimensions=4、value signals=4、risk signals=4、customer summaries=4、handoff guards=4、pending reconciliation=12、formal report/business decision basis/customer contact/collection/legal/payment/bank=0、report grade=D，当前仍为 NO_GO/Q4/D/blocked。该 phase 仅只读执行 raw/private aggregate alignment 且公开证据不发布 raw 文件名、hash、字段/表头明文、客户/项目明文或业务值；未执行 Stage 16 review、GitHub upload、protected source matching、lineage full check、正式报告生成、UI runtime、live connector、app reinstall、OpMe 深度耦合、外部邮件连接器、完整报告邮件正文、客户联络、催收、法务、开票、付款、银行操作或业务执行。

当前模型说明覆盖 v0.1.4 Stage 10 整体复审、v0.1.4 S10-P3 报告导出、v0.1.4 S10-P2 报告可信等级、v0.1.4 S10-P1 报告模板、v0.1.4 Stage 9 整体复审、v0.1.4 S09-P3 口径转换与差异核对、v0.1.4 S09-P2 毛利与现金毛利、v0.1.4 S09-P1 项目成本事实层、v0.1.4 Stage 8 整体复审、v0.1.4 S08-P3 实体匹配质量、v0.1.4 S08-P2 业务实体模型、v0.1.4 S08-P1 项目组合键、v0.1.4 Stage 7 整体复审、v0.1.4 S07-P3 Redcircle postponement、v0.1.4 S07-P2 WPS file adapter、v0.1.4 S07-P1 finance file adapter、v0.1.4 Stage 6 整体复审、v0.1.4 S06-P3 validation evidence、v0.1.4 S06-P2 difference queue、v0.1.4 S06-P1 zero-delta validator、v0.1.4 Stage 5 整体复审、v0.1.4 S05-P3 权威基准锁定、v0.1.4 S05-P2 字段级黄金基准、v0.1.4 S05-P1 A0 文件登记、v0.1.4 Stage 4 整体复审、v0.1.4 S04-P3 基础工具测试、v0.1.4 S04-P2 字段标准化、v0.1.4 S04-P1 金额精度与基础工具、v0.1.4 Stage 3 整体复审、v0.1.4 S03-P3 源优先级、v0.1.4 S03-P2 数据源检查矩阵、v0.1.4 S03-P1 文件型导入登记、v0.1.4 Stage 2 整体复审、v0.1.4 S02-P3 数据质量等级、v0.1.4 S02-P2 不可污染原则、v0.1.4 S02-P1 metadata 协议、v0.1.4 Stage 1 整体复审、v0.1.4 S01-P3 no-omission baseline、v0.1.4 S01-P2 public-safe baseline sync、v0.1.4 S01-P1 只读检查与范围锁定，以及既有 public-safe KMFA 治理、metadata、质量门禁、文件导入、源优先级、金额精度、字段标准化、A0 基准、差异队列、报告、UI、人工处理、财务经营、通知、运维和回归验收模型。v0.1.4 Stage 10 review 只证明 S10-P1/S10-P2/S10-P3 public-safe 报告层本地复审闭环：phase_results 全部 PASS，open findings=0，fixed findings=2，report templates=2，report grade records=2，report exports=2，HTML exports=2，CSV appendices=2，Excel-compatible CSV downloads=2，pending reconciliation=12，confirmed resolution=0，formal report=0，business decision basis=0，当前仍为 NO_GO/Q4/D/blocked。本 review 未读取 raw inbox，不执行 S11、GitHub upload、actual business raw value matching、lineage 完整检查、正式报告生成、UI runtime、live connector、app reinstall、OpMe 深度耦合、外部邮件连接器、完整报告邮件正文、采购执行、付款审批、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收或法律决策。

## Active Model

### MOD-KMFA-GOV-001

- type: deterministic governance contract
- purpose: 控制 Stage/Phase 边界、GitHub 上传门禁、公开仓库隐私边界和质量优先规则。
- fact_level: EXTRACTED
- evidence: `KMFA/AGENTS.md`, `KMFA/docs/governance/model_registry.yaml`, `KMFA/tools/check_v014_s16_p3_customer_business_analysis.py`, `KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_manifest.json`
- current_v014_scope_lock: `S16-P3 completed; GitHub upload/Stage16 review/protected source matching/lineage full check/formal report/UI runtime/live connector/app reinstall/OpMe/customer contact/collection/legal/invoice/payment/bank/business execution all false`

### FORM-KMFA-V014-S16P3-CUSTOMER-BUSINESS-ANALYSIS-001

- type: deterministic public-safe customer business analysis gate
- purpose: 验证 v0.1.4 S16-P3 客户经营分析证据，覆盖 S16-P2 dependency、S08/S09/S13 public-safe fact manifests、v1.4 taskpack/roadmap requirements、客户价值、项目毛利、回款质量、账龄风险、客户经营摘要、handoff guards、只读 raw/private aggregate alignment 和 no-contact/no-collection/no-legal/no-payment/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s16p3_valid = s16p2_dependency_PASS AND upstream_public_safe_fact_manifests_PASS AND v014_s16p3_validator_PASS AND focused_unit_test_PASS AND source_lane_count == 7 AND customer_value_dimension_count == 4 AND customer_value_signal_count == 4 AND customer_risk_signal_count == 4 AND customer_summary_count == 4 AND handoff_guard_count == 4 AND pending_reconciliation_count == 12 AND raw_private_alignment_readonly == true AND raw_filename_hash_header_value_customer_project_committed == false AND formal_report_count == 0 AND business_decision_basis_count == 0 AND customer_contact_action_count == 0 AND collection_action_count == 0 AND legal_collection_decision_count == 0 AND payment_execution_count == 0 AND bank_operation_count == 0 AND stage16_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s16_p3_customer_business_analysis.py`, `KMFA/tools/check_v014_s16_p3_customer_business_analysis.py`, `KMFA/tests/test_v014_s16_p3_customer_business_analysis.py`, `KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/machine/customer_business_analysis_manifest.json`, `KMFA/stage_artifacts/V014_S16_P3_CUSTOMER_BUSINESS_ANALYSIS/human/customer_business_analysis_report.md`
- limitation: 只证明客户经营分析 public-safe review queue 与人工 handoff guard；不证明 Stage 16 review、GitHub upload、raw value matching、lineage full check、正式报告、客户联络、催收、法务、开票、付款、银行或业务执行。

### FORM-KMFA-V014-S16P2-PROJECT-STATUS-LIFECYCLE-001

- type: deterministic public-safe project status lifecycle gate
- purpose: 验证 v0.1.4 S16-P2 项目状态生命周期证据，覆盖 S16-P1 dependency、legacy S16-P2 public-safe baseline、v1.4 taskpack/roadmap requirements、source lanes、lifecycle records、exception items、handoff guards、只读 raw/private aggregate alignment 和 no-site/no-signature/no-invoice/no-collection/no-payment/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s16p2_valid = s16p1_dependency_PASS AND legacy_s16p2_public_safe_baseline_PASS AND v014_s16p2_validator_PASS AND focused_unit_test_PASS AND source_lane_count == 6 AND lifecycle_record_count == 4 AND exception_item_count == 3 AND handoff_guard_count == 3 AND pending_reconciliation_count == 12 AND raw_private_alignment_readonly == true AND raw_filename_hash_header_value_committed == false AND site_operation_count == 0 AND signature_operation_count == 0 AND invoice_issuance_count == 0 AND collection_action_count == 0 AND formal_report_count == 0 AND business_decision_basis_count == 0 AND s16_p3_performed == false AND stage16_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s16_p2_project_status_lifecycle.py`, `KMFA/tools/check_v014_s16_p2_project_status_lifecycle.py`, `KMFA/tests/test_v014_s16_p2_project_status_lifecycle.py`, `KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE/machine/project_status_lifecycle_manifest.json`, `KMFA/stage_artifacts/V014_S16_P2_PROJECT_STATUS_LIFECYCLE/human/project_status_lifecycle_report.md`
- limitation: 只证明项目状态生命周期 public-safe review queue 与人工 handoff guard；不证明 S16-P3、Stage 16 review、GitHub upload、raw value matching、lineage full check、正式报告、现场施工、安全签字、技术签字、开票、催收、法务、付款、银行或业务执行。

### FORM-KMFA-V014-S16P1-SUBCONTRACT-PROCUREMENT-001

- type: deterministic public-safe subcontract procurement gate
- purpose: 验证 v0.1.4 S16-P1 外协采购归集证据，覆盖 Stage 15 review dependency、legacy S16-P1 public-safe baseline、v1.4 taskpack/roadmap requirements、source lanes、project matches、unallocated cost pool、duplicate payment candidates、cross-project cost candidates 和 no-procurement/no-payment/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s16p1_valid = stage15_review_dependency_PASS AND legacy_s16p1_public_safe_baseline_PASS AND v014_s16p1_validator_PASS AND focused_unit_test_PASS AND source_lane_count == 4 AND project_match_count == 5 AND unallocated_cost_pool_count == 2 AND anomaly_candidate_count == 4 AND duplicate_payment_candidate_count == 2 AND cross_project_cost_candidate_count == 2 AND pending_reconciliation_count == 12 AND procurement_execution_count == 0 AND payment_approval_count == 0 AND payment_execution_count == 0 AND bank_operation_count == 0 AND formal_report_count == 0 AND business_decision_basis_count == 0 AND s16_p2_performed == false AND s16_p3_performed == false AND stage16_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s16_p1_subcontract_procurement.py`, `KMFA/tools/check_v014_s16_p1_subcontract_procurement.py`, `KMFA/tests/test_v014_s16_p1_subcontract_procurement.py`, `KMFA/stage_artifacts/V014_S16_P1_SUBCONTRACT_PROCUREMENT/machine/subcontract_procurement_manifest.json`, `KMFA/stage_artifacts/V014_S16_P1_SUBCONTRACT_PROCUREMENT/human/subcontract_procurement_report.md`
- limitation: 只证明外协/采购/付款归集 public-safe review queue；不证明 S16-P2、S16-P3、Stage 16 review、GitHub upload、raw value matching、lineage full check、正式报告、采购执行、付款审批、付款执行、银行、催收、法务或业务执行。

### FORM-KMFA-V014-S15-STAGE-REVIEW-001

- type: deterministic public-safe Stage 15 review gate
- purpose: 复跑 v0.1.4 S15-P1/S15-P2/S15-P3 validators、legacy Stage 15 review、v1.4 Stage 15 review validator 和 focused unit test，锁定绩效事实字段、复核清单和工资边界均为 public-safe D 级本地证据，并确认 upload/S16/salary/payment/business gates 均未开启。
- fact_level: EXTRACTED
- expression: `s15_review_valid = s15p1_validator_PASS AND s15p2_validator_PASS AND s15p3_validator_PASS AND legacy_s15_review_PASS AND v014_s15_review_validator_PASS AND focused_unit_test_PASS AND phase_results == 3_PASS AND open_findings == 0 AND fixed_findings >= 1 AND performance_fact_row_count == 4 AND abnormal_review_item_count == 16 AND future_salary_system_readiness_row_count == 4 AND pending_review_item_count == 16 AND salary_calculation_count == 0 AND wage_calculation_count == 0 AND bonus_approval_count == 0 AND payroll_export_count == 0 AND final_compensation_decision_count == 0 AND final_payment_count == 0 AND payment_execution_count == 0 AND s16_p1_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s15_stage_review.py`, `KMFA/tools/check_v014_s15_stage_review.py`, `KMFA/tests/test_v014_s15_stage_review.py`, `KMFA/stage_artifacts/V014_S15_STAGE_REVIEW/machine/stage15_review_manifest.json`, `KMFA/stage_artifacts/V014_S15_STAGE_REVIEW/human/stage15_review_report.md`
- limitation: 只证明 Stage 15 public-safe local review closure；不证明 S16-P1、GitHub upload、raw value matching、lineage full check、正式报告、live salary integration、API endpoint、connector、file export、工资计算、奖金审批、薪资导出、最终发放、付款、银行或业务执行。

### FORM-KMFA-V014-S15P3-SALARY-BOUNDARY-001

- type: deterministic public-safe salary boundary gate
- purpose: 验证 v0.1.4 S15-P3 与工资项目边界证据，覆盖 S15-P2 dependency、legacy S15-P3 public-safe baseline、v1.4 taskpack/roadmap requirements、1 个事实输出接口契约、4 条未来工资系统读取草案、人工最终审批/发放边界和 no-live-integration/no-salary/no-payment/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s15p3_valid = s15p2_dependency_PASS AND legacy_s15p3_public_safe_baseline_PASS AND v014_s15p3_validator_PASS AND focused_unit_test_PASS AND fact_output_interface_contract_count == 1 AND future_salary_system_readiness_row_count == 4 AND human_approval_boundary_count == 4 AND pending_review_item_count == 16 AND salary_calculation_count == 0 AND wage_calculation_count == 0 AND bonus_approval_count == 0 AND payroll_export_count == 0 AND final_compensation_decision_count == 0 AND final_payment_count == 0 AND payment_execution_count == 0 AND live_salary_system_integration_allowed == false AND stage15_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s15_p3_salary_boundary.py`, `KMFA/tools/check_v014_s15_p3_salary_boundary.py`, `KMFA/tests/test_v014_s15_p3_salary_boundary.py`, `KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/machine/salary_boundary_manifest.json`, `KMFA/stage_artifacts/V014_S15_P3_SALARY_BOUNDARY/human/salary_boundary_report.md`
- limitation: 只证明绩效事实输出接口契约、未来读取草案和人工最终审批/发放边界；不证明 Stage 15 review、GitHub upload、raw value matching、lineage full check、正式报告、live salary integration、API endpoint、connector、file export、工资计算、奖金审批、薪资导出、最终发放、付款、银行或业务执行。

### FORM-KMFA-V014-S15P2-PERFORMANCE-REVIEW-LIST-001

- type: deterministic public-safe performance review list gate
- purpose: 验证 v0.1.4 S15-P2 绩效复核清单证据，覆盖 S15-P1 dependency、legacy S15-P2 public-safe baseline、v1.4 taskpack/roadmap requirements、4 条绩效事实行、16 条异常/人工复核事项、4 个人工复核字段和 no-salary/no-bonus/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s15p2_valid = s15p1_dependency_PASS AND legacy_s15p2_public_safe_baseline_PASS AND v014_s15p2_validator_PASS AND focused_unit_test_PASS AND performance_fact_row_count == 4 AND abnormal_review_item_count == 16 AND manual_review_field_count == 4 AND salary_calculation_count == 0 AND wage_calculation_count == 0 AND bonus_approval_count == 0 AND payroll_export_count == 0 AND final_compensation_decision_count == 0 AND final_payment_count == 0 AND s15_p3_performed == false AND stage15_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s15_p2_performance_review_list.py`, `KMFA/tools/check_v014_s15_p2_performance_review_list.py`, `KMFA/tests/test_v014_s15_p2_performance_review_list.py`, `KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/machine/performance_review_manifest.json`, `KMFA/stage_artifacts/V014_S15_P2_PERFORMANCE_REVIEW_LIST/human/performance_review_list_report.md`
- limitation: 只证明绩效事实表和异常/人工复核清单的 public-safe evidence；不证明 S15-P3 工资边界、Stage 15 review、GitHub upload、raw value matching、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终发放、付款、银行或业务执行。

### FORM-KMFA-V014-S15P1-PERFORMANCE-FACT-FIELDS-001

- type: deterministic public-safe performance fact field gate
- purpose: 验证 v0.1.4 S15-P1 绩效事实字段证据，覆盖 Stage 14 review dependency、legacy S15-P1 public-safe baseline、v1.4 taskpack/roadmap requirements、6 个绩效事实字段、6 个字段绑定、4 个人工复核字段和 no-review-list/no-salary/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s15p1_valid = stage14_review_dependency_PASS AND legacy_s15p1_public_safe_baseline_PASS AND v014_s15p1_validator_PASS AND focused_unit_test_PASS AND field_definition_count == 6 AND field_binding_count == 6 AND manual_review_field_count == 4 AND performance_fact_table_count == 0 AND abnormal_project_review_list_count == 0 AND salary_calculation_count == 0 AND bonus_approval_count == 0 AND payroll_export_count == 0 AND final_payment_count == 0 AND s15_p2_performed == false AND s15_p3_performed == false AND stage15_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s15_p1_performance_fact_fields.py`, `KMFA/tools/check_v014_s15_p1_performance_fact_fields.py`, `KMFA/tests/test_v014_s15_p1_performance_fact_fields.py`, `KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/machine/performance_fact_fields_manifest.json`, `KMFA/stage_artifacts/V014_S15_P1_PERFORMANCE_FACT_FIELDS/human/performance_fact_fields_report.md`
- limitation: 只证明绩效事实字段定义、字段绑定、source refs/hash refs 和人工复核标记；不证明 S15-P2 复核清单、S15-P3 工资边界、Stage 15 review、GitHub upload、raw value matching、lineage full check、正式报告、工资计算、奖金审批、薪资导出、最终发放、付款、银行或业务执行。

### FORM-KMFA-V014-S14-STAGE-REVIEW-001

- type: deterministic public-safe Stage 14 review gate
- purpose: 复跑 v0.1.4 S14-P1/S14-P2/S14-P3 validators、legacy Stage 14 review、v1.4 Stage 14 review validator 和 focused unit test，锁定资金计划现金贷款、发票税务计划和政策证据计划均为 public-safe D 级本地证据，并确认 upload 继续延期。
- fact_level: EXTRACTED
- expression: `s14_review_valid = s14p1_validator_PASS AND s14p2_validator_PASS AND s14p3_validator_PASS AND legacy_s14_review_PASS AND v014_s14_review_validator_PASS AND focused_unit_test_PASS AND phase_results == 3_PASS AND open_findings == 0 AND fixed_findings == 1 AND pending_reconciliation_count == 12 AND report_grade == D AND formal_report_count == 0 AND business_decision_basis_count == 0 AND payment_or_bank_operation_count == 0 AND loan_management_action_count == 0 AND tax_filing_count == 0 AND invoice_issuance_count == 0 AND policy_application_submission_count == 0 AND subsidy_application_count == 0 AND s15_p1_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s14_stage_review.py`, `KMFA/tools/check_v014_s14_stage_review.py`, `KMFA/tests/test_v014_s14_stage_review.py`, `KMFA/stage_artifacts/V014_S14_STAGE_REVIEW/machine/stage14_review_manifest.json`, `KMFA/stage_artifacts/V014_S14_STAGE_REVIEW/human/stage14_review_report.md`
- limitation: 只证明 Stage 14 public-safe local review closure；不证明 S15-P1、GitHub upload、raw value matching、lineage full check、正式报告、政策资格结论、政策申报、补贴申请、纳税申报、发票开具、付款、银行、贷款管理、工资计算、奖金审批、薪资导出、最终发放或业务执行。

### FORM-KMFA-V014-S14P3-POLICY-EVIDENCE-PLAN-001

- type: deterministic public-safe policy evidence plan gate
- purpose: 验证 v0.1.4 S14-P3 政策证据计划证据，覆盖 S14-P2 dependency、legacy S14-P3 public-safe artifacts、v1.4 taskpack/roadmap/HTML baseline、5 类政策证据目录、5 条证据缺口、5 条风险提示、1 个 HTML overview 和 no-review/no-upload/no-policy-conclusion-or-submission 边界。
- fact_level: EXTRACTED
- expression: `s14p3_valid = s14p2_dependency_PASS AND legacy_s14p3_validator_PASS AND v014_s14p3_validator_PASS AND focused_unit_test_PASS AND policy_program_count == 5 AND evidence_directory_count == 5 AND evidence_gap_count == 5 AND risk_tip_count == 5 AND html_output_count == 1 AND pending_reconciliation_count == 12 AND report_grade == D AND formal_policy_conclusion_count == 0 AND policy_application_submission_count == 0 AND subsidy_application_count == 0 AND external_connector_action_count == 0 AND stage14_review_performed == false AND github_upload_performed == false AND raw_inbox_read_by_this_phase == false`
- evidence: `KMFA/tools/v014_s14_p3_policy_evidence_plan.py`, `KMFA/tools/check_v014_s14_p3_policy_evidence_plan.py`, `KMFA/tests/test_v014_s14_p3_policy_evidence_plan.py`, `KMFA/stage_artifacts/V014_S14_P3_POLICY_EVIDENCE_PLAN/machine/policy_evidence_plan_manifest.json`, `KMFA/stage_artifacts/V014_S14_P3_POLICY_EVIDENCE_PLAN/human/policy_evidence_plan_report.md`
- limitation: 只证明 S14-P3 public-safe 政策证据目录、证据缺口和风险提示；不证明 Stage 14 review、raw value matching、lineage full check、正式报告、政策资格结论、政策申报、补贴申请、纳税申报、发票开具、付款、银行、贷款管理、GitHub upload、live connector 或业务执行。

### FORM-KMFA-V014-S14P2-INVOICE-TAX-PLAN-001

- type: deterministic public-safe invoice tax plan gate
- purpose: 验证 v0.1.4 S14-P2 发票税务计划证据，覆盖 S14-P1 dependency、legacy S14-P2 public-safe artifacts、v1.4 human-flow HTML/UIUX baseline、3 条 source lanes、3 类候选事项、3 条资金汇总状态、1 个 HTML overview 和 no-review/no-upload/no-tax-or-invoice-operation 边界。
- fact_level: EXTRACTED
- expression: `s14p2_valid = s14p1_dependency_PASS AND legacy_s14p2_validator_PASS AND source_lane_count == 3 AND source_count == 6 AND field_mapping_count == 30 AND issue_candidate_count == 3 AND cash_summary_count == 3 AND html_output_count == 1 AND pending_reconciliation_count == 12 AND report_grade == D AND invoice_issuance_count == 0 AND tax_filing_count == 0 AND payment_or_bank_operation_count == 0 AND external_connector_action_count == 0 AND s14_p3_performed == false AND stage14_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s14_p2_invoice_tax_plan.py`, `KMFA/tools/check_v014_s14_p2_invoice_tax_plan.py`, `KMFA/tests/test_v014_s14_p2_invoice_tax_plan.py`, `KMFA/stage_artifacts/V014_S14_P2_INVOICE_TAX_PLAN/machine/invoice_tax_plan_manifest.json`, `KMFA/stage_artifacts/V014_S14_P2_INVOICE_TAX_PLAN/human/invoice_tax_plan_report.md`
- limitation: 只证明 S14-P2 public-safe 开票纳税候选和资金汇总状态；不证明 S14-P3、Stage 14 review、raw value matching、lineage full check、正式报告、纳税申报、发票开具、付款、银行、贷款管理、政策申报、补贴申报、GitHub upload、live connector 或业务执行。

### FORM-KMFA-V014-S13P3-CROSS-TABLE-REVIEW-001

- type: deterministic public-safe cross-table review gate
- purpose: 验证 v0.1.4 S13-P3 跨表复核证据，覆盖 S13-P1/S13-P2 dependencies、legacy S13-P3 public-safe artifacts、v1.4 human-flow HTML/UIUX baseline、4 个复核维度、4 条差异队列、1 份质量报告、1 个 HTML draft 和 no-review/no-upload/no-auto-resolution 边界。
- fact_level: EXTRACTED
- expression: `s13p3_valid = s13p1_dependency_PASS AND s13p2_dependency_PASS AND legacy_s13p3_validator_PASS AND review_dimension_count == 4 AND difference_queue_count == 4 AND quality_report_count == 1 AND html_draft_count == 1 AND pending_reconciliation_count == 12 AND report_grade == D AND formal_report_count == 0 AND business_decision_basis_count == 0 AND difference_auto_resolution_count == 0 AND difference_closure_count == 0 AND stage13_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s13_p3_cross_table_review.py`, `KMFA/tools/check_v014_s13_p3_cross_table_review.py`, `KMFA/tests/test_v014_s13_p3_cross_table_review.py`, `KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/machine/cross_table_review_manifest.json`, `KMFA/stage_artifacts/V014_S13_P3_CROSS_TABLE_REVIEW/human/cross_table_review_report.md`
- limitation: 只证明 S13-P3 public-safe 跨表一致性检查、差异队列和质量报告；不证明 Stage 13 review、S14、raw value matching、lineage full check、正式报告、差异关闭、催收、法务、付款、开票、税务、GitHub upload、live connector 或业务执行。

### FORM-KMFA-V014-S13P2-COLLECTION-RECEIVABLE-AGING-001

- type: deterministic public-safe collection receivable aging gate
- purpose: 验证 v0.1.4 S13-P2 回款应收账龄证据，覆盖 S13-P1 dependency、legacy S13-P2 public-safe artifacts、v1.4 human-flow HTML/UIUX baseline、5 条 source lanes、4 类问题、4 条优先级草案、4 条责任事项草案、1 个 HTML draft 和 no-review/no-upload/no-external-action 边界。
- fact_level: EXTRACTED
- expression: `s13p2_valid = s13p1_dependency_PASS AND legacy_s13p2_validator_PASS AND source_lane_count == 5 AND source_count == 5 AND field_mapping_count == 25 AND required_issue_type_count == 4 AND priority_item_count == 4 AND responsibility_item_count == 4 AND html_draft_count == 1 AND pending_reconciliation_count == 12 AND report_grade == D AND formal_report_count == 0 AND business_decision_basis_count == 0 AND legal_collection_decision_count == 0 AND payment_or_bank_operation_count == 0 AND s13_p3_performed == false AND stage13_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s13_p2_collection_receivable_aging.py`, `KMFA/tools/check_v014_s13_p2_collection_receivable_aging.py`, `KMFA/tests/test_v014_s13_p2_collection_receivable_aging.py`, `KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/machine/collection_receivable_aging_manifest.json`, `KMFA/stage_artifacts/V014_S13_P2_COLLECTION_RECEIVABLE_AGING/human/collection_receivable_aging_report.md`
- limitation: 只证明 S13-P2 public-safe 回款优先级和责任事项草案；不证明 S13-P3、Stage 13 review、raw value matching、lineage full check、正式报告、催收、法务、付款、开票、税务、GitHub upload、live connector 或业务执行。

### FORM-KMFA-V014-S10-STAGE-REVIEW-001

- type: deterministic public-safe Stage 10 review gate
- purpose: 复跑 v0.1.4 S10-P1/S10-P2/S10-P3 validators、legacy Stage 10 review 和 v0.1.3 Stage 10 review，锁定 open findings 为 0、修复 findings 为 2、报告层输出仍为 D 级 NO_GO，并确认 upload/S11/raw/formal/business gates 均未开启。
- fact_level: EXTRACTED
- expression: `s10_stage_review_valid = s10p1_validator_PASS AND s10p2_validator_PASS AND s10p3_validator_PASS AND legacy_stage10_review_PASS AND v013_stage10_review_PASS AND phase_pass_count == 3 AND open_review_finding_count == 0 AND fixed_review_finding_count == 2 AND report_template_count == 2 AND report_grade_record_count == 2 AND report_export_record_count == 2 AND pending_reconciliation_count == 12 AND confirmed_resolution_count == 0 AND formal_report_count == 0 AND business_decision_basis_count == 0 AND current_report_grade == D AND s11_p1_performed == false AND github_upload_performed == false AND raw_inbox_read_by_this_review == false`
- evidence: `KMFA/tools/v014_s10_stage_review.py`, `KMFA/tools/check_v014_s10_stage_review.py`, `KMFA/tests/test_v014_s10_stage_review.py`, `KMFA/stage_artifacts/V014_S10_STAGE_REVIEW/machine/stage10_review_manifest.json`, `KMFA/stage_artifacts/V014_S10_STAGE_REVIEW/human/stage10_review_report.md`
- limitation: 只证明 Stage 10 public-safe local review closure；不证明 S11、raw value matching、lineage full check、正式报告、UI runtime、GitHub upload、live connector 或业务执行。

### FORM-KMFA-V014-S10P1-REPORT-TEMPLATES-001

- type: deterministic public-safe report template gate
- purpose: 验证 v0.1.4 S10-P1 报告模板结构，覆盖 Stage 9 review dependency、legacy S10-P1 public-safe artifacts、v1.4 human-flow HTML/UIUX baseline、两个模板、十一章结构和 no-export/no-formal-report/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s10p1_valid = template_count == 2 AND section_count == 11 AND project_cost_section_count == 4 AND business_overview_section_count == 7 AND pending_reconciliation_count == 12 AND formal_report_count == 0 AND export_artifact_count == 0 AND s10_p2_performed == false AND s10_p3_performed == false AND stage10_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s10_p1_report_templates.py`, `KMFA/tools/check_v014_s10_p1_report_templates.py`, `KMFA/tests/test_v014_s10_p1_report_templates.py`, `KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/machine/report_templates_manifest.json`, `KMFA/stage_artifacts/V014_S10_P1_REPORT_TEMPLATES/human/report_templates_report.md`
- limitation: 只证明 public-safe 报告模板结构和 v1.4 HTML/UIUX baseline 对齐；不证明 S10-P2 报告可信等级、S10-P3 导出、Stage 10 review、raw value matching、lineage full check、正式报告、UI runtime、GitHub upload 或业务执行。

### FORM-KMFA-V014-S10P2-REPORT-TRUST-GRADE-001

- type: deterministic public-safe report trust grade gate
- purpose: 验证 v0.1.4 S10-P2 报告可信等级，覆盖 S10-P1 dependency、legacy S10-P2 runtime、v0.1.3 S10-P2 replay、A/B/C/D 等级驱动、版本绑定和 no-export/no-formal-report/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s10p2_valid = report_grade_record_count == 2 AND grade_distribution == D:2 AND pending_reconciliation_count == 12 AND confirmed_resolution_count == 0 AND source_quality_grade == Q4 AND zero_delta_passed == false AND record_version_binding_count == 2 AND formal_report_count == 0 AND export_artifact_count == 0 AND s10_p3_performed == false AND stage10_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s10_p2_report_trust_grade.py`, `KMFA/tools/check_v014_s10_p2_report_trust_grade.py`, `KMFA/tests/test_v014_s10_p2_report_trust_grade.py`, `KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/machine/report_trust_grade_manifest.json`, `KMFA/stage_artifacts/V014_S10_P2_REPORT_TRUST_GRADE/human/report_trust_grade_report.md`
- limitation: 只证明 public-safe 报告可信等级运行时和版本绑定；不证明 S10-P3 导出、Stage 10 review、raw value matching、lineage full check、正式报告、UI runtime、GitHub upload 或业务执行。

### FORM-KMFA-V014-S10P3-REPORT-EXPORT-001

- type: deterministic public-safe report export gate
- purpose: 验证 v0.1.4 S10-P3 报告导出，覆盖 S10-P2 dependency、legacy S10-P3 runtime、v0.1.3 S10-P3 replay、HTML/CSV/Excel-compatible CSV 导出证据、PDF private-runtime-only policy 和 no-formal-report/no-upload 边界。
- fact_level: EXTRACTED
- expression: `s10p3_valid = report_export_record_count == 2 AND html_export_count == 2 AND csv_appendix_count == 2 AND excel_compatible_download_count == 2 AND committed_pdf_file_count == 0 AND committed_excel_file_count == 0 AND formal_report_count == 0 AND business_decision_basis_count == 0 AND pending_reconciliation_count == 12 AND grade_distribution == D:2 AND stage10_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s10_p3_report_export.py`, `KMFA/tools/check_v014_s10_p3_report_export.py`, `KMFA/tests/test_v014_s10_p3_report_export.py`, `KMFA/stage_artifacts/V014_S10_P3_REPORT_EXPORT/machine/report_export_manifest.json`, `KMFA/stage_artifacts/V014_S10_P3_REPORT_EXPORT/human/report_export_report.md`
- limitation: 只证明 public-safe 报告导出证据和导出边界；不证明 Stage 10 review、raw value matching、lineage full check、正式报告、UI runtime、GitHub upload 或业务执行。

### MOD-KMFA-METADATA-001

- type: deterministic metadata governance contract
- purpose: 定义 metadata 七类目录、核心标识符、公开仓库隐私边界和协议检查。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/METADATA_PROTOCOL.md`, `KMFA/metadata/protocol/metadata_protocol.yaml`, `KMFA/tools/metadata_protocol_check.py`

### MOD-KMFA-IMMUTABILITY-001

- type: deterministic immutability contract
- purpose: 定义 raw manifest 不可变字段、派生数据版本化、前端/人工控制事件写入边界，防止原始数据污染。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/IMMUTABILITY_POLICY.md`, `KMFA/metadata/imports/raw_manifest_policy.yaml`, `KMFA/metadata/protocol/immutability_policy_lock_v1_4.json`, `KMFA/tools/immutability_policy_check.py`, `KMFA/tools/check_v014_s02_p2_immutability_policy.py`
- current_v014_scope_lock: `S02-P2 completed; raw inventory/S02-P3/Stage 2 review/GitHub upload/raw value matching/formal report/live connector/business execution all false`

### MOD-KMFA-QUALITY-GATE-001

- type: deterministic quality gate contract
- purpose: 定义 Q0-Q5 数据质量等级、A/B/C/D 报告可信等级和报告发布权限门禁。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/QUALITY_GATE_POLICY.md`, `KMFA/metadata/reports/report_release_gate.yaml`, `KMFA/metadata/protocol/quality_gate_lock_v1_4.json`, `KMFA/tools/check_report_grade_gate.py`, `KMFA/tools/check_v014_s02_p3_quality_gate.py`
- current_v014_scope_lock: `S02-P3 completed; Stage 2 review/GitHub upload/raw inventory/raw value matching/formal report/live connector/business execution all false`

### MOD-KMFA-FILE-IMPORT-001

- type: deterministic file metadata registration
- purpose: 对授权本地文件生成 hash、大小、导入批次、来源包记录、私有 storage ref 和操作提示，并安全解包 zip。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/file_import_register.py`, `KMFA/tools/v014_s03_p1_raw_file_registration.py`, `KMFA/tools/check_v014_s03_p1_file_registration.py`, `KMFA/metadata/imports/file_import_policy.yaml`, `KMFA/metadata/imports/v014_s03_p1_public_raw_file_register.json`, `KMFA/stage_artifacts/V014_S03_P1_FILE_REGISTRATION/machine/s03_p1_file_registration_manifest.json`, `KMFA/stage_artifacts/S03_P1_file_import/human/s03_p1_completion_record.md`
- limitation: S03-P1 只允许 raw root read-only list/stat/read/hash；raw 明细和内容 hash 仅留在 git-ignored private runtime，公开仓库只登记 public-safe metadata，不解析业务字段，不保存原始文件 bytes，不提交原始文件。

### MOD-KMFA-SOURCE-CHECK-001

- type: deterministic source readiness matrix
- purpose: 按来源系统、业务板块、文件包、主体、账户、频率生成检查矩阵，并以 metadata event 追加状态变化。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/source_check_matrix.py`, `KMFA/tools/v014_s03_p2_source_check_matrix.py`, `KMFA/tools/check_v014_s03_p2_source_check_matrix.py`, `KMFA/metadata/protocol/source_check_matrix_v1_4_s03_p2.json`, `KMFA/metadata/sources/v014_s03_p2_source_check_matrix.jsonl`, `KMFA/metadata/sources/v014_s03_p2_source_status_events.jsonl`, `KMFA/stage_artifacts/V014_S03_P2_SOURCE_CHECK_MATRIX/machine/source_check_matrix_manifest.json`, `KMFA/stage_artifacts/S03_P2_source_check_matrix/human/s03_p2_completion_record.md`
- limitation: S03-P2 只基于 S03-P1 public register 生成 public-safe matrix/status events，不读取 raw root，不做 owner mapping/source priority、自动选边、业务字段解析或 UI 检查板。

### MOD-KMFA-SOURCE-PRIORITY-001

- type: deterministic source priority contract
- purpose: 固化原始上传/授权导出优先于处理后数据；同源不一致失效缓存并请求重跑；跨源冲突进入人工差异队列。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/source_priority.py`, `KMFA/tools/v014_s03_p3_source_priority.py`, `KMFA/tools/check_v014_s03_p3_source_priority.py`, `KMFA/metadata/sources/source_priority_policy.yaml`, `KMFA/metadata/protocol/source_priority_v1_4_s03_p3.json`, `KMFA/metadata/sources/v014_s03_p3_source_priority_records.jsonl`, `KMFA/metadata/sources/v014_s03_p3_same_source_rerun_events.jsonl`, `KMFA/metadata/quality/v014_s03_p3_cross_source_difference_queue.jsonl`, `KMFA/stage_artifacts/V014_S03_P3_SOURCE_PRIORITY/machine/source_priority_manifest.json`, `KMFA/stage_artifacts/S03_P3_source_priority/human/s03_p3_completion_record.md`
- limitation: S03-P3 只使用 S03-P2 public matrix/status events，不读取 raw root，不解析金额，不读取真实业务源值，不自动选择跨源冲突一边，不执行 Stage 3 review 或 GitHub upload。

### FORM-KMFA-V014-S03-STAGE-REVIEW-001

- type: deterministic public-safe Stage 3 review gate
- purpose: 复跑 S03-P1/S03-P2/S03-P3 validators，锁定 Stage 3 本地整体复审证据，确认 open findings 为 0 且 GitHub upload 延后到 v1.4 Stage 1-18 完整复审后。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/check_v014_s03_stage_review.py`, `KMFA/tests/test_v014_s03_stage_review.py`, `KMFA/stage_artifacts/V014_S03_STAGE_REVIEW/human/stage3_review_report.md`, `KMFA/stage_artifacts/V014_S03_STAGE_REVIEW/machine/stage3_review_manifest.json`
- limitation: 只证明 Stage 3 public-safe local review closure；不读取 raw inbox，不发布 raw/private 明细，不执行 S04、GitHub upload、raw value matching、field mapping、lineage full check、formal report 或 business execution。

### FORM-KMFA-V014-S04P1-AMOUNT-PRECISION-001

- type: deterministic amount precision validation gate
- purpose: 复用金额标准化和 no-float 工具，锁定 v0.1.4 S04-P1 public-safe synthetic amount precision evidence。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/v014_s04_p1_amount_precision.py`, `KMFA/tools/check_v014_s04_p1_amount_precision.py`, `KMFA/tests/test_v014_s04_p1_amount_precision.py`, `KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/human/test_results.md`
- limitation: 只证明整数分金额标准化、异常拒绝和 no-float 基础工具边界；不做 S04-P2 字段标准化、raw value matching、zero-delta、事实层或报告验收。

### FORM-KMFA-V014-S04P2-FIELD-STANDARDIZATION-001

- type: deterministic public-safe field standardization gate
- purpose: 验证 v0.1.4 S04-P2 字段标准化，覆盖 canonical 字段、别名字典聚合计数、字段映射记录、缺失/异常字段质量状态、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s04p2_valid = canonical_field_count == 6 AND alias_dictionary_row_count == 32 AND mapping_record_count == 6 AND standardization_case_passed_count == 6 AND quality_status_count == 5 AND raw_dir_read_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/check_v014_s04_p2_field_standardization.py`, `KMFA/stage_artifacts/V014_S04_P2_FIELD_STANDARDIZATION/machine/field_standardization_manifest.json`
- limitation: S04-P2 只证明字段标准化和质量状态边界，不证明 raw value matching、S04-P3、Stage 4 review、正式报告或 GitHub upload readiness。

### FORM-KMFA-V014-S04P3-BASIC-TOOL-REPORT-001

- type: deterministic public-safe basic tool report gate
- purpose: 验证 v0.1.4 S04-P3 基础工具测试，覆盖金额小数、负数、万元、异常字符、中文日期、年月、空值、JSON/Markdown 工具报告、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s04p3_valid = synthetic_boundary_case_total == 22 AND synthetic_boundary_case_passed == 22 AND amount_boundary_case_count == 11 AND date_period_boundary_case_count == 11 AND json_report_generated == true AND markdown_report_generated == true AND raw_dir_read_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/check_v014_s04_p3_basic_tool_report.py`, `KMFA/stage_artifacts/V014_S04_P3_BASIC_TOOL_REPORT/machine/basic_tool_report_manifest.json`
- limitation: S04-P3 只证明基础工具 synthetic boundary 测试和工具报告生成；不证明 Stage 4 review、raw value matching、正式报告或 GitHub upload readiness。

### FORM-KMFA-V014-S04-STAGE-REVIEW-001

- type: deterministic public-safe Stage 4 review gate
- purpose: 复跑 S04-P1/S04-P2/S04-P3 validators，锁定 Stage 4 本地整体复审证据，确认 open findings 为 0 且 GitHub upload 延后到 v1.4 Stage 1-18 完整复审后。
- fact_level: EXTRACTED
- expression: `s04_stage_review_valid = phase_results == PASS/PASS/PASS AND open_review_finding_count == 0 AND raw_inbox_read_by_this_review == false AND github_upload_performed == false AND s05_p1_started == false AND current_go_no_go == NO_GO`
- evidence: `KMFA/tools/v014_s04_stage_review.py`, `KMFA/tools/check_v014_s04_stage_review.py`, `KMFA/stage_artifacts/V014_S04_STAGE_REVIEW/machine/stage4_review_manifest.json`
- limitation: 只证明 Stage 4 public-safe local review closure；不读取 raw inbox，不发布 raw/private 明细，不执行 GitHub upload、S05、raw value matching、lineage full check、formal report 或 business execution。

### FORM-KMFA-V014-S05P1-A0-FILE-REGISTRATION-001

- type: deterministic public-safe A0 file registration gate
- purpose: 验证 v0.1.4 S05-P1 A0 文件登记，覆盖 A0 文件聚合计数、Q3 candidate 计数、private diagnostic 放置、public raw hash/member name 不提交、raw inbox 只读授权操作和 upload-deferred NO_GO 边界。
- fact_level: EXTRACTED
- expression: `s05p1_valid = total_files == 9 AND pdf_files == 8 AND excel_files == 1 AND private_business_member_hash_record_count == 9 AND public_actual_raw_member_hash_committed_count == 0 AND q3_machine_candidate_count == 9 AND q4_human_locked_count == 0 AND raw_inbox_hashed_by_this_phase == true AND raw_inbox_mutated_by_this_phase == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s05_p1_a0_file_registration.py`, `KMFA/tools/check_v014_s05_p1_a0_file_registration.py`, `KMFA/stage_artifacts/V014_S05_P1_A0_FILE_REGISTRATION/machine/a0_file_registration_manifest.json`
- limitation: S05-P1 只证明文件登记和 private diagnostic 边界；不证明字段级 golden baseline、权威基准锁定、raw value matching、zero-delta、正式报告或 GitHub upload readiness。

### FORM-KMFA-V014-S05P2-FIELD-GOLDEN-BASELINE-001

- type: deterministic public-safe field golden baseline candidate gate
- purpose: 验证 v0.1.4 S05-P2 字段级黄金基准，覆盖 field contracts、field candidates、PDF private-only anchor/hash status、Excel owner/授权降级、Q3/Q4/Q5 状态、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s05p2_valid = field_contract_count == 5 AND field_candidate_count == 45 AND pdf_field_candidate_count == 40 AND excel_field_candidate_count == 5 AND source_anchor_recorded_private_only_count == 40 AND owner_downgraded_excel_field_count == 5 AND q4_human_confirmed_count == 0 AND q5_calculation_baseline_allowed_count == 0 AND raw_inbox_read_by_this_phase == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s05_p2_field_golden_baseline.py`, `KMFA/tools/check_v014_s05_p2_field_golden_baseline.py`, `KMFA/stage_artifacts/V014_S05_P2_FIELD_GOLDEN_BASELINE/machine/field_golden_baseline_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S05_P2_FIELD_GOLDEN_BASELINE/human/test_results.md`
- limitation: S05-P2 只证明字段级 public-safe candidate baseline 和 active owner/授权降级边界；不证明 S05-P3 权威基准锁定、Stage 5 review、raw value matching、zero-delta、正式报告或 GitHub upload readiness。

### FORM-KMFA-V014-S05P3-AUTHORITY-BASELINE-LOCK-001

- type: deterministic public-safe authority baseline lock gate
- purpose: 验证 v0.1.4 S05-P3 权威基准锁定，覆盖 authority records、Q5 calculation-baseline lock、Excel cross-source support only exclusion、Q4 human-confirmed release state、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s05p3_valid = authority_record_count == 45 AND q5_calculation_baseline_locked_count == 40 AND excluded_cross_source_support_only_count == 5 AND q4_human_confirmed_count == 40 AND q5_full_quality_grade_allowed_count == 0 AND formal_report_allowed_count == 0 AND zero_delta_validated_count == 0 AND lineage_full_check_completed_count == 0 AND raw_inbox_read_by_this_phase == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s05_p3_authority_baseline_lock.py`, `KMFA/tools/check_v014_s05_p3_authority_baseline_lock.py`, `KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/machine/authority_baseline_lock_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S05_P3_AUTHORITY_BASELINE_LOCK/human/test_results.md`
- limitation: S05-P3 只证明 public-safe authority baseline lock 和 Q5 calculation-baseline readiness；不证明 Stage 5 review、raw value matching、zero-delta、lineage full check、正式报告或 GitHub upload readiness。

### FORM-KMFA-V014-S05-STAGE-REVIEW-001

- type: deterministic public-safe Stage 5 review gate
- purpose: 复跑 S05-P1/S05-P2/S05-P3 validators，锁定 Stage 5 本地整体复审证据，确认 open findings 为 0 且 GitHub upload 延后到 v1.4 Stage 1-18 完整复审后。
- fact_level: EXTRACTED
- expression: `s05_stage_review_valid = S05-P1 PASS AND S05-P2 PASS AND S05-P3 PASS AND open_review_finding_count == 0 AND raw_inbox_read_by_this_review == false AND github_upload_performed == false AND s06_p1_started == false AND current_go_no_go == NO_GO`
- evidence: `KMFA/tools/v014_s05_stage_review.py`, `KMFA/tools/check_v014_s05_stage_review.py`, `KMFA/stage_artifacts/V014_S05_STAGE_REVIEW/machine/stage5_review_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S05_STAGE_REVIEW/human/test_results.md`
- limitation: Stage 5 review 只证明 S05 public-safe local review closure；不证明 GitHub upload、S06-P1、raw value matching、zero-delta validation、lineage full check、正式报告或 business execution。

### FORM-KMFA-V014-S06P1-ZERO-DELTA-VALIDATOR-001

- type: deterministic public-safe zero-delta validator gate
- purpose: 验证 v0.1.4 S06-P1 zero-delta validator，覆盖 Stage 5 review dependency、整数分字段级 pass fixture、1 cent mismatch failure、mismatch report schema、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s06p1_valid = s05_stage_review_dependency == PASS AND pass_fixture_field_comparison_count == 8 AND pass_fixture_mismatch_count == 0 AND one_cent_mismatch_detected == true AND mismatch_report_generated == true AND difference_queue_created == false AND metadata_quality_written == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s06_p1_zero_delta_validator.py`, `KMFA/tools/check_v014_s06_p1_zero_delta_validator.py`, `KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/machine/zero_delta_validator_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S06_P1_ZERO_DELTA_VALIDATOR/human/test_results.md`
- limitation: S06-P1 只证明 public-safe validator 行为；不创建 S06-P2 差异队列，不写 S06-P3 metadata quality，不执行 Stage 6 review、GitHub upload、actual business zero-delta、raw value matching、lineage full check、正式报告或 business execution。

### FORM-KMFA-V014-S06P2-DIFFERENCE-QUEUE-001

- type: deterministic public-safe cross-source difference queue gate
- purpose: 验证 v0.1.4 S06-P2 difference queue，覆盖 S06-P1 dependency、PDF/Excel 同项目同字段 1 cent conflict、人工队列、禁止自动处理、未关闭差异阻断 A 级报告、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s06p2_valid = s06_p1_dependency == PASS AND pdf_excel_conflict_detected == true AND queue_item_count == 1 AND difference_cents == 1 AND auto_correction_allowed == false AND averaging_allowed == false AND rounding_mask_allowed == false AND auto_selection_allowed == false AND report_grade_a_allowed == false AND metadata_quality_written == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s06_p2_difference_queue.py`, `KMFA/tools/check_v014_s06_p2_difference_queue.py`, `KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE/machine/difference_queue_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S06_P2_DIFFERENCE_QUEUE/human/test_results.md`
- limitation: S06-P2 只证明 public-safe unresolved difference queue 行为；不写 S06-P3 metadata quality，不关闭差异，不执行 Stage 6 review、GitHub upload、actual business raw value matching、lineage full check、正式报告或 business execution。

### FORM-KMFA-V014-S06P3-VALIDATION-EVIDENCE-001

- type: deterministic public-safe validation evidence gate
- purpose: 验证 v0.1.4 S06-P3 validation evidence，覆盖 S06-P1/S06-P2 dependencies、sanitized evidence output、metadata/quality 写入、Q5/A 级报告阻断、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s06p3_valid = s06_p1_dependency == PASS AND s06_p2_dependency == PASS AND metadata_quality_written == true AND project_status_count == 2 AND blocked_project_status_count == 2 AND q5_allowed_count == 0 AND report_grade_a_allowed_count == 0 AND stage6_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s06_p3_validation_evidence.py`, `KMFA/tools/check_v014_s06_p3_validation_evidence.py`, `KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE/machine/validation_evidence_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S06_P3_VALIDATION_EVIDENCE/human/test_results.md`
- limitation: S06-P3 只证明 public-safe validation evidence 和 metadata/quality 写入；不关闭差异，不执行 Stage 6 review、GitHub upload、actual business raw value matching、lineage full check、正式报告或 business execution。

### FORM-KMFA-V014-S06-STAGE-REVIEW-001

- type: deterministic public-safe Stage 6 review gate
- purpose: 复跑 S06-P1/S06-P2/S06-P3 validators，锁定 Stage 6 本地整体复审证据，确认 open findings 为 0 且 GitHub upload 延后到 v1.4 Stage 1-18 完整复审后。
- fact_level: EXTRACTED
- expression: `s06_stage_review_valid = S06-P1 PASS AND S06-P2 PASS AND S06-P3 PASS AND open_review_finding_count == 0 AND queue_item_count == 1 AND blocked_project_status_count == 2 AND q5_allowed_count == 0 AND report_grade_a_allowed_count == 0 AND raw_inbox_read_by_this_review == false AND github_upload_performed == false AND s07_p1_started == false AND current_go_no_go == NO_GO`
- evidence: `KMFA/tools/v014_s06_stage_review.py`, `KMFA/tools/check_v014_s06_stage_review.py`, `KMFA/stage_artifacts/V014_S06_STAGE_REVIEW/machine/stage6_review_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S06_STAGE_REVIEW/human/test_results.md`
- limitation: Stage 6 review 只证明 S06 public-safe local review closure；不证明 GitHub upload、S07-P1、difference closure、raw value matching、lineage full check、正式报告或 business execution。

### FORM-KMFA-V014-S07P1-FINANCE-FILE-ADAPTER-001

- type: deterministic public-safe finance file adapter gate
- purpose: 复用 public-safe finance adapter baseline，锁定 v0.1.4 S07-P1 财务支撑源登记、字段候选映射、只读字段报告、质量边界和 no-upload/no-review scope gate。
- fact_level: EXTRACTED
- expression: `s07p1_valid = S06 stage review PASS AND legacy finance adapter PASS AND source_category_count == 9 AND source_registry_count == 9 AND field_candidate_count == 45 AND hash_only_field_candidate_count == 45 AND readonly_field_report_count == 9 AND q5_allowed_count == 0 AND formal_report_allowed_count == 0 AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s07_p1_finance_file_adapter.py`, `KMFA/tools/check_v014_s07_p1_finance_file_adapter.py`, `KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/machine/finance_file_adapter_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S07_P1_FINANCE_FILE_ADAPTER/human/test_results.md`
- limitation: S07-P1 只证明 public-safe local finance file adapter evidence；不证明 S07-P2、S07-P3、Stage 7 review、raw value matching、lineage full check、正式报告、GitHub upload、delivery readiness 或 business execution。

### FORM-KMFA-V014-S07P2-WPS-FILE-ADAPTER-001

- type: deterministic public-safe WPS file adapter gate
- purpose: 复用 public-safe WPS adapter baseline，锁定 v0.1.4 S07-P2 WPS 导出源登记、hash-only 字段映射、转换提示、只读字段报告、映射规则版本、质量边界和 no-upload/no-review scope gate。
- fact_level: EXTRACTED
- expression: `s07p2_valid = S06 stage review PASS AND S07-P1 PASS AND legacy WPS adapter PASS AND source_export_type_count == 4 AND source_registry_count == 4 AND field_mapping_count == 20 AND hash_only_field_mapping_count == 20 AND conversion_guidance_count == 4 AND readonly_field_report_count == 4 AND mapping_rule_version_count == 1 AND q5_allowed_count == 0 AND formal_report_allowed_count == 0 AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s07_p2_wps_file_adapter.py`, `KMFA/tools/check_v014_s07_p2_wps_file_adapter.py`, `KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/machine/wps_file_adapter_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S07_P2_WPS_FILE_ADAPTER/human/test_results.md`
- limitation: S07-P2 只证明 public-safe local WPS file adapter evidence；不证明 S07-P3、Stage 7 review、raw value matching、lineage full check、正式报告、GitHub upload、delivery readiness 或 business execution。

### FORM-KMFA-V014-S07P3-REDCIRCLE-POSTPONEMENT-001

- type: deterministic public-safe Redcircle postponement gate
- purpose: 复用 public-safe Redcircle postponement baseline，锁定 v0.1.4 S07-P3 红圈预留导出模板、source registry、connector postponement policy、future rollback plan、质量边界和 no-upload/no-review scope gate。
- fact_level: EXTRACTED
- expression: `s07p3_valid = S06 stage review PASS AND S07-P1 PASS AND S07-P2 PASS AND legacy Redcircle postponement PASS AND redcircle_export_type_count == 4 AND reserved_template_count == 4 AND registry_source_count == 4 AND rollback_plan_count == 4 AND connector_policy_count == 1 AND d15_automatic_connector_allowed == false AND read_only_required_count == 4 AND hash_retention_required_count == 4 AND rollback_plan_required_count == 4 AND manual_approval_required_count == 4 AND q5_allowed_count == 0 AND formal_report_allowed_count == 0 AND stage7_review_performed == false AND s08_p1_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s07_p3_redcircle_postponement.py`, `KMFA/tools/check_v014_s07_p3_redcircle_postponement.py`, `KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/machine/redcircle_postponement_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S07_P3_REDCIRCLE_POSTPONEMENT_POLICY/human/test_results.md`
- limitation: S07-P3 只证明 public-safe local Redcircle postponement evidence；不证明 Stage 7 review、S08-P1、raw value matching、lineage full check、正式报告、GitHub upload、delivery readiness 或 business execution。

### FORM-KMFA-V014-S08P1-PROJECT-COMPOSITE-KEY-001

- type: deterministic public-safe project identity matching gate
- purpose: 验证 v0.1.4 S08-P1 项目组合键，覆盖 Stage 7 review dependency、legacy public-safe S08-P1 dependency、8 个 hash-only 组件、4 个 profiles、3 个 match results、2 条 manual review queue、权重阈值、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s08p1_valid = stage7_review_dependency == PASS AND legacy_s08_p1_dependency == PASS AND required_component_count == 8 AND profile_count == 4 AND match_result_count == 3 AND manual_review_queue_count == 2 AND strong_auto_match_count == 1 AND matching_weights_sum_bps == 10000 AND strong_threshold_bps == 8500 AND human_review_threshold_bps == 7000 AND weak_candidate_threshold_bps == 5000 AND missing_single_component_blocks_all_matching == false AND below_strong_threshold_enters_manual_review == true AND auto_merge_allowed_for_review_queue_count == 0 AND raw_inbox_read_by_this_phase == false AND s08_p2_performed == false AND s08_p3_performed == false AND stage8_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s08_p1_project_composite_key.py`, `KMFA/tools/check_v014_s08_p1_project_composite_key.py`, `KMFA/stage_artifacts/V014_S08_P1_PROJECT_COMPOSITE_KEY/machine/project_composite_key_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S08_P1_PROJECT_COMPOSITE_KEY/human/test_results.md`
- limitation: S08-P1 只证明 public-safe project composite key evidence；不证明 S08-P2 业务实体模型、S08-P3 匹配质量、Stage 8 review、raw value matching、lineage full check、正式报告、GitHub upload readiness 或 business execution。

### FORM-KMFA-V014-S08P2-BUSINESS-ENTITY-MODEL-001

- type: deterministic public-safe business entity model gate
- purpose: 验证 v0.1.4 S08-P2 业务实体模型，覆盖 S08-P1 dependency、legacy public-safe S08-P2 dependency、8 类实体、14 条 schema-only 关系、32 条 lifecycle statuses、每类实体 4 个状态、schema definition count、relationship graph、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s08p2_valid = s08_p1_dependency == PASS AND legacy_s08_p2_dependency == PASS AND required_entity_type_count == 8 AND relationship_count == 14 AND lifecycle_status_count == 32 AND lifecycle_status_per_entity_count == 4 AND schema_entity_definition_count == 8 AND relationship_graph_required_links_present == true AND entity_values_hash_ref_only == true AND relationship_values_schema_only == true AND lifecycle_values_status_only == true AND raw_inbox_read_by_this_phase == false AND s08_p3_performed == false AND stage8_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s08_p2_business_entity_model.py`, `KMFA/tools/check_v014_s08_p2_business_entity_model.py`, `KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/machine/business_entity_model_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S08_P2_BUSINESS_ENTITY_MODEL/human/test_results.md`
- limitation: S08-P2 只证明 public-safe business entity model schema/ref/count/status evidence；不证明 S08-P3 匹配质量、Stage 8 review、raw value matching、lineage full check、正式报告、GitHub upload readiness 或 business execution。

### FORM-KMFA-V014-S08P3-ENTITY-MATCHING-QUALITY-001

- type: deterministic public-safe entity matching quality gate
- purpose: 验证 v0.1.4 S08-P3 实体匹配质量，覆盖 S08-P2 dependency、legacy public-safe S08-P3 dependency、scenario/case/review/report counts、risk summary、manual-review no-auto-merge policy、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s08p3_valid = s08_p2_dependency == PASS AND legacy_s08_p3_dependency == PASS AND scenario_count == 4 AND quality_case_count == 4 AND manual_review_queue_count == 3 AND entity_matching_report_count == 1 AND risk_high == 2 AND risk_medium == 1 AND risk_low == 1 AND medium_high_risk_requires_manual_review == true AND manual_review_queue_auto_merge_allowed == false AND quality_report_is_formal_report == false AND raw_inbox_read_by_this_phase == false AND stage8_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s08_p3_entity_matching_quality.py`, `KMFA/tools/check_v014_s08_p3_entity_matching_quality.py`, `KMFA/stage_artifacts/V014_S08_P3_ENTITY_MATCHING_QUALITY/machine/entity_matching_quality_manifest.json`
- boundary_validation: `KMFA/stage_artifacts/V014_S08_P3_ENTITY_MATCHING_QUALITY/human/test_results.md`
- limitation: S08-P3 只证明 public-safe entity matching quality aggregate evidence；不证明 Stage 8 review、raw business value correctness、raw value matching、lineage full check、正式报告、GitHub upload readiness、live connector 或 business execution。

### FORM-KMFA-V014-S08-STAGE-REVIEW-001

- type: deterministic public-safe Stage 8 review gate
- purpose: 复跑 v0.1.4 S08-P1/S08-P2/S08-P3 validators，并验证 legacy Stage 8 review validator，锁定 Stage 8 本地整体复审证据和 upload-deferred/no-go 边界。
- fact_level: EXTRACTED
- expression: `s08_stage_review_valid = S08-P1 PASS AND S08-P2 PASS AND S08-P3 PASS AND legacy_stage8_review_validator PASS AND open_findings == 0 AND fixed_findings == 1 AND legacy_upload_current_gate == false AND raw_inbox_read_by_review == false AND s09_p1 == false AND github_upload == false`
- evidence: `KMFA/tools/v014_s08_stage_review.py`, `KMFA/tools/check_v014_s08_stage_review.py`, `KMFA/stage_artifacts/V014_S08_STAGE_REVIEW/machine/stage8_review_manifest.json`
- boundary_validation: `KMFA/tests/test_v014_s08_stage_review.py`, `KMFA/stage_artifacts/V014_S08_STAGE_REVIEW/human/test_results.md`
- limitation: Stage 8 review 只证明 S08 public-safe local review closure；不证明 S09-P1、raw business value correctness、raw value matching、lineage full check、正式报告、GitHub upload readiness、live connector、app reinstall 或 business execution。

### FORM-KMFA-V014-S09P1-PROJECT-COST-FACT-LAYER-001

- type: deterministic public-safe project cost fact layer gate
- purpose: 验证 v0.1.4 S09-P1 项目成本事实层，覆盖 Stage 8 review dependency、legacy public-safe S09-P1 dependency、6 类 required metrics、9 类成本分类、4 条 fact records、9 条 unallocated cost pool、人工复核队列、未解决差异、NO_GO/Q4/D/blocked 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s09p1_valid = s08_stage_review_dependency == PASS AND legacy_s09_p1_dependency == PASS AND required_metric_count == 6 AND cost_category_count == 9 AND fact_record_count == 4 AND unallocated_pool_count == 9 AND manual_review_queue_count == 3 AND unresolved_difference_count == 1 AND zero_delta_fail_count == 1 AND blocked_quality_result_count == 2 AND raw_inbox_read_by_this_phase == false AND s09_p2_performed == false AND s09_p3_performed == false AND stage9_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s09_p1_project_cost_fact_layer.py`, `KMFA/tools/check_v014_s09_p1_project_cost_fact_layer.py`, `KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/machine/project_cost_fact_layer_manifest.json`
- boundary_validation: `KMFA/tests/test_v014_s09_p1_project_cost_fact_layer.py`, `KMFA/stage_artifacts/V014_S09_P1_PROJECT_COST_FACT_LAYER/human/test_results.md`
- limitation: S09-P1 只证明 public-safe project cost fact layer aggregate/schema evidence；不证明 S09-P2 毛利/现金毛利、S09-P3 差异核对、Stage 9 review、raw business value correctness、raw value matching、lineage full check、正式报告、GitHub upload readiness、live connector、app reinstall、OpMe 深度耦合或 business execution。

### FORM-KMFA-V014-S09P2-MARGIN-CASH-MARGIN-001

- type: deterministic public-safe margin and cash margin gate
- purpose: 验证 v0.1.4 S09-P2 毛利与现金毛利，覆盖 S09-P1 dependency、legacy public-safe S09-P2 dependency、4 个 margin metrics、4 条 margin records、12 条 scope difference summary、8 个 authority field groups、NO_GO/Q4/D/blocked、authority/system no-overwrite 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s09p2_valid = s09p1_dependency == PASS AND legacy_s09_p2_dependency == PASS AND required_margin_metric_count == 4 AND margin_record_count == 4 AND difference_summary_count == 12 AND authority_system_overwrite_allowed_count == 0 AND public_amount_values_committed_count == 0 AND raw_inbox_read_by_this_phase == false AND s09_p3_performed == false AND stage9_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s09_p2_margin_cash_margin.py`, `KMFA/tools/check_v014_s09_p2_margin_cash_margin.py`, `KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/machine/margin_cash_margin_manifest.json`
- boundary_validation: `KMFA/tests/test_v014_s09_p2_margin_cash_margin.py`, `KMFA/stage_artifacts/V014_S09_P2_MARGIN_CASH_MARGIN/human/test_results.md`
- limitation: S09-P2 只证明 public-safe margin/cash-margin aggregate/hash-ref evidence；不证明 S09-P3 差异核对、Stage 9 review、raw business value correctness、raw value matching、lineage full check、正式报告、GitHub upload readiness、live connector、app reinstall、OpMe 深度耦合或 business execution。

### FORM-KMFA-V014-S09P3-SCOPE-RECONCILIATION-001

- type: deterministic public-safe scope reconciliation gate
- purpose: 验证 v0.1.4 S09-P3 口径转换与差异核对，覆盖 S09-P2 dependency、legacy public-safe S09-P3 dependency、6 类 reconciliation domains、8 个 human fields、12 条 reconciliation records、6 条 domain controls、0 条 confirmed resolutions、12 条 pending resolutions、NO_GO/Q4/D/blocked 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s09p3_valid = s09p2_dependency == PASS AND legacy_s09_p3_dependency == PASS AND required_reconciliation_domain_count == 6 AND required_human_field_count == 8 AND reconciliation_record_count == 12 AND domain_control_count == 6 AND confirmed_resolution_count == 0 AND pending_resolution_count == 12 AND derived_metric_rerun_allowed_count == 0 AND formal_report_rerun_allowed_count == 0 AND raw_inbox_read_by_this_phase == false AND stage9_review_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s09_p3_scope_reconciliation.py`, `KMFA/tools/check_v014_s09_p3_scope_reconciliation.py`, `KMFA/stage_artifacts/V014_S09_P3_SCOPE_RECONCILIATION/machine/scope_reconciliation_manifest.json`
- boundary_validation: `KMFA/tests/test_v014_s09_p3_scope_reconciliation.py`, `KMFA/stage_artifacts/V014_S09_P3_SCOPE_RECONCILIATION/human/test_results.md`
- limitation: S09-P3 只证明 public-safe reconciliation aggregate/hash-ref/status evidence；不证明 Stage 9 review、raw business value correctness、raw value matching、lineage full check、正式报告、GitHub upload readiness、live connector、app reinstall、OpMe 深度耦合或 business execution。

### FORM-KMFA-V014-S09-STAGE-REVIEW-001

- type: deterministic public-safe stage review gate
- purpose: 验证 v0.1.4 Stage 9 整体复审，覆盖 S09-P1/S09-P2/S09-P3 validators、legacy Stage 9 review validator、open findings 0、fixed findings 1、NO_GO/Q4/D/blocked、S10-P1=false 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s09_stage_review_valid = phase_pass_count == 3 AND open_review_finding_count == 0 AND fixed_review_finding_count == 1 AND reconciliation_record_count == 12 AND pending_resolution_count == 12 AND current_go_no_go == NO_GO AND s10_p1_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s09_stage_review.py`, `KMFA/tools/check_v014_s09_stage_review.py`, `KMFA/stage_artifacts/V014_S09_STAGE_REVIEW/machine/stage9_review_manifest.json`
- boundary_validation: `KMFA/tests/test_v014_s09_stage_review.py`, `KMFA/stage_artifacts/V014_S09_STAGE_REVIEW/human/test_results.md`
- limitation: Stage 9 review 只证明本地复审闭环；不证明 S10-P1、raw business value correctness、raw value matching、lineage full check、正式报告、GitHub upload readiness、live connector、app reinstall、OpMe 深度耦合或 business execution。

### FORM-KMFA-AMOUNT-001

- type: deterministic amount normalization
- purpose: 将授权来源中的业务金额标准化为整数分，并阻断 float 金额用法。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/amount_tools.py`, `KMFA/tools/check_no_float_money.py`, `KMFA/stage_artifacts/S04_P1_amount_tools/human/s04_p1_completion_record.md`, `KMFA/stage_artifacts/V014_S04_P1_AMOUNT_PRECISION/machine/amount_precision_manifest.json`
- boundary_validation: `KMFA/tests/test_basic_tool_boundaries.py`, `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md`
- limitation: 不做 zero-delta，不处理源冲突取舍。

### FORM-KMFA-FIELD-STANDARDIZATION-001

- type: deterministic field standardization
- purpose: 将日期、期间、公司主体、项目名称、客户/对手方、合同编号映射到 canonical fields，并把缺字段或异常字段写入 metadata 质量状态。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/field_standardization.py`, `KMFA/metadata/schema_maps/field_alias_dictionary.csv`, `KMFA/metadata/quality/field_quality_status.jsonl`, `KMFA/stage_artifacts/S04_P2_field_standardization/human/s04_p2_completion_record.md`
- boundary_validation: `KMFA/tests/test_basic_tool_boundaries.py`, `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md`
- limitation: 不解析真实业务源，不建立事实层，不生成报告。

### VALIDATION-KMFA-S04P3-001

- type: synthetic boundary validation report
- purpose: 用合成值验证金额、日期和期间基础工具边界，生成 JSON/Markdown 工具函数测试报告。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/generate_tool_test_report.py`, `KMFA/stage_artifacts/S04_P3_basic_tool_tests/human/tool_function_test_report.md`
- limitation: 只验证基础工具边界，不替代 A0、zero-delta、事实层或报告验收。

### FORM-KMFA-A0-FILE-REGISTRATION-001

- type: deterministic public-safe A0 file registration
- purpose: 登记 A0 文件数量、source package SHA256、legacy 指纹、A0 项目候选和 Q3/Q4/Q5 状态，不提交 raw PDF、Excel 或 zip。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/a0_file_register.py`, `KMFA/tools/check_a0_file_registration.py`, `KMFA/stage_artifacts/S05_P1_a0_file_registration/human/s05_p1_completion_record.md`
- limitation: 私有 A0 压缩包不可用时成员 SHA256 保持 pending；不抽取字段值，不完成 Q4/Q5。

### FORM-KMFA-A0-GOLDEN-FIXTURE-001

- type: deterministic public-safe A0 golden fixture candidate contract
- purpose: 为合同额、支出合计、毛利、毛利率、成本分类建立字段合同、private refs、hash/status 和 source anchor 状态。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/a0_golden_fixture.py`, `KMFA/tools/check_a0_golden_fixture.py`, `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/s05_p2_completion_record.md`
- limitation: S05-P2 完成本地候选合同和 owner/授权降级决策；Q5 authority lock 由 `FORM-KMFA-A0-AUTHORITY-BASELINE-LOCK-001` 单独约束。

### FORM-KMFA-A0-AUTHORITY-BASELINE-LOCK-001

- type: deterministic public-safe A0 authority baseline lock
- purpose: 将 40 条具备 private hash/source-anchor 证据的 PDF 字段锁定为 Q5 calculation baseline，并将 5 条 Excel 字段按 active owner/授权降级决策排除。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/a0_authority_baseline_lock.py`, `KMFA/tools/check_a0_authority_baseline_lock.py`, `KMFA/metadata/baseline/a0_authority_baseline_manifest.json`, `KMFA/stage_artifacts/S05_P3_authority_baseline_lock/human/s05_p3_completion_record.md`
- limitation: 只保存 public-safe hash/source-anchor baseline，不提交真实字段明文；Stage 5 review 为本地完成且 GitHub upload deferred，不代表 zero-delta、lineage 或正式报告发布完成。

### FORM-KMFA-A0-STAGE-REVIEW-001

- type: deterministic public-safe Stage 5 review gate
- purpose: 复跑 S05-P1/S05-P2/S05-P3 validator，锁定 Stage 5 本地整体复审证据，确认 open findings 为 0 且 GitHub upload 延后到 Stage 1-10 batch gate。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/v013_s05_stage_review.py`, `KMFA/tools/check_v013_s05_stage_review.py`, `KMFA/stage_artifacts/V013_S05_STAGE_REVIEW/human/stage5_review_report.md`, `KMFA/stage_artifacts/V013_S05_STAGE_REVIEW/machine/stage5_review_manifest.json`
- limitation: 只证明 Stage 5 public-safe local review closure；不读取 raw inbox，不发布 raw/private 明细，不执行 S06、GitHub upload、lineage full check、formal report 或 business execution。

### FORM-KMFA-REDCIRCLE-POSTPONEMENT-001

- type: deterministic redcircle export postponement policy
- purpose: 为红圈经营、合同、回款、财务四类导出预留 public-safe 模板，并明确 D15 文件型 MVP 不接自动接口。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/redcircle_postponement_policy.py`, `KMFA/tools/check_s07_p3_redcircle_postponement.py`, `KMFA/metadata/schema_maps/redcircle_postponement_manifest.json`, `KMFA/stage_artifacts/S07_P3_redcircle_postponement_policy/human/s07_p3_completion_record.md`
- limitation: 只保存 template id、hash/private ref、控制状态和 rollback metadata；不提交红圈原始导出、接口凭证、字段明文、真实业务值，不解锁事实层、lineage、正式报告、UI 或外部接口。

### FORM-KMFA-S17P3-OPERATIONS-SOP-001

- type: deterministic operations SOP governance contract
- purpose: 建立导入、复核、发布、回滚四类 public-safe 操作手册，登记财务 SOP/交接材料知识索引，并记录错误处理和备份恢复演练。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/operations_sop.py`, `KMFA/tools/check_s17_p3_operations_sop.py`, `KMFA/metadata/operations/operations_sop_manifest.json`, `KMFA/stage_artifacts/S17_P3_operations_sop/human/s17_p3_completion_record.md`
- boundary_validation: `KMFA/tests/test_operations_sop.py`, `KMFA/stage_artifacts/S17_P3_operations_sop/human/test_results.md`
- limitation: 只保存 metadata/manual SOP 证据，不执行 live connector、外部服务、生产恢复、正式报告、业务动作、Stage 17 review 或 GitHub upload。

### FORM-KMFA-S17P1-ACCESS-SECURITY-001

- type: deterministic access security governance policy
- purpose: 锁定 S17-P1 角色权限矩阵、公开仓库敏感材料禁入策略和导入/处理/报告/导出/通知审计日志策略。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/access_security_policy.py`, `KMFA/tools/check_s17_p1_access_security.py`, `KMFA/metadata/security/access_security_policy_manifest.json`, `KMFA/stage_artifacts/S17_P1_access_security/human/s17_p1_completion_record.md`
- required_roles: `management`, `finance`, `reviewer`, `readonly`
- required_audit_actions: `import`, `processing`, `report`, `export`, `notification`
- boundary_validation: `KMFA/tests/test_access_security_policy.py`, `KMFA/stage_artifacts/S17_P1_access_security/human/test_results.md`
- limitation: S17-P1 只定义权限、安全和审计策略；不发送通知、不生成完整报告正文、不执行 S17-P3 SOP、Stage 17 review、GitHub upload 或外部接口。

### FORM-KMFA-S17P2-NOTIFICATION-001

- type: deterministic notification reminder governance policy
- purpose: 锁定 S17-P2 报告生成完成、重大风险、数据源缺失三类提醒规则，并将通知事件和 dispatch 日志写入 metadata。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/notification_reminders.py`, `KMFA/tools/check_s17_p2_notifications.py`, `KMFA/metadata/notifications/notification_manifest.json`, `KMFA/stage_artifacts/S17_P2_notification/human/s17_p2_completion_record.md`
- required_triggers: `report_generation_completed`, `major_risk`, `data_source_missing`
- boundary_validation: `KMFA/tests/test_notification_reminders.py`, `KMFA/stage_artifacts/S17_P2_notification/human/test_results.md`
- limitation: S17-P2 只写 public-safe metadata outbox/log；不调用外部邮件连接器、不发送完整报告正文、不生成附件、不保存真实收件地址、不执行 S17-P3 SOP、Stage 17 review、GitHub upload 或外部接口。

### FORM-KMFA-PROJECT-COMPOSITE-KEY-001

- type: deterministic public-safe project identity matching
- purpose: 用合同编号、项目名称、对手方、主体、时间、金额签名、责任人、来源 hash 八个组件建立项目组合键并输出匹配候选。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/project_composite_key.py`, `KMFA/tools/check_s08_p1_project_composite_key.py`, `KMFA/metadata/schema_maps/project_composite_key_manifest.json`, `KMFA/stage_artifacts/S08_P1_project_composite_key/human/s08_p1_completion_record.md`
- limitation: 只保存组件 hash、private ref、整数权重、匹配状态和人工复核队列；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV；S08-P2 已由业务实体模型覆盖，但不实现 S08-P3、事实层、lineage、正式报告、UI 或外部接口。

### FORM-KMFA-BUSINESS-ENTITY-MODEL-001

- type: deterministic public-safe business entity schema
- purpose: 定义客户、合同、项目、成本、开票、回款、应收和税务证据 8 类业务实体，以及 14 条关系和 32 个生命周期状态。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/business_entity_model.py`, `KMFA/tools/check_s08_p2_business_entity_model.py`, `KMFA/metadata/schema_maps/business_entity_model_manifest.json`, `KMFA/docs/governance/BUSINESS_ENTITY_MODEL_SCHEMA.md`, `KMFA/stage_artifacts/S08_P2_business_entity_model/human/s08_p2_completion_record.md`
- limitation: 只保存 entity refs、source refs、source hashes、public-safe schema、关系和生命周期 metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不实现 S08-P3、事实层、lineage、正式报告、UI、外部接口、Stage 8 review 或 GitHub upload。

### FORM-KMFA-ENTITY-MATCHING-QUALITY-001

- type: deterministic public-safe entity matching quality gate
- purpose: 覆盖同名项目、多主体、多账户、多期间 4 类匹配质量场景，并将中高风险候选送入人工复核。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/entity_matching_quality.py`, `KMFA/tools/check_s08_p3_entity_matching_quality.py`, `KMFA/metadata/quality/entity_matching_quality_manifest.json`, `KMFA/metadata/quality/entity_matching_quality_cases.jsonl`, `KMFA/metadata/quality/entity_matching_review_queue.jsonl`, `KMFA/stage_artifacts/S08_P3_entity_matching_quality/machine/entity_matching_report.json`, `KMFA/stage_artifacts/S08_P3_entity_matching_quality/human/s08_p3_completion_record.md`
- limitation: 只保存 profile/entity/source hash refs、匹配分、风险等级、人工复核状态和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不执行 Stage 8 review、事实层、lineage、正式报告、UI、外部接口或 GitHub upload。

### FORM-KMFA-PROJECT-COST-FACT-LAYER-001

- type: deterministic public-safe project cost fact layer
- purpose: 为收入、合同额、开票、回款、成本合计、成本分类建立结构化 fact slots，并将未归项目成本进入未归集成本池。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/project_cost_fact_layer.py`, `KMFA/tools/check_s09_p1_project_cost_fact_layer.py`, `KMFA/metadata/reports/project_cost_fact_layer_manifest.json`, `KMFA/metadata/lineage/project_cost_fact_records.jsonl`, `KMFA/metadata/lineage/unallocated_project_cost_pool.jsonl`, `KMFA/stage_artifacts/S09_P1_project_cost_fact_layer/human/s09_p1_completion_record.md`
- limitation: 只保存 metric/category slots、private refs、hash refs、质量阻断状态和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不执行 S09-P2 毛利/现金毛利、S09-P3 差异核对、Stage 9 review、lineage 完整检查、正式报告、UI、外部接口或 GitHub upload。

### FORM-KMFA-MARGIN-CASH-MARGIN-001

- status: active
- type: deterministic public-safe margin and cash margin calculation contract
- purpose: 建立权威毛利、系统复算毛利、现金毛利和毛利率的整数分/basis points 计算合同，并保留权威显示值与系统复算值分离。
- evidence: `KMFA/tools/project_margin_cash_margin.py`, `KMFA/tools/check_s09_p2_margin_cash_margin.py`, `KMFA/metadata/reports/project_margin_cash_margin_manifest.json`, `KMFA/metadata/lineage/project_margin_cash_margin_records.jsonl`, `KMFA/metadata/quality/scope_difference_summary.jsonl`, `KMFA/stage_artifacts/S09_P2_margin_cash_margin/human/s09_p2_completion_record.md`
- limitation: 只保存 authority/system/cash margin private refs、hash refs、差异摘要状态和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV；S09-P3 已单独建立核对层，但 S09-P2 不代表 Stage 9 review、lineage 完整检查、正式报告、UI、外部接口或 GitHub upload 完成。

### FORM-KMFA-SCOPE-RECONCILIATION-001

- status: active
- type: deterministic public-safe scope reconciliation contract
- purpose: 将 S09-P2 的口径差异摘要转换为 owner-readable reconciliation records，并覆盖合同/项目收入、项目成本/财务费用、银行回款/应收账龄、开票/合同结算/税务、研发费用/项目人员证据、权威 PDF/Excel 与系统复算 6 类核对域。
- evidence: `KMFA/tools/project_scope_reconciliation.py`, `KMFA/tools/check_s09_p3_scope_reconciliation.py`, `KMFA/metadata/reports/project_scope_reconciliation_manifest.json`, `KMFA/metadata/quality/scope_reconciliation_records.jsonl`, `KMFA/metadata/quality/scope_reconciliation_domain_controls.jsonl`, `KMFA/stage_artifacts/S09_P3_scope_reconciliation/human/s09_p3_completion_record.md`
- limitation: 只保存 source refs、private refs、hash refs、原因候选、依据 refs、影响范围、责任角色、reviewer 和 pending 状态；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不关闭差异，不实际重跑派生指标或正式报告；Stage 9 review 已本地通过但不代表 lineage 完整检查、UI、外部接口或 GitHub upload 完成。

### FORM-KMFA-REPORT-TEMPLATE-001

- status: active
- type: deterministic public-safe report template contract
- purpose: 建立项目成本专题报告和经营总览报告模板，锁定管理可读章节与 v1.2 HTML/报告样板引用。
- evidence: `KMFA/tools/report_templates.py`, `KMFA/tools/check_s10_p1_report_templates.py`, `KMFA/metadata/reports/report_template_manifest.json`, `KMFA/metadata/reports/report_templates.jsonl`, `KMFA/metadata/reports/report_template_sections.jsonl`, `KMFA/stage_artifacts/S10_P1_report_templates/human/s10_p1_completion_record.md`
- limitation: 只保存模板结构、管理可读章节、source refs、HTML 验收样板引用、status 和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV，不判定 A/B/C/D 可信等级，不生成 HTML/CSV/Excel/PDF 导出，不执行 Stage 10 review、lineage 完整检查、UI、外部接口或 GitHub upload。

### FORM-KMFA-REPORT-GRADE-RUNTIME-001

- status: active
- type: deterministic public-safe report grade runtime
- purpose: 基于数据质量、zero-delta、pending reconciliation、lineage、人工确认和时效状态判定 A/B/C/D 报告可信等级，并在证据不足时阻断完整可信报告显示。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/report_grade_runtime.py`, `KMFA/tools/check_s10_p2_report_grade_runtime.py`, `KMFA/metadata/reports/report_grade_runtime_manifest.json`, `KMFA/metadata/reports/report_grade_runtime_records.jsonl`, `KMFA/stage_artifacts/S10_P2_report_grade_runtime/human/s10_p2_completion_record.md`
- limitation: 当前 2 条报告等级记录均为 D；只保存等级、版本绑定、hash/ref、scope gate 和 evidence metadata；不提交 raw business values、字段明文、Excel/PDF/zip/private CSV；HTML/CSV 导出由 `FORM-KMFA-REPORT-EXPORT-001` 单独约束；不执行 Stage 10 review、lineage 完整检查、UI、外部接口或 GitHub upload。

### FORM-KMFA-REPORT-EXPORT-001

- status: active
- type: deterministic public-safe report export runtime
- purpose: 基于 S10-P1 模板和 S10-P2 D 级阻断记录生成 public-safe HTML 预览、CSV/Excel-compatible 附表和 PDF private runtime policy。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/report_export_runtime.py`, `KMFA/tools/check_s10_p3_report_export.py`, `KMFA/metadata/reports/report_export_manifest.json`, `KMFA/metadata/reports/report_export_records.jsonl`, `KMFA/stage_artifacts/S10_P3_report_export/human/s10_p3_completion_record.md`
- limitation: 只提交 HTML/CSV/manifest/records/evidence metadata；不提交 raw business values、字段明文、Excel workbook、PDF、zip、sqlite 或 private CSV；2 条报告仍为 D 级阻断，不能作为正式经营决策依据；不执行 Stage 10 review、lineage 完整检查、UI、外部接口或 GitHub upload。

### FORM-KMFA-HOME-NAVIGATION-001

- status: active
- type: deterministic public-safe home navigation runtime
- purpose: 生成 KMFA 首页与导航的 public-safe manifest、模块 records 和蓝色商务风 HTML 样张，覆盖 8 个 S11-P1 必需入口。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/home_navigation_runtime.py`, `KMFA/tools/check_s11_p1_home_navigation.py`, `KMFA/tests/test_home_navigation_runtime.py`, `KMFA/metadata/reports/home_navigation_manifest.json`, `KMFA/metadata/reports/home_navigation_modules.jsonl`, `KMFA/stage_artifacts/S11_P1_home_navigation/human/s11_p1_completion_record.md`
- limitation: 只提交首页导航结构、公开安全摘要和 HTML 样张；不提交 raw business values、字段明文、Excel workbook、PDF、zip、sqlite 或 private CSV；S11-P2 已由数据源检查板覆盖，但 S11-P1 不实现 S11-P3 项目成本详情、Stage 11 review、正式报告、lineage full check、外部接口或 GitHub upload。

### FORM-KMFA-SOURCE-CHECK-BOARD-001

- status: active
- type: deterministic public-safe source check board runtime
- purpose: 生成 KMFA 数据源检查板的 public-safe manifest、来源状态 rows 和蓝灰商务风 HTML 样张，覆盖固定 11 列、5 种状态和状态点击详情。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/source_check_board_runtime.py`, `KMFA/tools/check_s11_p2_source_check_board.py`, `KMFA/tests/test_source_check_board_runtime.py`, `KMFA/metadata/reports/source_check_board_manifest.json`, `KMFA/metadata/reports/source_check_board_rows.jsonl`, `KMFA/stage_artifacts/S11_P2_source_check_board/human/s11_p2_completion_record.md`
- limitation: 只提交公开安全来源类别、业务板块、包引用、主体分组、账户/报表分组、状态、影响和下一步；不提交 raw business values、字段明文、真实源文件名、真实账号、Excel workbook、PDF、zip、sqlite 或 private CSV；不实现 S11-P3 项目成本详情、Stage 11 review、正式报告、lineage full check、外部接口或 GitHub upload。

### FORM-KMFA-PROJECT-COST-PAGE-001

- status: active
- type: deterministic public-safe project cost page runtime
- purpose: 生成 KMFA 项目成本页面的 public-safe manifest、项目页面 records 和蓝色商务风 HTML 页面，覆盖项目列表、毛利状态、成本结构、回款状态、差异状态、项目详情、来源证据、待处理事项和报告预览。
- fact_level: EXTRACTED
- evidence: `KMFA/tools/project_cost_page_runtime.py`, `KMFA/tools/check_s11_p3_project_cost_page.py`, `KMFA/tests/test_project_cost_page_runtime.py`, `KMFA/metadata/reports/project_cost_page_manifest.json`, `KMFA/metadata/reports/project_cost_page_projects.jsonl`, `KMFA/stage_artifacts/S11_P3_project_cost_page/human/s11_p3_completion_record.md`
- limitation: 只提交公开安全项目分组、状态、成本分类标签、证据引用、待处理事项、HTML 样张、manifest 和 records；不提交 raw business values、字段明文、真实源文件名、真实账号、Excel workbook、PDF、zip、sqlite/db 或 private CSV；报告预览可直接查看但必须显示 D 级且不可绕过质量等级；Stage 11 review/upload 已完成，但不代表 S12、正式报告、lineage full check 或外部接口完成。

### FORM-KMFA-MANUAL-RESOLUTION-EVENT-001

- status: active
- type: deterministic public-safe manual resolution event contract
- purpose: 建立 S12-P1 人工处理事件的 append-only 记录、manifest 和 HTML 工作台样张，覆盖字段映射、项目匹配、差异处理和备注。
- fact_level: EXTRACTED
- expression: `manual_resolution_events_valid = manual_event_count == 5 AND manual_action_kind_count == 4 AND approved_event_count == 1 AND reverse_event_count == 1 AND raw_layer_write_allowed == false AND impact_preview_publish_allowed == false AND derived_rerun_allowed == false AND formal_report_allowed == false AND stage12_review_allowed == false AND github_upload_allowed == false`
- evidence: `KMFA/tools/manual_resolution_events.py`, `KMFA/tools/check_s12_p1_manual_resolution_events.py`, `KMFA/tests/test_manual_resolution_events.py`, `KMFA/metadata/approvals/manual_resolution_event_manifest.json`, `KMFA/metadata/approvals/manual_resolution_events.jsonl`, `KMFA/stage_artifacts/S12_P1_manual_resolution_events/human/s12_p1_completion_record.md`
- limitation: 只提交公开安全事件类型、角色引用、时间、原因码、影响范围、版本和证据引用；不提交 raw business values、字段明文、真实金额、Excel workbook、PDF、zip、sqlite/db、private CSV 或 credentials；不发布 S12-P2 影响预览，不执行 S12-P3 派生重跑，不做 Stage 12 review/upload、lineage full check、正式报告或外部接口。

### FORM-KMFA-V014-S07-STAGE-REVIEW-001

- status: active
- type: deterministic public-safe stage review gate
- purpose: 验证 v0.1.4 Stage 7 整体复审，覆盖 S07-P1/S07-P2/S07-P3 validators、legacy S07 validators、open/fixed findings、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `stage7_review_valid = phase_results == PASS_PASS_PASS AND open_findings == 0 AND fixed_findings == 1 AND q5_allowed_count == 0 AND formal_report_allowed_count == 0 AND redcircle_automatic_connector_allowed == false AND s08_p1_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/v014_s07_stage_review.py`, `KMFA/tools/check_v014_s07_stage_review.py`, `KMFA/tests/test_v014_s07_stage_review.py`, `KMFA/stage_artifacts/V014_S07_STAGE_REVIEW/machine/stage7_review_manifest.json`, `KMFA/stage_artifacts/V014_S07_STAGE_REVIEW/human/stage7_review_report.md`
- limitation: 不证明 S08-P1、raw value matching、lineage full check、正式报告、live connector、业务执行或 GitHub upload 完成。

## Active Business Model

### MOD-KMFA-COST-001

- status: active with v0.1.4 S05-P3 authority baseline lock evidence and existing public-safe cost-analysis formulas
- purpose: 后续文件型项目成本分析 MVP。
- dependency: S05 A0 基准、S06 零差异、S08 项目身份匹配、S09 成本计算、S10 报告等级。
- current limitation: v0.1.4 S10-P3 report export is local-only public-safe HTML/CSV/Excel-compatible CSV evidence; Stage 10 review, GitHub upload, lineage full check, official report generation, UI runtime, live connectors and OpMe deep coupling are not completed in this run; current Go/No-Go remains NO_GO and D-grade report previews are not decision-grade reports.

## Counts

- active models: 8
- active formulas: 100
- active parameters: 775
- planned models: 0
- planned formulas: 0
- planned parameters: 1

## Stop Conditions

- 原始敏感经营数据进入公开仓库。
- 业务金额使用 float。
- 0.01 元差异被静默通过。
- 缺数据报告被伪装为完整报告。
- Stage 未完成复审修复即上传 GitHub。


### FORM-KMFA-V014-S01P3-NO-OMISSION-BASELINE-001

- status: active
- type: deterministic public-safe governance gate
- purpose: 验证 v0.1.4 S01-P3 防遗漏基线，覆盖 legacy requirements、v1.4 overlay requirements、18/54/162 roadmap registry、raw boundary 和 no-upload/no-review scope gate。
- fact_level: EXTRACTED
- expression: `s01p3_valid = legacy_requirements == 20 AND legacy_p0 == 9 AND legacy_p1 == 8 AND v14_overlay == 5 AND v14_stages == 18 AND v14_phases == 54 AND v14_tasks == 162 AND github_upload_performed == false`
- evidence: `KMFA/tools/check_v014_s01_p3_no_omission_baseline.py`, `KMFA/metadata/traceability/v1_4_no_omission_requirements.csv`, `KMFA/metadata/traceability/v1_4_stage_phase_task_status.jsonl`, `KMFA/stage_artifacts/V014_S01_P3_NO_OMISSION_BASELINE/machine/s01_p3_no_omission_baseline_manifest.json`
- limitation: 不证明 Stage 1 review、raw inventory、raw value matching、正式报告、GitHub upload 或 delivery readiness。

### FORM-KMFA-V014-S01-STAGE-REVIEW-001

- status: active
- type: deterministic public-safe review gate
- purpose: 验证 v0.1.4 Stage 1 整体复审，覆盖 S01-P1/S01-P2/S01-P3 phase validator 结果、open findings、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `stage1_review_valid = phase_results == PASS_PASS_PASS AND open_findings == 0 AND github_upload_performed == false AND s02_started == false AND current_go_no_go == NO_GO`
- evidence: `KMFA/tools/check_v014_s01_stage_review.py`, `KMFA/stage_artifacts/V014_S01_STAGE_REVIEW/machine/stage1_review_manifest.json`
- limitation: 不证明 S02、raw inventory、raw value matching、正式报告、GitHub upload 或 delivery readiness。

### FORM-KMFA-V014-S02P1-METADATA-PROTOCOL-001

- status: active
- type: deterministic public-safe metadata protocol gate
- purpose: 验证 v0.1.4 S02-P1 metadata 目录协议，覆盖七类 metadata 目录、五类核心标识符、raw-root public-safe protocol、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s02p1_valid = required_dirs == 7 AND required_identifiers == 5 AND raw_inbox_read == false AND raw_inbox_listed == false AND raw_inventory_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/check_v014_s02_p1_metadata_protocol.py`, `KMFA/tools/metadata_protocol_check.py`, `KMFA/metadata/protocol/raw_data_roots_v1_4.json`, `KMFA/stage_artifacts/V014_S02_P1_METADATA_PROTOCOL/machine/s02_p1_metadata_protocol_manifest.json`
- limitation: 不证明 raw readiness、raw inventory、raw value matching、S02-P2、S02-P3、Stage 2 review、正式报告、GitHub upload 或 delivery readiness。

### FORM-KMFA-V014-S02P2-IMMUTABILITY-POLICY-001

- status: active
- type: deterministic public-safe immutability policy gate
- purpose: 验证 v0.1.4 S02-P2 不可污染原则，覆盖 raw manifest append-only immutable fields、derived version no-overwrite actions、control event no-raw-write、raw boundary、NO_GO 和 upload-deferred gate。
- fact_level: EXTRACTED
- expression: `s02p2_valid = immutable_fields == 5 AND derived_actions == 4 AND control_event_types == 6 AND raw_inbox_read == false AND raw_inbox_listed == false AND raw_inventory_performed == false AND github_upload_performed == false`
- evidence: `KMFA/tools/check_v014_s02_p2_immutability_policy.py`, `KMFA/tools/immutability_policy_check.py`, `KMFA/metadata/protocol/immutability_policy_lock_v1_4.json`, `KMFA/stage_artifacts/V014_S02_P2_IMMUTABILITY_POLICY/machine/s02_p2_immutability_policy_manifest.json`
- limitation: 不证明 raw readiness、raw inventory、raw value matching、S02-P3、Stage 2 review、正式报告、GitHub upload 或 delivery readiness。


## FORM-KMFA-V014-S11P1-HOME-NAVIGATION-001
- Version: `0.1.4-s11p1-home-navigation`.
- Purpose: lock S11-P1 homepage navigation evidence for eight required Chinese modules, clickable navigation/actions, visible feedback, report-center entry, KM mark, blue business style, and v1.4 human-flow baseline reflection.
- Inputs: legacy S11-P1 local-only navigation artifacts, v0.1.4 Stage 10 review manifest, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S11_P1_HOME_NAVIGATION/machine/home_navigation_manifest.json` and public-safe human evidence under the same artifact directory.
- Controls: S11-P2, S11-P3, Stage 11 review, GitHub upload, raw value matching, lineage full check, formal report release, business decision basis, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S11P2-SOURCE-CHECK-BOARD-001
- Version: `0.1.4-s11p2-source-check-board`.
- Purpose: lock S11-P2 source check board evidence for public-safe matrix rows, required columns, allowed statuses, search feedback, status detail, status-change control events, blue-gray low-interference style, and v1.4 human-flow baseline reflection.
- Inputs: v0.1.4 S11-P1 dependency, legacy S11-P2 public-safe source check board artifacts, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S11_P2_SOURCE_CHECK_BOARD/machine/source_check_board_manifest.json` and public-safe human evidence under the same artifact directory.
- Controls: S11-P3, Stage 11 review, GitHub upload, raw value matching, lineage full check, formal report release, business decision basis, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S11P3-PROJECT-COST-PAGE-001
- Version: `0.1.4-s11p3-project-cost-page`.
- Purpose: lock S11-P3 project cost page evidence for public-safe project rows, list columns, cost structure, margin records, collection/difference status, project detail panels, source evidence, pending action panels, D-grade report preview, and v1.4 human-flow baseline reflection.
- Inputs: v0.1.4 S11-P2 dependency, legacy S11-P3 public-safe project cost page artifacts, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE/machine/project_cost_page_manifest.json`, `KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE/machine/project_cost_page_projects.jsonl`, `KMFA/stage_artifacts/V014_S11_P3_PROJECT_COST_PAGE/exports/html/kmfa_project_cost_page.html`, and public-safe human evidence under the same artifact directory.
- Controls: Stage 11 review, GitHub upload, raw value matching, lineage full check, formal report release, business decision basis, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S11-STAGE-REVIEW-001
- Version: `0.1.4-s11-stage-review`.
- Purpose: lock v0.1.4 Stage 11 overall review evidence after replaying S11-P1/S11-P2/S11-P3 validators and legacy S11 review.
- Inputs: v0.1.4 S11 phase manifests, legacy Stage 11 review manifest, v1.4 human-flow baseline evidence, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S11_STAGE_REVIEW/machine/stage11_review_manifest.json` and public-safe human review evidence under `KMFA/stage_artifacts/V014_S11_STAGE_REVIEW/`.
- Controls: S12, GitHub upload, raw value matching, lineage full check, formal report release, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S12P1-MANUAL-RESOLUTION-EVENTS-001
- Version: `0.1.4-s12p1-manual-resolution-events`.
- Purpose: lock v0.1.4 S12-P1 manual resolution event evidence for append-only field mapping, project matching, difference handling, note events, approved-event immutability, reverse-event chain, visible workbench feedback, and v1.4 human-flow baseline reflection.
- Inputs: v0.1.4 Stage 11 review dependency, legacy S12-P1 public-safe manual event artifacts, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/machine/manual_resolution_events_manifest.json`, `KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/machine/manual_resolution_events.jsonl`, `KMFA/stage_artifacts/V014_S12_P1_MANUAL_RESOLUTION_EVENTS/exports/html/kmfa_manual_resolution_workbench.html`, and public-safe human evidence under the same artifact directory.
- Controls: S12-P2, S12-P3, Stage 12 review, GitHub upload, raw value matching, lineage full check, formal report release, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.


## FORM-KMFA-V014-S12P2-MANUAL-IMPACT-PREVIEW-001
- Version: `0.1.4-s12p2-manual-impact-preview`.
- Purpose: lock v0.1.4 S12-P2 manual impact preview evidence for affected project refs, affected metric refs, affected report refs, high-risk second confirmation, blocked publish gates, allowed previews, visible impact-preview feedback, and v1.4 human-flow baseline reflection.
- Inputs: v0.1.4 S12-P1 dependency, legacy S12-P2 public-safe impact preview artifacts, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW/machine/manual_impact_preview_manifest.json`, `KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW/machine/manual_impact_previews.jsonl`, `KMFA/stage_artifacts/V014_S12_P2_MANUAL_IMPACT_PREVIEW/exports/html/kmfa_manual_impact_preview.html`, and public-safe human evidence under the same artifact directory.
- Controls: S12-P3, Stage 12 review, GitHub upload, raw value matching, lineage full check, formal report release, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.


## FORM-KMFA-V014-S12P3-MANUAL-RERUN-MECHANISM-001
- Version: `0.1.4-s12p3-manual-rerun-mechanism`.
- Purpose: lock v0.1.4 S12-P3 manual rerun mechanism evidence for cache invalidation, four-layer rerun steps, same-source consistency checks, blocked-preview exclusion, old-version retention, new-version append-only behavior, and v1.4 human-flow baseline reflection.
- Inputs: v0.1.4 S12-P2 dependency, public-safe S12-P2 impact preview records, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/machine/manual_rerun_manifest.json`, `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/machine/manual_rerun_cache_invalidations.jsonl`, `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/machine/manual_rerun_steps.jsonl`, `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/machine/manual_rerun_consistency_checks.jsonl`, `KMFA/stage_artifacts/V014_S12_P3_MANUAL_RERUN_MECHANISM/exports/html/kmfa_manual_rerun_mechanism.html`, and public-safe human evidence under the same artifact directory.
- Controls: Stage 12 review, GitHub upload, protected source matching, lineage full check, formal report release, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S12-STAGE-REVIEW-001
- Version: `0.1.4-s12-stage-review`.
- Purpose: lock v0.1.4 Stage 12 overall review evidence after replaying S12-P1, S12-P2, S12-P3, legacy Stage 12 review, v1.4 Stage 12 review validator, and focused unit test.
- Inputs: v0.1.4 S12 phase manifests, legacy Stage 12 review manifest as historical context, v1.4 human-flow baseline evidence, governance validators, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S12_STAGE_REVIEW/machine/stage12_review_manifest.json` and public-safe human review evidence under `KMFA/stage_artifacts/V014_S12_STAGE_REVIEW/`.
- Controls: S13, GitHub upload, protected source matching, lineage full check, formal report release, app reinstall, live connector, OpMe deep coupling, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S13P1-FINANCIAL-OPERATING-REPORT-001
- Version: `0.1.4-s13p1-financial-operating-report`.
- Purpose: lock v0.1.4 S13-P1 financial operating report evidence for operating situation, expense tax asset, cash situation and loan detail lanes plus weekly and monthly draft reports with visible data status and limitations.
- Inputs: v0.1.4 Stage 12 review dependency, legacy S13-P1 public-safe financial operating report artifacts, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_manifest.json`, `KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_source_lanes.jsonl`, `KMFA/stage_artifacts/V014_S13_P1_FINANCIAL_OPERATING_REPORT/machine/financial_operating_report_drafts.jsonl`, two public-safe HTML drafts, and public-safe human evidence under the same artifact directory.
- Controls: S13-P2, S13-P3, Stage 13 review, GitHub upload, protected source matching, lineage full check, formal report release, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S13-STAGE-REVIEW-001
- Version: `0.1.4-s13-stage-review`.
- Purpose: lock v0.1.4 Stage 13 overall review evidence after replaying S13-P1, S13-P2, S13-P3, legacy Stage 13 review, v1.4 Stage 13 review validator, and focused unit test.
- Inputs: v0.1.4 S13 phase manifests, legacy Stage 13 review manifest as historical context, v1.4 human-flow baseline evidence, governance validators, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S13_STAGE_REVIEW/machine/stage13_review_manifest.json` and public-safe human review evidence under `KMFA/stage_artifacts/V014_S13_STAGE_REVIEW/`.
- Controls: S14, GitHub upload, protected source matching, lineage full check, formal report release, app reinstall, live connector, OpMe deep coupling, difference closure, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.

## FORM-KMFA-V014-S14P1-FUND-CASH-LOAN-PLAN-001
- Version: `0.1.4-s14p1-fund-cash-loan-plan`.
- Purpose: lock v0.1.4 S14-P1 fund cash loan plan evidence for account list, monthly cash, fund plan and loan detail source lanes, cash pressure planning signals, loan due alerts, account balance summaries and public-safe HTML overview.
- Inputs: v0.1.4 Stage 13 review dependency, legacy S14-P1 public-safe fund/cash/loan artifacts, v1.4 HTML human-flow audit report, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN/machine/fund_cash_loan_plan_manifest.json`, `KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN/machine/fund_cash_loan_source_lanes.jsonl`, `KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN/machine/fund_cash_pressure_signals.jsonl`, `KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN/machine/loan_due_alerts.jsonl`, `KMFA/stage_artifacts/V014_S14_P1_FUND_CASH_LOAN_PLAN/machine/account_balance_summaries.jsonl`, one public-safe HTML overview, and public-safe human evidence under the same artifact directory.
- Controls: S14-P2, S14-P3, Stage 14 review, GitHub upload, protected source matching, lineage full check, raw value matching, formal report release, payment approval, payment execution, bank operation, loan management action, invoice issuance, tax filing, policy filing, subsidy application, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation must remain false.


## FORM-KMFA-V014-S16-STAGE-REVIEW-001
- Version: `0.1.4-s16-stage-review`.
- Purpose: lock v0.1.4 Stage 16 overall review evidence after replaying S16-P1 subcontract procurement, S16-P2 project status lifecycle, S16-P3 customer business analysis, v1.4 Stage 16 review validator, and focused unit test.
- Inputs: v0.1.4 S16 phase manifests, v1.4 taskpack/roadmap Stage 16 requirements, governance validators, and deterministic public-safe validator outputs.
- Outputs: `KMFA/stage_artifacts/V014_S16_STAGE_REVIEW/machine/stage16_review_manifest.json` and public-safe human review evidence under `KMFA/stage_artifacts/V014_S16_STAGE_REVIEW/`.
- Controls: S17-P1, GitHub upload, protected source matching, lineage full check, formal report release, app reinstall, live connector, OpMe deep coupling, procurement execution, payment approval, payment execution, bank operation, site operation, signature operation, invoice issuance, customer contact, collection action, legal decision, tax filing, business decision basis, business execution, and raw/private inbox read/list/stat/hash/mutation by this review must remain false.

## FORM-KMFA-V014-RAW-PROCESSED-COMPARABILITY-DIAGNOSTIC-001
- Version: `0.1.4-raw-processed-comparability-diagnostic`.
- Purpose: diagnose whether current private raw numeric fingerprints and existing processed target slots can form public-safe comparable pairs before any value comparison, materialization replay, lineage full check, formal report, upload or execution.
- Inputs: prior private raw value matching diagnostic, private processed value staging metadata, partial private processed value source map, unresolved owner worklist, active owner-authorized fill application record, and raw-root readonly list/stat/hash snapshot.
- Outputs: `KMFA/stage_artifacts/V014_RAW_PROCESSED_COMPARABILITY_DIAGNOSTIC/machine/raw_processed_comparability_diagnostic_manifest.json`, aggregate public-safe summary and Go/No-Go report, plus ignored private diagnostics under `.codex_private_runtime`.
- Controls: public evidence must stay aggregate-only; private diagnostics must remain git-ignored and untracked; raw root may not be modified, deleted, moved, copied, normalized or overwritten; raw-to-processed value comparison and business consistency verification remain false while comparable value pairs equal zero.
- Current result: `raw_unique_numeric_fingerprint_count=330`, `processed_target_slot_count=149`, `staged_processed_value_fingerprint_count=0`, `raw_processed_structural_key_intersection_count=0`, `comparable_value_pair_count=0`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate supplies target-slot to processed-value source-map evidence sufficient to create comparable pairs.

## FORM-KMFA-V014-RAW-PROCESSED-ALIGNMENT-BLOCKER-REPORT-001
- Version: `0.1.4-raw-processed-alignment-blocker-report`.
- Purpose: produce a public-safe blocker report and external-agent diagnostic packet explaining why raw-to-processed value alignment cannot yet be verified.
- Inputs: existing public-safe value consistency scope gate, private dry-run aggregate Go/No-Go report, processed value staging/source-map aggregate summaries, active owner-authorized fill application summary, raw/processed comparability diagnostic summary, and Stage 1-18 overall review Go/No-Go report.
- Outputs: `KMFA/stage_artifacts/V014_RAW_PROCESSED_ALIGNMENT_BLOCKER_REPORT/machine/raw_processed_alignment_blocker_manifest.json`, aggregate summary, Go/No-Go report, human blocker report, ChatGPT/agent diagnostic packet, test results, risk register and rollback plan.
- Controls: evidence remains public-safe and aggregate-only; this phase must not read, list, stat, hash, write, delete, move, copy, normalize or overwrite the raw inbox; private diagnostic details, raw source names, field/header plaintext, row/cell coordinates and business values remain out of public artifacts.
- Current result: `source_artifact_count=10`, `raw_value_fingerprint_count=871`, `raw_unique_numeric_fingerprint_count=330`, `processed_target_slot_count=149`, `staged_processed_value_fingerprint_count=0`, `usable_processed_source_map_count=0`, `authorized_filled_item_count=36`, `authorized_unfilled_item_count=113`, `raw_processed_structural_key_intersection_count=0`, `comparable_value_pair_count=0`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate supplies target-slot to processed-value source-map evidence sufficient to create comparable pairs.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-INPUT-KIT-001
- Version: `0.1.4-processed-value-source-map-completion-input-kit`.
- Purpose: generate the private-only completion template required for owner/authorized-delegate source-map completion while keeping public evidence aggregate-only.
- Inputs: v0.1.4 raw/processed alignment blocker summary, git-ignored owner worklist, and git-ignored active keep-pending fill record.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_INPUT_KIT/machine/processed_value_source_map_completion_input_kit_manifest.json`, aggregate summary, Go/No-Go report, owner/agent completion packet, and a git-ignored private completion template.
- Controls: raw inbox access and mutation must remain false; private completion template must be git-ignored and untracked; public artifacts may contain counts/status/gate refs only; downstream comparison, reconciliation, lineage, release, upload and app reinstall remain false until authorized processed value sources are supplied and separately validated.
- Current result: `source_worklist_item_count=113`, `active_fill_record_item_count=113`, `active_keep_pending_item_count=113`, `private_completion_template_item_count=113`, `private_completion_template_unique_target_slot_count=113`, `authorized_processed_value_fingerprint_count=0`, `source_map_records_applied_count=0`, `comparable_value_pair_count=0`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate fills the private completion template with authorized processed value source evidence.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-APPLICATION-001
- Version: `0.1.4-processed-value-source-map-completion-application`.
- Purpose: apply the private-only completion template as an authorization/source evidence check while keeping public evidence aggregate-only and stopping before any materialization or raw-to-processed value comparison.
- Inputs: v0.1.4 processed value source-map completion input kit summary and git-ignored private completion template.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_APPLICATION/machine/processed_value_source_map_completion_application_manifest.json`, aggregate summary, Go/No-Go report, owner/agent application packet, and a git-ignored private completion application diagnostic.
- Controls: raw inbox access and mutation must remain false; private diagnostic must be git-ignored and untracked; public artifacts may contain counts/status/gate refs only; source-map write, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false while valid completion items equal zero.
- Current result: `completion_template_item_count=113`, `pending_selected_action_count=113`, `valid_completion_item_count=0`, `authorized_processed_value_fingerprint_count=0`, `source_map_records_applied_count=0`, `comparable_value_pair_count=0`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate fills the private completion template with authorized processed value source evidence.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-READINESS-RECHECK-001
- Version: `0.1.4-processed-value-source-map-completion-readiness-recheck`.
- Purpose: recheck whether the private-only completion template has valid authorized source evidence before any source-map reapplication, materialization or raw-to-processed value comparison.
- Inputs: v0.1.4 processed value source-map completion application summary and git-ignored private completion template.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_READINESS_RECHECK/machine/processed_value_source_map_completion_readiness_recheck_manifest.json`, aggregate summary, Go/No-Go report, owner/agent recheck packet, and a git-ignored private readiness diagnostic.
- Controls: raw inbox access and mutation must remain false; private diagnostic must be git-ignored and untracked; public artifacts may contain counts/status/gate refs only; source-map reapplication, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false while valid completion items equal zero.
- Current result: `completion_template_item_count=113`, `pending_selected_action_count=113`, `valid_completion_item_count=0`, `source_map_completion_reapplication_ready=false`, `authorized_processed_value_fingerprint_count=0`, `source_map_records_applied_count=0`, `comparable_value_pair_count=0`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate fills the private completion template with authorized processed value source evidence.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-BLOCKER-AUDIT-001
- Version: `0.1.4-processed-value-source-map-completion-blocker-audit`.
- Purpose: record that the same owner/authorized-delegate source evidence blocker has repeated for three goal turns and stop before any source-map reapplication, materialization or raw-to-processed value comparison.
- Inputs: v0.1.4 processed value source-map completion application summary, readiness recheck summary and git-ignored private completion template.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_BLOCKER_AUDIT/machine/processed_value_source_map_completion_blocker_audit_manifest.json`, aggregate summary, Go/No-Go report, owner/agent blocker packet, and a git-ignored private blocker diagnostic.
- Controls: raw inbox access and mutation must remain false; private diagnostic must be git-ignored and untracked; public artifacts may contain counts/status/gate refs only; source-map reapplication, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false while valid completion items equal zero.
- Current result: `consecutive_goal_turn_blocker_count=3`, `blocked_audit_threshold_met=true`, `completion_template_item_count=113`, `pending_selected_action_count=113`, `valid_completion_item_count=0`, `source_map_completion_reapplication_ready=false`, `source_map_records_applied_count=0`, `comparable_value_pair_count=0`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate fills the private completion template with authorized processed value source evidence.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-OWNER-22-GROUP-DECISION-RESPONSE-INTAKE-001
- Version: `0.1.4-owner-22-group-decision-response-intake`.
- Purpose: intake the delegated conservative response for the private 22-group owner decision checklist while keeping application, reconciliation and release gates closed.
- Inputs: previous public-safe 22-group checklist summary, previous 22-group decision matrix, ignored private checklist, ignored private response template and ignored private checklist diagnostic.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_OWNER_22_GROUP_DECISION_RESPONSE_INTAKE/machine/processed_value_source_map_completion_owner_22_group_decision_response_intake_manifest.json`, aggregate summary, Go/No-Go report, public-safe matrix, human evidence and ignored private response diagnostics.
- Controls: raw inbox access and mutation must remain false; public artifacts may contain aggregate counts, statuses and evidence refs only; source-map mutation, partial authorization write, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false while unlinked blockers remain unresolved.
- Current result: `owner_22_group_count=22`, `owner_22_group_response_row_count=113`, `application_blocker_queue_count=113`, `linked_application_blocker_count=77`, `unlinked_application_blocker_count=36`, `actionable_group_decision_count=19`, `non_actionable_group_decision_count=3`, `source_map_records_applied_count=0`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: corrected source or owner exclusion resolution for the 36 unresolved unlinked application blockers.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-001
- Version: `0.1.4-corrected-source-or-owner-exclusion-resolution-input`.
- Purpose: prepare the private owner input template for the 36 unlinked blockers that require corrected-source evidence or explicit owner exclusion.
- Inputs: v0.1.4 owner 22-group response intake public summary, public matrix, ignored private 22-group follow-up queue and ignored private blocker resolution decision queue.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_manifest.json`, aggregate summary, Go/No-Go report, public-safe matrix, human evidence and ignored private input template/diagnostics.
- Controls: raw inbox access and mutation must remain false; public artifacts may contain aggregate counts, statuses and evidence refs only; source-map mutation, partial authorization write, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false while owner resolution input is absent.
- Current result: `private_resolution_item_count=36`, `unlinked_application_blocker_count=36`, `source_non_actionable_group_decision_count=3`, `owner_resolution_input_present=false`, `all_36_unlinked_blockers_resolved=false`, `source_map_records_applied_count=0`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate supplies 36 corrected-source or owner-exclusion resolution items.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-READINESS-001
- Version: `0.1.4-corrected-source-or-owner-exclusion-resolution-application-readiness`.
- Purpose: check whether the private 36-item corrected-source or owner-exclusion template has complete valid owner input before any source-map application is allowed.
- Inputs: v0.1.4 corrected-source or owner-exclusion resolution input public summary, public matrix, ignored private 36-item template and ignored private pending queue.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION_READINESS/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_application_readiness_manifest.json`, aggregate summary, Go/No-Go report, public-safe matrix, human evidence and ignored private readiness diagnostics.
- Controls: raw inbox access and mutation must remain false; public artifacts may contain aggregate counts, statuses and evidence refs only; source-map mutation, partial authorization write, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false while valid owner input count is 0.
- Current result: `private_resolution_item_count=36`, `private_pending_queue_count=36`, `valid_owner_input_count=0`, `missing_owner_input_count=36`, `application_blocker_queue_count=36`, `resolution_application_allowed=false`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: owner or authorized delegate fills 36 corrected-source or owner-exclusion resolution items.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-INPUT-RETRY-001
- Version: `0.1.4-corrected-source-or-owner-exclusion-resolution-input-retry`.
- Purpose: create a private delegated conservative owner-exclusion retry input package for the 36 no-match blockers before rerunning application readiness.
- Inputs: v0.1.4 corrected-source or owner-exclusion input summary, application-readiness summary, ignored private 36-item template, ignored private readiness blocker queue, and ignored private no-match dry-run evidence.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_INPUT_RETRY/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_input_retry_manifest.json`, aggregate summary, Go/No-Go report, public-safe matrix, human evidence and ignored private retry input artifacts.
- Controls: raw inbox access and mutation must remain false; public artifacts may contain aggregate counts, statuses and evidence refs only; source-map mutation, partial authorization write, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false until a later readiness/application phase.
- Current result: `private_retry_item_count=36`, `owner_exclusion_retry_item_count=36`, `corrected_source_retry_item_count=0`, `retry_input_valid_count=36`, `retry_input_missing_count=0`, `resolution_application_readiness_allowed_next_phase=true`, `resolution_application_allowed=false`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: run application readiness against the private retry template.

## FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-RETRY-APPLICATION-READINESS-001
- Version: `0.1.4-corrected-source-or-owner-exclusion-resolution-retry-application-readiness`.
- Purpose: check whether the private retry input package is application-ready for a later resolution application phase, without applying source-map records.
- Inputs: v0.1.4 retry input public summary/matrix plus ignored private retry template, retry queue and retry diagnostic.
- Outputs: `KMFA/stage_artifacts/V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_RETRY_APPLICATION_READINESS/machine/processed_value_source_map_completion_corrected_source_or_owner_exclusion_resolution_retry_application_readiness_manifest.json`, aggregate summary, Go/No-Go report, public-safe matrix, human evidence and ignored private readiness artifacts.
- Controls: raw inbox access and mutation must remain false; public artifacts may contain aggregate counts, statuses and evidence refs only; source-map mutation, partial authorization write, materialization, comparison, reconciliation, lineage, release, upload and app reinstall remain false until a later application phase.
- Current result: `private_retry_item_count=36`, `owner_exclusion_retry_item_count=36`, `corrected_source_retry_item_count=0`, `retry_application_ready_item_count=36`, `retry_application_blocker_queue_count=0`, `resolution_application_ready=true`, `resolution_application_allowed=false`, `business_value_consistency_verified=false`, `go_no_go=NO_GO`.
- Next input: run resolution application against the private retry readiness queue.
## V014 Corrected Source Or Owner Exclusion Resolution Application

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-CORRECTED-SOURCE-OR-OWNER-EXCLUSION-RESOLUTION-APPLICATION-001`
- parameter_ids: `PARAM-KMFA-1303`, `PARAM-KMFA-1304`, `PARAM-KMFA-1305`
- phase_id: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_CORRECTED_SOURCE_OR_OWNER_EXCLUSION_RESOLUTION_APPLICATION`
- version: `0.1.4-corrected-source-or-owner-exclusion-resolution-application`
- rule: private readiness queue count 36 plus owner-exclusion application count 36 produces an ignored private application result; corrected-source application count remains 0 and source-map records applied remains 0.
- gate: `NO_GO`; post-resolution readiness recheck, materialization, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private application diagnostic, result and queues stay under git-ignored runtime.

## V014 Post-Resolution Readiness Recheck

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-POST-RESOLUTION-READINESS-RECHECK-001`
- parameter_ids: `PARAM-KMFA-1306`, `PARAM-KMFA-1307`, `PARAM-KMFA-1308`
- phase_id: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_POST_RESOLUTION_READINESS_RECHECK`
- version: `0.1.4-post-resolution-readiness-recheck`
- rule: owner_exclusion_resolution_applied_count=36 closes the 36 unlinked blockers; the remaining linked blocker population yields 15 linked candidate groups and 77 source-map reapplication candidates.
- gate: `NO_GO`; source-map reapplication is ready for a later single phase, but this phase does not apply records, materialize values, compare raw-to-processed values, run reconciliation, produce a formal report, upload GitHub, reinstall the app or execute business actions.
- privacy: public artifacts contain aggregate counts and gate state only; private post-resolution diagnostic, candidate queue and blocker queue stay under git-ignored runtime.

## V014 Linked Source-Map Reapplication

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-PROCESSED-VALUE-SOURCE-MAP-COMPLETION-LINKED-REAPPLICATION-001`
- parameter_ids: `PARAM-KMFA-1309`, `PARAM-KMFA-1310`, `PARAM-KMFA-1311`
- phase_id: `V014_PROCESSED_VALUE_SOURCE_MAP_COMPLETION_LINKED_REAPPLICATION`
- version: `0.1.4-linked-source-map-reapplication`
- rule: post_resolution_reapplication_candidate_count=77 and linked_reapplication_applied_record_count=77 writes 77 private source-map records and stages 77 private materialization source-map inputs.
- gate: `NO_GO`; materialization replay, raw-to-processed comparison, reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private linked reapplication diagnostic, result, applied records, source map and materialization input stay under git-ignored runtime.

## V014 Linked-Scope Raw-To-Processed Comparison Dry Run

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-LINKED-SCOPE-RAW-TO-PROCESSED-COMPARISON-DRY-RUN-001`
- parameter_ids: `PARAM-KMFA-1318`, `PARAM-KMFA-1319`, `PARAM-KMFA-1320`
- phase_id: `V014_LINKED_SCOPE_RAW_TO_PROCESSED_COMPARISON_DRY_RUN`
- version: `0.1.4-linked-scope-raw-to-processed-comparison-dry-run`
- rule: linked_scope_dry_run_pair_count=77, exact_match_count=77, mismatch_count=0 and invalid_record_count=0 pass the linked-scope private fingerprint dry-run, but processed_target_slot_outside_linked_replay_scope_count=72 keeps full comparison incomplete.
- gate: `NO_GO`; full raw-to-processed comparison, processed-data reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private dry-run diagnostic and records stay under git-ignored runtime.

## V014 Processed Target Outside Linked-Scope Resolution

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-PROCESSED-TARGET-OUTSIDE-LINKED-SCOPE-RESOLUTION-001`
- parameter_ids: `PARAM-KMFA-1321`, `PARAM-KMFA-1322`, `PARAM-KMFA-1323`
- phase_id: `V014_PROCESSED_TARGET_OUTSIDE_LINKED_SCOPE_RESOLUTION`
- version: `0.1.4-processed-target-outside-linked-scope-resolution`
- rule: processed_target_slot_count=149, linked_scope_resolved_target_slot_count=77 and outside_linked_scope_target_slot_count=72 classify the remaining target slots outside linked replay scope; outside_scope_auto_resolvable_count=0 and outside_scope_authorized_source_map_required_count=72 block full comparison until authorized source-map extension is supplied.
- gate: `NO_GO`; source-map extension, full raw-to-processed comparison, processed-data reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private outside-scope resolution diagnostic, queue and report stay under git-ignored runtime.

## V014 Outside-Scope Authorized Source-Map Extension

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-001`
- parameter_ids: `PARAM-KMFA-1324`, `PARAM-KMFA-1325`, `PARAM-KMFA-1326`
- phase_id: `V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION`
- version: `0.1.4-outside-scope-authorized-source-map-extension`
- rule: source_outside_scope_resolution_queue_count=72 and private_authorized_extension_template_item_count=72 prepare the private intake surface; valid_authorized_extension_record_count=0 and missing_authorized_extension_record_count=72 keep source-map extension write blocked.
- gate: `NO_GO`; source-map extension write, full raw-to-processed comparison, processed-data reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private extension template, pending queue, diagnostic and report stay under git-ignored runtime.

## V014 Outside-Scope Authorized Source-Map Extension Readiness Recheck

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-AUTHORIZED-SOURCE-MAP-EXTENSION-READINESS-RECHECK-001`
- parameter_ids: `PARAM-KMFA-1327`, `PARAM-KMFA-1328`, `PARAM-KMFA-1329`
- phase_id: `V014_OUTSIDE_SCOPE_AUTHORIZED_SOURCE_MAP_EXTENSION_READINESS_RECHECK`
- version: `0.1.4-outside-scope-authorized-source-map-extension-readiness-recheck`
- rule: private_authorized_extension_template_item_count=72 and valid_authorized_extension_record_count=0 prove application readiness is not met; source_map_extension_blocker_count=72 keeps source-map application and full comparison blocked.
- gate: `NO_GO`; source-map application, full raw-to-processed comparison, processed-data reconciliation, business value consistency, lineage full check, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private readiness diagnostic, blocker queue and report stay under git-ignored runtime.
## V014 Outside-Scope Candidate Review Residual Difference Report

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-REPORT-001`
- parameter_ids: `PARAM-KMFA-1390`, `PARAM-KMFA-1391`, `PARAM-KMFA-1392`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_REPORT`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-report`
- rule: source_private_residual_queue_item_count=72 and residual_difference_report_item_count=72 produce an ignored private residual difference report; closed_discrepancy_count remains 0 and all downstream gates remain closed.
- gate: `NO_GO`; discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private residual difference diagnostic, queue and report stay under git-ignored runtime.

## V014 Outside-Scope Candidate Review Residual Difference Diagnostic Handoff

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-DIAGNOSTIC-HANDOFF-001`
- parameter_ids: `PARAM-KMFA-1393`, `PARAM-KMFA-1394`, `PARAM-KMFA-1395`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_DIAGNOSTIC_HANDOFF`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-diagnostic-handoff`
- rule: source_private_residual_difference_queue_item_count=72 and diagnostic_handoff_item_count=72 package all unresolved residual differences into ignored private diagnostic handoff artifacts; closed_discrepancy_count remains 0 and safe_auto_resolution_count remains 0.
- gate: `NO_GO`; discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private diagnostic handoff packet, queue and report stay under git-ignored runtime.

## V014 Outside-Scope Candidate Review Residual Difference Owner / Agent Diagnostic Intake

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-INTAKE-001`
- parameter_ids: `PARAM-KMFA-1396`, `PARAM-KMFA-1397`, `PARAM-KMFA-1398`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_INTAKE`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-intake`
- rule: source_private_diagnostic_handoff_queue_item_count=72, private_diagnostic_response_template_item_count=72 and pending_diagnostic_response_count=72 prove all residual differences remain pending; valid_diagnostic_response_count=0 and actionable_resolution_count=0 prevent discrepancy closure.
- gate: `NO_GO`; valid owner/agent response, discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private response template, pending queue, diagnostic and report stay under git-ignored runtime.

## V014 Outside-Scope Candidate Review Residual Difference Owner / Agent Diagnostic Readiness Recheck

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-READINESS-RECHECK-001`
- parameter_ids: `PARAM-KMFA-1399`, `PARAM-KMFA-1400`, `PARAM-KMFA-1401`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_READINESS_RECHECK`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-readiness-recheck`
- rule: source_private_diagnostic_response_template_item_count=72, source_private_diagnostic_pending_queue_item_count=72, diagnostic_response_ready_count=0 and diagnostic_response_blocker_count=72 prove all residual differences remain blocked; valid_diagnostic_response_count=0 and actionable_resolution_count=0 prevent discrepancy closure and source-map correction.
- gate: `NO_GO`; valid owner/agent response, discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private readiness diagnostic, blocker queue and report stay under git-ignored runtime.

## V014 Outside-Scope Candidate Review Residual Difference Owner / Agent Diagnostic Blocker Audit

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-BLOCKER-AUDIT-001`
- parameter_ids: `PARAM-KMFA-1402`, `PARAM-KMFA-1403`, `PARAM-KMFA-1404`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_AUDIT`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-blocker-audit`
- rule: prior_diagnostic_blocker_observation_count=1 and diagnostic_blocker_observation_count=2 record the second blocker observation; diagnostic_blocked_audit_threshold_met=false, valid_diagnostic_response_count=0 and open_residual_difference_count=72 keep discrepancy closure and source-map correction blocked.
- gate: `NO_GO`; valid owner/agent response, discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private audit diagnostic stays under git-ignored runtime and raw inbox remains untouched.

## V014 Outside-Scope Candidate Review Residual Difference Owner / Agent Diagnostic Blocker Threshold Recheck

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-BLOCKER-THRESHOLD-RECHECK-001`
- parameter_ids: `PARAM-KMFA-1405`, `PARAM-KMFA-1406`, `PARAM-KMFA-1407`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_BLOCKER_THRESHOLD_RECHECK`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-blocker-threshold-recheck`
- rule: prior_diagnostic_blocker_observation_count=2 and diagnostic_blocker_observation_count=3 meet the blocked audit threshold; valid_diagnostic_response_count=0 and open_residual_difference_count=72 keep discrepancy closure and source-map correction blocked.
- gate: `NO_GO`; valid owner/agent response, discrepancy closure, source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private threshold diagnostic stays under git-ignored runtime and raw inbox remains untouched.
## V014 Outside-Scope Candidate Review Residual Difference Owner / Agent Diagnostic Response Import

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-OWNER-OR-AGENT-DIAGNOSTIC-RESPONSE-IMPORT-001`
- parameter_ids: `PARAM-KMFA-1408`, `PARAM-KMFA-1409`, `PARAM-KMFA-1410`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_OWNER_OR_AGENT_DIAGNOSTIC_RESPONSE_IMPORT`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-owner-or-agent-diagnostic-response-import`
- rule: source template=72, source owner-authorized report=72, target slot match=72 and valid diagnostic response count=72 clear the missing-response blocker; non-actionable diagnostic response count=72, source-map actionable response count=0 and closed discrepancy count=0 keep discrepancy closure and source-map correction blocked.
- gate: `NO_GO`; source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private response import record/items/non-actionable queue/report stay under ignored runtime and raw inbox remains untouched.
## V014 Outside-Scope Candidate Review Residual Difference Response Import Readiness Recheck

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-RESPONSE-IMPORT-READINESS-RECHECK-001`
- parameter_ids: `PARAM-KMFA-1411`, `PARAM-KMFA-1412`, `PARAM-KMFA-1413`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_RESPONSE_IMPORT_READINESS_RECHECK`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-response-import-readiness-recheck`
- rule: valid_diagnostic_response_count=72 and missing_response_blocker_cleared=true prove the response gap is closed; non_actionable_diagnostic_response_count=72, source_map_correction_blocker_count=72 and closed_discrepancy_count=0 keep source-map correction and value consistency blocked.
- gate: `NO_GO`; source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private readiness diagnostic and source-map blocker queue stay under ignored runtime and raw inbox remains untouched.
## V014 Outside-Scope Candidate Review Residual Difference Source-Map Correction Blocker Audit

- model_id: `MOD-KMFA-GOV-001`
- formula_id: `FORM-KMFA-V014-OUTSIDE-SCOPE-CANDIDATE-REVIEW-RESIDUAL-DIFFERENCE-SOURCE-MAP-CORRECTION-BLOCKER-AUDIT-001`
- parameter_ids: `PARAM-KMFA-1414`, `PARAM-KMFA-1415`, `PARAM-KMFA-1416`
- phase_id: `V014_OUTSIDE_SCOPE_CANDIDATE_REVIEW_RESIDUAL_DIFFERENCE_SOURCE_MAP_CORRECTION_BLOCKER_AUDIT`
- version: `0.1.4-outside-scope-candidate-review-residual-difference-source-map-correction-blocker-audit`
- rule: valid_diagnostic_response_count=72 and missing_response_blocker_cleared=true preserve response availability; non_actionable_diagnostic_response_count=72, source_map_correction_blocker_count=72, source_map_correction_blocker_observation_count=1 and closed_discrepancy_count=0 prove source-map correction remains blocked.
- gate: `NO_GO`; source-map correction, raw-to-processed comparison, full reconciliation, formal report, GitHub upload, app reinstall and business execution remain blocked.
- privacy: public artifacts contain aggregate counts and gate state only; private source-map correction blocker audit diagnostic, queue and report stay under ignored runtime and raw inbox remains untouched.
