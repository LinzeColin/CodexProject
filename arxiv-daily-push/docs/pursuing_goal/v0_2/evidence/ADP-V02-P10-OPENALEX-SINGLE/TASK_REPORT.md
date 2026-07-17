# ADP-V02-P10 · 修 P08 的生产静默空转 —— ★NOT_DEPLOYED：被独立复核 BLOCK，未部署★

## 状态（先说结论，别误读）
- **线上仍是 `bd0f14211005`（P09）**。本目录里的修复**没有部署**，仓库里的 `worker_cloud.js`
  **与线上逐字节一致**，没有任何漂移。
- **P08 的研究元数据在生产上目前等于没有**（见 `../ADP-V02-P08-RESEARCH-META/test-results/openalex_429_finding.txt`）。
- 修复**已设计、已在边缘实测可行、并被独立复核独立验证过前提**，但**复核 BLOCK 了它**，
  8 条缺陷里 2 条 HIGH。**没有走完「修完 → 负控 → 复核 CONFIRMED_SOUND → 部署」的周期，就不部署。**

## 病灶（实测，复核独立复现）
P08 用一个批量 `?filter=doi:a|b|c`（50 个 DOI，1 个子请求）。从 Cloudflare 边缘：

| | 边缘 | 本机 curl |
|---|---|---|
| `/works?filter=doi:…`（P08 的设计） | **429 ×3/3**，`retry-after≈46884s`，`Insufficient budget… $0 remaining. Resets at midnight UTC` | 200 |
| `/works/doi:X`（单条） | **200 ×12/12** | 200 |

OpenAlex 按 IP 计预算；Workers 出口是**共享数据中心 IP**，预算早被耗尽；`mailto` 不解决。
把发货的 `enrichMeta` 原样跑在真 D1 + 真 OpenAlex 上：`degraded:["meta:http429"]`、`total_rows: 0`。
**这不是偶发，是每晚都会发生的静默空转。**

## 修法（`test-results/proposed_fix_patch.mjs`，边缘实测可行）
批量 → **N 条并行的单条 `/works/doi:X`**；`META_BATCH(50)` → `META_PER_RUN(12)`（**1 DOI = 1 子请求**，
cron 20/50 → **32/50**）；404=确知未收录→写 `found=0`；429/5xx/异常=**不知道**→**什么都不写**；
`select=` 让响应从 53671 → 1059 字节；单条端点回**规范记录**，故 P08 的 F3「重复 work 最后一条赢」**不复存在**。

**复核独立验证了前提，并把修好的版本跑在边缘上**：`requested:12, matched:12, degraded:[]`、1835ms
—— **正是 P08 失败的那个场景**。DIR-007 也被复核逐条数过：20 + 12 = 32/50 成立。

## ★复核 BLOCK 的 8 条（全部属实，未修）★
| # | 级别 | 缺陷 |
|---|---|---|
| 1 | **HIGH** | **`unknown` 守卫 100% 未被测到**：把 `if (hit.has(doi) \|\| unknown.has(doi))` 改成 `if (hit.has(doi))`，**套件照样绿** —— 因为 all-429 用例走的是 `if (errs === dois.length) return;` 早退，**根本到不了那行**。我那条「★429 → 一行都不写★」的断言是**早退喂出来的，不是那行保护出来的**＝**装饰** |
| 2 | **HIGH** | **完全没有「部分失败」用例**：`if (errs === dois.length) return;` 改成 `if (errs) return;` 也照样绿。所有用例都是同质的（全 200／全 404／全 429／全抛），而 12 个并行里**混着一个 5xx 才是真实形态** |
| 3 | MEDIUM | 没有 P10 证据包；`nc_results.txt` 陈旧 —— **nc8 还在给一个 P10 已经删掉的机制做负控** |
| 4 | MEDIUM | **12 个 fetch 没有超时**：worker 别处都用 `AbortSignal.timeout(15000/20000)`，这里没有。`Promise.all` 会等满 —— **一个挂住的连接会卡死 cron，而且是在 `selectDaily` 之前**，即为了补元数据把当日精选搞没 |
| 5 | LOW | **DOI 没做 URL 编码**（P08 有，是我改回归了）。OpenAlex 对畸形 DOI 回 **404**，与「真的没收录」**无法区分** → 会给真论文写 `found=0` |
| 6 | LOW | 套件里残留两处批量形态的 mock（`{results:[],meta:{count:0}}`），单条端点永远不会回这个形状 |
| 7 | LOW（P08 遗留） | `select=` 没带 `id` → `oa_id` 恒为 NULL。而 P10 的立论正是「单条端点回规范记录」—— **被丢掉的恰恰是那条规范记录的身份** |
| 8 | LOW | `degraded` 丢了状态码（`meta:err12` 而非 `meta:http429`）。**429 正是让 P08 隐形的那个信号**，不该被抹掉 |

## 下一个人要做的（顺序别乱）
1. 补**部分失败**用例（一部分 200、一部分 429），它必须能让缺陷 #1 与 #2 的变异**变红**。
2. 给那 12 个 fetch 加 `AbortSignal.timeout()`。
3. `encodeURIComponent` 那个 DOI。
4. 删掉两处陈旧 mock；重生成 `nc_results.txt`（去掉 nc8，补 `unknown` 守卫的负控）。
5. 把 `degraded` 的状态码留住（#8）—— 否则下次 vendor 变脸又会隐形。
6. 再送独立复核；**CONFIRMED_SOUND 之前不许部署**。

## 复核留的残余风险（值得记住）
> OpenAlex 对 `filter=` 计费，但单实体 GET 似乎不吃那份预算 —— **这正是 P10 能work的原因，
> 但那是未写进文档的厂商行为，随时可能变，一变就又悄悄回到 0 行/晚。**
> 而缺陷 #8（抹掉状态码）恰恰会让这种复发**很难被看见**。

## 我为什么没有硬上
本轮我自己反复栽的跟头就是「看着绿、其实什么都没检」。复核刚证明我这版的 429 断言**正是**那种东西。
在这种时候为了「有进展」而部署一个刚被 BLOCK 的改动，等于把整轮的教训又演一遍。
**线上维持 P09；P08 的徽章暂时不出数据 —— 这件事已经写在证据里，不是藏着。**
