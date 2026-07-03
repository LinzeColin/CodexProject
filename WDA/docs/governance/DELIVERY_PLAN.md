# WDA Delivery Plan

## Current Delivery State

WDA v0.2-R3 P1 has a locally verified app/API/dashboard/update skeleton. It is usable as a local control surface, but full product-grade report v2 and UX hardening remain open.

## Active Stage

`WDA-V0.2-R3 Desktop Realtime Frontend`

1. P1: local runtime, FastAPI service, dashboard, launcher, manual update, scheduler scripts. `completed`
2. P2: report v2 rewriting, evidence drill-down, responsive/detail UX hardening, final acceptance audit. `planned`

## Stop Conditions

- External drive access is required for frontend/runtime work.
- WeChat exporter is run without explicit approval.
- Raw/private data is committed to Git.
- Local launcher cannot open the frontend.
- FastAPI status/update paths cannot be verified.

## Default Next Step

Execute `WDA-V0.2-R3-P2` only after confirming the desired depth of report rewriting and evidence drill-down.
