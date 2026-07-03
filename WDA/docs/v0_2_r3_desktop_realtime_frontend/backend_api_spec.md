# Backend API Spec

Base URL: `http://127.0.0.1:18730`

## Routes

```text
GET  /
GET  /system
GET  /reports/{report_id}
GET  /api/health
GET  /api/status
POST /api/update/run
GET  /api/update/runs
GET  /api/reports
GET  /api/reports/{report_id}
GET  /api/dashboard
GET  /api/actions
GET  /api/contacts
GET  /api/contacts/{contact_id}
GET  /api/evidence/{evidence_id}
```

## Status Object

`GET /api/status` returns service status, runtime root, Data Core path, source workspace, local-only safety flags, import/report timestamps, raw gate status, warning/error lists, and counts for messages, conversations, contacts, and media.

Verified counts:

- messages: `612,664`
- conversations: `1,552`
- contacts: `5,870`
- media: `0`

## Update Behavior

`POST /api/update/run` queues a background refresh. The run writes:

- `state/last_run.json`
- `state/status.json`
- `reports/report_index.json`
- `dashboard/index.html`
- `logs/<run_id>.log`

## Safety

The API is local-only and reads the v0.2-R2 Data Core in read-only mode. It does not upload raw data, call cloud APIs, run WeChat exporter tools, or touch external drives.
