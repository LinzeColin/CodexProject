# Memory Security Threat Model

`TSK.OpenAIDatabase.PAM1.0012 / ACC.OpenAIDatabase.PAM1.0012` defines a
fail-closed boundary for untrusted memory inputs and privileged GitHub Actions.

## Trust boundaries

- Raw evidence, pull-request titles and bodies, and external documents are
  `data_only`. They never acquire system/developer authority and are never
  executed as commands.
- `memory_security.py` applies NFKC prompt-injection checks, the existing
  credential-pattern rules, and a conservative high-entropy token detector.
  Rejections expose stable reason codes and counts only; suspected values are
  absent from exceptions, reports, and logs.
- The raw importer runs the security gate before sanitization, splitting, or
  writes. Unsafe paths, symlinks, archives, invisible/bidi controls, injection,
  and suspected credentials therefore fail before any raw artifact exists.

## Privileged workflow and supply-chain boundary

The canonical root `workflow_security_audit.py` remains the single workflow
parser and policy owner. It proves every third-party Action reference is an
allowlisted full commit SHA with a resolution source. The Settlement role uses
the trusted default-branch workflow definition and live GitHub APIs only; it
does not check out pull-request code or consume pull-request artifacts/caches.

GitHub documents pull-request text and similar context as potentially
untrusted input, recommends full-length commit SHA pinning for Actions, and
warns that privileged `workflow_run` / `pull_request_target` workflows must not
execute untrusted code or trust untrusted artifacts or caches:

- https://docs.github.com/en/actions/concepts/security/script-injections
- https://docs.github.com/en/actions/reference/security/secure-use
- https://docs.github.com/en/actions/reference/security/securely-using-pull_request_target

## Incident response and non-goals

If a real credential is discovered, stop normal development, revoke and rotate
it first, preserve only non-secret evidence, and open a separately authorized
Git-history remediation task. This task never rewrites public history
automatically. The bounded ten-case fixture is a regression gate, not the full
160-case Gold benchmark owned by PAM1.0013/PAM1.0014.
