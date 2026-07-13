# packages/ingestion

Connector interfaces and source-specific ingestion adapters live here.

Gate: G7
Acceptance IDs: A096-A107

T706 provides a combined SEC connector smoke:

- default `fixture` mode uses only `httpx.MockTransport`, exercises 503/429 retry,
  validates the governed User-Agent/host boundary, and finishes with a zero-write dry-run;
- optional `live` mode requires `--allow-live-network`, an explicit CIK and a validated
  `SEC_USER_AGENT`; it fetches and normalizes only, with no database write or publication;
- neither mode closes A202, A209 or MVP release readiness.
