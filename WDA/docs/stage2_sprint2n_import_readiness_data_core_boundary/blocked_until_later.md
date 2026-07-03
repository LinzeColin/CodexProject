# Blocked Until Later

The following remain blocked after Sprint 2N:

| Area | Status | Why blocked |
|---|---|---|
| full export | blocked | only a bounded 500-row first-batch pack is validated |
| media paths | blocked | 2M-B uses `include_media_paths=false`; media index has zero rows |
| RAG | blocked | Data Core seed does not yet exist and broader import readiness is not proven |
| Web | blocked | no Data Core serving contract or UI scope is approved |
| Matrix | blocked | no matrix data model or full subject coverage exists |
| ChatGPT Pack using raw messages | blocked | raw-message packaging would expose private content and is not approved |
| production import | blocked | only local bounded validation is proven |

Sprint 2O may create a local Data Core seed only. It must not start any blocked
area listed above.

