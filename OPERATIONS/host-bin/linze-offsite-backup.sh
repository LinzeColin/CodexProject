#!/bin/bash
# 异地备份:每日 -> GitHub Release 资产(可轮转,不进 git 历史)。
# 2026-09-30:OCI 通道(原每周日再推一份)已整段移除——Owner:OCI 账号已过期,以后没有 OCI。
#   09-06 起每周日的 OCI 上传全是 HTTP 400,而 GitHub Release 每天 201,整机备份没有因此少过一天。
# 部署位置 /usr/local/bin/linze-offsite-backup.sh,由 root cron 每日 03:40 执行。
set -uo pipefail
TS=$(date -u +%Y%m%d-%H%M%S)
DEST=/srv/linze/backups; STAGE="$DEST/.stage-$TS"
ENCKEY=/srv/linze/secrets/backup_enc.key
GH_TOKEN=$(cat /srv/linze/secrets/github_backup_pat 2>/dev/null)
GH_REPO=LinzeColin/Private-Database
GH_TAG=infra-backups
KEEP=30

mkdir -p "$STAGE/db" "$STAGE/config"
for c in $(docker ps --format '{{.Names}} {{.Image}}' | awk '/postgres/{print $1}'); do
  U=$(docker exec "$c" printenv POSTGRES_USER 2>/dev/null); U=${U:-postgres}
  docker exec "$c" pg_dumpall -U "$U" 2>/dev/null | gzip > "$STAGE/db/${c}-${TS}.sql.gz"
done
cp /data/coolify/source/.env "$STAGE/config/coolify-env-${TS}.env" 2>/dev/null || true

# status 数据/日志(内存磁盘历史、快照、价格库、采集日志)一并进每日备份 → 随备份上 GitHub
mkdir -p "$STAGE/status"
for f in history.json snapshot.json prices.json usage_history.json selfheal.json; do
  cp "/srv/linze/apps/status/data/$f" "$STAGE/status/$f" 2>/dev/null || true
done
cp /srv/linze/apps/status/collect.log "$STAGE/status/collect.log" 2>/dev/null || true
cp /srv/linze/apps/status/selfheal.log "$STAGE/status/selfheal.log" 2>/dev/null || true

TAR="$DEST/linze-backup-${TS}.tar.gz"
tar -czf "$TAR" -C "$STAGE" .
ENC="${TAR}.enc"
openssl enc -aes-256-cbc -pbkdf2 -salt -in "$TAR" -out "$ENC" -pass file:"$ENCKEY"
rm -rf "$TAR" "$STAGE"
SZ=$(stat -c%s "$ENC"); NAME=$(basename "$ENC")

# ---- 主通道:GitHub Release 资产(每日,滚动保留 KEEP 份)----
GH_CODE=000
if [ -n "$GH_TOKEN" ]; then
  RID=$(curl -s -H "Authorization: Bearer $GH_TOKEN" \
        "https://api.github.com/repos/$GH_REPO/releases/tags/$GH_TAG" \
        | python3 -c 'import sys,json;print(json.load(sys.stdin).get("id",""))' 2>/dev/null)
  if [ -n "$RID" ]; then
    GH_CODE=$(curl -s -o /dev/null -w '%{http_code}' \
      -H "Authorization: Bearer $GH_TOKEN" -H "Content-Type: application/octet-stream" \
      --data-binary @"$ENC" \
      "https://uploads.github.com/repos/$GH_REPO/releases/$RID/assets?name=$NAME")
    # 轮转:超过 KEEP 份就删最旧的
    curl -s -H "Authorization: Bearer $GH_TOKEN" \
      "https://api.github.com/repos/$GH_REPO/releases/$RID/assets?per_page=100" \
      | python3 -c "
import sys,json
a=[x for x in json.load(sys.stdin) if x.get('name','').startswith('linze-backup-')]
a.sort(key=lambda x: x['created_at'])
for x in a[:max(0, len(a)-$KEEP)]: print(x['id'])
" 2>/dev/null | while read -r aid; do
        [ -n "$aid" ] && curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $GH_TOKEN" \
          "https://api.github.com/repos/$GH_REPO/releases/assets/$aid"
      done
  fi
fi

# ---- OCI 已退役(2026-09-30):原「每周日 PUT 到 OCI」整段删除 ----
# 日志行仍保留 offsite= 这一列,值固定为 removed_oci_expired:读这行日志的采集器
# (LinzeHomeHub status collector 只匹配 offsite=200 的历史行)不会因为少一列而解析错位。
OCI_CODE=removed_oci_expired

# ---- R2 写入禁用:零付费策略 ----
# GitHub Release 保留每日 30 份(唯一异地副本)，本地密文保留 2 份。
# 不删除既有 R2 对象；这里只阻止按日期新增整机副本导致 Standard 容量持续增长。
R2_CODE=disabled_zero_charge_policy

echo "$(date -u +%FT%TZ) github=$GH_CODE offsite=$OCI_CODE r2=$R2_CODE size=${SZ}B file=$NAME"

# 本地保留 2 份；长期历史由 GitHub Release 的 30 份承担。
ls -1t "$DEST"/linze-backup-*.enc 2>/dev/null | tail -n +3 | xargs -r rm -f
