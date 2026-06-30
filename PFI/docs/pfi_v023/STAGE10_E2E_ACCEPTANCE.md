# PFI v0.2.3 Stage 10 E2E Acceptance

## Stage 10 Phase 10.1

本轮只执行 Stage 10 Phase 10.1 入口 E2E，覆盖：

- app 打开验证：`~/Downloads/PFI.app` dry-run 指向当前 checkout，并通过 app 入口版本参数打开同一 Streamlit UI。
- localhost 打开验证：`http://127.0.0.1:8501` 健康，浏览器截图显示当前 PFI UI。
- build/hash 一致验证：运行时 metadata 的 web bundle hash 与当前 checkout 磁盘 manifest 一致。
- 清缓存验证：仅执行 dry-run，删除 0 项，未触碰报告、持仓、导入、SQLite 或市场 bar cache。

## Evidence

证据包位置：`PFI/reports/pfi_v023/stage_10/phase_10_1/`

已记录：

- `browser_validation.json`
- `build_hash_consistency.json`
- `cache_cleanup_dry_run.json`
- `screenshots/app_entry.png`
- `screenshots/localhost.png`

## Scope Guard

Phase 10.2 未执行。

Phase 10.3 未执行。

Stage 10 whole-stage review 未执行。

GitHub main upload 未执行。

本轮未创建、填充或替换任何财务数据；所有可见金额和流水状态来自当前本机 PFI 运行态与 MetaDatabase 读取结果。
