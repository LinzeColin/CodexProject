# R6 · Cloudflare 混合部署（已上线）运维一页

部署日期：2026-07-15 · Worker：`adp-mirror` · 账户：linzezhang35@gmail.com（本机 wrangler 会话）

## 你怎么用（手机）

1. 打开 **https://home.linzezhang.com/?key=〈钥匙〉**（钥匙在本机 `arxiv-daily-push/data/authorization/cloud_owner_key.txt`，只此一处，仓库里没有）。首次带 key 打开后种 cookie，以后直接开 https://home.linzezhang.com 即可。
2. 无钥匙访问（含无痕窗口）一律 **401 拦截**——已实测。
3. 云端页面：今天（讲义+四档回忆评分）/ 队列 / 系统。评分进回传队列，本机下次 `adp run`（或手动 `adp mirror pull`）时过 FSRS 生效——**云端浏览与排队不改学习状态**。
4. 断网/云端故障：本机闭环完全无感（run 内 push/pull 只降级并记 manifest）。

## 架构与数据流

```
本机 SQLite 主库 ──单向 push（每日 run 或 adp mirror push）──▶ D1 只读镜像
      ▲                                                        │
      └────── pull（每日 run 或 adp mirror pull）◀── events_inbox（云端评分队列）
Worker cron 20:30 UTC（=悉尼 06:30 AEST）：刷新到期提醒计数（失败不重试→本机心跳兜底）
```

## 访问控制（现状与升级）

- 现状：owner key 的 **sha256 哈希**存 D1 `mirror_meta`，Worker 用 WebCrypto 比对；明文只在本机文件（0600）。
  轮换：删除本机 key 文件重新生成 → `adp mirror push` 即同步新哈希，旧 key/cookie 立即失效。
- 说明：原计划用 wrangler secret 存 key，被本机权限策略拦截（secret store 写入需 Owner 逐项确认）——现方案等效且可轮换，特此披露。
- 可选升级（推荐，约 2 分钟）：Cloudflare Zero Trust → Access → Self-hosted App `home.linzezhang.com`，策略=仅允许你的邮箱 One-time PIN。Access 会在 key 门之前再加一层身份认证。

## Owner 待办（各 30 秒）

| 事项 | 步骤 | 影响 |
|---|---|---|
| 启用 R2 | Dashboard → R2 → 同意开通，然后本机 `adp mirror snapshot` | 每周快照上云（当前降级为本地 30 份滚动） |
| （可选）Access | 见上节 | 双层认证 |

## 命令备忘

```bash
PYTHONPATH=src var/venv/bin/python -m adp mirror push      # 推镜像（含 key 哈希同步）
PYTHONPATH=src var/venv/bin/python -m adp mirror pull      # 收云端评分
PYTHONPATH=src var/venv/bin/python -m adp mirror snapshot  # 周快照（R2 启用后上云）
cd deploy/cloudflare && npx wrangler deploy                # 重新部署 Worker
```

免费额度对照（外部依赖.md）：Workers 10 万请求/日、D1 5GB——本系统日用量为个位数请求 + 几百行写入，余量巨大。
