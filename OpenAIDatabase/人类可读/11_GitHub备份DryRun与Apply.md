# 11 GitHub 备份 Dry-Run 与 Apply

## 结论

S04 P3 已建立 GitHub backup 的本地控制面。任务 ID 为 `MA-V12-S04P3`，
验收 ID 为 `ACC-MA-V12-S04P3`，状态为
`phase_s04_p3_github_backup_completed_pending_s04_review`。

本阶段只让备份流程可 dry-run、可本地 apply，不上传 GitHub main。

## 命令

- Dry-run：`python scripts/atlasctl.py push --dry-run`
- Apply：`python scripts/atlasctl.py push --apply`

Dry-run 只输出 backup contract，不写文件、不 stage、不 commit、不 push。

Apply 只执行本地 `git add` 和 `git commit`，默认提交信息为
`Memory Atlas GitHub backup snapshot`。它不会执行远端 push。

## 备份范围

- `data/public_raw`
- `data/derived`
- `data/run_logs`
- `docs/reviews`
- `reports`

这些范围覆盖 raw、derived、reports 和 run logs。不存在的目录会被跳过；已有
tracked 目录即使当前不存在，也会纳入 Git 检查。

## 失败与 fallback

如果当前目录不是 Git worktree，命令会失败关闭，并输出中文原因和 fallback 建议。

如果备份范围没有变更，apply 不会伪造 commit，并会建议先运行 sync/build-atlas。

## 本阶段边界

- No GitHub main upload in this phase。
- 不执行远端 push。
- 不重装 app。
- 不删除或覆盖 raw。
- 不读取密码、验证码、cookie 或 session token。
- 不修改 ChatGPT 会话。

## 下一步

S04 的 P1、P2、P3 已完成。下一步只允许进入 S04 Review。
