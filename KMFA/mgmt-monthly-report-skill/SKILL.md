---
name: mgmt-monthly-report-skill
description: Use when creating, operating, validating, backing up, or maintaining the KMFA management monthly report workflow that converts seven governed input slots into the v6-aligned Excel report and board PDF.
---

# Management Monthly Report Skill

中文名：经营管理月报

Canonical GitHub path:

```text
KMFA/mgmt-monthly-report-skill/
```

Public-safe metadata path:

```text
KMFA/metadata/mgmt-monthly-report-skill/
```

## Use First

Before any monthly run, read:

1. `references/runbook.md`
2. `references/data_contract.md`
3. `references/excel_pdf_contract.md`
4. `references/data_governance.md`
5. `config/input_manifest.7slots.template.yml`
6. `config/v6_spec.json`
7. `KMFA/AGENTS.md`

Then inspect the exact input directory and output report directory for the target
period.

## Purpose

This skill turns each monthly经营管理报表 run into a repeatable governed process:

- map seven user-facing input slots to the v6 task-pack business groups;
- rebuild or refresh the v6-aligned Excel workbook;
- create the board PDF only after the Excel passes validation;
- register hashes, lineage, validation, logs, database export, backup status, and
  any owner-authorized plaintext GitHub upload status under
  `KMFA/metadata/mgmt-monthly-report-skill/`;
- leave only final report files in the local report output directory after
  cleanup.

## Non-Negotiable Outputs

Formal user-facing deliverables are exactly:

```text
经营管理分析报表 YYYYMM.xlsx
董事会经营分析摘要 YYYYMM.pdf
```

Internal governance artifacts are not formal deliverables:

```text
自动验收报告 YYYYMM.json
run manifest
backup registry
public-safe source index
database SQL export
cleanup report
logs
```

## Hard Boundaries

- Owner-authorized raw sensitive Excel, contracts, bank/tax/payroll data, real
  report bodies, and SQLite/database exports may be committed to GitHub only
  under `KMFA/metadata/` after explicit owner authorization, secret scan, and an
  upload manifest record.
- Do not commit credentials, tokens, API keys, webhook secrets, signing keys, or
  private keys to GitHub.
- Do commit governance structures, hash indexes, manifests, validation summaries,
  SQL schemas/exports, backup registration, and authorized plaintext upload
  manifests.
- Do not use directory-wide auto-discovery as business truth. Every source must be
  mapped through the input manifest.
- Do not treat a copied v6 baseline workbook as a completed monthly refresh.
- Do not generate the PDF until the Excel for the same `YYYYMM` has passed the
  validation gate.
- Do not delete user raw files automatically. Cleanup removes only skill-created
  temp/cache/log/runtime artifacts unless the owner gives a separate destructive
  deletion instruction.

## Seven Input Slots

The task pack describes six business input groups. This skill exposes seven
user-facing input slots so non-technical operation can be monitored:

1. `collection_2026`
2. `invoice_tax_cash`
3. `receivable_contract`
4. `aging`
5. `deposit`
6. `three_major_projects`
7. `project_status_contracts`

The seventh slot may contain multiple physical files, normally production project
status plus RedCircle main-contract exports. The manifest must record every
physical file actually used.

## Validation

Run from repository root:

```bash
python3 KMFA/mgmt-monthly-report-skill/tools/validate_skill_package.py
```

Register a period without copying raw data:

```bash
python3 KMFA/mgmt-monthly-report-skill/scripts/mgmt_monthly_report.py \
  register \
  --period YYYYMM \
  --input-dir /path/to/inputs \
  --output-dir /path/to/reports \
  --metadata-root KMFA/metadata/mgmt-monthly-report-skill \
  --write
```

Run deliverable validation after reports exist:

```bash
python3 KMFA/mgmt-monthly-report-skill/scripts/validate_deliverables.py \
  --period YYYYMM \
  --input-dir /path/to/inputs \
  --excel "/path/to/reports/经营管理分析报表 YYYYMM.xlsx" \
  --pdf "/path/to/reports/董事会经营分析摘要 YYYYMM.pdf" \
  --config KMFA/mgmt-monthly-report-skill/config/v6_spec.json \
  --report "KMFA/metadata/mgmt-monthly-report-skill/validation/自动验收报告 YYYYMM.json" \
  --strict
```
