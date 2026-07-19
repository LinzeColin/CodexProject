#!/usr/bin/env python3
"""Golden Path — home.linzezhang.com 跳转卡片同步 (STAGE-13/Home)。

把一个可部署服务的卡片 upsert 进 LinzeHomeHub/src/data/projects.json。
production 健康后由 Golden Path 的 home-sync job 调用, 卡片自动出现在 home。

只用标准库; 通过 GitHub Contents API 读改写, 幂等 (按 id upsert, 无变化则不提交)。
需要环境变量 GITHUB_TOKEN (对 LinzeHomeHub 有 contents:write)。
"""
import argparse, base64, json, os, sys, urllib.request, urllib.error

API = "https://api.github.com"

def _req(method, path, token, data=None):
    url = API + path
    body = json.dumps(data).encode() if data is not None else None
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
         "User-Agent": "linze-home-sync"}
    r = urllib.request.Request(url, data=body, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read())

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--id", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--category", default="Cloud Service")
    ap.add_argument("--summary", default="")
    ap.add_argument("--live-url", required=True)
    ap.add_argument("--fallback-url", default="")
    ap.add_argument("--mode", default="voyage")
    ap.add_argument("--status", default="Live")
    ap.add_argument("--compat", default="L2")
    ap.add_argument("--repo", default="LinzeColin/LinzeHomeHub")
    ap.add_argument("--path", default="src/data/projects.json")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    card = {"id": a.id, "name": a.name, "category": a.category,
            "compatibilityLevel": a.compat, "deploymentStatus": a.status,
            "futureLevel": "L3 gated", "summary": a.summary,
            "liveUrl": a.live_url, "fallbackUrl": a.fallback_url, "mode": a.mode}

    token = os.environ.get("GITHUB_TOKEN", "")
    if not a.dry_run and not token:
        sys.exit("需要 GITHUB_TOKEN (对目标仓 contents:write)")

    if a.dry_run and not token:
        # 无 token 的纯本地演示: 从 stdin 读现有数组
        cards = json.load(sys.stdin) if not sys.stdin.isatty() else []
        sha = None
    else:
        meta = _req("GET", f"/repos/{a.repo}/contents/{a.path}", token)
        cards = json.loads(base64.b64decode(meta["content"]))
        sha = meta["sha"]

    idx = next((i for i, c in enumerate(cards) if c.get("id") == a.id), None)
    action = "update" if idx is not None else "insert"
    if idx is None:
        cards.append(card)
    else:
        if cards[idx] == card:
            print(f"home-sync: '{a.id}' 无变化, 跳过提交")
            return
        cards[idx] = card

    new_content = json.dumps(cards, ensure_ascii=False, indent=2) + "\n"
    if a.dry_run:
        print(f"[dry-run] 将 {action} 卡片 '{a.id}' -> {a.repo}/{a.path}")
        print(new_content)
        return

    _req("PUT", f"/repos/{a.repo}/contents/{a.path}", token, {
        "message": f"home-sync: {action} {a.id} 跳转卡片 [golden-path]",
        "content": base64.b64encode(new_content.encode()).decode(), "sha": sha})
    print(f"home-sync: 已 {action} '{a.id}' -> {a.repo}, home.linzezhang.com 将重建")

if __name__ == "__main__":
    main()
