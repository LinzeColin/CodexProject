# airM2 macdata HANDOFF

更新时间：2026-07-05T21:50:00+10:00

当前目标：安装并启用 `airM2` macdata Codex Automation 任务包，提交到 `LinzeColin/CodexProject`，并建立 `macdata-airM2` 归档分支。

当前状态：

- 本机硬件已确认为 `MacBook Air / Mac14,2 / Apple M2 / 8GB`。
- 任务包已安装到 `OpenAIDatabase/macdata/airM2`。
- 用户确认文件已创建：`config/owner_confirmations.json`。
- 用户覆盖任务包默认边界：允许 raw 远程验证成功后执行受控 Docker/Homebrew/用户态系统缓存/项目缓存清理。
- GitHub `main` 已推送：`be257db9483b0fb463d5a8d1e95f33e34c4caaf7`。
- GitHub 归档分支 `macdata-airM2` 已创建并验证：`c40633e9ab6130e78afaeb063422f60336b171ec`。
- Codex Automation 已创建并启用：`macdata-airm2-daily-controlled-archive`。
- 本次完整运行成功：raw commit `3f5c9c61bf7197de13ab7aa1e7d046c45bfb807f`，report commit `c40633e9ab6130e78afaeb063422f60336b171ec`。
- 清理结果：Docker 不可用跳过；Homebrew 已执行；用户态缓存释放 53.03 MB；项目缓存释放 0.09 MB。

关键决策：

- Time Machine 不采集，iCloud 不使用。
- API key、token、password 及等价凭证禁止进入 GitHub。
- `main` 保存任务包和配置；`macdata-airM2` 保存每日归档历史。
- GitHub 未存在的归档分支由首次上传自动创建。

下一步：

1. 每天 01:10 Australia/Sydney 检查 automation run 是否成功。
2. 若 preflight 失败，先修设备/repo/owner confirmation 差异，不手动绕过。
3. 若 GitHub push 或远程验证失败，保留本机旧数据和缓存，先修 remote/auth。
4. 若 Air 长期低于 70GB free 或 swap 超过 1GB，减少本地重负载并转 Pro/Codespaces。

验证结果：

- `python3 -m unittest discover -s OpenAIDatabase/macdata/airM2/tests -p 'test_*.py'`：4 tests OK。
- `python3 OpenAIDatabase/macdata/airM2/scripts/run_controlled_cycle.py --repo-root . --preflight-only`：ok true。
- `git ls-remote https://github.com/LinzeColin/CodexProject.git refs/heads/main refs/heads/macdata-airM2`：main 与归档分支 hash 已返回。
