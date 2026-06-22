# Stage 1 Migration Runbook

适用范围：arXiv Daily Push Stage 1，板块一 B1/arXiv。  
当前状态：迁移准备，不是 `ARXIV_PRODUCTION_ACCEPTED`。

## 1. 迁移前本机边界

- 不启动长期生产调度。
- 不执行 30 日真实重放。
- 不发真实 Gmail SMTP。
- 不上传 GitHub Release。
- 不生成视频。
- 不保存 secret 值到仓库、日志、manifest 或迁移包。

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
- `RESTORE_DRILL.md`
- `backups/*/backup_manifest.json`

## 3. 新机器验证顺序

1. 安装 Python、Git，并确认 SSL/network 可访问。
2. 克隆仓库并 checkout 已验收 commit。
3. 配置 secret 名称对应的环境变量；只在系统 secret store 或 GitHub Secrets 中写值。
4. 执行 `adp migration verify` 校验迁移包 hash。
5. 执行 `adp restore --confirm-restore` 到显式新路径。
6. 执行 `adp storage inspect` 校验 SQLite/WAL/FTS5。
7. 执行 `adp runtime-audit`、`adp tick`、`adp watchdog`。
8. 只有完成新机器实测后，才进入 S1-11 以后重资源验收。

## 4. Secret 名称

只迁移名称，不迁移值：

- `ADP_SMTP_HOST`
- `ADP_SMTP_PORT`
- `ADP_SMTP_USERNAME`
- `ADP_SMTP_PASSWORD`
- `ADP_SMTP_TO`
- `ADP_RELEASE_TARGET`

## 5. 停止条件

任一条件出现即停止：

- 迁移包 hash 校验失败；
- restore 需要覆盖未知数据库；
- SQLite inspect 不通过；
- runtime audit 发现 production flag 已启用；
- 可用磁盘低于紧急阈值；
- 任何 secret 值出现在文件、日志、manifest 或邮件正文中。
