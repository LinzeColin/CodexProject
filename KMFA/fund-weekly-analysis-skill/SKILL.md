name: fund-weekly-analysis-skill
description: Use when operating, reviewing, automating, modifying, or handing off KMFA fund weekly/monthly analysis, DingTalk finance screenshot evidence, cash-flow净化, tax/loan risk analysis, company-bank account matrix, Excel fund dashboard generation, local Codex automation, or GitHub main governance under LinzeColin/CodexProject/KMFA.

# KMFA Fund Weekly Analysis Skill

## Use First

This skill is the portable operating entry for KMFA资金与税费管理自动化. Use it only with a clone of `LinzeColin/CodexProject` and start from `main`.

Canonical GitHub path:

    KMFA/fund-weekly-analysis-skill/

Before acting, read these files in order:

1. `references/runbook.md`
2. `references/configuration.md`
3. `references/operating_contract.md`
4. `references/source_of_truth_contract.md`
5. `references/validation_checks.md`
6. `templates/excel_sheet_spec.yaml`
7. `templates/fund_weekly_analysis_config.yaml`
8. `KMFA/HANDOFF.md` if present
9. The exact source files you will touch or process

## No simulation / no synthetic financial data

No simulation: production reports must be generated only from real source files, real DingTalk finance screenshots, real bank exports, real tax/payment/deposit/project ledgers, or explicitly reviewed manual corrections. Missing values remain blank or enter the exception queue.

## Hard Boundaries

* Do not create branches, PRs, issues, forks, or worktrees unless the user explicitly changes this rule in the current thread.
* Work on `main` only. If not on `main`, stop and report.
* Any change to this skill, its automation prompt, validator, template, or governance file must be committed and pushed to GitHub `main` in the same run after validation passes.
* Local Codex automation state is not Git by itself. The canonical automation prompt must be mirrored under `automation/` in this folder before the local automation is updated.
* Do not commit raw screenshots, raw bank exports, raw DingTalk archives, full bank account numbers, passwords, tokens, webhook URLs, app secrets, employee private plaintext, payroll raw data, or non-redacted report bodies to public GitHub.
* Do not use sample, test, synthetic, fake, demo, or estimated financial data in production reports. If a field cannot be extracted from real source evidence, leave it blank and send it to the review queue.
* Do not silently correct amount/date/counterparty discrepancies. Put all mismatches into the exception queue with source references.
* Do not count internal transfers as operating income or operating expense.
* Do not treat票据、电子承兑、理财、保证金、应收账款 as T0 cash. Always separate liquidity tiers.
* Do not let low-confidence OCR/vision extraction enter the final facts table without human review.
* Do not show full account numbers, ID numbers, personal phone numbers, passwords, employee-sensitive details, or private raw screenshots on management dashboards.

## Current Automation Rules

* Automation name: `KMFA资金周报日报自动化`.
* Timezone: `Australia/Sydney`.
* Daily run time: 11:30 local Sydney time.
* Reference only: 11:30 Australia/Sydney equals 09:30 Asia/Shanghai during the current UTC+10 offset. The local scheduler must use Sydney local time, not Beijing time.
* Input directory:

      /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群

* Public metadata/config root:

      KMFA/metadata/fund_weekly_analysis/

* Private runtime root, gitignored by default:

      KMFA/metadata/fund_weekly_analysis/private_runtime/

* Skill root:

      KMFA/fund-weekly-analysis-skill/

## Three-Layer Analytical Contract

The analysis must follow this order every time:

1. **净化层：钱是不是真的经营现金流？**
   * Build evidence index first.
   * Classify and pair internal transfers.
   * Separate operating cash flow, financing, investing/cash management, tax, deposits, guarantees, bills, loans, and unclassified net movement.
   * Output `待归类/内部调拨净额` separately. Never merge it into operating cash flow.

2. **定位层：钱在哪里，钱怎么变动？**
   * Build daily balance continuity ledger.
   * Preserve company, bank, account alias, liquidity tier, source evidence, and review status.
   * Generate company-bank matrix for every company and every bank/account alias found in real source data.
   * Show T0 bank cash,票据/电子汇票,理财,保证金, and total funds separately.

3. **预测层：钱什么时候可用，现在和将来够不够，有没有风险？**
   * Roll up daily, weekly, monthly, quarterly, half-year, and yearly views when enough real data exists.
   * Use only known real data for forecast inputs: taxes, payroll if supplied, project cost, customer receipts, deposit refunds, loan repayment, wealth-management redemption, bills maturity, and approved transfers.
   * Unconfirmed future items remain risk/opportunity lines, not fact values.

## Required Excel Output

The final workbook must be `.xlsx`, native Excel, editable, and compatible with Microsoft Excel and WPS.

Visible sheets, in this exact order:

1. `01_首页总览`
2. `02_资金趋势预测`
3. `03_三层净流余额`
4. `04_税费融资风险`
5. `05_公司银行矩阵`
6. `06_CodexSkill流程`

Hidden sheets, in this exact order after visible sheets:

* `H01_资金事实主表`
* `H02_异常任务池`
* `H03_钉钉证据索引`
* `H04_客户合同辅助`
* `H05_复审检查`
* `H06_配置规则`

Excel visual rules:

* Font: `Microsoft YaHei`; fallback to system sans-serif when unavailable.
* Title fill: `#0F172A`; title font white, bold.
* Positive/normal: green family `#DCFCE7` / `#15803D`.
* Warning: amber family `#FEF3C7` / `#D97706`.
* High risk: red family `#FEE2E2` / `#DC2626`.
* Table header blue/teal: `#1D4ED8` or `#0F766E`.
* All charts must be native Excel charts, not images.
* 首页 and trend charts must be line charts unless the user explicitly changes the chart type.
* No chart may exceed width 18 inches or height 9 inches. Treat this as max 1728 x 864 px at 96 dpi.
* Charts must not overlap tables or other charts.
* Sheet elements must be native cells, tables, charts, conditional formatting, or sparklines. Do not paste screenshots as report elements.
* Visible sheets must be legible for non-finance C-level/board users.

## Minimum Outputs Per Run

Write outputs under:

    KMFA/metadata/fund_weekly_analysis/private_runtime/runs/<run_id>/

Required files:

* `资金与税费管理母版_<run_id>.xlsx`
* `run_manifest.json`
* `evidence_index.csv`
* `fund_ledger.csv`
* `net_flow_ledger.csv`
* `company_bank_matrix.csv`
* `tax_loan_risk.csv`
* `exception_tasks.csv`
* `cross_review.json`
* `audit_log.json`
* `run_summary.md`

Current deterministic runner status contract:

* Missing configured folder returns `SOURCE_MISSING`, writes fail-closed artifacts, and may list private source candidates such as sibling `DWS_Outputs.zip` or `DWS_Archive/<group>` for explicit materialization. It must not silently switch to those candidates.
* Existing configured folder returns `INDEXED_PENDING_EXTRACTION`, hashes real files, copies the current native Excel mother template into the private run folder, writes the required CSV/JSON package, and creates exception tasks for every evidence item that still needs OCR/table extraction or human review.
* `INDEXED_PENDING_EXTRACTION` is not a management conclusion. It means no amount was generated, inferred, forecast, or promoted into facts yet.

Explicit source materialization:

* Use `tools/materialize_fund_source.py` when the configured `DWS_Outputs/付款请示群` folder is missing but a verified private candidate such as `DWS_Archive/付款请示群` exists.
* Dry-run is default. `--apply` is required before any files are copied.
* The tool copies only missing files, skips identical files, fails on target hash conflicts, detects OneDrive/macOS `dataless` source files as `SOURCE_UNREADABLE`, and writes `source_materialization_manifest.json` plus `source_materialization_files.csv` under ignored private runtime.
* Do not materialize from unverified zip/archive contents silently during daily runner execution.

The shipped editable workbook template is:

      templates/资金与税费管理母版_真实数据预览_v2.xlsx

It is the current mother template. It keeps `01_首页总览` first, clears visible report-page row 2 explanatory text, shows the requested 4+4 homepage KPI card order, and contains exactly two homepage native line charts for the latest 15 and 30 daily snapshots. Generated production outputs still belong under private runtime and must not be committed.

Track only public-safe manifests/configs in Git unless the user gives explicit current-run authorization and the repo/privacy boundary permits raw data.

## Data Quality Gates

Stop before producing a management conclusion if any blocking gate fails:

1. Formula error scan finds Excel errors.
2. Any generated amount comes from non-real data.
3. Daily balance continuity gap exceeds 0.01 and is not explicitly sent to exceptions.
4. Internal transfer pairing rules were not applied.
5. T0 cash and total funds are not separated.
6. Tax version conflict is not flagged.
7. Raw sensitive data is visible on management sheets.
8. Required sheet order or sheet names are wrong.
9. Hidden audit/review sheets are not hidden.
10. GitHub main sync is required but validation failed.

## Agent Behavior

When uncertain, do not guess. Use `待识别`, `待复核`, or `需人工确认` and write a task into `exception_tasks.csv`. Every decision must leave a source trail: source file path, sheet/image name, evidence_id, row number when available, extraction confidence, and reviewer status.
