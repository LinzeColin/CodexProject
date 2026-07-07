# Validation Checks

Blocking checks:

* Required files and input directory exist.
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
