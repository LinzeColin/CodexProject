# Weixin Ingestion Contract - Consumption Analysis System

Date: 2026-06-05

## Purpose

This contract defines how Weixin messages, screenshots, videos, and files enter the consumption analysis system without duplicating the Weixin bot, OpenClaw gateway, or cross-system master platform code.

## Ownership Boundary

| Layer | Owner | Responsibility |
|---|---|---|
| Weixin channel and OpenClaw Gateway | `<LOCAL_WEIXIN_GATEWAY_ROOT>` | Receive Weixin inbound messages/media, keep gateway loopback-only, route known commands or media paths. |
| Consumption intake adapter | This project | Archive incoming text/media, OCR supported screenshots, parse official Alipay/WeChat bills, write candidate status and finance-specific records into SQLite. |
| Master/ResearchBus | External master system | Cross-system report index, global entity IDs, decision records, and schema coordination. This project should publish facts, not own the global bus. |

## Current Connection Evidence

- OpenClaw Gateway: loopback `127.0.0.1:18789`, connectivity probe OK.
- Weixin channel: enabled, configured, running.
- Existing Weixin monitor calls this project through `scripts/weixin_alipay_fund_ingest.py` for media ingestion.
- This project already supports Alipay and WeChat CSV/XLSX bills through the common transaction schema.

## Intake Status Rules

| Input | Stored Where | Data Status | Production Ledger Effect |
|---|---|---|---|
| Weixin text message | `weixin_intake_items` and private archived `.txt` | `NEEDS_REVIEW` | None |
| Screenshot | `weixin_intake_items`; OCR if possible | `NEEDS_REVIEW` or `PARSED_CANDIDATE` | None unless extractor and review pass |
| Video | `weixin_intake_items`; archived only for now | `NEEDS_REVIEW` | None |
| Official Alipay/WeChat bill CSV/XLSX | Existing bill parser plus `weixin_intake_items` | `PARSED_CANDIDATE` after parse | Can create reviewed finance records; production consumption reports remain governed by existing import/review pipeline |
| Large or ambiguous item | Existing manual review queue | `NEEDS_REVIEW` | Not included until confirmed |

## SQLite Tables

| Table/View | Purpose |
|---|---|
| `weixin_intake_items` | Generic Weixin candidate inbox for text/media/file metadata, status, routing, and ledger effect. |
| `v_weixin_intake_items` | Read-only downstream view of the intake inbox. |
| `alipay_fund_source_files` | Finance-source archive and extraction status for Alipay/Weixin-transferred fund material. |
| `alipay_fund_records` | Auto-reviewed fund records extracted from official bills or high-confidence screenshots. |
| `alipay_fund_review_runs` | Multi-pass review evidence before any fund record is inserted. |
| `alipay_update_status` | Daily update state for finance-related Weixin/Alipay intake. |

## Non-Duplication Rule

- Do not implement another Weixin bot in this project.
- Do not store Weixin credentials, QR links, targets, or account IDs in this project.
- Do not create a second global entity registry here.
- Do not write ResearchBus schema from this project.
- Reuse `scripts/weixin_alipay_fund_ingest.py` as the local subsystem adapter.

## Downstream Publish Contract

This system may expose these facts to PFIOS, AI Research, or a future master platform:

- `v_weixin_intake_items`: candidate input state and routing.
- `v_fact_transactions_audit`: classified historical transaction facts.
- `v_fact_expense_allocations`: production consumption allocation facts.
- `v_fact_pending_large_review`: pending review items.
- `v_cashflow_monthly`, `v_cashflow_weekly`, `v_cashflow_yearly`: cashflow facts.
- `v_category_summary`, `v_risk_summary`, `v_control_plan`: behavior and control summaries.

## Acceptance Checks

- Text-only Weixin input is archived and marked `NEEDS_REVIEW`, with no production ledger effect.
- Official bill input reuses the existing parser and records its intake effect.
- Screenshots/videos never enter formal consumption reports unless parsed, reviewed, and explicitly mapped by existing rules.
- All downstream access remains read-only unless a user-confirmed review file is supplied.
