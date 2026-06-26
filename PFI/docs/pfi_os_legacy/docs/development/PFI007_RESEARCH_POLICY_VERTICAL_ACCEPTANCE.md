# PFI-007 Research + Policy Vertical Acceptance

Last updated: 2026-06-20 Australia/Sydney

PFI-007 advances Gate 3 for the Research + Policy vertical slice. The
acceptance goal is a local, review-only chain from curated policy opportunities
and report decision payloads into citation locator, report manifest, UI read
model, Operational Store evidence, human-review task, and rollback proof.

## Scope

- Workspace: `研究`.
- Schema: `PFI007ResearchPolicyVerticalAcceptanceV1`.
- UI read model: `PFI007ResearchPolicyUIReadModelV1`.
- Source mode: deterministic local Golden fixture.
- Storage mode: temporary Operational Store only.
- Safety: research-only, no live policy scraping, no government portal action,
  no legal/tax advice, no broker/order execution, no private holdings.

## Acceptance Chain

`src/pfi_os/application/pfi007_research_policy_acceptance.py` proves:

- Data chain: reviewed policy opportunities and report decision payloads ->
  `PFIOSPolicyIntelligenceRadarV1` plus `PFIOSReportEvidenceGapTasksV1`.
- Domain chain: policy authority, policy opportunity, and research evidence-gap
  cards plus review-only decision object.
- API/read-model chain: `PFI007ResearchPolicyUIReadModelV1` exposes the
  research route, primary feature view, cards, citation locator, report
  manifest, review queue, and decision fields.
- UI chain: Web Shell has same-shell Chinese panels for `研究与政策垂直切片`,
  `引用定位`, and `报告清单`.
- Citation locator: official policy citations have source type, source URL or
  evidence path, authority status, linked cards, and manual-review requirement.
- Report manifest: NeedsMoreEvidence report rows are grouped with metadata path,
  source report, evidence gaps, and validation task ids.
- Evidence/task chain: source, evidence, completed job, and human-review task
  records are written to Operational Store.
- Golden metrics: workflow id, policy record count, authoritative source count,
  official citation count, report gap count, report manifest count, confidence,
  and target weight change are deterministic.
- Rollback proof: temporary source/evidence/job/task rows are deleted and
  residue counts are zero.

## Runtime Evidence

Current local run:

```bash
scripts/pfi007ResearchPolicyAcceptance.sh --summary-json
```

Observed:

- `status=Pass`
- `pass=14`
- `fail=0`
- `policy_record_count=2`
- `official_citation_count=1`
- `report_gap_count=3`
- `report_manifest_count=1`
- `rollback_status=Pass`
- Focused Research/Policy/Web Shell contracts: 62 passed.
- Target gate: 58 passed, secret scan passed.
- UI visual acceptance after Web Shell research changes: 98 passed, 0 failed.
- `git diff --check`: passed.

## Verification Commands

```bash
python -m pytest tests/contract/test_pfi007_research_policy_vertical_acceptance.py -q
scripts/pfi007ResearchPolicyAcceptance.sh --summary-json
python -m pytest tests/contract/test_phase_b_research_policy_workflow.py tests/contract/test_pfi007_research_policy_vertical_acceptance.py -q
python -m pytest tests/contract/test_pfi_web_shell_contract.py tests/e2e/test_pfi_web_shell_static_flow.py tests/test_scripts.py -q
scripts/pfiGate.sh target
git diff --check
```

## Stop Condition

PFI-007 is locally closed when the PFI-007 contract tests pass, the acceptance
script returns `status=Pass`, target gate remains green, and GitHub CI passes.
With PFI-006 through PFI-009 now covered by local vertical acceptances, Gate 3
is closed for the current evidence scope and must be re-run in the final Gate 7
release package.
