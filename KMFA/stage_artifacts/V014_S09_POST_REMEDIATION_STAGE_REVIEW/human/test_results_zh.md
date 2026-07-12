# Stage 9 修补后整体复审测试结果

| 检查 | 结果 | 退出码 |
|---|---:|---:|
| `s09_p1_validator` | `PASS` | `0` |
| `s09_p2_validator` | `PASS` | `0` |
| `s09_p3_validator` | `PASS` | `0` |
| `original_s09_review_validator` | `PASS` | `0` |
| `global_residual_validator` | `PASS` | `0` |
| `remaining_eleven_validator` | `PASS` | `0` |
| `no_float_money` | `PASS` | `0` |
| `no_omission` | `PASS` | `0` |

- dependency checks：`8/8`
- public-safe matrix：`24/24`
- full regression：`1200/1200`，`9556.914s`，`OK`，exit `0`
- current phase focused tests：`2/2`，`22.386s`，`OK`
- strict validator（含 private evidence）：`PASS`
- governance validators：project required、lean required、changed-only sync 均为 `0 error / 0 warning`
- no-float / no-omission：`PASS / PASS`
- structured public parse：JSON `10`、JSONL `3`、YAML `6`、CSV `2`，parse error `0`
- changed-file secret / forbidden suffix / tracked private scan：`0 / 0 / 0`
- raw-root marker scan：`2` 个预期模式命中，均来自 `HANDOFF.md` 同一条已授权只读根目录声明；未授权 raw 文件名、字段、金额或明细命中 `0`
- raw snapshot：生成前后、跨 phase、当前复核均 exact match，并完成两轮复核。
