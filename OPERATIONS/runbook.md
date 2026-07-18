# Linze Operate Runbook (OVH VPS-1 主节点)

> 敏感值(密钥/密码/token)不在本仓;均存运维私有保险柜 `_protected/`。本文件只写「怎么做」。

## 1. 系统拓扑
- 主机: OVH Singapore VPS-1 (amd64, Ubuntu 24.04),纯 SSH key 登录(密码登录已关)
- 容器编排: Docker + Coolify 4.1.2(控制面,8000 仅本机+ufw 挡公网)
- 反代/TLS: Coolify Traefik(entrypoints http/https,certresolver letsencrypt,网络 coolify)
- 已上线服务:
  - 身份 `account.linzezhang.com` — Keycloak 26 + Postgres(`/srv/linze/apps/identity`)
  - 监控 `status.linzezhang.com` — Gatus(`/srv/linze/apps/monitoring`)
- 目录: `/srv/linze/{apps,data,logs,backups,secrets,staging}`(secrets 700)

## 2. 备份(均离机副本 + 本机保留 14 份)
| 对象 | 脚本 | cron | 位置 |
|---|---|---|---|
| Coolify DB+.env | /usr/local/bin/linze-coolify-backup.sh | 03:17 UTC | /srv/linze/backups/coolify |
| 身份 keycloak DB+.env | /usr/local/bin/linze-identity-backup.sh | 03:37 UTC | /srv/linze/backups/identity |

关键恢复材料另存 `_protected/`: Coolify .env(APP_KEY)、Keycloak pg/admin 密码、各 token。

## 3. 恢复(RESTORE)—— 已实测通过
### 身份 DB
```
DUMP=$(ls -1t /srv/linze/backups/identity/keycloak-db-*.sql.gz | head -1)
docker exec -i identity-identity-postgres-1 psql -U keycloak -d keycloak < <(gunzip -c "$DUMP")
docker restart identity-keycloak-1
```
校验: `curl -s https://account.linzezhang.com/realms/linze/.well-known/openid-configuration`(issuer 正确)
### Coolify DB
```
DUMP=$(ls -1t /srv/linze/backups/coolify/coolify-db-*.sql.gz | head -1)
gunzip -c "$DUMP" | docker exec -i coolify-db psql -U coolify -d coolify
```
> 演练方式(不碰生产): 起临时 `postgres:16-alpine`,导入 DUMP,核对行数,再销毁。两库均已如此演练并一致。

## 4. 回滚(ROLLBACK)
- 应用部署: Coolify 每个应用保留历史部署,`POST /api/v1/applications/{uuid}` 或面板可回滚到上一个成功镜像。
- 配置回滚: sshd/ufw/docker daemon 配置改动前先 `cp *.bak`;身份/监控 compose 在 git 或 `/srv/linze/apps/*`,改前留档。
- realm 配置: 定期 `GET /admin/realms/linze/partial-export` 存档,回滚用 `partialImport`。

## 5. 主机重建(REBUILD)
1. OVH 重装 Ubuntu 24.04 + 绑定 `linze-ovh-production` 公钥
2. 跑 bootstrap(ufw/fail2ban/swap/docker/目录) — 见 PLATFORM 脚本
3. 装 Coolify,用 `_protected/` 的 .env 恢复 APP_KEY,导入 Coolify DB 备份
4. 起身份/监控 compose,导入 keycloak DB 备份
5. DNS 已指向同 IP 则无需改;换 IP 则更新 A 记录(account/status)

## 6. 迁移(MIGRATE)
- 所有状态在: Docker 具名卷 + Postgres 备份 + `_protected/` 密钥 + compose 文件。
- 换主机 = 主机重建流程 + 更新 Cloudflare A 记录指向新 IP。无本机绝对路径依赖(除 `/srv/linze`,可重建)。

## 7. 监控/告警
- Gatus @ status.linzezhang.com 盯身份站+现有站。告警通道(邮件/webhook)待 NitroSend 批准或接免费 webhook 后加。

## 8. 已知待办
- 离机备份目标(R2/Oracle)接入后,把本机备份同步出去(当前仅 `_protected/` 存关键恢复材料)
- Coolify 整机(卷)级备份;告警通道
