# Route Options Matrix

Generated: 2026-07-03T09:04:48+10:00

| Route | Feasible now? | Needs hard drive? | Safety fit | Expected output | Decision |
|---|---:|---:|---|---|---|
| R1: Owner-provided readable export/artifact contract | Yes, as planning | Depends on where artifact is stored | Strong if owner supplies explicit readable data without bypass/decrypt | A future approved import contract for a readable message artifact | Recommended next route. |
| R2: Official or user-authorized export path | Yes, as planning | Depends on export location | Strong if produced by user-controlled app/export flow without third-party decrypt tools | Candidate readable export package plus manifest | Recommended fallback. |
| R3: Metadata-only WDA planning | Yes | No | Safe but cannot power message RAG/Web/Matrix | Product scope, UI shells, governance, import interface contracts | Allowed, but does not open Raw Gate. |
| R4: Rebuild minimal candidate bundle from APFS | Only if current local bundle is lost/stale | Yes | Safe only with read-only mount and same exclusions | Refreshed local candidate bundle | Not needed now. |
| R5: Retry plain SQLite schema probe on current bundle | Yes | No | Safe but low ROI after 91/91 failures | Repeated negative result unless tooling changes | Not recommended now. |
| R6: SQLCipher/decrypt/key extraction route | No | Maybe | Violates current rules | Would require forbidden methods | Rejected. |
| R7: Third-party WeChat export/decrypt tool | No | Maybe | Violates current rules | Tool-derived raw export | Rejected. |
| R8: Copy entire old WeChat cache | No | Yes | Too broad and high-cost | Large raw cache copy | Rejected/not recommended. |

Decision summary: choose R1 first, R2 as fallback, and keep R3 available for non-data-dependent WDA planning. Do not execute any route in Sprint 2B-C.
