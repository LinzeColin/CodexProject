#!/usr/bin/env python3
"""ADP V0.1 generated deployment status (ADP-S1-P01-T011).

Derives the authoritative CURRENT deployment status from the deployment manifest
(tools/generate_manifest.py output) plus the live /build.json build id. Because
the status is regenerated from the manifest, hand-written old-architecture docs
cannot override the generated current -- they are flagged by check_status_drift.py.

Writes STATUS_GENERATED.md. Usage:
  python3 generate_status.py [--out PATH] [--build-id ID] [--manifest PATH]
"""
import argparse, json, subprocess, sys, pathlib

HERE = pathlib.Path(__file__).resolve().parent
V01 = HERE.parent
DEFAULT_MANIFEST = V01 / "deployment_manifest.sample.json"
DEFAULT_OUT = V01 / "STATUS_GENERATED.md"

RETIRED = {
    "R6_tunnel_mirror": "RETIRED -- superseded by J5 cloud-native (no Cloudflare Tunnel, no Mac 127.0.0.1 mirror, no LaunchAgent residents)",
}


def load_manifest(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def live_build_id(explicit):
    if explicit:
        return explicit
    # try the live endpoint; fall back to the manifest-embedded absence
    try:
        import urllib.request
        with urllib.request.urlopen("https://adp.linzezhang.com/build.json", timeout=10) as r:
            return json.loads(r.read().decode())["build_id"]
    except Exception:
        return "UNVERIFIED_LIVE"


def render(m, build_id):
    b = m["binding"]
    tables = ", ".join(b["schema"].get("tables", []))
    lines = [
        "# STATUS_GENERATED · ADP 当前部署状态（机器生成，勿手改）",
        "",
        "> 任务 `ADP-S1-P01-T011` 交付物。**本文件由 `tools/generate_status.py` 从部署 manifest + 线上 /build.json 生成**；",
        "> 手写旧架构文档不得覆盖本 generated current（漂移由 `tools/check_status_drift.py` 拦截）。要改状态，改源（manifest/worker）后重跑生成器。",
        "",
        "## 当前架构（唯一真相）= 云端原生 Cloud-native",
        "",
        f"- **架构**：整套系统跑在 Cloudflare —— Worker `{b['worker']['name']}` + D1 + cron；**无 Cloudflare Tunnel、无 Mac 127.0.0.1 镜像、无本机 LaunchAgent**。",
        f"- **运行 build**：`build_id {build_id}`（线上 /build.json）。",
        f"- **绑定 commit**：`{b['commit']}`。",
        f"- **cron**：`{b['cron']}`（每日 UTC）。",
        f"- **D1 schema**：`{b['schema'].get('sha256','')[:12]}…`，表：{tables}。",
        f"- **来源 registry**：`{b['sources'].get('registry_ver')}`（config/boards_v0_3.yaml）。",
        f"- **manifest content_hash**：`{m['content_hash']}`。",
        "- **对象存储 R2**：未启用（FACT-012；如需再由 Owner 后台开）。",
        "",
        "## 已退役（历史，非当前）",
        "",
    ]
    for k, v in RETIRED.items():
        lines.append(f"- **{k}**：{v}")
    lines += [
        "",
        "## 一致性",
        "",
        "- 本文件与线上 /build.json 的 build_id 一致；与部署 manifest 的 commit/cron/schema/registry 一致（`check_status_drift.py` 校验）。",
        "- `docs/v03/STATUS.yaml` 的 R6（隧道/Mac 镜像）必须标 `superseded_by: J5_cloud_native`，否则判 DRIFT。",
    ]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    ap.add_argument("--build-id")
    args = ap.parse_args()
    m = load_manifest(args.manifest)
    out = render(m, live_build_id(args.build_id))
    pathlib.Path(args.out).write_text(out, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
