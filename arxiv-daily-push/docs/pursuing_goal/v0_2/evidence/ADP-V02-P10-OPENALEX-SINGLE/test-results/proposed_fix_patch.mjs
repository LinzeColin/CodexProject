// ADP-V02-P10 = 修 P08 在生产上的静默空转。
//
// ★事实（实测，不是推断）★：P08 的整个设计是「一个 filter= 批量查 50 个 DOI」。
// 把发货的 enrichMeta 原样绑到真实 D1 + 真实 OpenAlex 跑一次 →
//     counts.degraded: ["meta:http429"] , total_rows: 0
// 从 Cloudflare 边缘实测：
//     /works?filter=doi:…  → 429 ×3/3，retry-after≈46884s（13 小时），mailto 不解决
//     /works/doi:X（单条） → 200 ×3/3，0.8–1.7s，数据正确
//     同样两条从本机 curl  → 全部 200
// 429 原文：Insufficient budget. This request costs $0.0001 but you on…
// → OpenAlex 按 IP 计预算，Workers 出口是【共享数据中心 IP】，预算早被别人耗尽。
//   这不是偶发，是系统性的：P08 每晚都会 429 → 静默降级 → 补 0 条。
//
// ★这是我自己的盲区★：六轮复核里我和复核者都只从【本机】验 OpenAlex，从未从边缘验。
//   我还特地用真 D1 结清了 env.DB.batch([SELECT,SELECT]) 的契约 —— 验的是 D1 的 batch，
//   不是 OpenAlex 的 filter= 在边缘能不能用。「从我这儿能通」≠「从生产能通」。
//
// ── 改法（每一条都在边缘实测过）───────────────────────────────────────────────
// 1. 批量 filter= → N 条并行的单条 /works/doi:X。实测 12 条并行：2302ms、0 次 429、共 10566 字节。
// 2. `select=` 在单条端点有效：1059 字节 vs 53671（约 50×）。
// 3. 未收录 → 干净的 404（不是错误体）→ found=0 的信号明确无歧义。
// 4. ★DIR-007 重算★：cron 现用 20/50 外部子请求；单条查询 = 1 个子请求/DOI。
//    故取 META_PER_RUN = 12 → 20+12 = 32/50，留 18 个余量。
//    代价如实记：约 600 条候选按 12/晚 要约 50 晚补完（批量设计原本 12 晚）——
//    但 **12 条/晚 > 0 条/永远**，而 0 条/永远正是现在生产上的真实状态。
// 5. 单条端点回的是【规范记录】，故 P08 F3 的「同一 DOI 多条 work、最后一条赢」问题
//    随之消失 —— 不再需要响应侧去重。请求侧的「一个 DOI 广播回 N 个条目」保留。
// 6. 截断判定（meta.count > results.length）随批量一起删除：单条查询没有分页，不存在截断。
import { readFileSync, writeFileSync } from 'node:fs';
const path = process.argv[2];
let src = readFileSync(path, 'utf8');
function rep(o, n, label) {
  const c = src.split(o).length - 1;
  if (c !== 1) { console.error(`ABORT [${label}]: anchor ${c} times`); process.exit(1); }
  src = src.replace(o, n); console.log('  ok  ', label);
}

// ── 常量：批量上限 → 每次 cron 的子请求预算 ─────────────────────────────────
rep(
`const META_BATCH = 50;        // 一批查多少个 DOI —— 一批只花【1 个】外部子请求。
                              // ★这是我们自己的保守取值，不是 API 上限★：OpenAlex 的 doi OR 上限
                              // 实测是 100（101 个即报 Maximum number of values exceeded for doi）。
                              // 取 50 的理由：重复 work 存在（50 个 DOI 实测回过 58 条），100 个 DOI
                              // 在高重复率下会逼近 per-page=200 的天花板；50 留足余量。
                              // （原注释写「其 OR 上限就是 50」是假的 —— 把自己的选择说成 API 的强制。）`,
`const META_PER_RUN = 12;      // 每次 cron 补多少条 —— ★单条查询：1 个 DOI = 1 个外部子请求★。
                              // ★DIR-007★：cron 现用 20/50，故 20+12 = 32/50，留 18 个余量。
                              // 为什么不是批量：P08 原本用 /works?filter=doi:a|b|c 一次查 50 个（只花 1 个子请求），
                              // 但那条路【在生产上是死的】—— 从 Cloudflare 边缘实测 429 ×3/3
                              // （Insufficient budget…，retry-after≈13 小时，mailto 不解决）：
                              // OpenAlex 按 IP 计预算，而 Workers 出口是共享数据中心 IP，预算早被耗尽。
                              // 同一边缘上单条 /works/doi:X 是 200 ×3/3。实测 12 条并行：2302ms、0 次 429。
                              // 代价如实记：约 600 条候选按 12/晚 要约 50 晚补完（批量原本 12 晚）——
                              // 但 12 条/晚 > 0 条/永远，而后者正是现在生产上的真实状态。`,
  'META_BATCH -> META_PER_RUN (subrequest budget, not an OR-list size)');

// ── 取候选：上限改用 META_PER_RUN ────────────────────────────────────────────
rep(
`      if (!byDoi.has(doi)) byDoi.set(doi, []);
      byDoi.get(doi).push(it.id);
      if (byDoi.size >= META_BATCH) break;`,
`      if (!byDoi.has(doi)) byDoi.set(doi, []);
      byDoi.get(doi).push(it.id);
      if (byDoi.size >= META_PER_RUN) break;   // 子请求预算：一个 DOI 一个子请求`,
  'candidate cap uses META_PER_RUN');

// ── 核心：批量 filter= → 并行单条 /works/doi:X ──────────────────────────────
rep(
`    const dois = [...byDoi.keys()];
    // ★per-page 必须大于 META_BATCH★：OpenAlex 对一个 DOI 可能回**多条** work，50 个 DOI 实测回过 58 条，
    // per-page=50 会把第 50 条之后的截掉 → 那些**真论文**会被我们自己写成 found=0（「OpenAlex 不认识」），
    // 而事实是「我们把自己的响应页截断了」。复核实测被截掉的正是 FedAvg（5641 次引用）。
    // 又因候选是「最近 200 条」的窗口、按新到旧取，被误判 found=0 的条目会沉到窗口外 → 几乎永不重试。
    // authorships 只为取个 .length 却要拉回整份作者表（实测 1.33MB 批 JSON.parse 2.48ms），不值 → 不要了。
    const url = OPENALEX_WORKS + '?per-page=200&mailto=' + encodeURIComponent(META_UA_MAILTO)
      + '&select=' + encodeURIComponent('doi,type,primary_location,cited_by_count,open_access,publication_year')
      + '&filter=' + encodeURIComponent('doi:' + dois.join('|'));
    const r = await fetch(url, { headers: { 'User-Agent': 'adp-cloud (mailto:' + META_UA_MAILTO + ')' }, cf: { cacheTtl: 3600 } });
    if (!r.ok) { counts.degraded.push('meta:http' + r.status); return; }
    const data = await r.json();
    const got = (data && data.results) || [];
    // ★dedup rules（响应侧）★：OpenAlex 对同一个 DOI 会回**多条** work（未合并的重复记录）。
    // 复核用真实 API 实测 arxiv:1506.01497 回 2 条，cited_by 分别是 18240 与 6274；D1 batch 按序执行
    // ＝**最后一条赢** → 页面会把 6274 当作事实展示，而 OpenAlex 自己的规范记录是 18240。
    // 「在冲突记录之间随机挑一条当事实」正是本项目不许干的事，故规则必须**确定**：
    // 取 cited_by_count 最大者（规范记录是合并后的，引用数最全），并列时取 OpenAlex id 字典序最小者。
    const best = new Map();
    for (const w of got) {
      const key = metaKey(w.doi);
      if (!byDoi.has(key)) continue;            // 回了没要的，忽略（不臆造归属）
      const cur = best.get(key);
      const c = Number(w.cited_by_count) || 0, cc = cur ? (Number(cur.cited_by_count) || 0) : -1;
      if (!cur || c > cc || (c === cc && String(w.id || '') < String(cur.id || ''))) best.set(key, w);
    }
    // 响应是否被截断：被截断时「没回」并不等于「查不到」，此时**不得**写 found=0。
    // 未知必须【向安全侧倒】：拿不到 meta.count 就无法判断是否被截断，此时绝不能写 found=0
    // （否则又回到「把自己的截断栽赃成 OpenAlex 查不到」那条路上）。复核指出的残余风险，堵掉。
    const cnt = data && data.meta && data.meta.count;
    const truncated = typeof cnt !== 'number' || cnt > got.length;
    const now = nowISO(), stmts = [], hit = new Set();
    for (const [key, w] of best) {
      const ids = byDoi.get(key);
      hit.add(key);`,
`    const dois = [...byDoi.keys()];
    // ★单条查询，并行★。每个 DOI 一个子请求（预算见 META_PER_RUN）。
    // 单条端点回的是【规范记录】，故 P08 的「同一 DOI 多条 work、最后一条赢、被引数会错」
    // （复核 F3：arxiv:1506.01497 回 2 条 18240/6274）随之消失 —— 不再需要响应侧去重。
    // 截断判定也一并删除：单条查询没有分页，不存在截断。
    const SEL = encodeURIComponent('doi,type,primary_location,cited_by_count,open_access,publication_year');
    const settled = await Promise.all(dois.map(async (doi) => {
      const u = OPENALEX_WORKS + '/doi:' + doi + '?mailto=' + encodeURIComponent(META_UA_MAILTO) + '&select=' + SEL;
      try {
        const r = await fetch(u, { headers: { 'User-Agent': 'adp-cloud (mailto:' + META_UA_MAILTO + ')' }, cf: { cacheTtl: 3600 } });
        if (r.status === 404) return { doi, miss: true };          // 未收录：干净的 404 → 可以写 found=0
        if (!r.ok) return { doi, err: r.status };                  // 429/5xx：不知道，绝不写 found=0
        return { doi, work: await r.json() };
      } catch (e) { return { doi, err: e.name }; }
    }));
    const best = new Map();
    let errs = 0;
    for (const s of settled) {
      if (s.work) best.set(s.doi, s.work);
      else if (s.err) errs++;                                      // 未知 → 向安全侧倒
    }
    if (errs) counts.degraded.push('meta:err' + errs);
    if (errs === dois.length) return;                              // 全挂：什么都别写
    const now = nowISO(), stmts = [], hit = new Set();
    const unknown = new Set(settled.filter(s => s.err).map(s => s.doi));
    for (const [key, w] of best) {
      const ids = byDoi.get(key);
      hit.add(key);`,
  'batch filter= -> parallel single /works/doi:X');

// ── found=0 只写「确知未收录」的（404），不写「不知道」的 ─────────────────────
rep(
`    // 查过但没回的：记 found=0，避免每天重查同一批查不到的；META_RETRY_DAYS 后自动重试。
    // ★但只有在确知响应没被截断时才这么判★ —— 否则是把自己的截断栽赃成「OpenAlex 查不到」。
    if (!truncated) {
      for (const [doi, ids] of byDoi) {
        if (hit.has(doi)) continue;
        for (const id of ids) stmts.push(env.DB.prepare(
          'INSERT INTO cn_item_meta (item_id,doi,found,enriched_at) VALUES (?1,?2,0,?3) ON CONFLICT(item_id) DO UPDATE SET enriched_at=excluded.enriched_at')
          .bind(id, doi, now));
      }
    } else counts.degraded.push('meta:truncated');`,
`    // 只给【确知未收录】的（HTTP 404）写 found=0，避免每晚重查同一批查不到的；META_RETRY_DAYS 后重试。
    // ★「不知道」（429/5xx/异常）绝不写 found=0★ —— 那等于把我们自己的失败栽赃成「OpenAlex 查不到」，
    // 而被误判的条目会随窗口下沉、几乎永不重试。未知一律留白，下次再来。
    for (const [doi, ids] of byDoi) {
      if (hit.has(doi) || unknown.has(doi)) continue;
      for (const id of ids) stmts.push(env.DB.prepare(
        'INSERT INTO cn_item_meta (item_id,doi,found,enriched_at) VALUES (?1,?2,0,?3) ON CONFLICT(item_id) DO UPDATE SET enriched_at=excluded.enriched_at')
        .bind(id, doi, now));
    }`,
  'found=0 only for a definitive 404, never for "unknown"');

rep(`    counts.meta = { requested: byDoi.size, matched: hit.size, truncated: truncated || undefined };`,
    `    counts.meta = { requested: byDoi.size, matched: hit.size, unknown: unknown.size || undefined };`,
  'counts.meta reports unknowns instead of truncation');

writeFileSync(path, src);
console.log('P10 APPLIED');
