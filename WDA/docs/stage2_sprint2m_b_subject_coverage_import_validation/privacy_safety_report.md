# Privacy Safety Report

## Local Sensitive Handling

- Full-sensitive bounded JSONL was read locally for validation accuracy.
- Local full-sensitive Raw Import Pack was written only under WDA_MetaData.
- No raw messages, contacts, transfer bundle, keys, decrypted DBs, or Raw Import
  Pack files are committed to Git.
- Repo-safe docs contain counts, schemas, hashes, field mappings, and decisions
  only.

## Forbidden Actions Check

| Action | Status |
|---|---|
| upload raw data | not performed |
| run WeChat exporter tools on new computer | not performed |
| access external hard drive | not performed |
| run RAG/Web/Matrix | not performed |
| expand beyond 2M-A bounded sample | not performed |
| include media paths or media DB handling | not performed |
| reintroduce `李晶工作交接` as subject | not performed |

The raw-sensitive output root remains local and outside Git:

`/Users/linzezhang/Downloads/WDA_MetaData/stage2_outputs/sprint2m_b_subject_coverage_import_validation/`
