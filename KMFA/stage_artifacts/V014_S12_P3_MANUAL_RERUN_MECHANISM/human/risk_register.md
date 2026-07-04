# v0.1.4 S12-P3 Risk Register

| Risk | Control |
| --- | --- |
| Blocked preview is accidentally rerun | Validator requires invalidation, rerun, and consistency records to cover only preview-passed events |
| Old derived outputs are overwritten | Rerun step records require old versions retained and new versions appended |
| Stage review or upload is implied too early | Phase boundary keeps Stage 12 review and GitHub upload false |
| Public evidence leaks protected business data | Public evidence validator rejects private tokens, native file suffixes, and source payload markers |
