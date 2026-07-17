// ADP-V02-P09 (T043 上线) 验收。跑【发货的】coverageGrid/coverageHTML，不是复制品。
//
// T043 acceptance: 每个 enabled source/year/month 有 count 或解释；0 个静默未解释空洞。
// ★但这条验收有个洞，必须先说清楚★：它分辨不出「诚实的空洞」和「错的解释」。
// v0_1 的 gap_detector 对真实线上数据跑出 unexplained=0（PASS），靠的是把 93% 的格子
// 标成 source_not_yet_active（「那时这个源还不存在」）—— 对 arXiv/Nature/NEJM 全是假话。
// 所以这里除了验「每格有 count 或解释」，还必须验「解释本身不是编的」。
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const WORKER = resolve(HERE, '../../../../../../deploy/cloudflare/worker_cloud.js');
const w = readFileSync(WORKER, 'utf8');
const S = w.indexOf('// ───────────────────────── T043 覆盖与缺口（Source-Year-Month） ');
const E = w.indexOf('async function systemPage');
if (S < 0 || E < 0) { console.error('FAIL: could not locate the shipped T043 block'); process.exit(1); }
const helpers = `const BOARD_NAMES={board1:'板块一',board2:'板块二',board3:'板块三',board4:'板块四'};
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}\n`;
const mod = await import('data:text/javascript;base64,' + Buffer.from(
  helpers + w.slice(S, E) + '\nexport {coverageGrid, coverageHTML, covMonths, COV_REASON, COVERAGE_START};'
).toString('base64'));

let fails = 0;
const ok = (c, m) => { if (!c) { fails++; console.log('  FAIL ' + m); } else console.log('  PASS ' + m); };

// ★真 D1：node:sqlite + 真 schema_cloud.sql★
// 第一版这里是个哑 mock，prepare(q) 根本不看 q —— 复核把发货查询换成
// "SELECT this_column_does_not_exist FROM table_that_does_not_exist" 后套件照样 ACCEPTANCE = PASS。
// 一条在每次 /system 都会 500 的查询能干净通过验收。这与 P08 第 1 轮 BLOCK 的 F1 是同一个错，
// 我在 P08 用真 sqlite 修好了，转头在 P09 又写了个哑 mock。故此处改用真库跑真 SQL。
import { DatabaseSync } from 'node:sqlite';
const SCHEMA = readFileSync(resolve(HERE, '../../../../../../deploy/cloudflare/schema_cloud.sql'), 'utf8');
function mkDB(sources, items) {
  const db = new DatabaseSync(':memory:');
  const clean = SCHEMA.split('\n').filter(l => !/^\s*--/.test(l)).join('\n');
  let made = 0;
  for (const st of clean.split(';')) {
    const t = st.trim();
    if (/^CREATE (TABLE|INDEX)/i.test(t) && /(cn_items|cn_sources)/.test(t)) { db.exec(t + ';'); made++; }
  }
  if (made < 2) { console.error('FAIL: real schema did not load -> fixture would be fake'); process.exit(1); }
  const si = db.prepare('INSERT INTO cn_sources (id,board_id,name,method,health) VALUES (?,?,?,?,?)');
  for (const s of sources) si.run(s.id, s.board_id, s.name || s.id, 'rss', s.health || 'active');
  const ii = db.prepare('INSERT INTO cn_items (id,board_id,source_id,kind,title,url,fetched_at,first_seen_at,published_at) VALUES (?,?,?,?,?,?,?,?,?)');
  let k = 0;
  for (const it of items) for (let i = 0; i < it.n; i++)
    ii.run('x' + (k++), it.board_id, it.source_id, 'paper', 't', 'u', '2026-07-01', '2026-07-01', it.mo + '-15');
  return db;
}
function mkEnv(sources, items, opts = {}) {
  const db = mkDB(sources, items); let queries = 0;
  const wrap = q => ({ _q: q, all: async () => { queries++; return { results: db.prepare(q).all() }; } });
  return { _q: () => queries, _db: db, DB: {
    prepare(q) { if (opts.throw) throw new Error('D1 down'); return wrap(q); },
    batch: async (sts) => { queries++; return sts.map(st => ({ results: db.prepare(st._q).all() })); },
  } };
}
// 线上真实形态：37 个登记源，但只有 31 个抓到过条目 —— 复核 BLOCK-1 就在这个差里
const SRC = [
  { id: 'arxiv-all', board_id: 'board1' }, { id: 'biorxiv', board_id: 'board1' },
  { id: 'nature', board_id: 'board2' }, { id: 'ndrc-gov', board_id: 'board3' },
  { id: 'stats-gov', board_id: 'board3' },      // ← A0 官方源，线上一条都没抓到
  { id: 'lancet', board_id: 'board2' },         // ← 同上
];
const LIVE = [
  { source_id: 'arxiv-all', board_id: 'board1', mo: '2026-07', n: 150 },
  { source_id: 'arxiv-all', board_id: 'board1', mo: '2018-09', n: 2 },
  { source_id: 'biorxiv', board_id: 'board1', mo: '2026-07', n: 90 },
  { source_id: 'nature', board_id: 'board2', mo: '2026-07', n: 40 },
  { source_id: 'ndrc-gov', board_id: 'board3', mo: '2026-07', n: 20 },
];

console.log('shipped COVERAGE_START =', mod.COVERAGE_START);

console.log('\n== 发货的 SQL 必须能对着真 schema 跑通（哑 mock 抓不到这一条） ==');
{
  // 判定要靠断言不靠崩溃：SQL 写坏时真库会抛，那时必须【报告失败】而不是让整轮死掉，
  // 否则后面所有断言都失去报告机会（复核在 P08/T041 都点过这个）。
  let ran = true, err = '';
  try { await mod.coverageGrid(mkEnv(SRC, LIVE)); } catch (e) { ran = false; err = String(e.message || e).slice(0, 80); }
  ok(ran, '发货的两条查询都能对着真 schema_cloud.sql 执行' + (ran ? '' : ' —— 实际抛了：' + err));
  if (!ran) { console.log('\nACCEPTANCE = FAIL'); process.exit(1); }
}

console.log('\n== ★核心★：发货代码绝不声称「那时这个源还不存在」 ==');
{
  const env = mkEnv(SRC, LIVE);
  const g = await mod.coverageGrid(env);
  const html = mod.coverageHTML(g);
  const reasons = Object.keys(mod.COV_REASON);
  ok(!reasons.includes('source_not_yet_active'),
    'COV_REASON 里没有 source_not_yet_active —— 没有独立证据就不下这个判断');
  // （这里原本还有一行 `ok(... || true, 'placeholder')` —— 一条【永远不会失败】的断言。
  //   那正是本项目反复栽的那个跟头：不会失败的断言不是证据，是装饰。已删。）
  // 整份产物里不得出现「该源当时不存在」这个 claim。
  // 注意 not_backfilled 的文案里含有「不是这个源当时不存在」——那是在【否定】这个说法，
  // 故先把那句否定剔掉再检查，否则会把「澄清」误判成「断言」。
  const body = JSON.stringify(g) + html.split('不是这个源当时不存在').join('');
  const claimsInactive = /source_not_yet_active/.test(body) || /源当时还不存在/.test(body);
  ok(!claimsInactive, '输出里不含「该源当时不存在」的断言（v0_1 工具对同样数据会给出 3665/3937 = 93% 这样的假解释）');
  ok(mod.COV_REASON.not_backfilled.includes('不是这个源当时不存在'),
    '未覆盖的月份被明确解释为「未回填」，并点명它不等于源不存在');
}

console.log('\n== 每格都有 count 或解释，且 0 未解释 ==');
{
  const g = await mod.coverageGrid(mkEnv(SRC, LIVE));
  ok(g.cells === g.months * g.sources_in_registry, `cells = months × 登记源数 (${g.months} × ${g.sources_in_registry} = ${g.cells})`);
  ok(g.covered + g.not_backfilled === g.cells, `covered(${g.covered}) + not_backfilled(${g.not_backfilled}) = cells(${g.cells}) —— 无遗漏`);
  // ★复核 BLOCK-4：原本这里是 ok(g.unexplained === 0)，而 unexplained 是个恒为 0 的字面量 ——
  //   任何改动都推翻不了它。一条不可能失败的断言就是装饰，而这份套件上面还刚吹过自己删掉了一条。已删。
  //   能失败的等价不变量是下面这条：登记表里的每个源都必须出现在网格里，一格都不许少。
  ok(g.sources_in_registry === SRC.length,
    `网格覆盖登记表里【全部】 ${SRC.length} 个源（实得 ${g.sources_in_registry}）—— 抓不到东西的源不许消失`);
  ok(g.covered + g.not_backfilled === g.cells, '每格非 covered 即 not_backfilled —— 无静默空洞');
  ok(g.coverage_pct < 5, `时间覆盖率如实很低（${g.coverage_pct}%）—— 这是真实债务，不是失败`);
}

console.log('\n== 覆盖率算得对（拿真实分布验算） ==');
{
  const g = await mod.coverageGrid(mkEnv(SRC, LIVE));
  // arxiv-all 覆盖 2 个月（2018-09, 2026-07），其余 3 源各 1 个月 => 5 格 covered
  ok(g.covered === 5, `covered = 5（arxiv 2 月 + 其余 3 源各 1 月），实得 ${g.covered}`);
  const arx = g.per_source.find(s => s.source_id === 'arxiv-all');
  ok(arx.months_covered === 2 && arx.items === 152, `arxiv-all: 2 个月 / 152 条（实得 ${arx.months_covered} / ${arx.items}）`);
  ok(arx.first === '2018-09' && arx.last === '2026-07', `已覆盖区间 2018-09 … 2026-07（实得 ${arx.first} … ${arx.last}）`);
  ok(g.per_source.length === SRC.length, `per_source 有全部 ${SRC.length} 个登记源（实得 ${g.per_source.length}）`);
  // ★复核 BLOCK-1 的定钉★：一条都没抓到过的源必须【出现在网格里并被点名】，不许静默消失
  ok(g.sources_never_ingested.includes('stats-gov') && g.sources_never_ingested.includes('lancet'),
    `从未抓到条目的源被点名而不是被隐藏：${JSON.stringify(g.sources_never_ingested)}`);
  ok(g.sources_with_items === 4 && g.sources_in_registry === 6,
    `登记 6 个源、其中 4 个真抓到过（实得 ${g.sources_in_registry} / ${g.sources_with_items}）`);
  const ghost = g.per_source.find(x => x.source_id === 'stats-gov');
  ok(ghost && ghost.months_covered === 0 && ghost.months_missing === g.months,
    'stats-gov（P04 接进来的 A0 官方源）在网格里是 0/127，而不是不存在');
  const pct = Math.round((g.covered / g.cells) * 1000) / 10;
  ok(g.coverage_pct === pct, `coverage_pct 是算出来的不是写死的（${g.coverage_pct}）`);
}

console.log('\n== 月份窗口正确（2016-01 起，含闰年与跨年） ==');
{
  const ms = mod.covMonths('2016-01', '2016-03');
  ok(ms.length === 3 && ms[0] === '2016-01' && ms[2] === '2016-03', 'covMonths(2016-01..2016-03) = 3 个月');
  const yr = mod.covMonths('2016-11', '2017-02');
  ok(yr.length === 4 && yr[1] === '2016-12' && yr[2] === '2017-01', '跨年正确：2016-12 -> 2017-01');
  ok(mod.covMonths('2016-01', '2015-12').length === 0, 'end 早于 start -> 空（不产生负数格）');
  const g = await mod.coverageGrid(mkEnv(SRC, LIVE));
  ok(g.months > 120, `窗口是 2016-01 至今，约 ${g.months} 个月（不是只看最近）`);
}

console.log('\n== DIR-007：一次聚合查询，行数由「源×月」组合数决定 ==');
{
  const env = mkEnv(SRC, LIVE);
  await mod.coverageGrid(env);
  ok(env._q() === 1, `整个覆盖网格只发 1 条 D1 查询（实得 ${env._q()}）`);
}

console.log('\n== 覆盖视图坏掉不许把 /system 带下线 ==');
{
  let threw = false;
  try { await mod.coverageGrid(mkEnv(SRC, LIVE, { throw: true })); } catch (e) { threw = true; }
  ok(threw, 'coverageGrid 本身会抛（由 systemPage 的 try/catch 兜住）');
  const src = w.slice(w.indexOf('async function systemPage'), w.indexOf('async function systemPage') + 900);
  ok(/try\s*\{\s*covHTML = coverageHTML\(await coverageGrid\(env\)\)/.test(src) && /catch\s*\(e\)\s*\{\s*covHTML = ''/.test(src),
    'systemPage 用 try/catch 包住覆盖视图 —— 它坏了页面照常渲染（与 P08 attachMeta 同一条纪律）');
}

console.log('\n== 空库不炸 ==');
{
  const g = await mod.coverageGrid(mkEnv([], []));
  ok(g.cells === 0 && g.covered === 0 && g.coverage_pct === 0, '空库 -> 0 格 0 覆盖 0%，不除零');
  ok(typeof mod.coverageHTML(g) === 'string', '空库仍能渲染');
}

console.log('\nACCEPTANCE = ' + (fails ? 'FAIL' : 'PASS'));
process.exit(fails ? 1 : 0);
