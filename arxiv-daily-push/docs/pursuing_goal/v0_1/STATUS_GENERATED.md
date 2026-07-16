# STATUS_GENERATED · ADP 当前部署状态（机器生成，勿手改）

> 任务 `ADP-S1-P01-T011` 交付物。**本文件由 `tools/generate_status.py` 从部署 manifest + 线上 /build.json 生成**；
> 手写旧架构文档不得覆盖本 generated current（漂移由 `tools/check_status_drift.py` 拦截）。要改状态，改源（manifest/worker）后重跑生成器。

## 当前架构（唯一真相）= 云端原生 Cloud-native

- **架构**：整套系统跑在 Cloudflare —— Worker `adp-cloud` + D1 + cron；**无 Cloudflare Tunnel、无 Mac 127.0.0.1 镜像、无本机 LaunchAgent**。
- **运行 build**：`build_id bd67a78020a3`（线上 /build.json）。
- **绑定 commit**：`83a845bed55c6046c2a59dd89de3f1e7bad7da7f`。
- **cron**：`30 20 * * *`（每日 UTC）。
- **D1 schema**：`bfb4704bbd8a…`，表：cn_events, cn_items, cn_lessons, cn_meta, cn_reviews, cn_run_log, cn_selections, cn_sources。
- **来源 registry**：`boards-v03-2`（config/boards_v0_3.yaml）。
- **manifest content_hash**：`sha256:810a0a1bf416af0f75b17212960a7f21588cc499cc963d8d8f8ec58bb56ba610`。
- **对象存储 R2**：未启用（FACT-012；如需再由 Owner 后台开）。

## 已退役（历史，非当前）

- **R6_tunnel_mirror**：RETIRED -- superseded by J5 cloud-native (no Cloudflare Tunnel, no Mac 127.0.0.1 mirror, no LaunchAgent residents)

## 一致性

- 本文件与线上 /build.json 的 build_id 一致；与部署 manifest 的 commit/cron/schema/registry 一致（`check_status_drift.py` 校验）。
- `docs/v03/STATUS.yaml` 的 R6（隧道/Mac 镜像）必须标 `superseded_by: J5_cloud_native`，否则判 DRIFT。
