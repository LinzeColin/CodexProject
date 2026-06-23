# Stage 1 Migration Runbook

适用范围：arXiv Daily Push Stage 1，板块一 B1/arXiv。  
当前状态：Stage 1 已验收；下一步是本机 Codex/local runner 生产运行与 2026-06-30 新电脑迁移准备。

## 1. 迁移前本机边界

- 不启用 GitHub cloud scheduled production。
- 不把 GitHub Actions 当每日生产 runner。
- 不在未确认前安装 launchd 常驻任务。
- 不把 Gmail SMTP secret 写入仓库、日志、plist 或迁移包。
- 不上传 GitHub Release。
- 不生成视频。

## 2. 生成迁移包

```bash
PYTHONPATH=arxiv-daily-push/src python3 -m arxiv_daily_push migration export \
  --project-root . \
  --db /path/to/adp.sqlite3 \
  --output-dir /path/to/adp-stage1-migration \
  --generated-at 2026-06-22T22:20:00+10:00 \
  --json
```

迁移包应包含：

- `migration_manifest.json`
- `LOW_RESOURCE_SMOKE.json`
- `NEW_MACHINE_BOOTSTRAP_CHECKLIST.md`
- `SECRET_NAMES_CHECKLIST.md`
- `LOCAL_RUNNER_RUNBOOK.md`
- `RESTORE_DRILL.md`
- `backups/*/backup_manifest.json`

## 3. 新机器验证顺序

1. 安装 Python、Git，并确认 SSL/network 可访问。
2. 克隆仓库并 checkout 已验收 commit。
3. 配置 secret 名称对应的环境变量；只在本机环境或 Keychain-backed shell 中写值。
4. 执行 `adp migration verify` 校验迁移包 hash。
5. 执行 `adp restore --confirm-restore` 到显式新路径。
6. 执行 `adp storage inspect` 校验 SQLite/WAL/FTS5。
7. 执行 `adp runtime-audit`、`adp tick`、`adp watchdog`、`adp local-runner preflight`。
8. 执行一次 `adp local-runner daily` smoke test，确认 queue、ledger、report 和 email preview 都落在本机 state 目录。
9. 只有新机器 smoke test 通过后，才安装 launchd。

## 4. Secret 名称

只迁移名称，不迁移值：

- `ADP_SMTP_HOST`
- `ADP_SMTP_PORT`
- `ADP_SMTP_USERNAME`
- `ADP_SMTP_PASSWORD`
- `ADP_SMTP_TO`

## 5. 停止条件

任一条件出现即停止：

- 迁移包 hash 校验失败；
- restore 需要覆盖未知数据库；
- SQLite inspect 不通过；
- runtime audit 发现 production flag 已启用；
- 可用磁盘低于紧急阈值；
- 任何 secret 值出现在文件、日志、manifest 或邮件正文中。
- GitHub cloud scheduled production 被启用或成为每日 production runner。
