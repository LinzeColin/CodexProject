# proM2 运维手册

## 日常运行

由 Codex Automation 在每天 01:10 调用：

```bash
python3 OpenAIDatabase/macdata/proM2/scripts/run_controlled_cycle.py --repo-root . --execute
```

脚本不会自行定时。没有 `--execute` 时不会采集、上传或清理。

## 流程

1. 读取配置。
2. 检查 owner confirmations。
3. 设备预检。
4. 采集明文指标。
5. 生成全中文报告草稿。
6. 凭证扫描。
7. raw 数据通过唯一短命 PR 进入 `main`。
8. 等待 Project Governance 与 trusted Settlement，逐文件 SHA-256 验证并确认 `0/0/0`。
9. 验证成功后清理本机 3 天以前数据、macdata 临时缓存和受控开发环境缓存。
10. 只读确认 trusted Settlement 已删除事务对象；设备脚本不执行 GitHub janitor 写操作。
11. 生成最终中文报告。
12. 最终报告通过第二个顺序短命 PR 进入 `main`，再次验证并回到 `0/0/0`。
13. Codex session 输出全中文报告；全过程不得同时存在两个 PR。

## 失败处理

| 失败 | 处理 |
|---|---|
| owner_confirmations.json 不存在 | 停止，先问用户 |
| 设备不匹配 | 停止，列出差异，先问用户 |
| 凭证扫描失败 | 停止上传，保留本地数据 |
| branch push / PR / CI / Settlement 失败 | 补偿关闭 PR、删除事务分支，不清理本机旧数据 |
| main hash reconciliation / 0/0/0 失败 | 不清理本机旧数据 |
| 清理失败 | 报告中明文写出失败原因 |
| Settlement 终态审计失败 | 报告中明文写出失败原因，停止后续 GitHub 事务 |

## 本机减负边界

允许删除或执行：

```text
OpenAIDatabase/macdata/proM2/data/current_3days/raw/ 中 3 天以前日期目录
OpenAIDatabase/macdata/proM2/reports/current_3days/ 中 3 天以前日期目录
OpenAIDatabase/macdata/proM2/data/run_logs/ 中 3 天以前日期目录
OpenAIDatabase/macdata/proM2/data/cache/archive_push/ 临时浅克隆缓存
docker system prune -f（默认不使用 -a，不清理 volumes）
brew cleanup
purge（系统缓存 best-effort，权限不足则报告）
项目内白名单缓存目录：__pycache__、.pytest_cache、.mypy_cache、.ruff_cache、.tox、.nox、.vite、node_modules/.cache、.next/cache、dist/.vite
GitHub 对象不在本设备清理范围；只由 trusted Settlement 结算
```

不允许删除：

```text
Docker volumes
Docker 全量 images prune（`-a`）
~/Library/Caches/* 全目录
项目 node_modules / .venv / build / dist 根目录
main 分支或任意 GitHub ref/PR/Issue
任何 OpenAIDatabase/macdata/airM2 内容
```
