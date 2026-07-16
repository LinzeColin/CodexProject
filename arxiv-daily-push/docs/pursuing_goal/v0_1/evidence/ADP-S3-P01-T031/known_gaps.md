# Known gaps · ADP-S3-P01-T031

- **NOT_DEPLOYED（任务边界，非缺陷）**：本任务是**连接器内核 SDK**，未接 worker/D1。真实 A0 适配器（国务院政策+法规 T034、统计+发改委 T035、网信办+国家数据局 T036）实现各源的 discover/verify/normalize/attachments 解析规则；本任务只给接口 + 一个 mock 全链路 + 真实 fetch 能力。
- **真实抓取为 live 时点证据、不逐字复现**：按 Owner 决策，内核 `HttpFetcher` 是真 urllib GET；`real_fetch_smoke.json` 记录实抓 gov.cn 的 status/bytes/sha256/fetched_at/标题，但站点会变，**bytes/sha256 不逐字复现**。确定性契约测试跑在 mock + 本地 loopback（CI 无外网）。
- **Worker 子请求成本待接线时核算**：本任务的实抓从**开发环境**跑（非 worker），故 0 云成本。一旦 T034+ 把 fetch 接进 worker cron，每次 fetch = Worker 子请求（免费档约 ~50/请求上限，见 T023 教训），须核 DIR-007 免费额度并加每 run 抓取上限。
- **`nda.gov.cn`（国家数据局）需浏览器**：连接性实测 `nda.gov.cn` 返回 193B（JS shell），urllib GET 拿不到内容；T036 接入该源时可能需 `mcp__Claude_Browser` 或该站的 RSS/API 入口，属 T036 范围。
- **verify 的 A0 判定为最小实现**：mock 用 `.gov.cn` 域判官方；真实 A0 身份（主办单位、目录、可取证网站标识）由 T033 强化。normalize 的文号/日期/状态抽取为 mock 演示，真实站点解析规则在 T034+。
- **robots/礼貌**：单次 GET、标注 research UA。真实批量抓取（T034+）须遵守各站 robots + 抓取频率上限；本任务未做 robots 解析（单页 smoke）。
