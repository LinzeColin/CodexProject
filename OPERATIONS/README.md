# OPERATIONS —— 生产主机上跑的东西

## 为什么会有这个目录(2026-08-11 建)

在此之前,OVH 生产主机上有 **14 个 `/usr/local/bin/linze-*.sh` 和 14 个 `/etc/cron.d/linze-*`,
源码一个都不在任何仓里** —— `schedule_registry.yaml` 登记了它们的调用路径、用途、日志位置,
但没有代码本身。也就是说:**那台机器一旦没了,这些脚本就没了。**

这个缺口是在 2026-08-10 的 VPS-1 → VPS-3 迁移里暴露的。那次迁移全靠一台一台 `tar` 对拷,
中途发现过三批漏迁(10 个常驻 service、整个 signal-lattice、4 个 `/srv` 顶层目录);
如果当时旧机是硬件故障而不是计划退役,这些只存在于机器上的东西没有任何一份可以回滚的副本。

## 目录含义

| 目录 | 对应主机路径 | 说明 |
|---|---|---|
| `host-bin/` | `/usr/local/bin/` | 定时任务与守卫脚本本体 |
| `host-cron/` | `/etc/cron.d/` | 触发它们的 cron 条目 |
| `schedule_registry.yaml` | —— | 调度登记表(谁在什么时候跑、日志在哪、谁负责) |
| `runbook.md` | —— | 处置手册 |

## 同步方向:**仓是源,主机是部署产物**

改动一律先改仓、再部署到主机;不要反过来在主机上改完就算完 —— 那正是这些脚本
一年多都没进版本控制的原因。

部署单个脚本:

```bash
KEY=~/Documents/Codex/GithubProject/_protected/alpha_deploy_private/linze_ovh_production_ed25519
scp -i "$KEY" OPERATIONS/host-bin/linze-xxx.sh ubuntu@15.235.141.201:/tmp/
ssh -i "$KEY" ubuntu@15.235.141.201 'sudo install -m 755 -o root -g root /tmp/linze-xxx.sh /usr/local/bin/ && rm -f /tmp/linze-xxx.sh'
```

**核对仓与主机是否已分叉**(定期跑,或改动前跑):

```bash
KEY=~/Documents/Codex/GithubProject/_protected/alpha_deploy_private/linze_ovh_production_ed25519
for f in OPERATIONS/host-bin/*; do
  n=$(basename "$f")
  a=$(shasum -a 256 "$f" | cut -d' ' -f1)
  b=$(ssh -i "$KEY" ubuntu@15.235.141.201 "sudo shasum -a 256 /usr/local/bin/$n 2>/dev/null | cut -d' ' -f1")
  [ "$a" = "$b" ] && echo "✓ $n" || echo "✗ $n  仓=$a  机=$b"
done
```

## 凭据:这里一个都没有,也永远不要有

这 28 个文件上传前逐个扫过(高熵串 + `token=`/`secret=`/`password=` 赋值形态),**零命中**。
它们全部通过 `EnvironmentFile` 或读 `/etc/<项目>/*.env`、`/etc/<项目>/secrets/*` 取凭据,
不内嵌任何密钥 —— 保持这个写法。

铁律:`_protected/` 永不上传。真要托管凭据,走 Private-Database 私有仓 + AES-256 加密包,
口令只留本机 `_protected/`。

## 主机上还有什么没进仓(如实记,别假装干净)

以下是**有意不上传**的,各有原因:

| 内容 | 为什么不传 |
|---|---|
| `/etc/<项目>/*.env` | 含真实凭据。属 `_protected` 范畴 |
| `/etc/fail2ban/jail.local` | 含 owner 家宽网段(`ignoreip`),算环境信息 |
| `/srv/linze/apps/status/data/prices.json` | 运行态数据,owner 在 `/admin` 编辑,不是代码 |
| systemd unit 文件 | 一部分已在各自项目仓(如 `LinzeHomeHub/status/deploy/systemd/`),不跨仓搬 |

**这张表本身就是交付的一部分** —— 下一个人接手时,能一眼看出"仓里没有的是哪些、
为什么没有",而不是以为仓 = 全部。

## host-traefik/ —— 反向代理路由

对应主机 `/data/coolify/proxy/dynamic/`。

**为什么单独放而不是塞进 `coolify.yaml`**:那个文件由 Coolify 自动生成,顶部明写
「不要手工编辑」—— 它每次重新生成会把手工加的东西冲掉。traefik 的 file provider
扫整个 `dynamic/` 目录,独立文件同样生效且不会被覆盖。

**2026-08-11 事故**:VPS-1 → VPS-3 迁移时漏了 `weread-api.linzezhang.com` 这条路由。
后果是一条**谁都没在看的边缘链路**断了整天:

    Cloudflare Worker(weread-port) → 回源 https://weread-api.linzezhang.com
      → traefik 无此 Host → 落到 default_redirect_503 → 503
      → 页面显示「账户服务尚未完成安全连接」

而同一时刻:`127.0.0.1:8788/readyz` 返回 200、systemd 服务全 active、
13 项验收**全绿**、9 个域名全 200。**服务健康 ≠ 用户能用。**

漏掉的原因是验收的域名清单**手写了 9 个,weread 和 weread-api 都不在里面**。
现已改成从 Cloudflare DNS 动态取(21 个),见 `host-bin/linze-cf-web-domains.py`。
