# Agent Loop ROI policy

The former workflow-owned paid Codex implementation loop is retired. Current
Automation C keeps repository automation narrow:

- the compatibility workflow performs Task Pack validation only;
- implementation and validation happen in an isolated external workspace;
- one explicit external publisher creates one PR;
- required CI is read-only;
- settlement is API-only and deterministic.

This removes repeated paid calls, autofix loops, artifact reruns, and Issue
state churn from the trusted GitHub path. A failed transaction must be diagnosed
from its required-check result and bounded local evidence before a fresh branch
is published.

Any future workflow-owned model execution, planner, review, or autofix requires
a separate approved Task Pack with a call budget, threat model, credential
boundary, deterministic stop conditions, and regression tests. It is not
implicitly enabled by legacy Task Pack fields such as `max_paid_codex_calls`,
`executor_mode`, or `roi_budget_usd`.
