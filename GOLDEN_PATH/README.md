# Linze Golden Path (骨架 · STAGE-13.1)

一次接线, 之后每个可部署新项目 push 到 main 即自动 verify→部署→上 home。

## 组成
- `.github/workflows/linze-golden-path.reusable.yml` — 可复用工作流 (verify/deploy/home-sync)
- `GOLDEN_PATH/caller-example.yml` — 各仓调用示例

## 部署触发方式
走 Coolify API：调用方把 `COOLIFY_BASE_URL`（控制面域名 `https://server.linzezhang.com`，Traefik + LE，登录受保护）
与最小 deploy 权限的 `COOLIFY_API_TOKEN` 存为仓库 Secret，本工作流据此触发部署。
（另一条路：在 Coolify 里装 GitHub App，由 Coolify 监听 push 自行拉取部署，不走本工作流的 webhook 分支，私有仓也适用。）

## 待办 (生产化)
- verify job 接入各仓真实测试/契约校验
- home-sync 接 LinzeHomeHub projects.json 自动生成卡片
- 部署仅允许由不可变版本 (tag/SHA) 触发

## 现状
工作流已在 main（PR #285 合入），并受 `governance/workflow_policy.json` 审计（action 全部固定到 commit SHA）。
调用方在各自仓的 `.github/workflows/` 里 `uses:` 本工作流；各服务的部署结果以调用方仓的 Actions 为准，本文不记录运行状态。
