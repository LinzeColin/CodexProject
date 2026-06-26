# PFI-011 Local LLM Deep Path

Status: local Gate 5 evidence complete.

As of: 2026-06-20 Australia/Sydney

## Scope

PFI-011 adds a local LLM Deep Path acceptance layer for Gate 5. The goal is not
to make PFI depend on an LLM. The default path remains `DisabledProvider`, and
optional local providers may only create evidence summaries for human review.

## Implemented

- `src/pfi_os/application/pfi011_local_llm_deep_path.py`
  - `PFI011LocalLLMDeepPathContractV1`
  - `PFI011LocalLLMDeepPathAcceptanceV1`
  - `PFI011LocalLLMDeepPathReadModelV1`
  - `PFI011LocalLLMOutputV1`
  - `PFI011HardwareAuditV1`
- Provider interface with:
  - default `DisabledProvider`
  - deterministic local provider for offline acceptance
  - timeout fallback to `DisabledProvider`
- Hardware audit with no model/network probe.
- Citation-backed output schema validation.
- Prompt-injection blocking before provider call.
- Cancel proof through existing `DurableJobStore`.
- Resource budget checks for prompt/context size.
- Operational Store source/evidence/task records.
- Web Shell runtime exposure through `workflow_runtime.local_llm_deep_path`.
- User-facing Web Shell wording is Chinese-first: the runtime card shows
  `本地模型`, `本地模型深度路径`, `模型 外部模型未启用`, `校验通过`,
  and `提示注入防护通过` instead of raw provider/schema/debug labels.

## Verification

```bash
python -m pytest tests/contract/test_pfi011_local_llm_deep_path.py -q
scripts/pfi011LocalLLMDeepPathAcceptance.sh --summary-json
```

Observed:

- PFI-011 contract: 7 passed.
- User-facing Web Shell/static repair: 21 passed for PFI-011 plus Shell
  static-flow tests.
- Browser UI acceptance after the rejection repair:
  - `status=Pass`
  - `pass=134`
  - `fail=0`
  - screenshot: `data/systemAudit/UIVisualAcceptance_20260620_063836.png`
- Acceptance script:
  - `status=Pass`
  - `pass=12`
  - `fail=0`
  - `hardware_status=Pass`
  - `schema_validation=Pass`
  - `citation_validation=Pass`
  - `citation_count=3`
  - `timeout_fallback=Pass`
  - `cancel=Pass`
  - `resource_budget=Pass`
  - `prompt_injection=Pass`
  - `disabled_provider_fallback=Pass`

## Boundaries

- Default model provider is `DisabledProvider`.
- Local model is optional and never blocks core workflows.
- No network probe is performed during acceptance.
- No provider fetch, broker call, order execution, payment, betting, or
  autonomous advice path is created.
- All generated text remains evidence-summary material requiring human review.

## Remaining Release Work

- Re-run PFI-011 during Gate 7 final packaging.
- If a real local provider is configured later, add provider-specific hardware
  and latency evidence without making it required for core PFI workflows.
