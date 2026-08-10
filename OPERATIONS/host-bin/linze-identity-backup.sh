#!/bin/bash
set -euo pipefail
TS=$(date -u +%Y%m%d-%H%M%S); DEST=/srv/linze/backups/identity; mkdir -p "$DEST"
docker exec identity-identity-postgres-1 pg_dump -U keycloak -d keycloak | gzip > "$DEST/keycloak-db-$TS.sql.gz"
cp /srv/linze/apps/identity/.env "$DEST/identity-env-$TS.env" 2>/dev/null || true
chmod 600 "$DEST"/* 2>/dev/null || true
ls -1t "$DEST"/keycloak-db-*.sql.gz | tail -n +15 | xargs -r rm -f
ls -1t "$DEST"/identity-env-*.env 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "identity backup ok $TS"
