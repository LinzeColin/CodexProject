# Hard Drive Usage Matrix

Generated: 2026-07-03T09:04:48+10:00

Sprint 2B-C hard drive requirement: **not required**.

Sprint 2B-C external drive access: **none**.

| Step | Needs external hard drive? | Reason | Decision |
|---|---:|---|---|
| Sprint 2B-C route decision | No | Uses existing repo reports only. | Complete in this run. |
| Re-read Sprint 2 / 2B reports | No | Reports are committed under WDA docs. | Allowed. |
| Re-run Sprint 2B-B schema-only probe from the local copied bundle | No | The local bundle is already isolated from the APFS source. | Allowed only if needed. |
| Verify local bundle manifest/checksums | No | Uses local copied bundle and repo checksum file. | Allowed only if needed. |
| Rebuild the candidate bundle from the authoritative APFS source | Yes | Requires the source sparseimage. | Do not run in Sprint 2B-C. |
| Copy a new minimal candidate bundle from APFS | Yes | Requires source access and must repeat read-only/source-write safeguards. | Future approved run only. |
| Import owner-provided readable message artifact | Depends | No drive needed if the artifact is provided locally; drive needed only if the owner stores it there. | Recommended future route, not executed here. |
| Copy the entire old WeChat cache | No as a recommendation | Too broad; not needed for the current safe route. | Not recommended. |
| Decrypt or bypass protected stores | Not applicable | Forbidden regardless of drive availability. | Rejected. |
