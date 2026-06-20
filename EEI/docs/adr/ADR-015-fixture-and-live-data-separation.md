# ADR-015 - Fixture and Live Data Separation

Status: Accepted
Date: 2026-06-19

## Decision

Every record must carry source mode or dataset classification:

- `fixture`
- `curated_official_fixture`
- `dry_run`
- `live`

UI and API cannot present fixture records as live facts. Mixed views must label source mode and coverage.

## Acceptance IDs

A025, A067, A096, A097, A098, A099, A100, A101, A102, A103, A104, A105, A106, A107, A202

## Consequences

Synthetic Golden Vertical scenarios can be used for tests and demos, but they cannot become production evidence.

Curated official anchors are not synthetic, but they are still separated from
live facts through `record_mode = 'curated_official_fixture'`. UI/API layers
must expose this mode and must not display those anchors as live relationships.
