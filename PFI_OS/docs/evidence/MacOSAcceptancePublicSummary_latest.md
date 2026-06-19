# PFI_OS macOS Public Acceptance Summary

- Schema: `PFIOSMacOSPublicAcceptanceSummaryV1`
- Status: `Pass`
- Generated at: `2026-06-17T08:30:19Z`

## Evidence Sources

| Source | Status | Raw schema | Generated at | Pass/Fail |
| --- | --- | --- | --- | --- |
| MacOSRuntimeAcceptance_latest.json | Pass | PFIOSMacOSRuntimeAcceptanceV1 | 2026-06-16T18:59:28 | 10/0 |
| UIVisualAcceptance_latest.json | Pass | PFIOSUIVisualAcceptanceV1 | 2026-06-17T08:12:44.488Z | 16/0 |

## Coverage

| Gate | Status | Evidence |
| --- | --- | --- |
| App open runtime acceptance | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Local health after app start | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Cache delete refusal while running | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Stop command and post-stop health | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Post-stop cache dry-run | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Rendered PFI_OS workspace | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| macOS lifecycle panel visible | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Runtime evidence visible in UI | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Lifecycle action buttons visible | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| No visible runtime errors | Pass | sanitized pass/fail only; raw local evidence stays gitignored |
| Screenshot captured | Pass | sanitized pass/fail only; raw local evidence stays gitignored |

## Privacy Boundary

- Raw local JSON evidence, screenshots, browser executable paths, process IDs, absolute project paths, and runtime logs stay local.
- This summary is safe to commit because it only stores schemas, statuses, counts, gate names, and sanitized evidence.

## Heavy Smoke Policy

This public summary is generated from existing local evidence only. It does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, market refresh, broker connections, orders, payments, or holdings writes.
