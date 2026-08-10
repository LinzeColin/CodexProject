#!/bin/bash
# 2 天保留自愈 —— OVH 只留 2 天的运行数据与日志。
#
# 为什么需要它(2026-08-02 盘点):
#   - status-gate 每跑一轮 gate 就留一份 483M 的 node 工具链,一天跑 5 轮 = 2.4G
#   - syslog 一天涨几百 M
#   - 整机加密归档每份 108M 且每天 +8M,本地却留 7 份
#   38G 的盘按这个速度几天就满。linze-selfheal 只在 ≥85% 时清"可回收空间",
#   清不动上面这些 —— 它日志里连续出现 "88%→88%"、"97%→93%" 就是清不动的证据。
#
# 分工(照 owner 定的权威层边界):
#   OVH   = 计算节点,磁盘只留必要短期运行数据
#   GitHub Private-Database = 长期事实与运行日志归档
#   OCI   = 冷备的异地备份(周日)
#   R2    = 既有对象只读保留；零付费策略禁止 Runtime Journal 按日期持续新增
#
# 处置策略:
#   可重建的(npm 缓存 / node_modules / venv)     → 直接删,不浪费带宽归档
#   运行数据与日志(spool / superseded / *.log)   → 打包加密 → 上传 → 再删
#   整机备份                                      → 本地留 2 份(GitHub 已有 30 份滚动)
#
# 零 agent、零模型调用:纯 bash + curl。
# 由 /etc/cron.d/linze-retention 每日 02:40 UTC 跑(排在 03:40 整机备份之前)。
set -uo pipefail

RETAIN_DAYS=2
KEEP_LOCAL_BACKUPS=2
KEEP_REMOTE_JOURNALS=30
MAX_ARCHIVE_MB=300              # 单次归档硬上限,防止盘不够或传输失控
MIN_FREE_MB=2048                # 低于这个可用空间就跳过归档、只做删除

GH_TOKEN=$(cat /srv/linze/secrets/github_backup_pat 2>/dev/null)
PAR=$(cat /srv/linze/secrets/oci_par_url 2>/dev/null)
ENCKEY=/srv/linze/secrets/backup_enc.key
GH_REPO=LinzeColin/Private-Database
GH_TAG=runtime-journal
LOG=/srv/linze/logs/retention.log
TS=$(date -u +%Y%m%d-%H%M%S)
WORK=/srv/linze/work/retention-$TS

DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

mkdir -p "$(dirname "$LOG")" "$WORK"
say() { echo "$(date -u +%FT%TZ) $*" >> "$LOG"; [ -t 1 ] && echo "$*"; }
kb()  { du -sk "$1" 2>/dev/null | cut -f1; }
free_mb() { df -Pk / | awk 'NR==2{print int($4/1024)}'; }

FREED_KB=0
drop() {  # drop <路径> <理由>
  [ -e "$1" ] || return 0
  local s; s=$(kb "$1")
  if [ "$DRY_RUN" = 1 ]; then say "  [dry] 会删 $((s/1024))M  $1  ($2)"; return 0; fi
  rm -rf "$1" && FREED_KB=$((FREED_KB+s)) && say "  删 $((s/1024))M  $1  ($2)"
}

say "===== retention 开始 (保留 ${RETAIN_DAYS} 天, 可用 $(free_mb)MB, dry_run=$DRY_RUN) ====="

# ---------- 1) 可重建物:直接删,不归档 ----------
# status-gate 每轮 gate 的 node 工具链。保留最新一份供当前轮次复用。
LATEST_TC=$(ls -1dt /srv/status-gate/private/toolchain-* 2>/dev/null | head -1)
for d in $(ls -1dt /srv/status-gate/private/toolchain-* 2>/dev/null | tail -n +2); do
  [ "$d" = "$LATEST_TC" ] && continue
  drop "$d" "npm-cache+node_modules,npm ci 可重建"
done
# 更老的 venv / node_modules 残留
find /srv/linze/staging -maxdepth 1 -mtime +$RETAIN_DAYS 2>/dev/null | while read -r p; do
  [ -n "$p" ] && [ "$p" != "/srv/linze/staging" ] && drop "$p" "staging 遗留"
done

# ---------- 2) 运行数据:打包 → 加密 → 上传 → 删 ----------
STAGE="$WORK/journal"; mkdir -p "$STAGE"
COLLECTED=0
collect() {  # collect <路径> <归档子目录>
  [ -e "$1" ] || return 0
  local s; s=$(kb "$1")
  if [ $(( (s + $(kb "$STAGE")) / 1024 )) -gt "$MAX_ARCHIVE_MB" ]; then
    say "  ! 跳过归档(超 ${MAX_ARCHIVE_MB}M 上限): $1"; return 0
  fi
  mkdir -p "$STAGE/$2" && cp -a "$1" "$STAGE/$2/" 2>/dev/null && COLLECTED=1
}

if [ "$(free_mb)" -ge "$MIN_FREE_MB" ]; then
  # gate 的 spool 与已被取代的输入
  while read -r p; do collect "$p" status-gate; done < <(find /srv/status-gate/private -maxdepth 1 -name 'spool-*-gate' -mtime +$RETAIN_DAYS 2>/dev/null)
  while read -r p; do [ "$p" != "/srv/status-gate/private/superseded-inputs" ] && collect "$p" status-gate/superseded; done < <(find /srv/status-gate/private/superseded-inputs -maxdepth 1 -mtime +$RETAIN_DAYS 2>/dev/null)
  # 已轮转的系统日志
  while read -r p; do collect "$p" var-log; done < <(find /var/log -maxdepth 1 -type f \( -name '*.gz' -o -name '*.[0-9]' \) -mtime +$RETAIN_DAYS 2>/dev/null)
  # 应用日志
  while read -r p; do collect "$p" app-logs; done < <(find /srv/linze/logs /srv/linze/apps/status -maxdepth 1 -type f -name '*.log' -mtime +$RETAIN_DAYS 2>/dev/null)
else
  say "  ! 可用空间 $(free_mb)MB < ${MIN_FREE_MB}MB,跳过归档,只做删除"
fi

GH_CODE=skip; OCI_CODE=skip
if [ -n "$(ls -A "$STAGE" 2>/dev/null)" ] && [ "$DRY_RUN" = 0 ]; then
  TAR="$WORK/linze-journal-${TS}.tar.gz"
  tar -czf "$TAR" -C "$STAGE" . 2>/dev/null
  ENC="${TAR}.enc"
  openssl enc -aes-256-cbc -pbkdf2 -salt -in "$TAR" -out "$ENC" -pass file:"$ENCKEY" && rm -f "$TAR"
  NAME=$(basename "$ENC"); SZ=$(stat -c%s "$ENC" 2>/dev/null)

  if [ -n "$GH_TOKEN" ] && [ -s "$ENC" ]; then
    RID=$(curl -s -m 30 -H "Authorization: Bearer $GH_TOKEN" \
          "https://api.github.com/repos/$GH_REPO/releases/tags/$GH_TAG" \
          | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
    if [ -z "$RID" ]; then   # tag 不存在就建一次
      RID=$(curl -s -m 30 -X POST -H "Authorization: Bearer $GH_TOKEN" \
            -d "{\"tag_name\":\"$GH_TAG\",\"name\":\"Runtime Journal\",\"body\":\"OVH 运行数据与日志的 2 天滚动归档,由 linze-retention-2d.sh 自动上传。\",\"prerelease\":true}" \
            "https://api.github.com/repos/$GH_REPO/releases" \
            | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
    fi
    if [ -n "$RID" ]; then
      GH_CODE=$(curl -s -m 300 -o /dev/null -w '%{http_code}' \
        -H "Authorization: Bearer $GH_TOKEN" -H "Content-Type: application/octet-stream" \
        --data-binary @"$ENC" \
        "https://uploads.github.com/repos/$GH_REPO/releases/$RID/assets?name=$NAME")
      # 远端滚动保留
      curl -s -m 30 -H "Authorization: Bearer $GH_TOKEN" \
        "https://api.github.com/repos/$GH_REPO/releases/$RID/assets?per_page=100" \
        | python3 -c "
import sys,json
a=[x for x in json.load(sys.stdin) if x.get('name','').startswith('linze-journal-')]
a.sort(key=lambda x: x['created_at'])
for x in a[:max(0, len(a)-$KEEP_REMOTE_JOURNALS)]: print(x['id'])
" 2>/dev/null | while read -r aid; do
          [ -n "$aid" ] && curl -s -m 30 -o /dev/null -X DELETE \
            -H "Authorization: Bearer $GH_TOKEN" \
            "https://api.github.com/repos/$GH_REPO/releases/assets/$aid"
        done
    fi
  fi
  # OCI:周日一份异地(PAR 只写,不可删,所以不每天推)
  if [ "$(date -u +%u)" = "7" ] && [ -n "$PAR" ] && [ -s "$ENC" ]; then
    OCI_CODE=$(curl -s -m 300 -o /dev/null -w '%{http_code}' -T "$ENC" "${PAR}${NAME}")
  fi
  # R2 写入禁用：GitHub Release 仍保留 30 份，OCI 仍保留每周异地副本。
  # 不删除既有对象；避免时间戳对象让 R2 Standard 容量无限增长。
  R2_CODE=disabled_zero_charge_policy
  say "  归档 $NAME size=$((SZ/1024/1024))M github=$GH_CODE oci=$OCI_CODE r2=$R2_CODE"

  # 只有上传成功才删源文件 —— 传丢了宁可留着占盘,也不能凭空消失
  if [ "$GH_CODE" = "201" ] || [ "$GH_CODE" = "200" ]; then
    find /srv/status-gate/private -maxdepth 1 -name 'spool-*-gate' -mtime +$RETAIN_DAYS 2>/dev/null \
      | while read -r p; do drop "$p" "已归档"; done
    find /var/log -maxdepth 1 -type f \( -name '*.gz' -o -name '*.[0-9]' \) -mtime +$RETAIN_DAYS -delete 2>/dev/null
    find /srv/linze/logs /srv/linze/apps/status -maxdepth 1 -type f -name '*.log' -mtime +$RETAIN_DAYS -delete 2>/dev/null
    say "  源文件已删(归档成功)"
  else
    say "  ! 归档未成功(github=$GH_CODE),源文件保留不删"
  fi
fi

# ---------- 3) 整机备份本地只留 2 份 ----------
if [ "$DRY_RUN" = 0 ]; then
  while read -r f; do drop "$f" "GitHub Release 已有 30 份滚动"; done < <(ls -1t /srv/linze/backups/linze-backup-*.enc 2>/dev/null | tail -n +$((KEEP_LOCAL_BACKUPS+1)))
fi

# ---------- 3.5) docker build cache ----------
# 实测:清空后一天就长回 2 GB。它纯粹是构建中间层缓存,删掉只会让下次构建慢一点,
# 不碰镜像也不碰容器(owner 要求 docker 本体不动 —— build cache 不是 docker 本体)。
if [ "$DRY_RUN" = 0 ]; then
  BC=$(docker builder prune -f 2>/dev/null | awk '/^Total:/{print $2}')
  [ -n "$BC" ] && say "  docker build cache 回收 $BC"
fi

# ---------- 4) systemd journal 收到 2 天 ----------
if [ "$DRY_RUN" = 0 ]; then
  journalctl --vacuum-time=${RETAIN_DAYS}d >/dev/null 2>&1 && say "  journal 收到 ${RETAIN_DAYS} 天"
fi

rm -rf "$WORK"
say "===== retention 结束: 本次释放 $((FREED_KB/1024))M, 现可用 $(free_mb)MB, 磁盘 $(df -Ph / | awk 'NR==2{print $5}') ====="
