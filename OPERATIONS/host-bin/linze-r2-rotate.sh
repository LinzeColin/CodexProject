#!/bin/bash
# R2 前缀轮转 —— 用法: linze-r2-rotate.sh <bucket> <前缀> <保留份数>
#
# 为什么必须有它(2026-08-10 复盘):
#   2026-08-02 给 offsite-backup 和 retention 加 R2 通道时,只写了 PUT,忘了轮转。
#   GitHub Release 那条线有 KEEP=30 在轮转,R2 这条线没有 —— 8 天堆了 7 份整机备份
#   0.89 GB,按每天 +118 MB 的速度,R2 免费额度(Standard 10 GB)约 38 天后触顶,
#   之后按量计费。铁律 7 要求"新增周期性任务先算月操作量",当时没算存储增量。
#
# 成本口径(CF R2 定价):
#   DELETE 免费;LIST 属 Class A(免费额度 100 万次/月)。本脚本每次跑 1 次 LIST +
#   若干次 DELETE,按每天 2 次调用算,月操作量约 62 次 —— 相对额度可忽略。
#   绝不使用 InfrequentAccess 存储类(IA 无免费额度且按整单位向上取整)。
set -uo pipefail
BUCKET=${1:?bucket}; PREFIX=${2:?prefix}; KEEP=${3:-7}
ACC=a8e86fa4be62ee3f9b5873b2aa934256
T=$(cat /srv/linze/secrets/cf_r2_write_token 2>/dev/null)
[ -z "$T" ] && { echo "no-token"; exit 1; }
API="https://api.cloudflare.com/client/v4/accounts/$ACC/r2/buckets/$BUCKET/objects"

# 只在本前缀"这一层"里轮转,不递归进子目录(子目录各自轮转各自的)
DEL=$(curl -s -m 60 -H "Authorization: Bearer $T" "$API?prefix=$PREFIX&per_page=1000" | python3 -c "
import sys,json
try: objs=json.load(sys.stdin).get('result') or []
except: sys.exit()
pre='$PREFIX'
# 排除更深一层的对象:key 去掉前缀后不应再含 '/'
flat=[o for o in objs if '/' not in o['key'][len(pre):]]
flat.sort(key=lambda o:o.get('uploaded') or o['key'])
for o in flat[:max(0,len(flat)-$KEEP)]: print(o['key'])
")

n=0
while IFS= read -r k; do
  [ -z "$k" ] && continue
  # DELETE 在 R2 不计费
  curl -s -o /dev/null -X DELETE -H "Authorization: Bearer $T" "$API/$k" && n=$((n+1))
done <<< "$DEL"
echo "rotated=$n kept=$KEEP prefix=$PREFIX"
