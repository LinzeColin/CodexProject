# Linze Golden Path (骨架 · STAGE-13.1)

一次接线, 之后每个可部署新项目 push 到 main 即自动 verify→部署→上 home。

## 组成
- `.github/workflows/linze-golden-path.reusable.yml` — 可复用工作流 (verify/deploy/home-sync)
- `GOLDEN_PATH/caller-example.yml` — 各仓调用示例

## 部署触发的前置(二选一, 均需 Owner 一次)
Coolify 当前只在服务器本地可达 (8000 被 ufw 挡公网), GitHub Runner 无法直连。要让 push 自动部署, 需其一:
1. **暴露控制面**: 给 Coolify 设实例域名 `server.linzezhang.com` (走其自带 Traefik + LE, 登录受保护),
   然后把 `COOLIFY_BASE_URL=https://server.linzezhang.com` + 最小 deploy 权限 `COOLIFY_API_TOKEN` 存为仓库/组织 Secret。
2. **Coolify GitHub App**: 在 Coolify 里装 GitHub App, 由 Coolify 监听 push 自行拉取部署 (无需入站),
   私有仓也适用。此法不走本工作流的 webhook 分支。

## 待办 (生产化)
- 所有 action 固定到 commit SHA
- verify job 接入各仓真实测试/契约校验
- home-sync 接 LinzeHomeHub projects.json 自动生成卡片
- 部署仅允许由不可变版本 (tag/SHA) 触发

## 现状
本骨架已写好、**本地提交、未推**。Owner 认可 + 选定上面触发方式后再推 main 并接线。
