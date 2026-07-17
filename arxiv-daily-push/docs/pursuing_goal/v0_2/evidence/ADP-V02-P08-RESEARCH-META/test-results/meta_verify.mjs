// ADP-V02-P08 (T063) acceptance. Runs the REAL metaDoi/enrichMeta/attachMeta/metaFacts extracted from
// the shipped worker_cloud.js (no retyping drift). T063's acceptance is exactly two clauses:
//   1. 预印本/期刊不混淆
//   2. 增强失败不阻塞原始论文
// Both are asserted here against the shipped code, and both have a negative control in nc_results.txt:
// an assertion that cannot fail on broken code is not evidence, it is decoration.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
// test-results -> TASK -> evidence -> v0_2 -> pursuing_goal -> docs -> arxiv-daily-push  (6 levels)
const WORKER = resolve(HERE, '../../../../../../deploy/cloudflare/worker_cloud.js');
const w = readFileSync(WORKER, 'utf8');

const S = w.indexOf('// ───────────────────────── T063 研究元数据（OpenAlex） ');
const E = w.indexOf('function factsheetHTML');
if (S < 0 || E < 0) { console.error('FAIL: could not locate the shipped T063 block'); process.exit(1); }
const helpers = `const OPENALEX_WORKS='https://api.openalex.org/works';
function nowISO(){return '2026-07-17T00:00:00.000Z';}\n`;
const mod = await import('data:text/javascript;base64,' + Buffer.from(
  helpers + w.slice(S, E) +
  '\nexport {metaDoi, metaKey, enrichMeta, attachMeta, metaFacts, META_PER_RUN, META_SCAN, META_RETRY_DAYS};'
).toString('base64'));

// ★自检：这份套件自己必须盯住「有没有整节被悄悄删掉」★
// 复核的原话：「失败模式不是粗心，而是【没有任何东西盯着静默删除】—— 而那正是你报告开头写着的那条教训。」
// 我第 3 轮的一次 section 拼接一口气吃掉了【四节】（我以为是两节），其中两节守着 P10 的全部价值
// （retry 窗口）与一条前面复核 BLOCK 过的原缺陷（IN() → TEMP B-TREE）。套件全绿，没人知道。
//
// ★第一版这个自检本身是【永远不会失败】的★（复核第 5 轮抓到）：它拿 REQUIRED_SECTIONS 去
// `self.includes(t)` 匹配【整份源码文本】—— 而 REQUIRED_SECTIONS 就写在这份源码里，
// 于是每个名字都被【需求清单自己】满足了。删掉整节它照样印「全部 17 个必备小节在场」——
// 一个制造虚假安心的守卫比没有守卫更糟，因为它让人不再去看。（与 'grants' 那次同形。）
// 更糟的是我当时声称「删掉 F2 验证过，exit=1」—— 那个 exit=1 是我自己的拼接把文件切成了
// 语法错误（下标写反：j < i），不是守卫发的。★看见 exit=1 就写「验证过」——正是 nc6 的原罪。★
//
// 现在改为：把小节标题【从源码里解析出来】，再拿清单去比对解析结果 —— 清单与证据成了两个不同的对象。
const REQUIRED_SECTIONS = [
  'metadata adapters', 'metaKey', 'ACCEPTANCE 1', 'ACCEPTANCE 2', 'dedup rules',
  'DIR-007', 'DOI 必须 URL 编码', '带超时', '部分失败', 'F7', 'ORDER BY', 'META_SCAN',
  'select= 的字段', '单条端点回规范记录', '404=确知未收录', 'not-found bookkeeping', 'F2',
];
{
  const self = readFileSync(fileURLToPath(import.meta.url), 'utf8');
  // ★只认【真实存在的小节标题】★，不认源码里任何别的文本（包括上面这张清单本身）
  // 标题末尾不一定有空格再接 ==（第一版正则要求空格，于是把 4 个真实存在的小节误报成缺失 ——
  //  太严的守卫会被当成噪音关掉，和太松一样有害）。这里只认「== … ==」之间的内容。
  const headers = [...self.matchAll(/console\.log\('\\n== (.*?)\s*==/g)].map(m => m[1]);
  const missing = REQUIRED_SECTIONS.filter(t => !headers.some(h => h.includes(t)));
  if (missing.length) {
    console.log('  FAIL ★整节被删★：' + JSON.stringify(missing) +
      ' —— 这份套件曾被一次 section 拼接静默吃掉四节；不许再发生。');
    console.log('\nACCEPTANCE = FAIL');
    process.exit(1);
  }
  console.log('self-check: %d 个必备小节全部在场（从源码解析出 %d 个小节标题比对，非文本 includes）',
    REQUIRED_SECTIONS.length, headers.length);
}

let fails = 0, passCount = 0;
const ok = (c, msg) => { if (!c) { fails++; console.log('  FAIL ' + msg); } else { passCount++; console.log('  PASS ' + msg); } };
// 「压根没发请求」必须表现为断言失败，而不是 new URL(null) 抛 TypeError 把整轮打断 ——
// 一崩，后面的断言就再也没机会报告了（nc5 就是这样：11 条真失败，却连最终判定都跑不到）。
// 判定要靠断言，不能靠崩溃。
// （原先这里有个 qp() 助手，用来解析批量 ?filter= 的 query —— 那条设计已被删除，助手随之成为死代码，
//   复核 #5 指出后一并删掉：对批量设计的死引用留着只会误导下一个人。）

console.log('shipped constants: META_PER_RUN=%s META_SCAN=%s META_RETRY_DAYS=%s', mod.META_PER_RUN, mod.META_SCAN, mod.META_RETRY_DAYS);

console.log('\n== metadata adapters: REAL live id/url forms (taken from the production D1) ==');
// every expectation below was confirmed against the live OpenAlex API before being written here
const CASES = [
  [{ id: 'arxiv:1904.06520', url: 'https://arxiv.org/abs/1904.06520' }, '10.48550/arxiv.1904.06520'],
  [{ id: 'biorxiv:10.64898/2026.03.04.709430', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430' }, '10.64898/2026.03.04.709430'],
  [{ id: 'feed:3f18', url: 'https://www.medrxiv.org/content/10.64898/2026.07.12.26357871v1?rss=1' }, '10.64898/2026.07.12.26357871'],
  [{ id: 'feed:db54', url: 'https://www.nature.com/articles/d41586-026-02188-y' }, '10.1038/d41586-026-02188-y'],
  [{ id: 'feed:2d37', url: 'https://www.nature.com/articles/s41467-026-74639-z' }, '10.1038/s41467-026-74639-z'],
  [{ id: 'feed:6da8', url: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2512275?af=R&rss=currentIssue' }, '10.1056/NEJMoa2512275'],
  [{ id: 'feed:6306', url: 'https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3003884' }, '10.1371/journal.pbio.3003884'],
  [{ id: 'feed:d801', url: 'https://www.pnas.org/doi/abs/10.1073/iti2726123?af=R' }, '10.1073/iti2726123'],
  [{ id: 'feed:8f0e', url: 'https://elifesciences.org/articles/109351' }, '10.7554/elife.109351'],
];
let adapters = 0;
for (const [it, want] of CASES) { const got = mod.metaDoi(it); if (got === want) adapters++; else console.log(`    got ${got} want ${want}`); }
ok(adapters === CASES.length, `all ${CASES.length} live source forms resolve to the right DOI`);
// NC: things with no DOI must return null -- an adapter that GUESSES is worse than one that abstains
const NO_DOI = [
  { id: 'feed:6a25', url: 'https://www.science.org/content/article/bungee-jumping-mice-may-reveal' },
  { id: 'a0:abc', url: 'https://www.ndrc.gov.cn/xxgk/zcfb/tz/202607/t20260716_1406539.html' },
  { id: 'feed:xyz', url: 'https://spectrum.ieee.org/some-story' },
  { id: '', url: '' }, { id: 'feed:q', url: 'https://example.com/10.1234' },
  // 复核 F6：PLOS 附件链接里的「DOI」是资源名，不是作品 DOI。原实现会返回
  // 10.1371/journal.pbio.3003906.PDF —— 那是猜。抽不准必须弃权。
  { id: 'feed:pdf', url: 'https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3003906.PDF&type=printable' },
  { id: 'feed:xml', url: 'https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3003884.XML&type=manuscript' },
];
ok(NO_DOI.every(x => mod.metaDoi(x) === null), 'NC: sources with no DOI resolve to null (abstains, does not guess)');

console.log('\n== metaKey: OpenAlex lowercases the DOI it returns -- the map key must survive that ==');
ok(mod.metaKey('https://doi.org/10.1056/nejmoa2512275') === mod.metaKey('10.1056/NEJMoa2512275'),
  'request-side NEJMoa2512275 and response-side nejmoa2512275 collapse to the same key');
ok(mod.metaKey('https://dx.doi.org/10.1038/X') === '10.1038/x', 'strips the doi.org prefix and lowercases');

// ── a REAL D1: node:sqlite running the REAL schema ───────────────────────────────────
// ★这是复核 BLOCK 的 F1★：原来的假 env 的 all() 无视 WHERE/ORDER BY/LIMIT，直接把 rows 原样吐回，
// 于是整条 SELECT 从来没被测过 —— 复核把 board_id 改成 'nope'、LIMIT 改成 999999、删掉 ORDER BY，
// 我的套件照样 PASS。这与 P07 的 NC2 是同一个病根（mock 无视它自称在测的 SQL），只隔了一轮。
// 现在用真 SQLite + 真 schema 跑真 SQL，那三种改法都必然变红（见 nc_results.txt）。
import { DatabaseSync } from 'node:sqlite';
const SCHEMA = readFileSync(resolve(HERE, '../../../../../../deploy/cloudflare/schema_cloud.sql'), 'utf8');
function mkDB(items = []) {
  const db = new DatabaseSync(':memory:');
  // 真 schema 的 cn_items 段 + 其索引（含 idx_cn_items_board_recency —— F2 就是靠它）。
  // 先去掉 -- 行注释再按 ; 切：schema 里每条 CREATE 前面都有一行中文注释，不剥掉就永远匹配不上
  // （第一版就栽在这，症状是 'no such table: cn_items'）。
  const clean = SCHEMA.split('\n').filter(l => !/^\s*--/.test(l)).join('\n');
  let made = 0;
  for (const stmt of clean.split(';')) {
    const t = stmt.trim();
    if (/^CREATE (TABLE|INDEX)/i.test(t) && /cn_items/.test(t)) { db.exec(t + ';'); made++; }
  }
  if (made < 2) { console.error('FAIL: real schema did not load (got ' + made + ' stmts) -- the fixture would be fake'); process.exit(1); }
  const ins = db.prepare('INSERT OR REPLACE INTO cn_items (id,board_id,source_id,kind,title,url,summary,published_at,fetched_at,first_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?)');
  for (const it of items) ins.run(it.id, it.board_id || 'board1', it.source_id || 's', 'paper',
    it.title || 't', it.url || '', it.summary || '', it.published_at ?? null, it.fetched_at || '2026-07-17T00:00:00Z', '2026-07-01T00:00:00Z');
  // ★ANALYZE 是这条 fixture 的关键，不是装饰★
  // 没有统计信息时，SQLite 只能走有序索引 idx_cn_items_board_recency，于是「删掉 ORDER BY 也照样有序」——
  // 我据此写下「ORDER BY 无法被覆盖」，那是**假前提**：那是 fixture 没统计信息的产物，不是查询的性质。
  // 一旦有统计信息，计划就降级成 SCAN cn_items（SCAN 与 idx_cn_items_board 都合法，planner 没有保序义务），
  // 「先补最新」当场垮成 8/50 → ORDER BY 是**承重**的。复核用这一行证伪了我的「无法覆盖」。
  db.exec('ANALYZE');
  return db;
}
// 一个尽量贴近 D1 的适配器：prepare/bind/all/run/batch，参数用 ?1 风格（node:sqlite 支持，已验证）
function mkEnv(items = []) {
  const db = mkDB(items), sql = [], written = [];
  const wrap = (q) => ({
    bind(...a) {
      const st = { _q: q, _a: a,
        all: async () => { sql.push(q); return { results: db.prepare(q).all(...a) }; },
        run: async () => { sql.push(q); db.prepare(q).run(...a); return {}; } };
      return st;
    },
    run: async () => { sql.push(q); db.exec(q); return {}; },
    _q: q, _a: [],
  });
  const selRows = [];
  return { _db: db, _sql: sql, _written: written, _selRows: selRows, DB: {
    prepare: (q) => wrap(q),
    batch: async (stmts) => stmts.map(s => {
      sql.push(s._q);
      if (/^\s*SELECT/i.test(s._q)) {
        const rs = db.prepare(s._q).all(...(s._a || []));
        // 记录候选查询真正读回了多少行 —— META_SCAN 是否承重，只能这样观测
        if (s._q.startsWith('SELECT id, url FROM cn_items')) selRows.push(rs.length);
        return { results: rs };
      }
      db.prepare(s._q).run(...(s._a || []));
      written.push({ q: s._q, a: s._a });
      return {};
    }),
  } };
}
// 读回真正落库的元数据行（不再靠窥探 bind 参数猜）
const metaRows = (env) => env._db.prepare('SELECT * FROM cn_item_meta ORDER BY item_id').all();
// 真 OpenAlex 【总是】回 meta.count（已对线上实测确认），mock 就必须也回 —— 否则 mock 比真 API 更
// 宽松，会把「未知截断状态」这条路径测成一个真实里不存在的场景。mock 不忠实 = 测的是 mock。
// ★mock 必须映射真实的【单条】端点★（200 命中 / 404 未收录 / 429 限额）。
// P08 原本打 /works?filter= 批量 —— 那条路在生产上 429 ×3/3、每晚补 0 条，而当时的 mock 只认批量、
// 从不区分端点，所以那个【致命缺陷测不出来】。现在能了。
const OA = (works, opts = {}) => async (u, init) => {
  const url = String(u);
  const m = /\/works\/doi:([^?]+)/.exec(url);
  if (!m) return { ok: false, status: 400, json: async () => ({}) };
  const doi = decodeURIComponent(m[1]).toLowerCase();
  const hit = works.find(w => String(w.doi || '').toLowerCase().endsWith(doi));
  if (!hit) return { ok: false, status: 404, json: async () => ({}) };
  // ★mock 必须【遵守 select=】★：真 API 只回被选中的字段。mock 若无视 select=，
  // 那么「把 id 从 select 里删掉」这种改动就【永远测不出来】—— 这正是 P08 的 F1、P09 的 BLOCK-3
  // 一而再再而三的那个病：mock 无视它自称在测的请求。
  const sel = new URL(url).searchParams.get('select');
  if (opts.recordInit) opts.recordInit.push(init || {});
  if (!sel) return { ok: true, status: 200, json: async () => hit };
  const keep = new Set(sel.split(','));
  const out = {};
  for (const k of Object.keys(hit)) if (keep.has(k)) out[k] = hit[k];
  return { ok: true, status: 200, json: async () => out };
};
const work = (doi, type, srcName, srcType, cited = 0, oa = 'closed') => ({
  id: 'https://openalex.org/W1', doi: 'https://doi.org/' + doi.toLowerCase(), type,
  primary_location: { source: { display_name: srcName, type: srcType } },
  cited_by_count: cited, open_access: { oa_status: oa }, publication_year: 2026, authorships: [{}, {}],
});

console.log('\n== ACCEPTANCE 1: 预印本/期刊不混淆 ==');
{
  const rows = [
    { id: 'p1', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' },
    { id: 'p2', board_id: 'board1', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430' },
    { id: 'j1', board_id: 'board2', url: 'https://www.nejm.org/doi/full/10.1056/NEJMoa2512275' },
    { id: 'j2', board_id: 'board2', url: 'https://www.nature.com/articles/s41467-026-74639-z' },
  ];
  globalThis.fetch = OA([
    work('10.48550/arxiv.1904.06520', 'preprint', 'arXiv (Cornell University)', 'repository'),
    work('10.64898/2026.03.04.709430', 'preprint', 'bioRxiv (Cold Spring Harbor Laboratory)', 'repository'),
    work('10.1056/NEJMoa2512275', 'article', 'New England Journal of Medicine', 'journal', 2, 'green'),
    work('10.1038/s41467-026-74639-z', 'article', 'Nature Communications', 'journal', 0, 'gold'),
  ]);
  const env = mkEnv(rows), counts = { degraded: [] };
  await mod.enrichMeta(env, counts);
  const pre = new Map(metaRows(env).map(r => [r.item_id, r.is_preprint]));   // 从真库读回，不是窥探 bind 参数
  ok(pre.get('p1') === 1 && pre.get('p2') === 1, 'arXiv + bioRxiv are recorded as 预印本 (is_preprint=1)');
  ok(pre.get('j1') === 0 && pre.get('j2') === 0, 'NEJM + Nature Communications are NOT recorded as 预印本 (is_preprint=0)');
  const venue = new Map(metaRows(env).map(r => [r.item_id, r.venue]));
  ok(venue.get('j1') === 'New England Journal of Medicine' && venue.get('p1') === 'arXiv (Cornell University)',
    'the venue recorded is the one OpenAlex reports, verbatim');
  // the label a reader actually sees
  const preFacts = mod.metaFacts({ is_preprint: 1, venue: 'arXiv (Cornell University)', cited_by: 4, oa_status: 'green' });
  const jFacts = mod.metaFacts({ is_preprint: 0, venue: 'New England Journal of Medicine', cited_by: 2, oa_status: 'green' });
  ok(preFacts[0][0] === '预印本' && jFacts[0][0] === '发表于', 'the rendered label separates 预印本 from 发表于');
  ok(!JSON.stringify(preFacts.concat(jFacts)).includes('研究论文'),
    'NC: never claims 研究论文 -- OpenAlex reports Nature news as type=article too, so that label would be false');
  // a repository-hosted work whose type is NOT preprint is still a repository -> 预印本 side
  globalThis.fetch = OA([work('10.48550/arxiv.1904.06520', 'article', 'arXiv (Cornell University)', 'repository')]);
  const e2 = mkEnv([{ id: 'p1', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  await mod.enrichMeta(e2, { degraded: [] });
  // 复核提的健壮性 nit：条目一条都没补上时 metaRows(e2)[0] 是 undefined → TypeError 会让整轮中断，
  // 后面的断言就再也没机会报告了（nc5 就是这样）。判定要靠断言，不能靠崩溃。
  ok((metaRows(e2)[0] || {}).is_preprint === 1, 'source.type=repository alone is enough to call it 预印本 (not conflated with a journal)');
}

console.log('\n== ACCEPTANCE 2: 增强失败不阻塞原始论文 ==');
{
  const rows = [{ id: 'p1', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }];
  // (a) the network throws
  globalThis.fetch = async () => { throw new TypeError('network down'); };
  let counts = { degraded: [] }, threw = false;
  try { await mod.enrichMeta(mkEnv(rows), counts); } catch { threw = true; }
  ok(!threw && counts.degraded.some(d => d.startsWith('meta:')), 'fetch throwing -> enrichMeta degrades, never throws (cron survives)');
  // (b) OpenAlex returns 500
  globalThis.fetch = async () => ({ ok: false, status: 500, json: async () => ({}) });
  counts = { degraded: [] }; threw = false;
  const env500 = mkEnv(rows);
  try { await mod.enrichMeta(env500, counts); } catch { threw = true; }
  ok(!threw && counts.degraded.includes('meta:http500'), 'HTTP 500 -> degraded WITH its status code, never throws');
  ok(metaRows(env500).length === 0, 'HTTP 500 writes NO found=0 row (unknown != not-found)');
  // (c) malformed JSON body
  // 真 Response 永远有 .status；mock 少了它，r.status===404 会是 undefined —— 别让 mock 比真 API 宽松。
  globalThis.fetch = async () => ({ ok: true, status: 200, json: async () => { throw new SyntaxError('bad json'); } });
  counts = { degraded: [] }; threw = false;
  try { await mod.enrichMeta(mkEnv(rows), counts); } catch { threw = true; }
  ok(!threw && counts.degraded.some(d => d.startsWith('meta:')), 'malformed JSON -> degrades, never throws');
  // (d) the DB itself is broken while ATTACHING -> the page must still render
  const badEnv = { DB: { prepare() { throw new Error('D1 down'); } } };
  const items = [{ id: 'p1', title: 'a real paper' }];
  let out, threw2 = false;
  try { out = await mod.attachMeta(badEnv, items); } catch { threw2 = true; }
  ok(!threw2 && out[0].title === 'a real paper' && !out[0]._meta,
    'attachMeta with a dead D1 -> returns the papers unchanged, no _meta, no throw (原文不被阻塞)');
}

console.log('\n== dedup rules: two items, one DOI ==');
{
  // the same paper arriving through two different feeds must cost ONE lookup and enrich BOTH items
  const rows = [
    { id: 'dupA', board_id: 'board1', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430' },
    { id: 'dupB', board_id: 'board1', url: 'https://www.biorxiv.org/content/10.64898/2026.03.04.709430v2' },
  ];
  let calls = 0, asked = null;
  globalThis.fetch = async (u) => { calls++; asked = String(u);
    return { ok: true, status: 200, json: async () => work('10.64898/2026.03.04.709430', 'preprint', 'bioRxiv', 'repository') }; };
  const env = mkEnv(rows);
  await mod.enrichMeta(env, { degraded: [] });
  // asked 可能是 null（例如候选查询一条都没选中时根本不会发请求）—— 那时直接判失败，
  // 而不是让 new URL(null) 抛 TypeError 把整轮打断、后面的断言再也没机会报告。
  ok(!!asked, 'a request was actually issued (otherwise nothing below is meaningful)');
  ok(calls === 1 && /10\.64898/.test(decodeURIComponent(asked || '')),
    `the duplicated DOI is requested ONCE, not twice (one URL, one subrequest; calls=${calls})`);
  const ids = metaRows(env).filter(r => r.found === 1).map(r => r.item_id);
  ok(ids.includes('dupA') && ids.includes('dupB'), 'the single result is broadcast back to BOTH items');
  ok(calls === 1, 'DIR-007: exactly ONE external subrequest for the whole batch');
}

console.log('\n== DIR-007: 一个 DOI 一个子请求，上界 META_PER_RUN ==');
{
  const rows = Array.from({ length: 300 }, (_, i) => ({ id: 'x' + i, board_id: i % 2 ? 'board1' : 'board2', url: `https://arxiv.org/abs/24${String(i).padStart(2, '0')}.1234${i % 10}` }));
  let calls = 0; const urls = [];
  globalThis.fetch = async (u) => { calls++; urls.push(String(u)); return { ok: false, status: 404, json: async () => ({}) }; };
  await mod.enrichMeta(mkEnv(rows), { degraded: [] });
  console.log(`  300 candidates -> ${calls} subrequests (META_PER_RUN=${mod.META_PER_RUN}); cron 20/50 -> ${20 + calls}/50`);
  ok(calls === mod.META_PER_RUN, `exactly META_PER_RUN(${mod.META_PER_RUN}) subrequests -- one per DOI (got ${calls})`);
  ok(20 + calls <= 50, `DIR-007: cron stays inside the 50-subrequest Free limit (20 + ${calls} = ${20 + calls})`);
  // ★这条抓的就是【已发货的】那个缺陷★：批量 filter= 从边缘 429 ×3/3，P08 因此每晚静默补 0 条。
  ok(urls.length > 0 && urls.every(u => /\/works\/doi:/.test(u)) && !urls.some(u => /[?&]filter=/.test(u)),
    '每个请求都打【单条】/works/doi:X，绝不打 ?filter= 批量（批量在生产上 429，P08 因此每晚补 0 条）');
  // 复核 #5：DOI 必须编码，否则畸形 DOI 的 404 与「真没收录」无法区分 -> 给真论文写 found=0
  ok(urls.every(u => !/\/works\/doi:[^?]*[|&#]/.test(u)), 'DOI 里没有裸露的 |&# （URL 结构不会被撑破）');
}

console.log('\n== ★DOI 必须 URL 编码 —— 但真正的凶手是 # 和 ?，不是 &★ ==');
{
  // ★我上一版把这条的机理写错了，复核抓到了，这是本轮同一个病的第六次。★
  // 我写的是「& 会撑破 query → OpenAlex 回 404 → 真论文被写成 found=0」。实测（urlsplit）：
  //     '10.1234/abc&def' -> path DOI 原样 INTACT，mailto 也在  → & 是合法的 path sub-delim，什么都没坏
  //     '10.1234/abc#def' -> path DOI 变成 '10.1234/abc'，mailto=None、select=None  ★DOI 被截断★
  //     '10.1234/abc?def' -> path DOI 变成 '10.1234/abc'，mailto=None                ★DOI 被截断★
  // 即：# 之后是 fragment、? 之后是 query —— 它们不但截断 DOI，还把 mailto/select 整个吞掉。
  // 修复（encodeURIComponent）本身是对的，但依据必须是真的 —— 故这条改测 # 与 ?。
  // 两者都经同一个 id 形态 /^(?:biorxiv|medrxiv):(10\.\d{4,9}\/[^\s]{1,80})$/ 可达（实测确认）。
  for (const [ch, doi] of [['#', '10.1234/abc#def'], ['?', '10.1234/abc?def'], ['&', '10.1234/abc&def']]) {
    const urls = [];
    globalThis.fetch = async (u) => { urls.push(String(u)); return { ok: false, status: 404, json: async () => ({}) }; };
    ok(mod.metaDoi({ id: 'biorxiv:' + doi, url: '' }) === doi, `${ch}: 这个 DOI 确实经 id 形态到得了适配器`);
    await mod.enrichMeta(mkEnv([{ id: 'biorxiv:' + doi, board_id: 'board1', url: '' }]), { degraded: [] });
    if (!urls.length) { ok(false, `${ch}: no request issued`); continue; }
    const u = new URL(urls[0]);
    const seen = decodeURIComponent(u.pathname.split('doi:')[1] || '');
    ok(seen === doi, `${ch}: 服务端看到的 DOI 与我们要查的【完全一致】（实得 ${JSON.stringify(seen)}）—— 未编码时 # / ? 会把它截断`);
    ok(u.searchParams.get('mailto') && u.searchParams.get('select'),
      `${ch}: mailto 与 select 都还在 —— 未编码时 # / ? 会把它们整个吞掉，请求变成匿名且不带 select`);
  }
}

console.log('\n== ★每个 OpenAlex 请求必须带超时★：Promise.all 会等满，一个挂住的连接会卡死 cron（在 selectDaily 之前）==');
{
  // 复核 #4：worker 别处都用 AbortSignal.timeout(15000/20000)，P10 第一版这里没有。
  // 元数据是【增强】，不许为了补它把当日精选拖没。
  const inits = [];
  globalThis.fetch = async (u, init) => { inits.push(init || {}); return { ok: false, status: 404, json: async () => ({}) }; };
  await mod.enrichMeta(mkEnv([{ id: 'a', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]), { degraded: [] });
  ok(inits.length > 0, 'a request was issued');
  ok(inits.every(i => i && i.signal), '每个 OpenAlex fetch 都带 AbortSignal（超时），否则一个挂住的连接会卡死 cron');
}

console.log('\n== ★部分失败：12 个并行里混一个 429 —— 这才是真实形态，也是 unknown 守卫唯一被测到的地方★ ==');
{
  // ★复核 BLOCK #1/#2 就在这里★：原来只有同质用例（全 200/全 404/全 429/全抛）。
  // 全 429 会走 `if (errs === dois.length) return;` 早退 —— 于是 unknown 守卫【根本到不了】，
  // 把它删掉套件照样绿。那条「429 不写行」的断言是【早退喂出来的】＝装饰。
  // 部分失败才会真正走到 unknown 守卫：一部分 200、一部分 429。
  const good = { id: 'https://openalex.org/W1', doi: 'https://doi.org/10.48550/arxiv.1904.06520', type: 'preprint',
    primary_location: { source: { display_name: 'arXiv (Cornell University)', type: 'repository' } },
    cited_by_count: 4, open_access: { oa_status: 'green' }, publication_year: 2019 };
  globalThis.fetch = async (u) => {
    const s = decodeURIComponent(String(u));
    if (s.includes('1904.06520')) return { ok: true, status: 200, json: async () => good };
    return { ok: false, status: 429, json: async () => ({}) };      // 另一条被限流
  };
  const env = mkEnv([
    { id: 'good', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' },
    { id: 'rl', board_id: 'board1', url: 'https://arxiv.org/abs/1602.05629' },
  ]);
  const counts = { degraded: [] };
  await mod.enrichMeta(env, counts);
  const rows = metaRows(env);
  const byId = new Map(rows.map(r => [r.item_id, r]));
  ok(byId.has('good') && byId.get('good').found === 1, '成功的那条正常入库 found=1');
  ok(!byId.has('rl'), '★被限流的那条一行都不写★ —— 不是 found=0。写了就等于把我们自己的失败栽赃成「OpenAlex 不认识」，' +
     '而它会随 200 条窗口下沉、几乎永不重试（这条断言正是 unknown 守卫的唯一守护者）');
  ok(counts.degraded.includes('meta:http429'), '部分失败仍如实记降级并保留状态码');
  ok(rows.length === 1, `只写了成功的那一行（实得 ${rows.length}）`);
}

console.log('\n== F7: metadata rows for pruned items must not accumulate forever ==');
{
  globalThis.fetch = OA([]);
  const env = mkEnv([{ id: 'live', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  await mod.enrichMeta(env, { degraded: [] });   // 先跑一次让发货代码建表
  env._db.prepare("INSERT INTO cn_item_meta (item_id,doi,found,enriched_at) VALUES ('gone','10.1/x',1,'2026-07-01T00:00:00Z')").run();
  await mod.enrichMeta(env, { degraded: [] });
  ok(!metaRows(env).some(r => r.item_id === 'gone'), 'an orphan meta row (its cn_item was pruned) is deleted');
}

console.log('\n== the ORDER BY must actually be load-bearing: newest papers get enriched FIRST ==');
{
  // 自查：删掉 ORDER BY 时上面所有断言仍然全绿（nc7）。一个删掉也不会红的子句，就是没被测。
  // 语义是「先补最新的」：候选远多于一批时，被选中的必须是最新的那 50 条，而不是任意 50 条。
  const items = Array.from({ length: 300 }, (_, i) => ({
    id: 'n' + String(i).padStart(3, '0'), board_id: 'board1',
    // i 越大越新；DOI 唯一，便于回读到底问了哪些
    published_at: '2026-' + String(1 + (i % 12)).padStart(2, '0') + '-' + String(1 + (i % 28)).padStart(2, '0'),
    url: 'https://arxiv.org/abs/' + String(2000 + i) + '.10001',
  }));
  // 用真实的 recency 排序算出「应该被问到的最新 50 条」
  const db0 = mkDB(items);
  const want = db0.prepare(`SELECT id FROM cn_items WHERE board_id='board1'
    ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT ` + mod.META_PER_RUN).all().map(r => r.id);
  const askedUrls = [];
  globalThis.fetch = async (u) => { askedUrls.push(String(u)); return { ok: false, status: 404, json: async () => ({}) }; };
  await mod.enrichMeta(mkEnv(items), { degraded: [] });
  // 单条端点：从每条 /works/doi:<doi> 的 URL 里还原被问到的 DOI
  const askedIds = askedUrls.map(u => { const m = /arxiv\.(\d+)/.exec(decodeURIComponent(u)); return m ? 'n' + String(Number(m[1]) - 2000).padStart(3, '0') : null; }).filter(Boolean);
  const overlap = askedIds.filter(id => want.includes(id)).length;
  console.log(`  asked for ${askedIds.length} DOIs; ${overlap} of them are among the most recent ${mod.META_PER_RUN}`);
  // 一条没问到时 overlap===askedIds.length 会退化成 0===0 → 印出 PASS 却什么都没断言。
  // 本文件开篇就写着「不会失败的断言不是证据，是装饰」—— 那就先钉死这一轮非空。
  ok(askedIds.length === mod.META_PER_RUN, `a full run of ${mod.META_PER_RUN} DOIs was actually requested (guards the check below from passing on an empty run)`);
  ok(overlap === askedIds.length, 'the run is exactly the most-recent items (ORDER BY is doing real work -- nc7 proves it)');
}

console.log('\n== META_SCAN must actually bound the READ (nc6 was mislabelled 承重 in round 2) ==');
{
  // 自查+复核：我原来的 nc6 把 `LIMIT ?3` 改成 `LIMIT 999999`，留下一个没用上的绑定参数 →
  // 测试是因为**绑定参数个数不匹配**而红的，不是因为 LIMIT 语义。我看到 exit=1 就写了「承重」。
  // 那是**假的覆盖声明**，正是本项目的病根。真正的观测方式：候选远多于 META_SCAN 时，
  // 每板读回的行数必须恰好等于 META_SCAN（LIMIT 生效），而不是把整板都读回来。
  const per = mod.META_SCAN + 120;                    // 每板都超过 META_SCAN
  const items = [];
  for (const b of ['board1', 'board2'])
    for (let i = 0; i < per; i++)
      items.push({ id: b + '-' + String(i).padStart(4, '0'), board_id: b,
        published_at: '2026-07-' + String(1 + (i % 28)).padStart(2, '0'),
        url: 'https://arxiv.org/abs/' + (3000 + items.length) + '.20002' });
  globalThis.fetch = async () => ({ ok: false, status: 404, json: async () => ({}) });   // 单条端点的真实「未收录」回法
  const env = mkEnv(items);
  await mod.enrichMeta(env, { degraded: [] });
  console.log(`  ${per} candidates per board -> SELECT returned ${JSON.stringify(env._selRows)} rows (META_SCAN=${mod.META_SCAN})`);
  ok(env._selRows.length === 2 && env._selRows.every(n => n === mod.META_SCAN),
    'each per-board candidate query reads exactly META_SCAN rows -- the LIMIT bounds the READ');
  // 上面那条会随 META_SCAN 一起缩放（用例规模就是从常量推出来的），所以它证明「LIMIT 起作用」，
  // 但【证明不了 META_SCAN 取值合理】—— 把 META_SCAN 调成 999999 它照样绿。故另加一条守常量的 lint。
  // ★如实说明这条断言【是什么】★：它是对常量的算术校验，不是实测读取量，DB 都没参与。
  // 真实读取量另有其人兜底：KEEP_PER_BOARD=300 把 board1+board2 限在约 600 行，
  // 所以 META_SCAN=999999 其实【不会】真的烧穿 D1 预算（实际仍约 600 行/晚）——
  // 这条 lint 防的是「常量被调成离谱值」，不是在测预算。别把它读成预算实测。
  const cap = 2 * mod.META_SCAN;
  console.log(`  lint (arithmetic, no DB): 2 x META_SCAN = ${cap}; real reads are bounded by KEEP_PER_BOARD=300 -> ~600 rows/night`);
  ok(cap <= 25000, 'META_SCAN stays a sane constant (lint on the constant, NOT a measured read budget)');
}

console.log('\n== ★select= 的字段必须是 OpenAlex 真的认的★（mock 只验形状，不验合法性 —— 复核 #2）==');
{
  // 复核实测：往 select= 里塞一个不存在的字段（如 authors_count）→ 真 API 回
  //   HTTP 400 {"error":"Invalid query parameters error.","message":"authors_count is not a valid select field..."}
  // 而我的 mock 只按形状裁字段、从不校验合法性 → 套件照样 PASS，生产却会 12/12 全 400 →
  // 全部落入 unknown → errs===dois.length → ★每晚 0 行★ —— 与 P08 的静默空转【同一个盲区】。
  // 这里把「发货代码 select= 里的每个字段都必须在 OpenAlex 的合法集合内」钉死。
  // 合法集合取自 OpenAlex 的 Work 对象顶层字段（复核已对真 API 逐个确认过本清单里用到的那些）。
  // ★不许手写这个集合★：第一版我凭记忆写了 48 个字段，其中 'grants' 真 API 会拒（400）——
  // 守卫会【放行】一个真 API 不认的字段＝比没有守卫更糟（它让人以为查过了）。复核问「你这列表是真的吗」，
  // 一查就是假的。故改为读【从 API 自己的 400 报文抓下来的】产物，出处与抓取日期都在文件里。
  const VALID_WORK_FIELDS = new Set(JSON.parse(readFileSync(
    resolve(HERE, '../../ADP-V02-P10-OPENALEX-SINGLE/test-results/openalex_valid_select_fields.json'), 'utf8')).valid_select_fields);
  ok(VALID_WORK_FIELDS.size > 40, `合法字段集来自 API 自己的 400 报文（${VALID_WORK_FIELDS.size} 个），不是我手写的`);
  ok(!VALID_WORK_FIELDS.has('grants'), "'grants' 不在其中 —— 这正是我手写版里那个真 API 会拒的字段");
  const urls = [];
  globalThis.fetch = async (u) => { urls.push(String(u)); return { ok: false, status: 404, json: async () => ({}) }; };
  await mod.enrichMeta(mkEnv([{ id: 'a', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]), { degraded: [] });
  ok(urls.length > 0, 'a request was issued (otherwise nothing below is meaningful)');
  const sel = (new URL(urls[0])).searchParams.get('select');
  ok(!!sel, 'the request carries a select= (payload stays small)');
  const fields = (sel || '').split(',').filter(Boolean);
  const bogus = fields.filter(f => !VALID_WORK_FIELDS.has(f));
  ok(fields.length > 0 && bogus.length === 0,
    `select= 的每个字段都是 OpenAlex 认的（非法字段会让真 API 回 400 → 12/12 全 unknown → 每晚 0 行，` +
    `正是 P08 那种静默空转）。非法字段：${JSON.stringify(bogus)}`);
  // 发货代码确实依赖这些字段落库，故它们必须在 select= 里 —— 少一个就是另一种静默空转
  for (const need of ['id', 'doi', 'type', 'primary_location', 'cited_by_count', 'open_access'])
    ok(fields.includes(need), `select= 必须包含 ${need}（落库要用它；漏了就是 NULL 字段的静默降级）`);
}

console.log('\n== 单条端点回规范记录 -> P08 的「重复 work」问题从根上消失（含 oa_id 的【行为】断言）==');
{
  // ★这一整节在第 3 轮被我自己的 section 拼接误删了★ —— 连同 oa_id 的行为断言一起。
  // 复核的 ncO（select= 里仍写着 id，落库却 bind null）因此变得测不出来：套件照样绿。
  // 教训与本文件开篇同一句：★行为测试，不是拿正则去 grep 请求★。lint 查请求，这里查【结果】，两者都要。
  //
  // 背景：P08 用批量 filter= 时同一 DOI 会回多条 work（复核实测 arxiv:1506.01497 回 2 条：18240 / 6274），
  // D1 batch 按序执行＝最后一条赢 → 页面会把 6274 当事实。换成 /works/doi:X 后端点直接回【规范记录】
  // （复核独立实测 5/5 一致回 W2613718673 / 18240），故响应侧去重不再需要 —— 问题不是被绕过，是不存在了。
  const canonical = { id: 'https://openalex.org/W2613718673', doi: 'https://doi.org/10.48550/arxiv.1506.01497',
    type: 'preprint', primary_location: { source: { display_name: 'arXiv (Cornell University)', type: 'repository' } },
    cited_by_count: 18240, open_access: { oa_status: 'green' }, publication_year: 2015 };
  globalThis.fetch = OA([canonical]);
  const env = mkEnv([{ id: 'w', board_id: 'board1', url: 'https://arxiv.org/abs/1506.01497' }]);
  await mod.enrichMeta(env, { degraded: [] });
  const rows = metaRows(env);
  ok(rows.length === 1 && rows[0].cited_by === 18240,
    `规范记录的被引数 18240 落库（实得 ${rows[0] && rows[0].cited_by}）`);
  ok(rows[0] && rows[0].oa_id === 'https://openalex.org/W2613718673',
    `★oa_id 真的落库了规范记录的身份★（实得 ${rows[0] && rows[0].oa_id}）—— P10 的立论就是「单条端点回规范记录」，` +
    `而那条记录的身份正是被丢掉过、又被我删掉断言的那个字段`);
  ok(rows[0] && rows[0].venue === 'arXiv (Cornell University)' && rows[0].is_preprint === 1,
    'venue / is_preprint 也照 OpenAlex 的口径落库');
}

console.log('\n== 404=确知未收录 / 429=不知道：后者绝不写 found=0 ==');
{
  // 这一节同样在第 3 轮被误删。批量时代的「截断」判定随分页消失了，但这条纪律更重要：
  // 把「不知道」写成「查不到」＝把我们自己的失败栽赃给 OpenAlex，而被误判的条目会随 200 条窗口下沉、
  // 几乎永不重试（META_RETRY_DAYS 只救得了 found=0 的，救不了从没写过的）。
  globalThis.fetch = async () => ({ ok: false, status: 404, json: async () => ({}) });
  const e404 = mkEnv([{ id: 'ghost', board_id: 'board1', url: 'https://arxiv.org/abs/2999.99999' }]);
  await mod.enrichMeta(e404, { degraded: [] });
  const r404 = metaRows(e404);
  ok(r404.length === 1 && r404[0].found === 0, '404（确知未收录）-> 写 found=0，不必每晚重查');

  globalThis.fetch = async () => ({ ok: false, status: 429, json: async () => ({}) });
  const e429 = mkEnv([{ id: 'rl', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  const c429 = { degraded: [] };
  await mod.enrichMeta(e429, c429);
  ok(metaRows(e429).length === 0, '429 -> 一行都不写（不知道 != 查不到）');
  ok(c429.degraded.includes('meta:http429'), '429 保留状态码（正是让 P08 隐形整整一轮的那个信号）');
}

console.log('\n== not-found bookkeeping：别每晚重问同一批 miss，但也别永远不再问（★P10 的价值全靠它★）==');
{
  // ★这一节被我第 3 轮的 section 拼接吃掉过，复核第 4 轮才发现★（我当时以为只丢了两节，其实是四节）。
  // 它守的是 P10 的【全部价值】：12 条/晚 啃 ~600 条候选、约 50 晚。
  // 一旦 `OR m.enriched_at >= ?2` 没了，found=0 的行不再被排除 → 配合 ORDER BY recency + LIMIT 12，
  // ★同样那 12 条最新的 miss 会被每晚重问，永远★ —— 存量一步都不前进，12 个子请求全烧在重复确认已知的 miss 上。
  // 那是一种静默的近乎空转：正是 P10 存在要治的那个病。
  globalThis.fetch = OA([]);   // OpenAlex 不认识它 -> 单条端点回 404
  const env = mkEnv([{ id: 'ghost', board_id: 'board1', url: 'https://arxiv.org/abs/2999.99999' }]);
  await mod.enrichMeta(env, { degraded: [] });
  const row = metaRows(env).find(r => r.item_id === 'ghost');
  ok(row && row.found === 0, 'a miss is recorded (found=0) so it is not re-requested every run');
  // ★行为测试，不是拿正则去 grep SQL★（复核 F1：grep 冒充行为测试）。真跑一次：miss 之后再跑，
  // 该条目不应再被请求；把 enriched_at 推到 META_RETRY_DAYS 之前，它必须重新被请求。
  let asked2 = null;
  globalThis.fetch = async (u) => { asked2 = u; return { ok: false, status: 404, json: async () => ({}) }; };
  asked2 = null; await mod.enrichMeta(env, { degraded: [] });
  ok(asked2 === null, 'a fresh miss is NOT re-requested on the next run');
  env._db.prepare("UPDATE cn_item_meta SET enriched_at = '2026-01-01T00:00:00Z' WHERE item_id='ghost'").run();
  asked2 = null; await mod.enrichMeta(env, { degraded: [] });
  ok(asked2 !== null && decodeURIComponent(asked2).includes('2999.99999'), 'but it IS retried once enriched_at ages past META_RETRY_DAYS');
}

console.log('\n== F2：LIMIT 限的是返回行数不是扫描量 —— 计划必须走 recency 索引、不许 TEMP B-TREE ==');
{
  // 复核实测：board_id IN ('board1','board2') 会放弃 idx_cn_items_board_recency 并 USE TEMP B-TREE
  // FOR ORDER BY —— 即先把整个板块排完序再 LIMIT。LIMIT 限的是返回行数，不是扫描量。
  // 先让【发货代码自己】把 cn_item_meta 建出来（用它自己的 DDL，不是我另写一份 —— 否则测的是我的表）
  // ★这一节也被那次拼接吃掉了★。它守的是【前面某一轮复核 BLOCK 过的那个原缺陷】：
  // board_id IN (两个值) 会让计划放弃 idx_cn_items_board_recency → USE TEMP B-TREE FOR ORDER BY，
  // 即先把整板排完序再 LIMIT。守卫没了，那个缺陷就能原样回来而没人知道。
  const planEnv = mkEnv([]);
  globalThis.fetch = OA([]);
  await mod.enrichMeta(planEnv, { degraded: [] });
  const db = planEnv._db;
  const plan = (sql) => db.prepare('EXPLAIN QUERY PLAN ' + sql).all().map(r => r.detail).join(' | ');
  const inPlan = plan(`SELECT id, url FROM cn_items WHERE board_id IN ('board1','board2')
      AND NOT EXISTS (SELECT 1 FROM cn_item_meta m WHERE m.item_id = cn_items.id AND (m.found = 1 OR m.enriched_at >= '2026-01-01'))
    ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 200`);
  const eqPlan = plan(`SELECT id, url FROM cn_items WHERE board_id = 'board1'
      AND NOT EXISTS (SELECT 1 FROM cn_item_meta m WHERE m.item_id = cn_items.id AND (m.found = 1 OR m.enriched_at >= '2026-01-01'))
    ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 200`);
  console.log('  IN(2 boards): ' + inPlan.slice(0, 96));
  console.log('  = 1 board   : ' + eqPlan.slice(0, 96));
  ok(/TEMP B-TREE/i.test(inPlan), 'reproduces the defect: IN (2 boards) forces USE TEMP B-TREE FOR ORDER BY');
  ok(!/TEMP B-TREE/i.test(eqPlan), 'the shipped per-board query needs NO temp sort');
  ok(/idx_cn_items_board_recency/.test(eqPlan), 'the shipped per-board query uses idx_cn_items_board_recency');
  // and the shipped code really does issue per-board equality queries, not an IN
  const env = mkEnv([{ id: 'a', board_id: 'board1', url: 'https://arxiv.org/abs/1904.06520' }]);
  globalThis.fetch = OA([]);
  await mod.enrichMeta(env, { degraded: [] });
  const sel = env._sql.filter(q => q.startsWith('SELECT id, url FROM cn_items'));
  ok(sel.length === 2 && sel.every(q => /board_id = \?1/.test(q)) && !sel.some(q => /board_id IN/.test(q)),
    'the shipped code issues one equality query per board (board1, board2), never board_id IN (...)');
}

// ★复核第 6 轮的 attack B（残余 #3，非阻塞，我采纳）★：小节盘点只守「整节被删」，守不住
// 「留着标题、把断言掏空」—— 复核实测这样能悄悄从 67 掉到 63，而守卫一声不吭。
// 这不是假想：本轮第 3 轮我就真的把 oa_id 的行为断言掏掉过。故把断言总数钉住：数量掉了就红。
// 加断言时把这个数一起改 —— 那是【有意识的动作】，正是我们想要的摩擦。
// 钉的是【ok() 计的断言数】(passCount+fails)，不是 grep 出来的行数 ——
// 这条自检自己也会印一行 PASS，grep 会把它算进去，于是 67 变 68。数错对象也是一种假前提。
const EXPECTED_ASSERTIONS = 67;
{
  const n = passCount + fails;
  if (n !== EXPECTED_ASSERTIONS) {
    console.log(`  FAIL ★断言数从 ${EXPECTED_ASSERTIONS} 变成了 ${n}★ —— 要么有断言被掏空（覆盖悄悄流失），` +
      `要么你加了断言但没更新 EXPECTED_ASSERTIONS。两种都要人看一眼，不许静默通过。`);
    fails++;
  } else console.log(`  PASS 断言数 ${n} 与钉住的一致（防「留着标题、掏空断言」式的覆盖流失）`);
}

console.log('\nACCEPTANCE = ' + (fails ? 'FAIL' : 'PASS'));
process.exit(fails ? 1 : 0);
