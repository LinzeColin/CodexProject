# Next v0.1-B Analysis Layer Plan

## Recommended Next Step

Build a local-only analysis layer over the v0.1-A seed database.

## Allowed Scope

- read only `/Users/linzezhang/Downloads/WDA_MetaData/v0_1/data_core_seed/wda_v0_1_seed.sqlite`
- produce aggregate counts and schema-safe summaries
- validate subject, conversation, sender, timestamp, and message-type coverage
- keep raw message text local and out of Git

## Still Forbidden

- no WeChat exporter tools
- no external hard drive
- no full export
- no media path handling
- no RAG/Web/Matrix
- no ChatGPT Pack using raw messages
- no upload

## Stop Conditions

Stop if the next sprint needs unbounded raw data, media files, raw-message
packaging, or a full Raw Gate Go claim.
