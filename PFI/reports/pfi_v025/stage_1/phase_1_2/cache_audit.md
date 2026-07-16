# PFI v0.2.5 Stage 1 Phase 1.2 Cache Audit

- Acceptance：`ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE`
- Scope：HTTP、URL-addressable assets、PFI `srcdoc` inline assets、Service Worker、CacheStorage、bfcache、Streamlit `st.cache_data`、launcher process reuse、runtime API ownership。
- Data/DB impact：无。所有真实数据检查只生成 hash/status；未写财务数据或 SQLite。

| Layer | Baseline truth | Phase 1.2 result | Status / evidence |
|---|---|---|---|
| Streamlit HTML | 现有 1.35 runtime 仅发送 `no-cache` | same-process wrapper 发送 `no-cache, private`，保留 ETag、Last-Modified，`If-None-Match` 返回 304 | PASS — `cache_headers.json` |
| URL-addressable Streamlit JS/CSS | 文件名含 content hash，但 1.35 仅发送 `public` | 仅 hash-named URL 使用 `public, max-age=31536000, immutable` | PASS — `cache_headers.json` |
| Unhashed Streamlit assets | 可能被统一当作 public | `favicon.png` 等使用 `no-cache, private` | PASS — `cache_headers.json` |
| PFI-owned JS/CSS | official Streamlit path 从磁盘读取后内联到 component `srcdoc`，没有独立 HTTP cache entry | launcher 前重算 14-file canonical frontend bundle hash；manifest/runtime gate 验证 actual inline-source bytes identity | PASS；不是 hashed URL claim |
| Runtime manifest/cache API | Phase 1.1 manifest API 可被旧 imported backend 从新磁盘 manifest 冒充 | 响应包含 import-time running backend hash；manifest/policy 都为 `no-store, private` + validators；`If-None-Match` 优先于日期条件且支持 weak/list/wildcard，非 release routes 保持原语义 | PASS — Python API test / `streamlit_cache_policy.json` |
| Service Worker | repo 无当前注册代码，但历史浏览器 registration/controller 未知 | 明确禁用：枚举并注销 dedicated PFI origin registrations，删除该 origin CacheStorage；surviving controller fail closed | PASS — `service_worker_audit.md` / browser trace |
| bfcache/pageshow | 无 `pageshow.persisted` recheck | persisted event 立即隐藏 shell，并重取 manifest + cache policy；epoch 防止旧成功覆盖新失败 | PASS — Node 8/8 / browser trace |
| Real Chromium back/forward | 未记录 | 实际 navigation type=`back_forward`；本次 DevTools-controlled headless run 的 `persisted=false`，如实记录，未冒充 hit | OBSERVED — `browser_validation.json` |
| Streamlit read model | official builder 直接调用；legacy `read_model_hash` 含生成时间、连续调用不稳定 | startup adapter 用 public `st.cache_data`，TTL 30 秒、memory-only、composite key 显式作为参数；真实 AppTest 证明重复调用 hit | PASS — Phase 1.2 Python 12/12 |
| Composite key | release marker 未含 data/parameter/formula/FX/read-model runtime dimensions | key 含 build、commit、frontend/backend、data、parameter、formula、FX id/hash、stable read-model、Streamlit version、requirements lock hash | PASS — `streamlit_cache_policy.json` |
| Launcher process reuse | 旧 marker 可在 cache namespace 变化后被误复用 | marker 必须包含并匹配 `PFI_STREAMLIT_CACHE_KEY`；旧/缺失 marker 拒绝复用 | PASS — source + Python test |
| Runtime API port | 默认固定 8766；旧进程可占有 | 两个 canonical launcher 对新进程强制 `PFI_V021_RUNTIME_API_PORT=0`；same-process wrapper 在进入 Streamlit CLI 前预启动 owner，验证 loopback 且拒绝 8766 | PASS — source + Python test |

## Stable read-model hash

现有 `build_v024_read_model_status().read_model_hash` 把生成时间纳入输入，不能直接作为 cache key。Phase 1.2 只对白名单状态字段做 canonical SHA-256：schema/contract、source status/evidence hash/as-of/count/date range、core metric status/count/as-of/formula/calculation state、blocked metrics 与 surfaces。生成时间、legacy hash、绝对路径、财务 value/amount/rate 不进入稳定 hash；状态、evidence、count、as-of 或 formula 变化会改变 hash。

## Review remediation

初始 `5edd3788` / `df7e2add` pair 的三路复核合并结果为 `C0/I4/M0`，已明确 superseded 且不会 attestation。新的 content commit `b3885f15cd2e983c0839be6a20d7e4a9391c6324` 修复 API owner、stable hash、conditional request 与 trace ZIP privacy 四项问题；fresh re-review 与 post-commit attestation 仍由 binding commit 之后的外部证据完成。

## Runtime version boundary

当前 canonical `.venv` 实测 Streamlit `1.35.0`，`requirements.lock` 声明 `1.54.0`。wrapper 对 1.35 实际 HTTP 完成验证，并对支持 `server.useStarlette` 的 runtime 强制 Tornado mode；Phase 1.3 canonical reinstall 后仍须对实际安装版本重跑同一证据脚本。此处不声称已运行 1.54。

## Explicitly not done

- 未停止、重启或读取现有 8501/8502 页面；浏览器/HTTP 验证只用 ephemeral loopback origin。
- 未安装 PFI.app、未进入 Finder/new-profile/canonical-copy 验收；这些属于 Phase 1.3。
- 未 push、未修改数据/DB、未修改 model/formula/parameter semantics。
