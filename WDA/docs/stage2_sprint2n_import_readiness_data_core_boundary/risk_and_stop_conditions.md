# Risk And Stop Conditions

## Risks

- Treating bounded 500-row evidence as full Raw Gate Go.
- Accidentally committing raw JSONL, contacts, transfer bundles, or SQLite DBs.
- Creating a database under the repo instead of WDA_MetaData.
- Introducing media handling despite `media_index.csv` being header-only.
- Starting RAG/Web/Matrix before Data Core readiness is proven.

## Sprint 2O Stop Conditions

Stop Sprint 2O if:

- input row counts differ from `500/5/23/0`
- checksum validation fails
- database output path is inside Git
- media references are non-empty
- the task tries to run exporter tools
- the task tries to access the external hard drive
- the task expands beyond the Sprint 2M-B bounded pack
- raw content would be committed or uploaded
- RAG/Web/Matrix work is requested before the Data Core seed gate

## Rollback

Delete only the local Sprint 2O output folder if database creation fails:

`/Users/linzezhang/Downloads/WDA_MetaData/data_core/sprint2o_minimal_seed/`

Do not modify the Sprint 2M-B Raw Import Pack during rollback.

