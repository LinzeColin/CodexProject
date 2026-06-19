# Security Policy

## Hard Boundaries

- Never automate ChatGPT login, export download, saved-memory editing, browser profile access, or cookie/session extraction.
- Never commit raw `OpenAI-export.zip`, nested export ZIPs, unredacted full messages, API keys, passwords, private keys, cookies, session tokens, or `.env`.
- Never run CI against the user's real raw export.
- Never expose `secret` content through search, fetch, or MCP.
- Never upload plaintext high-risk secrets to GitHub, even when downstream finance/trading agents may need the credential. Store discoverable `secret_ref` metadata instead.

## Redaction

Redact before writing user-authored snippets into reports. Detect at minimum:

- OpenAI API keys
- GitHub tokens
- AWS access keys
- private key blocks
- bearer tokens
- password/credential assignments
- session/cookie hints
- email and phone-like PII

Reports may contain short redacted snippets and source references, but not full raw messages.

## Secret References

For credentials needed by finance, trading, automation, or other agents:

- Commit only a redacted `secret_ref`, purpose, agent/workflow scope, required approval, and local resolver hint.
- Do not commit the plaintext value, decrypted archive, key file, broker credential, API key, session token, or `.env`.
- Mark secret references as sensitive or secret and keep them out of normal personalization.
- A future agent may use a `secret_ref` only to ask the user or local secret resolver for authorization; it must not infer or reconstruct the secret from memory records.
- For trading or broker access, fail closed unless the user has explicitly authorized the concrete action in the current workflow.

## Archive

If archiving raw ZIPs, encrypt locally first. Store encryption keys outside tracked files, normally in `.local_keys/`, and ensure `.gitignore` excludes that directory.

If encryption is unavailable, record a fail-closed archive status in the run manifest instead of copying raw ZIPs into a tracked location.

## Review Gate

Generated candidates are not active memories. They remain `review_status = pending` until the user accepts or edits them.
