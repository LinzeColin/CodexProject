# fund_weekly_analysis metadata

Create this folder under:

```text
KMFA/metadata/fund_weekly_analysis/
```

Recommended tracked files:

* `README.md`
* `.gitignore`
* redacted manifest schemas
* validation summaries without private raw values

Recommended private runtime path, ignored by Git:

```text
KMFA/metadata/fund_weekly_analysis/private_runtime/
```

The local editable workbook prerequisite belongs at:

```text
KMFA/metadata/fund_weekly_analysis/private_runtime/templates/fund_weekly_template.xlsx
```

`KMFA_FUND_TEMPLATE_PATH` may override that ignored local path. The runner fails closed with `PRIVATE_TEMPLATE_MISSING` before reading any source when the template is unavailable. Never track or package the workbook.
