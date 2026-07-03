# Live Environment Requirement

## Finding

Most automated WeChat acquisition routes depend on the live WeChat environment
because public tool documentation commonly references process-memory key
discovery, a running client, local database roots, or app-specific runtime
access.

## Device Implication

- Old computer: highest-value WeChat data source and likely required execution
  environment for acquisition if its live WeChat profile is the target.
- New computer: WDA Control Plane, validation host, future RAG/Web/database host,
  and destination for approved output artifacts.

## Trial Implication

The first real acquisition trial should run on the old computer if the target
data is the old-computer WeChat account/cache. The new computer should not try
to reconstruct acquisition from copied protected DBs because Sprint 2B-B already
showed that the copied candidates are not plain SQLite-readable under the safe
path.

## Hard Drive

The external hard drive is not required for Sprint 2G. It should not be accessed
for this planning sprint.

