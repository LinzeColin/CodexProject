// P12 回填验证器 —— 真 node:sqlite 夹具（真 schema_cloud.sql）+ mock OAI + 承重负控。
// 判定标准贯穿本会话：不是「exit=1」，而是【哪一条断言变红】。每条负控都指名它该打中的断言。
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, writeFileSync, unlinkSync, existsSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join, parse } from 'node:path';

// 自定位：从本文件向上走，找到 arxiv-daily-push/deploy/cloudflare/{worker_cloud.js,schema_cloud.sql}。
// 这样无论从 scratchpad 还是从证据包里跑都能解析（P07 曾因写死 ../ 层数踩过 ENOENT）。
const HERE = dirname(fileURLToPath(import.meta.url));
const REL = 'arxiv-daily-push/deploy/cloudflare';
function locate() {
  let d = HERE, root = parse(d).root;
  while (true) {
    if (existsSync(join(d, REL, 'worker_cloud.js'))) return join(d, REL);
    if (existsSync(join(d, 'deploy/cloudflare/worker_cloud.js'))) return join(d, 'deploy/cloudflare');
    if (d === root) throw new Error('找不到 worker_cloud.js（从 ' + HERE + ' 向上）');
    d = dirname(d);
  }
}
const DIR = locate();
const WORKER = join(DIR, 'worker_cloud.js');
const SCHEMA = join(DIR, 'schema_cloud.sql');

// ★直接从发货文件抽取 //@P12-CORE 段并测它本体 —— 不是测副本，测的就是 worker_cloud.js 里跑的那段。★
const wsrc = readFileSync(WORKER, 'utf8');
const coreM = wsrc.match(/\/\/@P12-CORE-START([\s\S]*?)\/\/@P12-CORE-END/);
if (!coreM) { console.log('FAIL: worker_cloud.js 里找不到 //@P12-CORE 标记'); process.exit(1); }
const TMP = join(HERE, '.p12core.extracted.mjs');
writeFileSync(TMP, coreM[1] + '\nexport { nextBackfillFrom, advanceCursor, backfillWindow, runBackfill };\n');
const { nextBackfillFrom, advanceCursor, backfillWindow, runBackfill } = await import(pathToFileURL(TMP).href);
const TODAY = '2026-07-18';
const START = '2016-01-01';

let pass = 0, fail = 0;
const ok = (c, m) => { if (c) { pass++; } else { fail++; console.log('  FAIL:', m); } };
const section = (s) => console.log('\n== ' + s + ' ==');

function freshDb() {
  const db = new DatabaseSync(':memory:');
  db.exec(readFileSync(SCHEMA, 'utf8'));
  db.prepare("INSERT INTO cn_sources (id,board_id,name,platform,website,method,feed_url,official,cadence) VALUES ('arxiv-all','board1','arXiv','arxiv','','oai',NULL,1,'每日')").run();
  return db;
}
// 真 INSERT，复刻 worker 的 itemStmt：published_at = 论文真实 created 日 → 落进正确的覆盖格；ON CONFLICT 去重。
function realInsert(db) {
  return (items) => {
    for (const p of items) {
      db.prepare(`INSERT INTO cn_items (id,board_id,source_id,kind,title,url,summary,categories,authors,published_at,fetched_at,first_seen_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET fetched_at=excluded.fetched_at`)
        .run(p.id,'board1','arxiv-all','paper',p.title,'u','','','', p.published, TODAY+'T00:00:00Z', TODAY+'T00:00:00Z');
    }
  };
}
// 覆盖网格的落格查询，复刻 worker coverageGrid：按 published_at 的月份分格。
function coveredMonths(db) {
  const rows = db.prepare("SELECT substr(COALESCE(published_at,fetched_at),1,7) mo, COUNT(*) n FROM cn_items WHERE source_id='arxiv-all' GROUP BY mo").all();
  return new Map(rows.map(r => [r.mo, r.n]));
}
const cursorIO = (db) => ({
  get: async () => { const r = db.prepare("SELECT value FROM cn_meta WHERE key='backfill_from'").get(); return r ? r.value : null; },
  set: async (v) => db.prepare("INSERT INTO cn_meta (key,value) VALUES ('backfill_from',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value").run(v),
});
// mock OAI：给定要吐出的「页」序列（每页 {items, nextToken}），按调用次序返回。
function mockFetch(pages) {
  let i = 0;
  return async () => (i < pages.length ? pages[i++] : { items: [], nextToken: null });
}
// 真实 token 格式（本会话实测：token 值 url-encode 了 from=YYYY-MM-DD）
const REAL_TOKEN = 'verb%3DListRecords%26metadataPrefix%3DarXiv%26from%3D2016-03-04%26until%3D2016-03-05';

// ───────────────────────────────────────────────────────────────────────────
section('A. 游标从真实 OAI token 解析（无状态，token 里编码了 from=）');
ok(nextBackfillFrom(REAL_TOKEN) === '2016-03-04', 'A1 real token -> 2016-03-04');
ok(nextBackfillFrom(null) === null, 'A2 no token -> null');
ok(nextBackfillFrom('') === null, 'A3 empty -> null');

section('B. 窗口计算：until 封顶到 today，不越未来');
ok(backfillWindow('2016-01-01', TODAY, 30).until === '2016-01-31', 'B1 span=30 -> until=2016-01-31');
ok(backfillWindow('2026-07-01', TODAY, 30).until === TODAY, 'B2 span 越过 today -> until=today');
ok(backfillWindow('2016-01-01', TODAY, 30).from === '2016-01-01', 'B3 from = cursor');

section('C. 游标单调推进（★只进不退★）');
ok(advanceCursor('2016-03-01', REAL_TOKEN, '2016-03-31') === '2016-03-04', 'C1 有 token -> 停在 token 的 from');
ok(advanceCursor('2016-03-01', null, '2016-01-31') === '2016-03-01', 'C2 无 token 且 until<cursor -> 不后退，停原地');
ok(advanceCursor('2016-03-01', null, '2016-03-31') === '2016-03-31', 'C3 无 token -> 推进到窗口末');

// ───────────────────────────────────────────────────────────────────────────
section('D. 落格：历史条目按 created 落进正确的历史格（覆盖债务真的被填）');
{
  const db = freshDb();
  const before = coveredMonths(db);
  ok(!before.has('2016-03') && !before.has('2018-07'), 'D0 起始：2016-03 / 2018-07 两格为空');
  const degraded = [];
  await runBackfill({
    fetchPage: mockFetch([{ items: [
      { id: 'arxiv:1603.001', title: 't1', published: '2016-03-15T00:00:00Z' },
      { id: 'arxiv:1807.002', title: 't2', published: '2018-07-02T00:00:00Z' },
    ], nextToken: null }]),
    insertItems: realInsert(db), getCursor: cursorIO(db).get, setCursor: cursorIO(db).set,
    today: TODAY, START, PAGES: 2, SPAN_DAYS: 30, degraded,
  });
  const after = coveredMonths(db);
  ok(after.get('2016-03') === 1, 'D1 2016-03 格被填（+1）');
  ok(after.get('2018-07') === 1, 'D2 2018-07 格被填（+1）');
  ok(!after.has('2026-07'), 'D3 条目【没有】错落进 today(2026-07) 的格');
  ok(degraded.length === 0, 'D4 无降级');
}

section('E. 去重：同一 arxiv id 再来一次不产生重复行（ON CONFLICT）');
{
  const db = freshDb(); const degraded = [];
  const page = { items: [{ id: 'arxiv:1603.dup', title: 't', published: '2016-03-15T00:00:00Z' }], nextToken: null };
  for (let k = 0; k < 3; k++) {
    db.prepare("DELETE FROM cn_meta WHERE key='backfill_from'").run();      // 重置游标，强制重抓同一页
    await runBackfill({ fetchPage: mockFetch([page]), insertItems: realInsert(db),
      getCursor: cursorIO(db).get, setCursor: cursorIO(db).set, today: TODAY, START, PAGES: 2, SPAN_DAYS: 30, degraded });
  }
  const n = db.prepare("SELECT COUNT(*) c FROM cn_items WHERE id='arxiv:1603.dup'").get().c;
  ok(n === 1, 'E1 抓 3 次仍只有 1 行');
}

section('F. 页封顶 = 预算（DIR-007）：给 5 页却只抓 PAGES=2');
{
  const db = freshDb(); const degraded = [];
  let calls = 0;
  const fp = async (from, until, tok) => { calls++; return { items: [{ id: 'arxiv:p' + calls, title: 't', published: '2016-0' + calls + '-01T00:00:00Z' }], nextToken: REAL_TOKEN }; };
  await runBackfill({ fetchPage: fp, insertItems: realInsert(db), getCursor: cursorIO(db).get, setCursor: cursorIO(db).set,
    today: TODAY, START, PAGES: 2, SPAN_DAYS: 30, degraded });
  ok(calls === 2, 'F1 恰好抓 2 页（不是 5）');
}

section('G. ★永不抛★：抓取失败只降级，绝不拖垮当日运行');
{
  const db = freshDb(); const degraded = [];
  let threw = false, ret;
  try {
    ret = await runBackfill({ fetchPage: async () => { throw new TypeError('boom'); }, insertItems: realInsert(db),
      getCursor: cursorIO(db).get, setCursor: cursorIO(db).set, today: TODAY, START, PAGES: 2, SPAN_DAYS: 30, degraded });
  } catch { threw = true; }
  ok(!threw, 'G1 runBackfill 没有抛');
  ok(degraded.some(d => d.startsWith('backfill:')), 'G2 降级里记了 backfill:');
}

section('H. 追平近端：游标 >= today 时跳过（近端交给每日 cron）');
{
  const db = freshDb(); const degraded = []; let fetched = false;
  await cursorIO(db).set(TODAY);
  const r = await runBackfill({ fetchPage: async () => { fetched = true; return { items: [], nextToken: null }; },
    insertItems: realInsert(db), getCursor: cursorIO(db).get, setCursor: cursorIO(db).set, today: TODAY, START, PAGES: 2, SPAN_DAYS: 30, degraded });
  ok(r.skipped === 'caught_up' && !fetched, 'H1 已追平 -> 跳过、不抓');
}

// ───────────────────────────────────────────────────────────────────────────
// 承重负控。★只留真的★：把守卫的前提在【真 runBackfill】里破坏，看指定断言是否变红。
// 已删掉三条「独立复述一个假设、不跑真代码路径」的负控（NC-A/C/F）—— 那正是 P11 里被复核 BLOCK 的
// NC0 反模式（一个从被检查对象那里继承结论的对照，不是对照）。A1/C2/F1 本身就非空、就承重
// （各自断言一个具体值/计数，逻辑一坏就红），不需要再套一层假证明。
// 真正值得单列的只有落格：created-vs-fetched 是本阶段最微妙的 bug（datestamp≠created 的直接后果）。
section('NC-D. 证明 D1/D3 承重：在真 runBackfill 里把 published_at 换成 null（→COALESCE 落到 today）');
{
  const db = freshDb();
  const brokenInsert = (items) => { for (const p of items) db.prepare(`INSERT INTO cn_items (id,board_id,source_id,kind,title,url,summary,categories,authors,published_at,fetched_at,first_seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)`).run(p.id,'board1','arxiv-all','paper',p.title,'u','','','', null, TODAY+'T00:00:00Z', TODAY+'T00:00:00Z'); };
  await runBackfill({ fetchPage: mockFetch([{ items: [{ id: 'arxiv:x', title: 't', published: '2016-03-15T00:00:00Z' }], nextToken: null }]),
    insertItems: brokenInsert, getCursor: cursorIO(db).get, setCursor: cursorIO(db).set, today: TODAY, START, PAGES: 2, SPAN_DAYS: 30, degraded: [] });
  const m = coveredMonths(db);
  ok(!m.has('2016-03') && m.get('2026-07') === 1, 'NC-D 坏 insert 下历史格空、条目堆 today 格 -> D1/D3 确会红（故 D1/D3 承重）');
}

section('I. OAI 忙(503)：★不推进游标★，本夜降级、下夜重试同窗口');
{
  const db = freshDb(); const degraded = [];
  await cursorIO(db).set('2016-05-01');
  const r = await runBackfill({ fetchPage: async () => ({ items: [], nextToken: null, busy: true }),
    insertItems: realInsert(db), getCursor: cursorIO(db).get, setCursor: cursorIO(db).set,
    today: TODAY, START, PAGES: 2, SPAN_DAYS: 366, degraded });
  const after = await cursorIO(db).get();
  ok(r.busy === true && degraded.includes('backfill:oai503'), 'I1 忙 -> busy + 降级 backfill:oai503');
  ok(after === '2016-05-01', 'I2 游标【未推进】（下夜重试同窗口）');
}

section('J. ★防卡死★：单日≥一页时 token.from==cursor（skip= 被丢弃），仍强制 +1 天前进');
{
  const db = freshDb(); const degraded = [];
  await cursorIO(db).set('2016-03-01');
  const denseToken = 'verb%3DListRecords%26from%3D2016-03-01%26until%3D2016-12-31%26skip%3D1300'; // token 的 from 仍是 cursor
  const r = await runBackfill({ fetchPage: async () => ({ items: [{ id: 'arxiv:dense', title: 't', published: '2016-03-01T00:00:00Z' }], nextToken: denseToken }),
    insertItems: realInsert(db), getCursor: cursorIO(db).get, setCursor: cursorIO(db).set, today: TODAY, START, PAGES: 1, SPAN_DAYS: 366, degraded });
  const after = await cursorIO(db).get();
  ok(after === '2016-03-02', 'J1 游标强制前进到 2016-03-02（无此守卫会卡在 2016-03-01 永久重放）');
  ok(r.more === true, 'J2 more=true（窗口内还有数据）');
}

// ───────────────────────────────────────────────────────────────────────────
const EXPECTED_ASSERTIONS = 24;
section('自检');
console.log(`  pass=${pass} fail=${fail} total=${pass + fail}`);
ok(pass + fail === EXPECTED_ASSERTIONS, `SELF 断言总数 == ${EXPECTED_ASSERTIONS}（防「留标题、掏空断言」）`);
try { unlinkSync(TMP); } catch (e) { }
console.log(fail === 0 ? '\nOK — all green（测的是从 worker_cloud.js 抽取的发货代码本体）' : `\nRED — ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
