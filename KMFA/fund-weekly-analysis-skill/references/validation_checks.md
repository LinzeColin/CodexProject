# Validation Checks

Blocking checks:

* `check_source_readiness.py` returns `READY` before extraction or Excel production starts.
* Required files and input directory exist.
* Missing configured input folder returns `SOURCE_MISSING` and does not read alternate private sources unless a separate explicit materialization step is run.
* Existing configured input folder with unreadable/cloud-only files returns `SOURCE_UNREADABLE` and does not write an Excel package.
* Source materialization dry-run creates no target files; apply copies missing files only, skips identical files, fails on conflicting existing targets, and returns `SOURCE_UNREADABLE` when OneDrive source files are cloud-only/dataless or otherwise unreadable.
* `INDEXED_PENDING_EXTRACTION` outputs do not contain generated financial amounts, forecasts, or management conclusions.
* `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW` outputs contain only amounts parsed from real structured CSV rows with the required column contract and still keep `management_conclusion_allowed=false`.
* `STRUCTURED_FACTS_EXTRACTED_PENDING_REVIEW` workbooks contain the same parsed facts in hidden `H01/H03`, homepage KPI cards, and visible flow/risk/matrix sheets; native chart files remain present.
* No production table contains `sample`, `demo`, `fake`, `synthetic`, or `模拟` data markers.
* Workbook sheets exactly match the required visible/hidden order.
* Hidden sheets are hidden.
* Formula error scan returns zero matches.
* Every management KPI can be traced to a ledger/evidence row.
* Balance continuity formula difference is within 0.01 or exceptioned.
* Internal transfer净化 was applied before operating cash flow summaries.
* T0 cash,票据/电子汇票,理财,保证金,总资金 are displayed separately.
* Tax version conflicts are flagged.
* Personal/secret fields are absent from visible management sheets.
* Chart type is line for 首页/趋势; chart dimensions are <= 1728 x 864 px.
* No visible chart/table overlaps another visible element.

Non-blocking warnings:

* Account alias has low confidence.
* Company-bank matrix contains `待识别` rows.
* Evidence grade C/D supports a management clue.
* OCR confidence below threshold.
