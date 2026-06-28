# Codex Review Ticket - Stage 13 Owner Specified

适用阶段：Stage 13 - 后置触发型复核。适用任务：`S13-P1-T1`、`S13-P1-T2`、`S13-P1-T3`。

## 触发条件

`交付前人工指定`。本轮 pursuing goal 明确要求完成 Stage 13，因此允许生成本地 Codex Review Ticket。无触发条件时不得生成 Codex Review Ticket。

## 复核范围

仅对异常区域进行复核，禁止全仓无差别扫描。scope files：

```text
PFI/config/pfi_parameters.yaml
PFI/config/pfi_v022_parameters.yaml
PFI/src/pfi_v02/stage_v022_runtime_diff.py
PFI/src/pfi_v02/stage_v022_post_review.py
PFI/review_queue/codex_review_stage13_owner_specified_20260628.md
PFI/docs/pfi_v022/STAGE13_POST_REVIEW.md
PFI/docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md
PFI/reports/pfi_v022_summary.md
PFI/开发记录.md
```

## 期望检查

1. 检查 Stage 7-12 参数、公式、阈值、双消费口径、Runtime Diff、Stage 12 交付物是否保持一致。
2. 检查 Downloads 污染文件夹清理是否只覆盖 PFI 预同步临时目录。
3. 检查复核结果是否写入开发记录，且包含问题、修复、验证、剩余风险。
4. 检查是否存在阻塞项仍继续交付。

## 禁止事项

- 不得联网。
- 不得调用外部 LLM。
- 不得全仓无差别扫描。
- 不得复核 EEI、ADP、Alpha、Serenity 或其它项目。
- 不得删除 `PFI.app`、用户 taskpack、roadmap、zip、md 源文件。
- 不得修改真实交易、支付、券商下单或任何实盘执行路径。

## 复核结论

| 问题 | 修复 | 验证 | 剩余风险 | 状态 |
| --- | --- | --- | --- | --- |
| 交付前人工指定触发 Stage 13，需要防止扩大成全仓无差别扫描。 | Ticket 只列出 Stage 13 相关 PFI scope files。 | Stage 13 合同测试验证 `full_repo_scan_allowed=false`。 | 无阻塞。 | 已修复 |
| Downloads 污染文件夹仍有 PFI 预同步临时目录。 | 归档后移出 Downloads。 | Stage 13 测试确认 `PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` 等目录不在 Downloads。 | 无阻塞。 | 已修复 |

