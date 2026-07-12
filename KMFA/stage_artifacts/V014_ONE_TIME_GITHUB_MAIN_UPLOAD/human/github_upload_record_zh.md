# KMFA v0.1.4 一次性 GitHub main 上传记录

- phase：`V014_ONE_TIME_GITHUB_MAIN_UPLOAD`
- task：`KMFA-V014-ONE-TIME-GITHUB-MAIN-UPLOAD-20260713`
- acceptance：`ACC-V014-ONE-TIME-GITHUB-MAIN-UPLOAD`
- target：`LinzeColin/CodexProject` 的 `refs/heads/main`
- source branch：`codex/kmfa`
- status：`uploaded_to_github_main_public_safe`
- upload closure commit：`recorded_by_commit_containing_this_file`
- push：只允许一次非 force 的 `HEAD -> main`

## 上传范围

本阶段只上传已经完成最终整体复审的 KMFA 代码、治理文件、validator、测试和 public-safe 证据。`origin/main` 已通过 merge commit 安全集成；最终上传提交必须同时包含本记录并在推送后满足 `HEAD == origin/main == remote main`。

本次上传不包含原始经营数据、压缩包、工作簿、PDF、私有表格、数据库、银行流水、合同、工资、税务材料、字段或表头明文、业务值、私有诊断、凭据或 secret。此前继承的 owner 明文授权策略不适用于本次 v0.1.4 上传。

## 业务边界

代码上传完成不等于业务发布。当前仍为 `Q4 / D / NO_GO / 3-9-2-1`，full lineage、正式报告、差异关闭、持久业务写入和业务执行均未完成。App 重装及本机/GitHub parity 必须作为下一独立 phase 执行。

## 证明方式

- 本文件所在 commit 是唯一 upload closure commit。
- 上传前执行完整 validator、测试、治理、raw/secret 和 diff 门禁。
- 推送前执行 dry-run，只执行一次非 force push。
- 推送后 fetch 并运行 `check_v014_one_time_github_main_upload.py --require-remote-parity`。
