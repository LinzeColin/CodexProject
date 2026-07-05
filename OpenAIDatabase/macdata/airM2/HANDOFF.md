# airM2 macdata HANDOFF

更新时间：2026-07-05T21:36:51+10:00

当前目标：安装并启用 `airM2` macdata Codex Automation 任务包，提交到 `LinzeColin/CodexProject`，并建立 `macdata-airM2` 归档分支。

当前状态：

- 本机硬件已确认为 `MacBook Air / Mac14,2 / Apple M2 / 8GB`。
- 任务包已安装到 `OpenAIDatabase/macdata/airM2`。
- 用户确认文件已创建：`config/owner_confirmations.json`。
- 用户覆盖任务包默认边界：允许 raw 远程验证成功后执行受控 Docker/Homebrew/用户态系统缓存/项目缓存清理。

关键决策：

- Time Machine 不采集，iCloud 不使用。
- API key、token、password 及等价凭证禁止进入 GitHub。
- `main` 保存任务包和配置；`macdata-airM2` 保存每日归档历史。
- GitHub 未存在的归档分支由首次上传自动创建。

下一步：

1. 运行单元测试和预检。
2. 提交并 push `main`。
3. 执行一次完整受控运行，创建或更新 `macdata-airM2`。
4. 验证远程 hash 后才允许本机旧数据与受控缓存清理。
