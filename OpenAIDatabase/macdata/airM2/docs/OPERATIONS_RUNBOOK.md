# airM2 运维手册

## 日常运行

由 Codex Automation 在每天 01:10 调用：

```bash
python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --execute
```

脚本不会自行定时。没有 `--execute` 时不会采集、上传或清理。

## 流程

1. 读取配置。
2. 检查 owner confirmations。
3. 设备预检。
4. 采集明文指标。
5. 生成全中文报告草稿。
6. 凭证扫描。
7. 上传 raw 数据到 `macdata-airM2`。
8. 远程 hash 验证。
9. 验证成功后清理本机 3 天以前数据、macdata 临时缓存、受控 Docker/Homebrew/用户态系统缓存/项目缓存。
10. 生成最终中文报告。
11. 上传最终报告到 `macdata-airM2`。
12. Codex session 输出全中文报告。

## 失败处理

| 失败 | 处理 |
|---|---|
| owner_confirmations.json 不存在 | 停止，先问用户 |
| 设备不匹配 | 停止，列出差异，先问用户 |
| 凭证扫描失败 | 停止上传，保留本地数据 |
| Git push 失败 | 不清理本机旧数据 |
| 远程验证失败 | 不清理本机旧数据 |
| 清理失败 | 报告中明文写出失败原因 |

## 本机减负边界

只允许删除：

```text
OpenAIDatabase/macdata/airM2/data/current_3days/raw/ 中 3 天以前日期目录
OpenAIDatabase/macdata/airM2/reports/current_3days/ 中 3 天以前日期目录
OpenAIDatabase/macdata/airM2/data/run_logs/ 中 3 天以前日期目录
OpenAIDatabase/macdata/airM2/data/cache/archive_push/ 临时浅克隆缓存
docker system prune -f，不含 volumes，不含 -a
brew cleanup -s，不使用 sudo
配置列出的 ~/Library/Caches/* 子目录
.pytest_cache / .mypy_cache / .ruff_cache / __pycache__ / node_modules/.cache / .next/cache
```

不允许删除：

```text
Docker volumes
docker system prune -a
~/Library/Caches 根目录
项目 node_modules / .venv / build / dist / 源码 / 数据
任何 OpenAIDatabase/macdata/proM2 内容
```
