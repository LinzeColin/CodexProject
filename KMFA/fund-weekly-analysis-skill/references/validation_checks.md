# Validation Checks

Blocking checks:

* `check_source_readiness.py` returns `READY` before extraction or Excel production starts.
* Required files and input directory exist.
* Missing configured input folder returns `SOURCE_MISSING` and does not read alternate private sources unless a separate explicit materialization step is run.
* Existing configured input folder with unreadable/cloud-only files returns `SOURCE_UNREADABLE` and does not write an Excel package.
* Source materialization dry-run creates no target files; apply copies missing files only, skips identical files, fails on conflicting existing targets, and returns `SOURCE_UNREADABLE` when OneDrive source files are cloud-only/dataless, bad zip, or otherwise unreadable.
* ZIP source materialization must be explicit via `--source-zip` and group-scoped via `--zip-prefix 付款请示群`; it must not copy other DingTalk groups or unsafe path members.
* ZIP source materialization accepts both `付款请示群/...` and `DWS_Outputs/付款请示群/...` member layouts when the operator passes `--zip-prefix 付款请示群`; relative output paths must strip the group/container prefix.
* `INDEXED_PENDING_EXTRACTION` outputs do not contain generated financial amounts, forecasts, or management conclusions.
* `kmfa_metadata_signals.csv` may carry only public-safe KMFA metadata signals and must keep all formal action / management conclusion gates false.
* `screenshot_ocr_coverage.csv` must include every screenshot evidence row and show whether a real OCR text sidecar exists; missing sidecars must stay `ocr_text_sidecar_missing`, `financial_fact_promoted=false`, and must not populate `fund_ledger.csv`.
* `screenshot_ocr_sidecar_generation_plan.csv`, summary JSON, and generated Vision OCR text sidecars may be written only under private runtime. Empty OCR output must not create a sidecar; successful rows must be append/resume safe and keep `financial_fact_promoted=false`; generated sidecars must not populate `fund_ledger.csv`.
* `ocr_text_candidates.csv` may carry only adjacent real OCR text sidecars or private Vision OCR sidecars linked by `screenshot_ocr_sidecar_generation_plan.csv`; all rows must stay pending review with `financial_fact_promoted=false`.
* `ocr_value_candidates.csv` may carry only date/amount candidates parsed from `ocr_text_candidates.csv`; all rows must stay pending review with `financial_fact_promoted=false` and must not populate `fund_ledger.csv`.
* `ocr_financial_fact_candidates.csv` may carry only conservative OCR-derived company/category/bank/amount candidates with source evidence and OCR text path; all rows must stay pending review with `financial_fact_promoted=false` and must not populate `fund_ledger.csv`.
* `ocr_fact_cross_review.csv` must summarize OCR fact candidates by metric for human cross-review only; every row must keep `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `review_status=pending_human_cross_review`.
* `ocr_fact_ledger_staging_preview.csv` must map OCR fact candidates into ledger-like review rows only; every row must keep `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `review_status=pending_human_ledger_staging_review`.
* `ocr_fact_review_apply_gate.csv`, `ocr_fact_review_authorization_template.json`, and `ocr_fact_review_authorization_preview.csv` must be validation-only. The template must default every authorization row to `authorized=false`; even a valid private `ocr_fact_review_authorizations/<run_id>.json` must keep `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `generated_financial_amount_count=0`.
* `chat_text_candidates.csv` may carry only real DingTalk `chat_records.csv` content/quoted_content rows with finance signals; all rows must stay pending review with `financial_fact_promoted=false`.
* `chat_value_candidates.csv` may carry only date/amount candidates parsed from `chat_text_candidates.csv`; all rows must stay pending review with `financial_fact_promoted=false` and must not populate `fund_ledger.csv`.
* `chat_evidence_links.csv` may carry only links from chat candidates to real `_manifest/manifest.csv` resource rows and evidence index rows; all links must stay pending review with `financial_fact_promoted=false` and must not populate `fund_ledger.csv`.
* `attachment_evidence_reconciliation.csv` must reconcile real `_manifest/manifest.csv` resource rows against evidence index rows; missing output paths, missing evidence, and SHA mismatches must create blocking exception tasks and must not populate `fund_ledger.csv`.
* `attachment_reconciliation_remediation.csv` must contain only operator actions derived from blocking attachment reconciliation rows; all rows must keep `automation_safe=false` and `formal_fact_allowed=false`.
* `attachment_remediation_dry_run.csv` must contain only dry-run assessments of attachment remediation rows; all rows must keep `safe_to_apply=false`, `apply_performed=false`, and `formal_fact_allowed=false`.
* `attachment_repair_plan.csv` must contain only plan-only steps derived from dry-run rows; all rows must keep `operator_confirmation_required=true`, `source_mutation_allowed=false`, `apply_performed=false`, and `formal_fact_allowed=false`.
* `attachment_repair_apply_gate.csv` must contain only fail-closed apply gate rows derived from repair plan rows; without a separate private operator authorization manifest, all rows must keep `operator_authorization_present=false`, `apply_allowed=false`, `source_mutation_allowed=false`, `apply_performed=false`, and `formal_fact_allowed=false`.
* `attachment_repair_authorization_template.json` is a private draft generated in the run directory. It must default every `repair_plan_authorizations[].authorized` value to `false`, keep `source_mutation_allowed=false` and `apply_execution_allowed=false`, and must not change `attachment_repair_apply_gate.csv` apply status.
* Private `attachment_repair_authorizations/<run_id>.json` manifests are validation-only. The accepted schema must include `authorization_manifest_version=1`, matching `run_id`, `authorization_scope=attachment_repair_plan_validation_only`, `source_mutation_allowed=false`, and `apply_execution_allowed=false`; even rows with `authorization_validation_status=valid_manifest_validation_only` must keep `apply_allowed=false` and `apply_performed=false`.
* `attachment_repair_authorization_preview.csv` must be derived from `attachment_repair_apply_gate.csv` only. It may mark valid manifest rows as `ready_for_operator_review_no_apply`, but all rows must keep `apply_allowed=false`, `source_mutation_allowed=false`, `apply_performed=false`, and `formal_fact_allowed=false`.
* `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW` outputs contain only amounts parsed from real structured CSV rows with the required column contract and still keep `management_conclusion_allowed=false`.
* `funding_forecast.csv` may contain only known due-date projections from real structured CSV risk/opportunity rows, including tax, deposit, loan, and project-cost flows, and must keep `management_conclusion_allowed=false`.
* `cashflow_validation.csv` must validate balance continuity, operating cashflow effect, and internal-transfer exclusion; continuity failures must create exception tasks and keep `management_conclusion_allowed=false`.
* `workbook_quality_checks.csv` must be emitted for generated workbooks and must cover sheet order, hidden sheets, visible row 2 cleanup, chart dimensions, formula error markers, and visible sensitive-value patterns.
* `goal_completion_audit.csv` must be emitted for successful output packages and must show `no_hallucinated_data=pass`, while formal fact promotion and management conclusions remain blocked unless explicit review gates pass.
* `management_conclusion_gate.csv` must be emitted for successful output packages and must keep every `management_conclusion_allowed=false` until source readiness, workbook quality, formal fact promotion execution, formal ledger population, cashflow validation, evidence cross-review, and automation checks all pass.
* `owner_action_queue.csv` must be emitted for successful output packages and must contain only pending owner/external-check actions derived from blocking management gates. Every row must keep `automation_safe=false`, `source_mutation_allowed=false`, `fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`.
* `fact_promotion_review_packet.csv` must be emitted for successful output packages; every row must keep `fund_ledger_write_allowed=false` and `financial_fact_promoted=false` until explicit owner authorization and review gates pass.
* `fact_promotion_authorization_template.json` must be emitted for successful output packages as a draft only. It must default every `review_packet_authorizations[].authorized` value to `false`, use `authorization_scope=fact_promotion_review_packet_validation_only`, and keep `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, and `management_conclusion_allowed=false`.
* `fact_promotion_authorization_preview.csv` must be emitted for successful output packages. It may validate private `fact_promotion_authorizations/<run_id>.json` rows as `valid_manifest_validation_only`, but every row must keep `financial_fact_promotion_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* `fact_promotion_execution_gate.csv` must be emitted for successful output packages. It may mark rows as `ready_for_controlled_fact_promotion_execution` only when owner authorization is valid and the review area has no blockers, but every row must keep `fact_promotion_execution_allowed=false`, `fund_ledger_write_allowed=false`, `financial_fact_promoted=false`, and `management_conclusion_allowed=false`.
* `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW` workbooks contain the same parsed facts in hidden `H01/H03/H05`, homepage KPI cards, `02_资金趋势预测`, and visible flow/risk/matrix sheets; native chart files remain present.
* No production table contains `sample`, `demo`, `fake`, `synthetic`, or `模拟` data markers.
* Workbook sheets exactly match the required visible/hidden order.
* Hidden sheets are hidden.
* Formula error scan returns zero matches.
* Every management KPI can be traced to a ledger/evidence row.
* Balance continuity formula difference is within 0.01 or exceptioned.
* Internal transfer净化 was applied before operating cash flow summaries.
* T0 cash,票据/电子汇票,理财,保证金,总资金 are displayed separately.
* Tax version conflicts are flagged.
* Personal/secret fields are absent from visible management sheets.
* Chart type is line for 首页/趋势; chart dimensions are <= 1728 x 864 px.
* No visible chart/table overlaps another visible element.

Non-blocking warnings:

* Account alias has low confidence.
* Company-bank matrix contains `待识别` rows.
* Evidence grade C/D supports a management clue.
* OCR confidence below threshold.
