# Memory Atlas v1.1.5 Stage 8 Release Notes

状态：Stage 8.1、Stage 8.2 和 Stage 8 整体复审已完成；GitHub main 上传需在最终 fast-forward 远端检查后执行。

## 本轮变化

- 本地 App 打包更稳：`~/Downloads/Memory Atlas.app` 和
  `/Applications/Memory Atlas.app` 使用 Application Support runtime，
  每次启动刷新脱敏快照并写入 runtime manifest。
- 本地 launcher 支持 npm / pnpm 两条依赖路径，缺少 Pillow 时也能生成
  `MemoryAtlas.icns`。
- Release Safety 新增 `validate:stage8-release-safety`，验证 Galaxy 与
  Timeline 的 feature flag rollback。
- Stage 8 整体复审新增 `validate:stage8`，统一复跑本地 App 打包、
  Release Safety、offline Cloudflare Pages + Access preflight、文档一致性和
  4177 cleanup。
- Galaxy 默认仍是 `memory-starfield`，可回滚到 `legacy`。
- Timeline 默认仍是 `memory-river`，可回滚到 `legacy`。

## 回滚

Galaxy 回滚方式：

- URL：`?galaxyRenderer=legacy`
- localStorage：`memory-atlas.galaxy-renderer = legacy`
- 环境变量：`VITE_MEMORY_ATLAS_GALAXY_RENDERER=legacy`
- UI：进入 `银河星云`，点击 `Legacy`

Timeline 回滚方式：

- URL：`?timelineRenderer=legacy`
- localStorage：`memory-atlas.timeline-renderer = legacy`
- 环境变量：`VITE_MEMORY_ATLAS_TIMELINE_RENDERER=legacy`
- UI：进入 `时间轴`，点击 `Legacy`

恢复新 renderer：

- Galaxy 使用 `memory-starfield` / `Flow Field`
- Timeline 使用 `memory-river` / `Memory River`

## 安全边界

- Memory Atlas 仍只读取脱敏派生快照。
- 前端写回仍是 proposal-only，不直接修改 active memory。
- 不包含 raw/private/cookie/session/secret。
- 不包含 Cloudflare live deploy。
- 不包含 Access policy change。

## 尚未完成

- GitHub main 上传。
- Cloudflare live deploy 仍需用户明确授权账号、邮箱或访问策略。
