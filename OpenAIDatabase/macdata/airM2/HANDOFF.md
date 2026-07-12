# airM2 macdata HANDOFF

更新时间：2026-07-06T06:22:50+10:00

当前目标：维护 `airM2` macdata Codex Automation，确保全中文明文报告以 `.md` 输出并归档。

当前状态：

- 本机硬件已确认为 `MacBook Air / Mac14,2 / Apple M2 / 8GB`。
- 任务包已安装到 `OpenAIDatabase/macdata/airM2`。
- 用户确认文件已创建：`config/owner_confirmations.json`。
- 已修复上一轮错误扩展：恢复原始任务包语义，不自动清理 Docker、Homebrew、系统缓存、项目缓存。
- GitHub `main` 本轮回退代码提交已推送：`7afdce529206652b7a9aac8ce5d4dbcc18e884ef`。
- GitHub 归档分支 `macdata-airM2` 已保留并验证：`c6679c425cee44b31e0fc02d7ba0b7481a9e4932`。
- Codex Automation 已创建并启用：`macdata-airm2-daily-controlled-archive`。
- 本次完整运行成功：raw commit `0d8037b200fb67e653cf6d2abf44e7456ca2c45f`，report commit `c6679c425cee44b31e0fc02d7ba0b7481a9e4932`。
- 旧运行曾错误执行 Homebrew/用户态/项目缓存清理；本轮已从代码、配置、文档和 automation prompt 中移除该行为。后续如需电脑大清理，应另建独立 cleanup 任务。
- 2026-07-06 已按用户要求回退 `.txt` 设置，目标最新报告路径恢复为 `reports/latest/latest_report.md`。
- 脚本会在写入 `latest_report.md` 前删除 stale `reports/latest/latest_report.txt`，避免 latest 目录同时出现 md/txt 双入口。

关键决策：

- Time Machine 不采集，iCloud 不使用。
- API key、token、password 及等价凭证禁止进入 GitHub。
- `main` 保存任务包和配置；`macdata-airM2` 保存每日归档历史。
- GitHub 未存在的归档分支由首次上传自动创建。

下一步：

1. 每天 01:10 Australia/Sydney 检查 automation run 是否成功。
2. 若 preflight 失败，先修设备/repo/owner confirmation 差异，不手动绕过。
3. 若 GitHub push 或远程验证失败，保留本机旧数据和缓存，先修 remote/auth。
4. 若 Air 长期低于 70GB free 或 swap 超过 1GB，另开独立 cleanup/降载任务，不混入 macdata 归档任务。

验证结果：

- `python3 -m unittest discover -s OpenAIDatabase/macdata/airM2/tests -p 'test_*.py'`：4 tests OK。
- `python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only`：ok true。
- `git ls-remote https://github.com/LinzeColin/CodexProject.git refs/heads/main refs/heads/macdata-airM2`：回退代码 main `7afdce529206652b7a9aac8ce5d4dbcc18e884ef`，归档分支 `c6679c425cee44b31e0fc02d7ba0b7481a9e4932`。
- 归档分支 `reports/latest/`：仅有 `.gitkeep` 和 `latest_report.md`，没有 stale `latest_report.txt`。
