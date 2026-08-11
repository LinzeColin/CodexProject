#!/bin/bash
# 迁移验收 goal —— VPS-1 → VPS-3 是否真的完成,靠这一条命令判定,不靠人记。
#
# 2026-08-10 迁移当天写下。判据是「owner 能不能做成他昨天能做成的事」,
# 所以查的是**域名可访问 + 容器健康 + 数据在 + 备份能跑**,不是「脚本存在」。
# 任一项失败即非零退出,可挂 cron 或 CI。
set -uo pipefail
FAIL=0
ok(){ printf "  ✓ %s\n" "$*"; }
no(){ printf "  ✗ %s\n" "$*"; FAIL=$((FAIL+1)); }

echo "═══ 迁移验收 $(date -u +%FT%TZ) ═══"

echo "【1】域名对外可访问(清单从 Cloudflare DNS 动态取,不手写)"
# 2026-08-11 事故:这里原来手写 9 个域名,而 **weread 和 weread-api 不在里面**。
# 结果 weread 的边缘链路断了整整一天(Worker 回源 weread-api → traefik 无此 Host → 503),
# 用户打开就是「账户服务尚未完成安全连接」,而这 13 项验收**全绿**。
# 又一次「口径只覆盖子集却当成全局」—— 手写清单必然漏,而且漏的那个永远不会自己冒出来。
#
# 现在从 Cloudflare DNS 拉真实子域列表。拉不到就**退回内置清单并报一条**,
# 不能因为取不到清单就当成"没有域名要测"(那是最坏的假绿)。
DOMS=""
# 清单由 /usr/local/bin/linze-cf-web-domains.py 从 Cloudflare DNS 拉。
# 拆成独立脚本而不是内嵌 python:第一版内嵌时被 shell 逐层吞掉引号,静默取不到清单。
if [ -r /etc/linze/cf-dns.env ]; then
  set -a; . /etc/linze/cf-dns.env; set +a
  DOMS=$(/usr/local/bin/linze-cf-web-domains.py 2>/dev/null)
fi
if [ -z "$DOMS" ]; then
  # 取不到清单**必须报一条**,不能当成"没有域名要测" —— 那是最坏的假绿。
  no "取不到 Cloudflare DNS 清单,退回内置列表(可能漏测新域名)"
  DOMS=$(printf "%s\n" home pfi serenity kmfa account uptime jobhunt status server weread weread-api \
    | sed "s/$/.linzezhang.com/")
fi
echo "    本轮测 $(printf "%s\n" "$DOMS" | grep -c .) 个域名"
for d in $DOMS; do
  # 单次 curl 偶尔会返回 000(自己超时,不是服务坏) —— 2026-08-10 连跑三次就中了一次。
  # 这脚本挂着每日 cron,单次判定会周期性假红;而假红比没有告警更糟。所以失败重试一次,
  # 两次都不通才算真不通。真出故障时两次一样红,灵敏度没有损失。
  c=$(curl -s -o /dev/null -w '%{http_code}' -m 15 -L "https://$d/" 2>/dev/null)
  case "$c" in 2*|3*) ;; *) sleep 3; c=$(curl -s -o /dev/null -w '%{http_code}' -m 25 -L "https://$d/" 2>/dev/null) ;; esac
  case "$c" in 200|301|302|304|401|403) ok "$d ($c)";; *) no "$d ($c)";; esac
done

echo "【2】容器健康"
u=$(docker ps --filter health=unhealthy -q | wc -l)
r=$(docker ps -q | wc -l)
[ "$u" -eq 0 ] && ok "$r 个容器运行,0 异常" || no "$u 个容器 unhealthy"
for n in coolify eei-db identity-keycloak-1 linze-status linze-status-admin monitoring-gatus-1 linze-smtp-bridge; do
  docker ps --format '{{.Names}}' | grep -qx "$n" && ok "$n" || no "$n 未运行"
done

echo "【3】数据在位"
for q in "eei-db|eei|eei|51" "identity-identity-postgres-1|keycloak|keycloak|87"; do
  IFS='|' read -r c u d exp <<< "$q"
  n=$(docker exec "$c" psql -U "$u" -d "$d" -tAc "select count(*) from information_schema.tables where table_schema='public'" 2>/dev/null | tr -d ' ')
  [ "$n" = "$exp" ] && ok "$d 库 $n 张表" || no "$d 库 $n 张表(应 $exp)"
done
[ -s /srv/linze/apps/status/data/snapshot.json ] && ok "status 快照存在" || no "status 快照缺失"

echo "【4】资源(迁移的意义所在)"
m=$(free -m | awk 'NR==2{printf "%d",$3/$2*100}')
d=$(df -P / | awk 'NR==2{gsub("%","",$5);print $5}')
[ "$m" -lt 60 ] && ok "内存 ${m}%" || no "内存 ${m}% 偏高"
[ "$d" -lt 70 ] && ok "磁盘 ${d}%" || no "磁盘 ${d}% 偏高"
s=$(free -m | awk 'NR==3{print $3}')
[ "$s" -lt 100 ] && ok "swap ${s}MB" || no "swap ${s}MB(不该用到)"

echo "【5】定时任务与守卫"
n=$(ls -1 /etc/cron.d/linze-* 2>/dev/null | wc -l)
[ "$n" -ge 13 ] && ok "$n 个 cron" || no "只有 $n 个 cron"
[ -x /usr/local/bin/linze-r2-free-tier-guard.py ] && ok "R2 零收费守卫在岗" || no "R2 守卫缺失"

echo "【6】常驻业务服务(2026-08-10 补:这批曾整体漏迁)"
# 迁移当天发现:清点只看了 timer,漏掉 10 个常驻 service —— 4 条 cloudflared 隧道
# 全在里面。域名当时仍是 200,因为 VPS-1 还活着在扛流量,退役那一刻才会塌。
# 所以这一节按「服务在不在跑」判,不看域名。
for s in weread-port-platform weread-port-import-worker social-archive-status-web \
         social-archive cloudflared cyberboss-cf-tunnel cyberboss-cloud \
         abd-shadow-cloudflared social-archive-cloudflared chatgpt-local-context-mcp \
         memory-atlas-api memory-atlas-api-proxy; do
  [ "$(systemctl is-active "$s.service" 2>/dev/null)" = "active" ] && ok "$s" || no "$s 未运行"
done
# socket 激活的桥:service 平时是 inactive,只有 socket 必须在
[ "$(systemctl is-active weread-port-traefik-bridge.socket 2>/dev/null)" = "active" ] \
  && ok "weread-port-traefik-bridge.socket" || no "weread-port-traefik-bridge.socket 未监听"

echo "【7】业务 timer 上次执行结果"
bad=0; tot=0
for t in $(systemctl list-timers --all --no-pager 2>/dev/null \
           | grep -oE "[a-z0-9@-]+\.timer" \
           | grep -vE "^(apt|dpkg|fstrim|logrotate|man-db|motd|systemd|e2scrub|update-notifier|ua-|anacron|snapd|plocate)" \
           | sort -u); do
  svc="${t%.timer}.service"
  # weread-port-platform-health 交给第 9 项按**实测**判:它每几分钟跑一次,
  # 单次瞬时失败会让"上次退出码"挂一整天,在这里报就是拿历史当现状。
  [ "$svc" = "weread-port-platform-health.service" ] && continue
  tot=$((tot+1))
  st=$(systemctl show "$svc" -p ExecMainStatus --value 2>/dev/null)
  res=$(systemctl show "$svc" -p Result --value 2>/dev/null)
  if [ -n "$st" ] && [ "$st" != "0" ] && [ "$res" != "success" ]; then
    bad=$((bad+1)); no "$svc 上次退出码 $st"
  fi
done
[ "$bad" -eq 0 ] && ok "$tot 个业务 timer 上次执行均成功"

echo "【8】KMFA 业务密钥非空"
# 2026-08-10 的坑:Coolify 库里有行、值也在,但每个 key 有两行,容器拿到的是空的那行;
# 而且每次部署 Coolify 会按 compose 重新同步变量行,把手工改的值刷掉。
# 只能按「容器里实际拿到什么」判 —— 查库会假绿。
c=$(docker ps --format '{{.Names}}' 2>/dev/null | grep '^skills-' | head -1)
if [ -z "$c" ]; then
  no "skills 容器未运行,无法校验密钥"
else
  empty=0
  for k in KMFA_PRIVATE_DB_READ_TOKEN KMFA_PAYROLL_PASSWORD KMFA_BACKUP_SSH_KEY_B64 \
           KMFA_CLOUDFLARE_ACCESS_AUD KMFA_CLOUDFLARE_ACCESS_TEAM_DOMAIN \
           DAILY_FUNDS_R2_ACCESS_KEY_ID DAILY_FUNDS_R2_SECRET_ACCESS_KEY \
           DAILY_FUNDS_R2_BUCKET DAILY_FUNDS_R2_ENDPOINT_URL \
           DAILY_FUNDS_CLOUDFLARE_API_TOKEN DAILY_FUNDS_D1_DATABASE_ID \
           DAILY_FUNDS_CF_ACCOUNT_ID DAILY_FUNDS_GIT_SSH_KEY_B64 \
           DAILY_FUNDS_GROUP_ID DAILY_FUNDS_SENDER_ID DAILY_FUNDS_OCI_PAR_URL \
           DAILY_FUNDS_RESTORE_DRILL_D1_DATABASE_ID KMFA_DWS_DATA_AUTH_REQUEST; do
    v=$(docker exec "$c" printenv "$k" 2>/dev/null)
    [ -n "$v" ] || { empty=$((empty+1)); no "密钥 $k 在容器里是空的"; }
  done
  [ "$empty" -eq 0 ] && ok "18 个 KMFA 业务密钥在容器内均非空"
fi

echo "【9】R2 对象存储可写(令牌 IP 白名单)"
# 迁移当天最隐蔽的一个:R2 令牌带 Client IP Filtering,只放行 VPS-1。
# 换机后同一份凭据 AccessDenied,而 env 逐键哈希完全一致 —— 查配置永远查不出来。
# 只能实打一次。weread 的健康检查本来就会做 PUT/GET/DELETE,直接复用它的判定。
# 这里读的是**上一次定时执行留下的快照**。2026-08-10 实测到一个陷阱:
# 只要有一次瞬时失败(当时另一个会话正在同机构建镜像,资源争抢导致 readyz 超时),
# 这条就会红一整天 —— 报的是历史,不是现在。所以快照说不 ok 时,**当场重测一次**,
# 以新结果为准。真正的故障(比如 R2 令牌没放行本机 IP)重测一样红,灵敏度不受影响。
if [ -s /var/lib/weread-port/platform-health.json ]; then
  r=$(python3 -c 'import json;d=json.load(open("/var/lib/weread-port/platform-health.json"));print("1" if d.get("ok") else "0")' 2>/dev/null)
  if [ "$r" != "1" ]; then
    systemctl reset-failed weread-port-platform-health.service 2>/dev/null
    systemctl start weread-port-platform-health.service 2>/dev/null
    sleep 8
    r=$(python3 -c 'import json;d=json.load(open("/var/lib/weread-port/platform-health.json"));print("1" if d.get("ok") else "0")' 2>/dev/null)
  fi
  if [ "$r" = "1" ]; then
    ok "weread 平台就绪(含 R2 写读删实测)"
  else
    ec=$(python3 -c 'import json;d=json.load(open("/var/lib/weread-port/platform-health.json"));print(d.get("errorCode","?"))' 2>/dev/null)
    no "weread 平台未就绪(重测仍失败,errorCode=$ec)—— 先查 R2 令牌是否放行本机 IP"
  fi
else
  no "weread 健康快照缺失"
fi

echo "【10】abd-shadow 影子容器"
# restart 策略是 no(与 VPS-1 一致),重启主机后不会自己回来 —— 所以必须有人盯
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q '^abd-shadow-blue-abd-shadow-1$'; then
  p=$(docker inspect --format '{{range $k,$v := .HostConfig.PortBindings}}{{range $v}}{{.HostPort}}{{end}}{{end}}' abd-shadow-blue-abd-shadow-1 2>/dev/null)
  code=$(curl -s -o /dev/null -m 8 -w '%{http_code}' "http://127.0.0.1:${p:-8081}/healthz" 2>/dev/null)
  [ "$code" = "200" ] && ok "abd-shadow 运行且 /healthz 200" || no "abd-shadow 在跑但 /healthz=$code"
else
  no "abd-shadow 容器未运行(restart=no,重启主机后需手工拉起)"
fi

echo "【11】旧主机 IP 残留(退役后仍指向 VPS-1 的都会静默失效)"
# 2026-08-10:/etc/weread-port/platform.env 里写着 RCLONE_BIND=139.99.61.6 ——
# rclone 把出站源地址绑到 VPS-1 的 IP,新机上没有这个地址,bind 直接失败。
# 报错是 "cannot assign requested address",跟凭据、跟网络都不像,极难联想到换机。
#
# 判据必须收紧到「真的把旧 IP 当目标用」,否则会自己造假红 —— 第一版只要文件里
# 出现旧 IP 就报,结果把两类东西也算进去了:
#   a) evidence/ 下的历史验收记录 —— 那是当时的事实,改了就是伪造历史;
#   b) 我自己写的「VPS-1 已退役」提示 —— 那句话本来就得提旧 IP 才说得清。
# 假红比没有告警更糟:一旦习惯了红色,真出事那次也不会有人看。
OLD_IP="139.99.61.6"
hits=$(grep -rn "$OLD_IP" /etc /srv/linze/apps /opt/weread-port/current /opt/cyberboss-cloud/current 2>/dev/null \
        | grep -vE "\.bak|linze-migration-goal\.sh|known_hosts" \
        | grep -vE "/(evidence|_archive|archive)/" \
        | grep -vE "退役|已迁|迁到|主机变更|retired|migrated" \
        | grep -E "(ssh|scp|rsync|curl|HOST=|BIND=|host:|@)$OLD_IP|$OLD_IP:" \
        | head -5)
if [ -n "$hits" ]; then
  while read -r l; do [ -n "$l" ] && no "旧 VPS-1 IP 仍被当作目标使用:${l%%:*}"; done <<< "$hits"
else
  ok "配置里没有把已退役的 VPS-1 IP 当目标用"
fi

echo "【12】rclone 版本(发行版包缺 OCI 后端)"
# VPS-3 装机自带 rclone v1.60.1-DEV(Ubuntu 包),而 OCI 冷备要 oracleobjectstorage
# 后端 —— 那是 v1.6x 之后才有的。版本不对时报 "didn't find backend called
# oracleobjectstorage",看起来像配置写错,实际是二进制太老。
if command -v rclone >/dev/null 2>&1; then
  if rclone help backends 2>/dev/null | grep -qi oracle; then
    ok "rclone $(rclone version 2>/dev/null | head -1 | awk '{print $2}') 含 oracleobjectstorage 后端"
  else
    no "rclone $(rclone version 2>/dev/null | head -1 | awk '{print $2}') 缺 oracleobjectstorage 后端 —— OCI 异地冷备会失败"
  fi
else
  no "rclone 未安装"
fi

echo "【13】重启后能不能自己回来(2026-08-10 一次重启实证)"
# 这一项是拿一次真重启换来的。当时 VPS-3 重启后有三样东西没回来:
#   - memory-atlas-api  → 一直是 active 但 enabled=disabled(有人手工起的),重启即丢
#   - abd-shadow 容器   → restart=no,重启即丢
#   - traefik-bridge.socket → failed,要 reset-failed 才肯起
# 共同点:**平时看它们都在跑,完全正常**,只有重启那一刻才暴露。所以不能等重启后再查,
# 要在平时就查"它是否具备重启后自己回来的能力"。
miss=0
for s in weread-port-platform weread-port-import-worker social-archive-status-web \
         social-archive cloudflared cyberboss-cf-tunnel cyberboss-cloud \
         abd-shadow-cloudflared social-archive-cloudflared chatgpt-local-context-mcp \
         memory-atlas-api; do
  # static/indirect 是被别的单元拉起的,不需要 enabled —— 只揪 disabled
  en=$(systemctl is-enabled "$s.service" 2>/dev/null)
  if [ "$en" = "disabled" ]; then
    miss=$((miss+1)); no "$s 在跑但 enabled=disabled —— 重启后不会自己回来"
  fi
done
[ "$miss" -eq 0 ] && ok "常驻服务均可开机自启"
# 容器侧:restart=no 的容器重启后同样不回来
# coolify-sentinel 例外:它的 restart=no 是设计如此,Coolify 启动时会自己重建它。
# 这不是猜的 —— 2026-08-10 那次重启实测:主机 19:47 重启,sentinel 19:48:12 自己起来了。
# 不排除它就会天天报一条永远修不掉的红,而假红比没有告警更糟:习惯了红色,真出事那次也没人看。
cbad=$(docker ps --format '{{.Names}}' 2>/dev/null | grep -vx 'coolify-sentinel' | while read -r c; do
  [ -n "$c" ] || continue
  p=$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' "$c" 2>/dev/null)
  [ "$p" = "no" ] || [ -z "$p" ] && echo "$c"
done | head -3)
if [ -n "$cbad" ]; then
  while read -r c; do [ -n "$c" ] && no "容器 $c 的 restart 策略是 no —— 重启后不会自己回来"; done <<< "$cbad"
else
  ok "所有运行中容器都带重启策略"
fi

echo ""
[ "$FAIL" -eq 0 ] && { echo "═══ 全绿:迁移完成 ═══"; exit 0; } || { echo "═══ $FAIL 项未达标 ═══"; exit 1; }
