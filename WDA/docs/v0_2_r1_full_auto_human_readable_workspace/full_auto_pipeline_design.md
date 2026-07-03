# Full-Auto Pipeline Design

## Current Automation

- New computer: one command regenerates local dashboard and Chinese reports from
  the existing local SQLite seed and analysis outputs.
- Local reports are full-sensitive and stay under WDA_MetaData.

## Full-Coverage Target

- Old computer: one command performs all-conversation export with chunking,
  checkpointing, resume, checksums, and failure logs.
- New computer: one command validates transfer bundle, imports into local Data
  Core, runs deterministic analysis, and generates Chinese reports.

## Boundary

This sprint does not run the old-computer exporter and does not claim full
coverage has already been produced.
