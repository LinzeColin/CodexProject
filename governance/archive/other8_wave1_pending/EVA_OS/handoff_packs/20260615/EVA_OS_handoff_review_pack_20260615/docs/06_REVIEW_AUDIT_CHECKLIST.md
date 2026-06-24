# EVA_OS 审核评估清单

This file is intended for ChatGPT, reviewers, and developers auditing the system.

## Review Objectives

1. Check whether current scope and safety boundaries are clear.
2. Identify implementation gaps before product claims.
3. Prioritize high-ROI next development tasks.
4. Reduce token/context cost for future agents.
5. Confirm public GitHub boundary is safe.

## Product Review Checklist

| Area | Question | Current Evidence | Review Result |
| --- | --- | --- | --- |
| Naming | Is every visible product name `EVA_OS`? | Last scan reported zero deprecated-name residue | Pending reviewer confirmation |
| User entry | Can users launch the app easily? | Desktop, Downloads, Applications app entries | Pending live user test |
| Core value | Does the system support actual research decisions? | Backtest, reports, evidence, command center | Partial |
| Safety | Does the system prevent live execution risk? | README and docs prohibit real trading/payment | Good, keep monitoring |
| Evidence quality | Are conclusions evidence-backed? | Evidence levels exist, but real inputs are incomplete | Needs improvement |
| Test health | Are checks repeatable? | 28 focused tests passed; full suite not claimed | Needs full env |
| Data privacy | Is public GitHub safe? | Upload manifest excludes private paths | Review before every push |

## Code Review Checklist

| Area | What to Check |
| --- | --- |
| Schema stability | `EVAOS*` schema names and generated data compatibility |
| Streamlit app size | `src/quantlab/app/streamlit_app.py` is very large; avoid broad edits |
| Script runtime | Scripts should consistently support `.venv`, `QUANTLAB_PYTHON`, or documented fallback |
| Data paths | Avoid hard-coded historical paths |
| External requests | 52ETF and provider calls should be cached, source-logged, and fail closed |
| Generated artifacts | Avoid committing private, large, or stale generated outputs |
| Tests | Add target tests for any changed subsystem |

## Security and Privacy Checklist

| Risk | Required Rule |
| --- | --- |
| Secrets | Never commit `.env`, API keys, tokens, passwords |
| Holdings | Do not upload private holdings or account-derived raw files |
| Runtime DB | Do not upload SQLite runtime state unless explicitly sanitized |
| Logs | Do not upload local logs, pids, locks |
| Broker execution | No real order submission without explicit future authorization and separate approval design |
| User content | Treat local screenshots/videos/imports as private |

## Acceptance Criteria for “Productized”

A subsystem can be called productized only when:

- it has clear user purpose and workflow;
- it has documented input schema;
- it has source/evidence logging;
- it has missing-data handling;
- it has generated outputs in JSON/CSV/MD/PDF where appropriate;
- it has focused tests;
- it has UI or CLI access;
- it has risk boundaries;
- it appears in Command Center status;
- it has a meaningful user-facing interpretation, not just raw data.

## Suggested Reviewer Output Format

Ask ChatGPT or another reviewer to return:

1. Top 10 risks.
2. Top 10 high-ROI improvements.
3. Which subsystem to do next and why.
4. What should not be built yet.
5. Any misleading wording in docs.
6. Minimum test gate before next GitHub push.
