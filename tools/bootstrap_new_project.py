#!/usr/bin/env python3
"""STAGE-14.2 新项目一键上 Golden Path。
做三件事: ①建 Coolify 应用 ②建 Cloudflare DNS ③打印该仓要粘的 caller 工作流。
用法:
  export COOLIFY_BASE_URL=https://server.linzezhang.com
  export COOLIFY_API_TOKEN=...   CLOUDFLARE_API_TOKEN=...
  python3 tools/bootstrap_new_project.py --service demo --repo LinzeColin/Foo \
      --base-dir /apps/demo --subdomain demo [--dry-run]
"""
import argparse, json, os, sys, urllib.request, urllib.error

UA = "Mozilla/5.0 (linze-bootstrap)"
SERVER_IP = "139.99.61.6"
COOLIFY_IDS = {  # 由平台线程维护; 见 _protected 台账
    "project_uuid": "kgqergvnolr8se3m3urs9gef",
    "server_uuid": "jduqkk523vdll718qomul3yf",
    "destination_uuid": "g2ga4fluotzeoglueqo2p7c7",
}

def api(url, token, data=None, method="GET"):
    body = json.dumps(data).encode() if data is not None else None
    h = {"Authorization": f"Bearer {token}", "User-Agent": UA, "Accept": "application/json"}
    if body: h["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        return {"_error": e.code, "_body": e.read().decode()[:300]}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--service", required=True, help="service_id, 同时作 Coolify 应用名")
    ap.add_argument("--repo", required=True, help="LinzeColin/Xxx")
    ap.add_argument("--base-dir", default="/", help="monorepo 子目录, 如 /apps/demo")
    ap.add_argument("--subdomain", required=True, help="demo → demo.linzezhang.com")
    ap.add_argument("--port", default="80")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    base = os.environ.get("COOLIFY_BASE_URL", "").rstrip("/")
    ctok = os.environ.get("COOLIFY_API_TOKEN", "")
    cftok = os.environ.get("CLOUDFLARE_API_TOKEN", "")
    if not (base and ctok and cftok):
        sys.exit("需要环境变量 COOLIFY_BASE_URL / COOLIFY_API_TOKEN / CLOUDFLARE_API_TOKEN")
    fqdn = f"{a.subdomain}.linzezhang.com"

    if a.dry_run:
        print(f"[dry-run] 将建 Coolify 应用 {a.service} ({a.repo}{a.base_dir}) 域名 {fqdn}")
        return 0

    # ① Coolify 应用
    payload = dict(COOLIFY_IDS, environment_name="production",
                   git_repository=f"https://github.com/{a.repo}", git_branch="main",
                   build_pack="dockerfile", base_directory=a.base_dir,
                   dockerfile_location="/Dockerfile", ports_exposes=a.port,
                   domains=f"https://{fqdn}", name=a.service, instant_deploy=False)
    r = api(f"{base}/api/v1/applications/public", ctok, payload, "POST")
    uuid = r.get("uuid")
    if not uuid:
        sys.exit(f"建 Coolify 应用失败: {r}")
    print(f"① Coolify 应用: {uuid}")

    # ② Cloudflare DNS (先 DNS-only, 待 LE 签证后再开代理)
    z = api("https://api.cloudflare.com/client/v4/zones?name=linzezhang.com", cftok)
    zid = (z.get("result") or [{}])[0].get("id")
    dns = api(f"https://api.cloudflare.com/client/v4/zones/{zid}/dns_records", cftok,
              {"type": "A", "name": a.subdomain, "content": SERVER_IP,
               "proxied": False, "ttl": 300, "comment": "Golden Path bootstrap"}, "POST")
    print(f"② DNS {fqdn} -> {SERVER_IP}: {'ok' if dns.get('success') else dns.get('errors')}")
    print("   (LE 签证成功后请把该记录改 proxied=true 以启用边缘缓存)")

    # ③ caller 工作流
    print(f"""③ 在 {a.repo} 加 .github/workflows/deploy.yml:

name: deploy
on:
  push:
    branches: [main]{("" if a.base_dir in ("/", "") else chr(10) + "    paths: ['" + a.base_dir.strip('/') + "/**']")}
jobs:
  golden-path:
    uses: LinzeColin/CodexProject/.github/workflows/linze-golden-path.reusable.yml@main
    with:
      service_name: {a.service}
      coolify_app_uuid: "{uuid}"
      home_live_url: "https://{fqdn}"
    secrets:
      COOLIFY_BASE_URL: ${{{{ secrets.COOLIFY_BASE_URL }}}}
      COOLIFY_API_TOKEN: ${{{{ secrets.COOLIFY_API_TOKEN }}}}

并设仓库 secrets: COOLIFY_BASE_URL / COOLIFY_API_TOKEN""")
    return 0

if __name__ == "__main__":
    sys.exit(main())
