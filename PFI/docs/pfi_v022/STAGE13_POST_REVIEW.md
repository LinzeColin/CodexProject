# Stage 13 - 后置触发型复核

本轮只复审解决 Stage 13。Stage 13 在 `交付前人工指定` 触发下生成本地 Codex Review Ticket，仅对异常区域进行复核，禁止全仓无差别扫描，不联网，不调用外部 LLM，不修改真实交易、支付、券商提交或实盘自动下单路径。

整体项目复审解决不在本轮实现。GitHub 同步不在本轮执行。app 入口重装不在本轮执行。本轮完成后只进入下一轮整体项目复审准备，不标记整体 goal 完成。

## Stage -> Phase -> Task

| Stage | Phase | Task ID | 任务 | 交付物 | 状态 |
| --- | --- | --- | --- | --- | --- |
| Stage 13 - 后置触发型复核 | Phase 13.1 触发型 Codex / LLM 复核 | `S13-P1-T1` | 生成 Codex Review Ticket | `PFI/review_queue/codex_review_stage13_owner_specified_20260628.md` | 本轮完成 |
| Stage 13 - 后置触发型复核 | Phase 13.1 触发型 Codex / LLM 复核 | `S13-P1-T2` | 仅对异常区域进行复核 | Review Ticket 指定 scope files | 本轮完成 |
| Stage 13 - 后置触发型复核 | Phase 13.1 触发型 Codex / LLM 复核 | `S13-P1-T3` | 复核结果写入开发记录 | `PFI/开发记录.md` | 本轮完成 |

## 触发条件

- 当前触发条件：`交付前人工指定`。
- 其它允许触发条件：P0 指标异常、跨板块金额不一致、公式冲突、分类/标签冲突、测试无法解释。
- 无触发条件时不得生成 Codex Review Ticket。

## 复核范围

仅对异常区域进行复核，范围由 ticket 指定：

- `PFI/config/pfi_parameters.yaml`
- `PFI/config/pfi_v022_parameters.yaml`
- `PFI/src/pfi_v02/stage_v022_runtime_diff.py`
- `PFI/src/pfi_v02/stage_v022_post_review.py`
- `PFI/review_queue/codex_review_stage13_owner_specified_20260628.md`
- `PFI/docs/pfi_v022/STAGE13_POST_REVIEW.md`
- `PFI/docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md`
- `PFI/docs/pfi_v022/reviews/STAGE13_REVIEW_20260629.md`
- `PFI/reports/pfi_v022_stage13_review_summary.md`
- `PFI/开发记录.md`

## 复核结果

| 问题 | 修复 | 验证 | 剩余风险 | 状态 |
| --- | --- | --- | --- | --- |
| 交付前人工指定触发 Stage 13，需要防止扩大成全仓无差别扫描。 | Codex Review Ticket 限定 scope files，并记录不联网、不调用外部 LLM。 | Stage 13 目标 + 复审测试验证 `full_repo_scan_allowed=false`、`network_allowed=false`、`external_llm_allowed=false`。 | 无阻塞；整体项目复审解决不在本轮实现。 | 已修复 |
| Downloads 污染文件夹仍有 PFI 预同步临时目录。 | 归档为 repo-scoped tar.gz 后移出 Downloads。 | 测试扫描 `PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` 等候选目录不再位于 Downloads，`PFI.app` 仍存在，manifest 保留 taskpack/roadmap/zip/md 来源名。 | 不在本轮恢复或制造 Downloads 源文件。 | 已修复 |
| Stage 13 内容曾混入 Stage 12 最终摘要。 | 新增 `PFI/reports/pfi_v022_stage13_review_summary.md`，Stage 12 摘要继续保持 Stage12-only。 | 复审测试验证 `PFI/reports/pfi_v022_summary.md` 不含 `S13-P1-T1`、`S13-P1-T2`、`S13-P1-T3`。 | 整体项目摘要将在第二阶段整体复审后生成。 | 已修复 |

本轮记录了问题、修复、验证、剩余风险。阻塞项数量：`0`。

## Downloads 清理

Downloads 污染文件夹清理记录见 `PFI/docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md`。本轮处理的白名单包含 `PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` 等 6 个 PFI 预同步临时目录；不删除 `PFI.app`，不删除用户提供的 taskpack、roadmap、zip、md 源文件。
