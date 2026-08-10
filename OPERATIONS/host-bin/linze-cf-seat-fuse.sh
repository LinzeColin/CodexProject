#!/bin/bash
# Cloudflare Access 免费席位熔断: >=45/50 时停用 Keycloak cloudflare IdP, <40 恢复
set -uo pipefail
AT=$(cat /srv/linze/secrets/cf_access_token)
KCPW=$(cat /srv/linze/secrets/kc_admin_password)
ACCT="a8e86fa4be62ee3f9b5873b2aa934256"
UA="Mozilla/5.0 (fuse)"
SEATS=$(curl -s -H "Authorization: Bearer $AT" "https://api.cloudflare.com/client/v4/accounts/$ACCT/access/users?per_page=1" | python3 -c 'import sys,json;print((json.load(sys.stdin).get("result_info") or {}).get("total_count",0))')
TOK=$(curl -s -A "$UA" -X POST "https://account.linzezhang.com/realms/master/protocol/openid-connect/token" -d grant_type=password -d client_id=admin-cli -d username=admin --data-urlencode password="$KCPW" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("access_token",""))')
[ -z "$TOK" ] && { echo "$(date -u +%FT%TZ) kc token fail (seats=$SEATS)"; exit 1; }
CUR=$(curl -s -A "$UA" -H "Authorization: Bearer $TOK" "https://account.linzezhang.com/admin/realms/linze/identity-provider/instances/cloudflare" )
EN=$(echo "$CUR" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("enabled"))')
ACTION=none
if [ "$SEATS" -ge 45 ] && [ "$EN" = "True" ]; then
  echo "$CUR" | python3 -c 'import sys,json;d=json.load(sys.stdin);d["enabled"]=False;print(json.dumps(d))' | \
  curl -s -A "$UA" -X PUT -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" -d @- "https://account.linzezhang.com/admin/realms/linze/identity-provider/instances/cloudflare"
  ACTION=FUSED
elif [ "$SEATS" -lt 40 ] && [ "$EN" = "False" ]; then
  echo "$CUR" | python3 -c 'import sys,json;d=json.load(sys.stdin);d["enabled"]=True;print(json.dumps(d))' | \
  curl -s -A "$UA" -X PUT -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" -d @- "https://account.linzezhang.com/admin/realms/linze/identity-provider/instances/cloudflare"
  ACTION=RESTORED
fi
echo "$(date -u +%FT%TZ) seats=$SEATS/50 idp_enabled=$EN action=$ACTION"
