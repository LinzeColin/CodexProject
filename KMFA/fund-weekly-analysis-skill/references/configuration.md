# Configuration

Canonical input directory:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群
```

Canonical repo target:

```text
KMFA/fund-weekly-analysis-skill/
KMFA/metadata/fund_weekly_analysis/
```

Public-safe tracked metadata:

```text
KMFA/metadata/fund_weekly_analysis/README.md
KMFA/metadata/fund_weekly_analysis/schema/*.yaml
KMFA/metadata/fund_weekly_analysis/manifests/redacted_*.json
KMFA/metadata/fund_weekly_analysis/.gitignore
```

Private runtime, gitignored:

```text
KMFA/metadata/fund_weekly_analysis/private_runtime/
```

Private OCR sidecars, gitignored:

```text
KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars/<run_id>/
```

Output run directory:

```text
KMFA/metadata/fund_weekly_analysis/private_runtime/runs/YYYYMMDDTHHMMSS+1000/
```

Successful user-facing outputs in that run directory:

```text
资金与税费管理母版_<run_id>.xlsx
资金与税费管理报告_<run_id>.pdf
```

Internal OCR, audit, log, and authorization sidecars in the same private runtime are validation materials only, not user-facing deliverables.

Scheduler timezone:

```text
Australia/Sydney
```

Scheduler local time:

```text
Monday/Saturday 11:00
```

Reference only:

```text
Australia/Sydney local time is authoritative. Beijing time must not be used as the scheduler timezone.
```

Default chart limit:

```text
max_chart_width_px: 1728
max_chart_height_px: 864
chart_type: line
```
