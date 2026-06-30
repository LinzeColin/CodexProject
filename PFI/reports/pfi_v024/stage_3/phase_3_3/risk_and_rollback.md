# Stage 3 Phase 3.3 Risk and Rollback

## Scope

This phase only validates navigation behavior in a real browser. It does not
modify app bundles, launcher C/Info.plist, financial data logic, formulas,
metrics, or user data.

## Risks

- Browser validation depends on the bundled Codex Playwright runtime being
  available through `NODE_PATH`.
- The validation script starts an ephemeral localhost static server; a local
  port collision should be avoided by binding port `0`.
- Phase 3 is candidate complete after this phase, but it is not Stage 3
  complete until whole-stage review runs in a separate gate.
- GitHub main upload is intentionally deferred until the Stage 3 review and
  any review fixes complete.

## Rollback

Revert the Phase 3.3 commit or remove the changed files listed in
`changed_files.txt`. This rolls back only the browser validation script,
Phase 3.3 contract, tests, evidence, and status documentation.
