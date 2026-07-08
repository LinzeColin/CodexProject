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

Scheduler timezone:

```text
Australia/Sydney
```

Scheduler local time:

```text
11:00 every Monday and Saturday
```

Reference only:

```text
Australia/Sydney local time is authoritative; do not convert from Beijing time.
```

Default chart limit:

```text
max_chart_width_px: 1728
max_chart_height_px: 864
chart_type: line
```
