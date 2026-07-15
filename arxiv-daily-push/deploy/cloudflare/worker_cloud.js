/**
 * ADP 云端原生 Worker（Owner 2026-07-15 指令：网页即主体，整套系统跑在 Cloudflare，
 * 不再依赖 Mac）。一个 Worker + 一个 D1 完成五环节：抓取 → 选择 → 讲义 → 主动回忆 → FSRS 排程。
 * cron 每日跑流水线；页面直接读写 D1；主动回忆评分即时进 FSRS（无回传队列，云端即真相）。
 *
 * Stage 1：数据基座 + 流水线 + today 页。Stage 2：六主题全 UI。Stage 3：切 adp.linzezhang.com。
 */

// ───────────────────────── 数据源注册表（对应 boards_v0_3.yaml；全部进每日精选） ─────────────────────────
const REGISTRY = [
  { board: 'board1', name: '板块一 · 研究前沿', sources: [
    { id: 'arxiv-all', name: 'arXiv 全站（所有领域）', platform: 'arXiv OAI-PMH', website: 'https://arxiv.org', method: 'arxiv', official: 1, cadence: '每日' },
    { id: 'biorxiv', name: 'bioRxiv 生物预印本', platform: 'bioRxiv 官方 API', website: 'https://www.biorxiv.org', method: 'biorxiv', official: 1, cadence: '每日' },
    { id: 'medrxiv', name: 'medRxiv 医学预印本', platform: 'medRxiv 官方 API', website: 'https://www.medrxiv.org', method: 'rss', feed: 'https://connect.medrxiv.org/medrxiv_xml.php?subject=all', official: 1, cadence: '每日' },
  ]},
  { board: 'board2', name: '板块二 · 顶级期刊', sources: [
    { id: 'nature', name: 'Nature 本刊', platform: 'nature.com 官方 RSS', website: 'https://www.nature.com', method: 'rss', feed: 'https://www.nature.com/nature.rss', official: 1 },
    { id: 'nature-medicine', name: 'Nature Medicine', platform: 'nature.com 官方 RSS', website: 'https://www.nature.com/nm', method: 'rss', feed: 'https://www.nature.com/nm.rss', official: 1 },
    { id: 'nature-biotech', name: 'Nature Biotechnology', platform: 'nature.com 官方 RSS', website: 'https://www.nature.com/nbt', method: 'rss', feed: 'https://www.nature.com/nbt.rss', official: 1 },
    { id: 'nature-machine-intel', name: 'Nature Machine Intelligence', platform: 'nature.com 官方 RSS', website: 'https://www.nature.com/natmachintell', method: 'rss', feed: 'https://www.nature.com/natmachintell.rss', official: 1 },
    { id: 'nature-comms', name: 'Nature Communications', platform: 'nature.com 官方 RSS', website: 'https://www.nature.com/ncomms', method: 'rss', feed: 'https://www.nature.com/ncomms.rss', official: 1 },
    { id: 'science-advances', name: 'Science Advances', platform: 'science.org 官方 RSS', website: 'https://www.science.org', method: 'rss', feed: 'https://www.science.org/action/showFeed?type=etoc&feed=rss&jc=sciadv', official: 1 },
    { id: 'science-news', name: 'Science 新闻', platform: 'science.org 官方 RSS', website: 'https://www.science.org', method: 'rss', feed: 'https://www.science.org/rss/news_current.xml', official: 1 },
    { id: 'cell', name: 'Cell 本刊', platform: 'cell.com 官方 RSS', website: 'https://www.cell.com', method: 'rss', feed: 'https://www.cell.com/cell/current.rss', official: 1 },
    { id: 'cell-neuron', name: 'Neuron', platform: 'cell.com 官方 RSS', website: 'https://www.cell.com', method: 'rss', feed: 'https://www.cell.com/neuron/current.rss', official: 1 },
    { id: 'pnas', name: 'PNAS 最新', platform: 'pnas.org 官方 RSS', website: 'https://www.pnas.org', method: 'rss', feed: 'https://www.pnas.org/action/showFeed?type=etoc&feed=rss&jc=pnas', official: 1 },
    { id: 'lancet', name: 'The Lancet', platform: 'thelancet.com 官方 RSS', website: 'https://www.thelancet.com', method: 'rss', feed: 'https://www.thelancet.com/rssfeed/lancet_current.xml', official: 1 },
    { id: 'nejm', name: 'NEJM', platform: 'nejm.org 官方 RSS', website: 'https://www.nejm.org', method: 'rss', feed: 'https://www.nejm.org/action/showFeed?jc=nejm&type=etoc&feed=rss', official: 1 },
    { id: 'jama', name: 'JAMA', platform: 'jamanetwork.com 官方 RSS', website: 'https://jamanetwork.com', method: 'rss', feed: 'https://jamanetwork.com/rss/site_3/67.xml', official: 1 },
    { id: 'bmj', name: 'The BMJ', platform: 'bmj.com 官方 RSS', website: 'https://www.bmj.com', method: 'rss', feed: 'https://www.bmj.com/rss/recent.xml', official: 1 },
    { id: 'plos-biology', name: 'PLOS Biology', platform: 'plos.org 官方 Atom', website: 'https://journals.plos.org/plosbiology', method: 'rss', feed: 'https://journals.plos.org/plosbiology/feed/atom', official: 1 },
    { id: 'elife', name: 'eLife', platform: 'elifesciences.org 官方 RSS', website: 'https://elifesciences.org', method: 'rss', feed: 'https://elifesciences.org/rss/recent.xml', official: 1 },
    { id: 'ieee-spectrum', name: 'IEEE Spectrum', platform: 'spectrum.ieee.org 官方 RSS', website: 'https://spectrum.ieee.org', method: 'rss', feed: 'https://spectrum.ieee.org/feeds/feed.rss', official: 1 },
  ]},
  { board: 'board3', name: '板块三 · 中国政策法规', sources: [
    { id: 'gnews-cn-policy', name: '政策要闻（国务院/工信部/发改委）', platform: 'Google News RSS 聚合', website: 'https://news.google.com', method: 'rss', feed: 'https://news.google.com/rss/search?q=%E5%9B%BD%E5%8A%A1%E9%99%A2%20OR%20%E5%B7%A5%E4%BF%A1%E9%83%A8%20OR%20%E5%8F%91%E6%94%B9%E5%A7%94%20%E6%94%BF%E7%AD%96&hl=zh-CN&gl=CN&ceid=CN:zh-Hans', official: 0 },
    { id: 'gnews-cn-tech-policy', name: '科技政策（科技部/网信办）', platform: 'Google News RSS 聚合', website: 'https://news.google.com', method: 'rss', feed: 'https://news.google.com/rss/search?q=%E7%A7%91%E6%8A%80%E9%83%A8%20OR%20%E7%BD%91%E4%BF%A1%E5%8A%9E%20%E6%94%BF%E7%AD%96&hl=zh-CN&gl=CN&ceid=CN:zh-Hans', official: 0 },
    { id: 'gnews-cn-finance-reg', name: '金融监管（央行/证监会）', platform: 'Google News RSS 聚合', website: 'https://news.google.com', method: 'rss', feed: 'https://news.google.com/rss/search?q=%E4%B8%AD%E5%9B%BD%E4%BA%BA%E6%B0%91%E9%93%B6%E8%A1%8C%20OR%20%E8%AF%81%E7%9B%91%E4%BC%9A%20OR%20%E9%87%91%E8%9E%8D%E7%9B%91%E7%AE%A1&hl=zh-CN&gl=CN&ceid=CN:zh-Hans', official: 0 },
    { id: 'gnews-cn-ai-reg', name: '人工智能治理与法规', platform: 'Google News RSS 聚合', website: 'https://news.google.com', method: 'rss', feed: 'https://news.google.com/rss/search?q=%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD%20%E7%9B%91%E7%AE%A1%20OR%20%E6%B3%95%E8%A7%84%20OR%20%E5%8A%9E%E6%B3%95&hl=zh-CN&gl=CN&ceid=CN:zh-Hans', official: 0 },
    { id: 'gnews-cn-nmpa', name: '药监与医疗器械（国家药监局）', platform: 'Google News RSS 聚合', website: 'https://news.google.com', method: 'rss', feed: 'https://news.google.com/rss/search?q=%E5%9B%BD%E5%AE%B6%E8%8D%AF%E7%9B%91%E5%B1%80%20OR%20NMPA%20%E5%AE%A1%E6%89%B9&hl=zh-CN&gl=CN&ceid=CN:zh-Hans', official: 0 },
  ]},
  { board: 'board4', name: '板块四 · 美国科技金融', sources: [
    { id: 'fed-press', name: '美联储新闻稿', platform: 'federalreserve.gov 官方 RSS', website: 'https://www.federalreserve.gov', method: 'rss', feed: 'https://www.federalreserve.gov/feeds/press_all.xml', official: 1 },
    { id: 'fed-monetary', name: '美联储货币政策', platform: 'federalreserve.gov 官方 RSS', website: 'https://www.federalreserve.gov', method: 'rss', feed: 'https://www.federalreserve.gov/feeds/press_monetary.xml', official: 1 },
    { id: 'fed-speeches', name: '美联储讲话', platform: 'federalreserve.gov 官方 RSS', website: 'https://www.federalreserve.gov', method: 'rss', feed: 'https://www.federalreserve.gov/feeds/speeches.xml', official: 1 },
    { id: 'sec-press', name: 'SEC 新闻稿', platform: 'sec.gov 官方 RSS', website: 'https://www.sec.gov', method: 'rss', feed: 'https://www.sec.gov/news/pressreleases.rss', official: 1 },
    { id: 'sec-speeches', name: 'SEC 讲话与声明', platform: 'sec.gov 官方 RSS', website: 'https://www.sec.gov', method: 'rss', feed: 'https://www.sec.gov/news/statements.rss', official: 1 },
    { id: 'ftc-press', name: 'FTC 新闻稿', platform: 'ftc.gov 官方 RSS', website: 'https://www.ftc.gov', method: 'rss', feed: 'https://www.ftc.gov/feeds/press-release.xml', official: 1 },
    { id: 'nist-news', name: 'NIST', platform: 'nist.gov 官方 RSS', website: 'https://www.nist.gov', method: 'rss', feed: 'https://www.nist.gov/news-events/news/rss.xml', official: 1 },
    { id: 'whitehouse-actions', name: '白宫总统令', platform: 'whitehouse.gov 官方 RSS', website: 'https://www.whitehouse.gov', method: 'rss', feed: 'https://www.whitehouse.gov/presidential-actions/feed/', official: 1 },
    { id: 'gnews-us-tech', name: '美国科技监管与反垄断', platform: 'Google News RSS 聚合', website: 'https://news.google.com', method: 'rss', feed: 'https://news.google.com/rss/search?q=US%20tech%20regulation%20OR%20antitrust%20FTC%20SEC&hl=en-US&gl=US&ceid=US:en', official: 0 },
  ]},
];
const BOARD_NAMES = Object.fromEntries(REGISTRY.map(b => [b.board, b.name]));
const AGG_BOARD = { id: 'board5', name: '板块五 · 跨板块总览' };

// 价值权重（thresholds_v0_3.yaml，合 104）+ 弃权线
const WEIGHTS = { relevance: 22, gap: 20, novelty: 14, transfer: 12, forgetting: 8, urgency: 6, evidence: 5, diversity: 17 };
const ABSTAIN_THRESHOLD = 59.6;
const INTEREST = ['cs.AI','cs.LG','cs.CL','cs.CV','stat.ML','q-bio','q-fin','eess'];
const UA = 'ADP/0.4 personal-learning (single-user cloud)';
const MAX_ITEMS_PER_FEED = 20;
const KEEP_PER_BOARD = 300;
const CANDIDATE_WINDOW_DAYS = 7;
// 免费档：每次 Worker 调用最多 ~50 个子请求（fetch + D1 调用都算）。
// 对策：D1 写入全部 batch（一次 batch = 一个子请求）；板块 feed 按天轮转抓取。
const ARXIV_CAP = 220;          // 单次入库 arXiv 上限（跨所有领域采样，控制子请求/CPU）
const ARXIV_PAGES = 2;
const FEED_ROTATE_SIZE = 12;    // 每次轮转抓取的板块 feed 数（全部约 28 个，2~3 天覆盖一轮）
const BATCH_CHUNK = 80;         // 每个 D1 batch 的语句数上限
function chunk(arr, n) { const o = []; for (let i = 0; i < arr.length; i += n) o.push(arr.slice(i, i + n)); return o; }
function dayOfYear() { const d = new Date(); return Math.floor((d - new Date(Date.UTC(d.getUTCFullYear(), 0, 0))) / 864e5); }

// ───────────────────────── 工具 ─────────────────────────
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const nowISO = () => new Date().toISOString();
const dayISO = (d = new Date()) => d.toISOString().slice(0, 10);
async function sha1(s) {
  const buf = await crypto.subtle.digest('SHA-1', new TextEncoder().encode(s));
  return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
}
function stripTags(s) { return String(s ?? '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim(); }
function decodeEntities(s) {
  return String(s ?? '')
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'").replace(/&amp;/g, '&').replace(/&#(\d+);/g, (_, n) => String.fromCharCode(+n));
}
function tag(block, name) {
  // (?:\s[^>]*)? 确保 <id> 不会前缀匹配 <identifier>（整名匹配）
  const m = block.match(new RegExp(`<${name}(?:\\s[^>]*)?>([\\s\\S]*?)</${name}>`, 'i'));
  return m ? decodeEntities(m[1]).trim() : '';
}

// ───────────────────────── Feed 解析（RSS <item> / Atom <entry>） ─────────────────────────
function parseFeed(xml) {
  const out = [];
  const blocks = xml.match(/<(item|entry)[\s>][\s\S]*?<\/(item|entry)>/gi) || [];
  for (const b of blocks) {
    let link = '';
    const hrefM = b.match(/<link[^>]*href="([^"]+)"/i);
    if (hrefM) link = hrefM[1];
    if (!link) link = tag(b, 'link');
    link = link.trim();
    const title = stripTags(tag(b, 'title'));
    if (!link || !title) continue;
    if (!/^https?:\/\//i.test(link)) continue;  // 只收 http/https，防注入
    const summary = stripTags(tag(b, 'summary') || tag(b, 'description') || tag(b, 'content'));
    let pub = tag(b, 'published') || tag(b, 'updated') || tag(b, 'pubDate') || tag(b, 'dc:date');
    let iso = null;
    if (pub) { const t = Date.parse(pub); if (!isNaN(t)) iso = new Date(t).toISOString(); }
    out.push({ link, title, summary: summary.slice(0, 800), published: iso, guid: tag(b, 'guid') || tag(b, 'id') || link });
  }
  return out.slice(0, MAX_ITEMS_PER_FEED);
}

// ───────────────────────── arXiv 全站（OAI-PMH ListRecords，所有领域） ─────────────────────────
function parseOaiArxiv(xml) {
  const out = [];
  const recs = xml.match(/<record>[\s\S]*?<\/record>/gi) || [];
  for (const r of recs) {
    if (/<header[^>]*status="deleted"/i.test(r)) continue;
    const rawId = tag(r, 'identifier') || tag(r, 'id');
    const title = stripTags(tag(r, 'title'));
    const abstract = stripTags(tag(r, 'abstract'));
    if (!rawId || !title) continue;
    const cats = (tag(r, 'categories') || '').split(/\s+/).filter(Boolean);
    const created = tag(r, 'created');
    const authors = (r.match(/<keyname>([\s\S]*?)<\/keyname>/gi) || [])
      .map(a => stripTags(a)).slice(0, 6).join(', ');
    const arxivId = rawId.replace(/^oai:arXiv.org:/i, '').trim();
    out.push({
      id: 'arxiv:' + arxivId,
      url: 'https://arxiv.org/abs/' + arxivId,
      title, summary: abstract.slice(0, 1200),
      categories: cats.join(','), authors,
      published: created ? new Date(created + 'T00:00:00Z').toISOString() : null,
    });
  }
  const tokM = xml.match(/<resumptionToken[^>]*>([^<]+)<\/resumptionToken>/i);
  return { items: out, token: tokM ? tokM[1].trim() : null };
}

async function fetchArxivAll(fromDay) {
  const base = 'https://export.arxiv.org/oai2';
  let url = `${base}?verb=ListRecords&metadataPrefix=arXiv&from=${fromDay}`;
  const items = [];
  for (let page = 0; page < ARXIV_PAGES; page++) {   // 页封顶，控制 CPU/子请求
    const resp = await fetch(url, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(20000) });
    if (resp.status === 503) { await new Promise(r => setTimeout(r, 3000)); continue; }  // OAI 忙，退避一次
    if (!resp.ok) break;
    const xml = await resp.text();
    const { items: got, token } = parseOaiArxiv(xml);
    items.push(...got);
    if (!token || items.length >= ARXIV_CAP) break;
    url = `${base}?verb=ListRecords&resumptionToken=${encodeURIComponent(token)}`;
  }
  return items;
}

async function fetchBiorxiv(fromDay, toDay) {
  const url = `https://api.biorxiv.org/details/biorxiv/${fromDay}/${toDay}/0`;
  const resp = await fetch(url, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(20000) });
  if (!resp.ok) throw new Error('http ' + resp.status);
  const data = await resp.json();
  return (data.collection || []).slice(0, 60).map(p => ({
    id: 'biorxiv:' + p.doi,
    url: 'https://www.biorxiv.org/content/' + p.doi,
    title: stripTags(p.title), summary: stripTags(p.abstract || '').slice(0, 1200),
    categories: p.category || '', authors: (p.authors || '').slice(0, 200),
    published: p.date ? new Date(p.date + 'T00:00:00Z').toISOString() : null,
  }));
}

// ───────────────────────── 入库（全部走 batch，控制子请求数） ─────────────────────────
function itemStmt(env, { id, board, source, kind, title, url, summary, categories, authors, published }) {
  const now = nowISO();
  return env.DB.prepare(
    `INSERT INTO cn_items (id, board_id, source_id, kind, title, url, summary, categories, authors, published_at, fetched_at, first_seen_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET fetched_at=excluded.fetched_at`
  ).bind(id, board, source, kind, String(title).slice(0, 300), url, (summary || '').slice(0, 1200),
         categories || '', authors || '', published, now, now);
}
async function batchWrite(env, stmts) {
  for (const c of chunk(stmts, BATCH_CHUNK)) if (c.length) await env.DB.batch(c);
}

async function seedSources(env) {
  const stmts = [];
  for (const b of REGISTRY) for (const s of b.sources) {
    stmts.push(env.DB.prepare(
      `INSERT INTO cn_sources (id, board_id, name, platform, website, method, feed_url, official, cadence)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(id) DO UPDATE SET name=excluded.name, platform=excluded.platform, website=excluded.website, method=excluded.method, feed_url=excluded.feed_url, official=excluded.official`
    ).bind(s.id, b.board, s.name, s.platform || '', s.website || '', s.method, s.feed || null, s.official || 0, s.cadence || '每日'));
  }
  if (stmts.length) await env.DB.batch(stmts);
}

function healthStmt(env, sourceId, ok, prevFails) {
  const fails = ok ? 0 : ((prevFails || 0) + 1);
  const health = ok ? 'active' : (fails >= 3 ? 'disabled_auto' : 'degraded');
  return env.DB.prepare('UPDATE cn_sources SET health=?, consecutive_failures=?, last_fetch=? WHERE id=?')
    .bind(health, fails, nowISO(), sourceId);
}

async function ingestAll(env, counts) {
  const today = new Date();
  const fromDay = dayISO(new Date(today.getTime() - 2 * 864e5)), toDay = dayISO(today);
  const itemStmts = [];
  const healthStmts = [];

  // 读取所有 feed 源的当前健康（一次查询）
  const { results: srcHealth } = await env.DB.prepare('SELECT id, health, consecutive_failures FROM cn_sources').all();
  const hmap = Object.fromEntries((srcHealth || []).map(r => [r.id, r]));

  // arXiv 全站（OAI-PMH，所有领域）
  try {
    const papers = (await fetchArxivAll(fromDay)).slice(0, ARXIV_CAP);
    for (const p of papers) itemStmts.push(itemStmt(env, { ...p, board: 'board1', source: 'arxiv-all', kind: 'paper' }));
    counts.arxiv = papers.length;
    healthStmts.push(healthStmt(env, 'arxiv-all', papers.length > 0, hmap['arxiv-all']?.consecutive_failures));
  } catch (e) { counts.degraded.push('arxiv:' + e.name); healthStmts.push(healthStmt(env, 'arxiv-all', false, hmap['arxiv-all']?.consecutive_failures)); }

  // bioRxiv（正常入库）
  try {
    const bio = await fetchBiorxiv(fromDay, toDay);
    for (const p of bio) itemStmts.push(itemStmt(env, { ...p, board: 'board1', source: 'biorxiv', kind: 'paper' }));
    counts.biorxiv = bio.length;
    healthStmts.push(healthStmt(env, 'biorxiv', bio.length > 0, hmap['biorxiv']?.consecutive_failures));
  } catch (e) { counts.degraded.push('biorxiv:' + e.name); healthStmts.push(healthStmt(env, 'biorxiv', false, hmap['biorxiv']?.consecutive_failures)); }

  // 板块 RSS：按天轮转抓一批（免费档子请求预算），跳过已自动停用的源
  const feeds = [];
  for (const b of REGISTRY) for (const s of b.sources) if (s.method === 'rss') feeds.push({ b: b.board, s });
  const eligible = feeds.filter(f => (hmap[f.s.id]?.health) !== 'disabled_auto');
  const start = (dayOfYear() * FEED_ROTATE_SIZE) % Math.max(1, eligible.length);
  const rotated = eligible.length <= FEED_ROTATE_SIZE ? eligible
    : Array.from({ length: FEED_ROTATE_SIZE }, (_, i) => eligible[(start + i) % eligible.length]);
  const settled = await Promise.allSettled(rotated.map(f =>
    fetch(f.s.feed, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(15000) })
      .then(r => r.ok ? r.text() : Promise.reject(new Error('http ' + r.status)))
      .then(xml => ({ f, items: parseFeed(xml) }))));
  let feedNew = 0;
  for (let i = 0; i < rotated.length; i++) {
    const res = settled[i], f = rotated[i];
    if (res.status === 'fulfilled') {
      for (const it of res.value.items) {
        itemStmts.push(itemStmt(env, { id: 'feed:' + await sha1(f.s.id + '|' + it.guid), board: f.b, source: f.s.id,
          kind: 'feed', title: it.title, url: it.link, summary: it.summary, categories: '', authors: '', published: it.published }));
        feedNew++;
      }
      healthStmts.push(healthStmt(env, f.s.id, true, hmap[f.s.id]?.consecutive_failures));
    } else {
      counts.degraded.push('feed:' + f.s.id);
      healthStmts.push(healthStmt(env, f.s.id, false, hmap[f.s.id]?.consecutive_failures));
    }
  }
  counts.feeds = feedNew;
  counts.feed_fetched = rotated.length;
  counts.feed_disabled = feeds.length - eligible.length;

  // 批量写入 + 健康 + 保留上限（每个 batch 一个子请求）
  await batchWrite(env, itemStmts);
  await batchWrite(env, healthStmts);
  await env.DB.prepare(
    `DELETE FROM cn_items WHERE id IN (
       SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY board_id ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC) rn FROM cn_items) WHERE rn > ?)`
  ).bind(KEEP_PER_BOARD).run();
}

// ───────────────────────── 选择打分（8 特征，跨全部板块） ─────────────────────────
function scoreItem(item, ctx) {
  const cats = (item.categories || '').split(',').filter(Boolean);
  const ageDays = item.published_at ? Math.max(0, (ctx.now - Date.parse(item.published_at)) / 864e5) : 3;
  const recency = Math.max(0, 1 - ageDays / CANDIDATE_WINDOW_DAYS);         // 越新越高
  const interestHit = cats.some(c => INTEREST.some(i => c.startsWith(i))) ? 1 : (item.kind === 'paper' ? 0.5 : 0.4);
  const summaryLen = (item.summary || '').length;
  const substance = Math.min(1, summaryLen / 600);                          // 摘要充分度
  const boardShare = ctx.recentBoards[item.board_id] || 0;                  // 近期该板占比
  const diversity = 1 - Math.min(1, boardShare);                            // 越少见越高
  const novelty = ctx.seenSources.has(item.source_id) ? 0.5 : 1;
  const f = {
    relevance: interestHit,
    gap: 0.5 + 0.5 * substance,
    novelty,
    transfer: cats.length >= 2 ? 1 : (item.kind === 'feed' ? 0.6 : 0.5),
    forgetting: 0.5,
    urgency: recency,
    evidence: item.url.startsWith('https://') ? (item.official ? 1 : 0.7) : 0.3,
    diversity,
  };
  let score = 0; const contrib = {};
  for (const k in WEIGHTS) { const c = WEIGHTS[k] * f[k]; contrib[k] = Math.round(c * 10) / 10; score += c; }
  return { score: Math.round(score * 10) / 10, contrib, features: f };
}

async function selectDaily(env, asOfDate, counts) {
  const cutoff = new Date(Date.now() - CANDIDATE_WINDOW_DAYS * 864e5).toISOString();
  const { results: items } = await env.DB.prepare(
    `SELECT i.*, s.official FROM cn_items i LEFT JOIN cn_sources s ON s.id = i.source_id
     WHERE COALESCE(i.published_at, i.fetched_at) >= ? ORDER BY COALESCE(i.published_at, i.fetched_at) DESC LIMIT 1200`
  ).bind(cutoff).all();
  counts.candidates = (items || []).length;
  // 近期板块分布（多样性上下文）
  const { results: recentSel } = await env.DB.prepare(
    'SELECT board_id FROM cn_selections WHERE abstain=0 ORDER BY as_of_date DESC LIMIT 14').all();
  const recentBoards = {}; for (const r of (recentSel || [])) recentBoards[r.board_id] = (recentBoards[r.board_id] || 0) + 1 / 14;
  const ctx = { now: Date.now(), recentBoards, seenSources: new Set((recentSel || []).map(r => r.board_id)) };

  let best = null;
  for (const it of (items || [])) {
    const sc = scoreItem(it, ctx);
    if (!best || sc.score > best.sc.score) best = { it, sc };
  }
  const runAt = nowISO();
  if (!best || best.sc.score < ABSTAIN_THRESHOLD) {
    await env.DB.prepare(
      `INSERT INTO cn_selections (as_of_date, item_id, score, why, abstain, abstain_reason, contributions_json, board_id, run_at)
       VALUES (?, ?, ?, ?, 1, ?, ?, ?, ?) ON CONFLICT(as_of_date) DO UPDATE SET
         item_id=excluded.item_id, score=excluded.score, why=excluded.why, abstain=1, abstain_reason=excluded.abstain_reason, contributions_json=excluded.contributions_json, board_id=excluded.board_id, run_at=excluded.run_at`
    ).bind(asOfDate, best ? best.it.id : null, best ? best.sc.score : 0,
           '', `今日无条目达到弃权线 ${ABSTAIN_THRESHOLD}（最高分 ${best ? best.sc.score : 0}）`,
           JSON.stringify(best ? best.sc.contrib : {}), best ? best.it.board_id : null, runAt).run();
    counts.selected = 'abstain';
    return null;
  }
  const it = best.it, sc = best.sc;
  const top = Object.entries(sc.contrib).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k]) => k);
  const why = `跨 ${counts.candidates} 条候选选中（${BOARD_NAMES[it.board_id] || it.board_id}）；主要因为 ${top.join('、')}（总分 ${sc.score}/104）`;
  await env.DB.prepare(
    `INSERT INTO cn_selections (as_of_date, item_id, score, why, abstain, abstain_reason, contributions_json, board_id, run_at)
     VALUES (?, ?, ?, ?, 0, NULL, ?, ?, ?) ON CONFLICT(as_of_date) DO UPDATE SET
       item_id=excluded.item_id, score=excluded.score, why=excluded.why, abstain=0, abstain_reason=NULL, contributions_json=excluded.contributions_json, board_id=excluded.board_id, run_at=excluded.run_at`
  ).bind(asOfDate, it.id, sc.score, why, JSON.stringify(sc.contrib), it.board_id, runAt).run();
  counts.selected = it.id;
  return { it, sc, why };
}

// ───────────────────────── 讲义（确定性八段模板） ─────────────────────────
const SECTION_TITLES = ['人话版', '领域脉络', '机制拆解', '证据与数字', '反例与边界', '跨领域连接与意外收获', '可复用方法', '术语表'];
const LESSON_TEMPLATE_VER = 'cloud-lesson-v1';
function splitSentences(text) {
  return (text || '').split(/(?<=[.。!?！？])\s+/).map(s => s.trim()).filter(s => s.length > 12);
}
function buildLesson(it) {
  const sents = splitSentences(it.summary);
  const cats = (it.categories || '').split(',').filter(Boolean);
  const numeric = sents.filter(s => /\d/.test(s));
  const limits = sents.filter(s => /(however|but|limit|only|fail|不足|局限|但|然而|仅)/i.test(s));
  const sec = (title, arr, fallback) => ({ title, sentences: (arr.length ? arr : [fallback]).slice(0, 4).map(text => ({ text })) });
  return [
    sec('人话版', sents.slice(0, 2), `本文标题：${it.title}。摘要过短，请点原文精读。`),
    sec('领域脉络', cats.length ? [`本文类目：${cats.slice(0, 5).join('、')}，属于其所在研究脉络的最新进展。`] : sents.slice(2, 3), `来源板块：${BOARD_NAMES[it.board_id] || it.board_id}。`),
    sec('机制拆解', sents.slice(2, 5), '摘要未展开方法细节——精读时重点看方法/模型部分。'),
    sec('证据与数字', numeric.slice(0, 3), '摘要未给出量化结果——留意原文的实验与数据。'),
    sec('反例与边界', limits, '摘要未声明局限与反例——这是需要警惕的信号，精读时先问边界。'),
    sec('跨领域连接与意外收获', cats.length >= 2 ? [`横跨 ${cats.length} 个类目（${cats.slice(0, 4).join('、')}），关注其在你兴趣板块间的迁移面。`] : [], '思考本文机制能否迁移到你正在跟进的问题。'),
    sec('可复用方法', [], '把本文机制与你手头项目对照，找一个两周内能验证的最小实验。'),
    sec('术语表', [], '精读时把不熟的术语记入此处，作为下次回忆的锚点。'),
  ];
}

async function makeLesson(env, asOfDate, it) {
  const sections = buildLesson(it);
  const id = 'lesson-' + asOfDate + '-' + (await sha1(it.id)).slice(0, 8);
  await env.DB.prepare(
    `INSERT INTO cn_lessons (id, as_of_date, item_id, doc_title, url, sections_json, generator, template_ver, created_at)
     VALUES (?, ?, ?, ?, ?, ?, 'deterministic', ?, ?) ON CONFLICT(id) DO UPDATE SET sections_json=excluded.sections_json`
  ).bind(id, asOfDate, it.id, it.title, it.url, JSON.stringify(sections), LESSON_TEMPLATE_VER, nowISO()).run();
  return id;
}

// ───────────────────────── FSRS-6（默认参数，紧凑实现） ─────────────────────────
const W = [0.2172,1.1771,3.2602,16.1507,7.0114,0.57,2.0966,0.0069,1.5261,0.112,1.0178,1.849,0.1133,0.3127,2.2934,0.2191,3.0004,0.7536,0.3332,0.1437,0.2];
const DECAY = -W[20], FACTOR = Math.pow(0.9, 1 / DECAY) - 1, RETENTION = 0.9;
const clampD = d => Math.min(10, Math.max(1, d));
const clampS = s => Math.max(0.01, s);
function nextInterval(stability) {
  const days = (stability / FACTOR) * (Math.pow(RETENTION, 1 / DECAY) - 1);
  return Math.min(3650, Math.max(1, Math.round(days)));
}
function initCard(grade) {
  const s = clampS(W[grade - 1]);
  const d = clampD(W[4] - Math.exp(W[5] * (grade - 1)) + 1);
  return { stability: s, difficulty: d, reps: 1, lapses: grade === 1 ? 1 : 0, state: grade === 1 ? 1 : 2 };
}
function reviewCard(card, grade, elapsedDays) {
  const R = Math.pow(1 + FACTOR * Math.max(0, elapsedDays) / card.stability, DECAY);
  let d = clampD(card.difficulty - W[6] * (grade - 3));
  d = clampD(W[7] * (W[4] - Math.exp(W[5] * 0) + 1) + (1 - W[7]) * d);
  let s;
  if (grade === 1) {
    s = clampS(W[11] * Math.pow(d, -W[12]) * (Math.pow(card.stability + 1, W[13]) - 1) * Math.exp(W[14] * (1 - R)));
    return { stability: s, difficulty: d, reps: card.reps + 1, lapses: card.lapses + 1, state: 3 };
  }
  const hardPenalty = grade === 2 ? W[15] : 1;
  const easyBonus = grade === 4 ? W[16] : 1;
  s = clampS(card.stability * (1 + Math.exp(W[8]) * (11 - d) * Math.pow(card.stability, -W[9]) * (Math.exp(W[10] * (1 - R)) - 1) * hardPenalty * easyBonus));
  return { stability: s, difficulty: d, reps: card.reps + 1, lapses: card.lapses, state: 2 };
}
function evidenceState(card) {
  if (!card || card.reps === 0) return '未学';
  if (card.state === 3 || card.lapses > 0 && card.reps <= card.lapses) return '重学中';
  if (card.stability >= 21) return '已掌握';
  return '学习中';
}
async function scheduleNewCard(env, itemId) {
  const existing = await env.DB.prepare('SELECT item_id FROM cn_reviews WHERE item_id=?').bind(itemId).first();
  if (existing) return;
  const due = new Date(Date.now() + 864e5).toISOString();
  await env.DB.prepare(
    `INSERT INTO cn_reviews (item_id, due_at, stability, difficulty, reps, lapses, state, evidence_state)
     VALUES (?, ?, NULL, NULL, 0, 0, 0, '未学') ON CONFLICT(item_id) DO NOTHING`
  ).bind(itemId, due).run();
}
async function gradeRecall(env, itemId, grade) {
  const today = dayISO();
  const dedup = `${itemId}:${today}`;
  const dup = await env.DB.prepare('SELECT id FROM cn_events WHERE dedup_key=?').bind(dedup).first();
  if (dup) return { duplicate: true, id: dup.id };
  const now = nowISO();
  const row = await env.DB.prepare('SELECT * FROM cn_reviews WHERE item_id=?').bind(itemId).first();
  let card;
  if (!row || row.reps === 0 || row.stability == null) card = initCard(grade);
  else {
    const elapsed = row.last_review ? (Date.now() - Date.parse(row.last_review)) / 864e5 : 1;
    card = reviewCard({ stability: row.stability, difficulty: row.difficulty, reps: row.reps, lapses: row.lapses, state: row.state }, grade, elapsed);
  }
  const dueAt = new Date(Date.now() + nextInterval(card.stability) * 864e5).toISOString();
  const evi = evidenceState(card);
  await env.DB.prepare(
    `INSERT INTO cn_reviews (item_id, due_at, stability, difficulty, reps, lapses, state, last_review, last_grade, evidence_state)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(item_id) DO UPDATE SET
       due_at=excluded.due_at, stability=excluded.stability, difficulty=excluded.difficulty, reps=excluded.reps,
       lapses=excluded.lapses, state=excluded.state, last_review=excluded.last_review, last_grade=excluded.last_grade, evidence_state=excluded.evidence_state`
  ).bind(itemId, dueAt, card.stability, card.difficulty, card.reps, card.lapses, card.state, now, grade, evi).run();
  const ins = await env.DB.prepare('INSERT INTO cn_events (item_id, kind, grade, at, dedup_key) VALUES (?, ?, ?, ?, ?)')
    .bind(itemId, 'grade', grade, now, dedup).run();
  return { duplicate: false, id: ins.meta.last_row_id, due_at: dueAt.slice(0, 10), evidence_state: evi, interval: nextInterval(card.stability) };
}

// ───────────────────────── 每日流水线 ─────────────────────────
async function runDaily(env, trigger) {
  const asOfDate = dayISO();
  const runId = new Date().toISOString().replace(/[:.]/g, '').slice(0, 15) + '-' + trigger;
  const counts = { degraded: [] };
  let result = '正常', note = null;
  try {
    await seedSources(env);
    const done = await env.DB.prepare("SELECT run_id FROM cn_run_log WHERE as_of_date=? AND result IN ('正常','降级','弃权')").bind(asOfDate).first();
    if (done) { result = '未运行'; note = `当日已成功运行 ${done.run_id}，幂等跳过`; }
    else {
      await ingestAll(env, counts);
      const pick = await selectDaily(env, asOfDate, counts);
      if (pick) { await makeLesson(env, asOfDate, pick.it); await scheduleNewCard(env, pick.it.id); }
      else result = '弃权';
      if (counts.degraded.length) result = result === '正常' ? '降级' : result;
    }
  } catch (e) { result = '失败'; note = e.name + ': ' + (e.message || '').slice(0, 200); }
  await env.DB.prepare(
    `INSERT INTO cn_run_log (run_id, as_of_date, result, counts_json, note, at) VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT(run_id) DO NOTHING`
  ).bind(runId, asOfDate, result, JSON.stringify(counts), note, nowISO()).run();
  return { runId, result, counts, note };
}

// ───────────────────────── UI ─────────────────────────
const CSS = `
:root{--bg:#f3eee1;--fg:#4a3d28;--card:#fdfaf2;--bd:#d8cfba;--ac:#8a5c16;--mt:#8b7a5c;--ink:#2f2618}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.75 -apple-system,"PingFang SC","Noto Sans SC",sans-serif}
header{position:sticky;top:0;background:var(--card);border-bottom:1px solid var(--bd);padding:12px 16px;display:flex;gap:14px;align-items:baseline;flex-wrap:wrap;z-index:9}
header b{color:var(--ink);font-size:17px}
nav a{color:var(--ac);text-decoration:none;margin-right:12px;font-size:14.5px}
nav a.active{font-weight:700;border-bottom:2px solid var(--ac)}
main{max-width:760px;margin:0 auto;padding:16px 16px 48px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:16px 18px;margin:14px 0}
h1{font-size:21px;color:var(--ink);margin:.2em 0}h2{font-size:16.5px;color:var(--ink)}h3{font-size:14.5px;color:var(--ac);margin:14px 0 4px}
.mt{color:var(--mt);font-size:13px}
.badge{display:inline-block;border:1px solid var(--bd);border-radius:999px;padding:1px 9px;font-size:12px;margin-left:6px}
.badge.ok{color:#2f7a34;border-color:#b6d8b8}.badge.info{color:#8a5c16}
button{min-height:44px;padding:9px 16px;border-radius:10px;border:1px solid var(--bd);background:var(--card);font-size:15px;color:var(--fg);cursor:pointer}
button.picked{background:var(--ac);color:#fff;border-color:var(--ac)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{padding:6px 8px;border-bottom:1px solid #e7dfcc;text-align:left;vertical-align:top}
a{color:var(--ac)}
.gradeRow{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
footer{max-width:760px;margin:0 auto;padding:12px 16px 40px;color:var(--mt);font-size:12px}
`;
const PAGE = (page, body) => `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>ADP 前沿学习</title>
<style>${CSS}</style></head><body>
<header><b>ADP 前沿学习</b><nav>
${[['/','今天'],['/queue','复习队列'],['/radar','前沿雷达'],['/system','系统与来源']].map(([h,t]) =>
  `<a href="${h}"${h===page?' class="active"':''}>${t}</a>`).join('')}
</nav></header><main>${body}</main>
<footer>整套系统运行在 Cloudflare（抓取·选择·讲义·回忆·排程都在云端）；每日 cron 自动更新。</footer>
</body></html>`;

async function todayPage(env) {
  const sel = await env.DB.prepare('SELECT * FROM cn_selections ORDER BY as_of_date DESC LIMIT 1').first();
  if (!sel) return PAGE('/', `<div class="card"><h1>还没有内容</h1><p class="mt">每日流水线尚未运行。可在 <a href="/system">系统页</a> 手动触发一次。</p></div>`);
  if (sel.abstain) return PAGE('/', `<div class="card"><h1>今日弃权</h1><p>${esc(sel.abstain_reason)}</p><p class="mt">决策日期 ${esc(sel.as_of_date)}——宁缺毋滥，明天再来。</p></div>`);
  const lesson = await env.DB.prepare('SELECT * FROM cn_lessons WHERE item_id=? ORDER BY created_at DESC LIMIT 1').bind(sel.item_id).first();
  const item = await env.DB.prepare('SELECT * FROM cn_items WHERE id=?').bind(sel.item_id).first();
  const review = await env.DB.prepare('SELECT * FROM cn_reviews WHERE item_id=?').bind(sel.item_id).first();
  let body = `<div class="card"><h2>为什么今天选它</h2><p>${esc(sel.why)}</p>
    <p class="mt">决策日期 ${esc(sel.as_of_date)} · ${esc(BOARD_NAMES[sel.board_id] || sel.board_id || '')}${review ? ' · 证据态 ' + esc(review.evidence_state) : ''}</p></div>`;
  if (item) {
    body += `<div class="card"><h1>${esc(item.title)}</h1>
      <p class="mt">${esc(item.authors || '')}${item.categories ? ' · ' + esc(item.categories) : ''} · <a href="${esc(item.url)}" rel="noopener">原文</a></p>`;
    if (lesson) for (const [i, s] of JSON.parse(lesson.sections_json).entries())
      body += `<h3>${i + 1}. ${esc(s.title)}</h3>${(s.sentences || []).map(x => `<p>${esc(x.text)}</p>`).join('')}`;
    body += `</div><div class="card"><h2>主动回忆</h2>
      <p class="mt">先合上讲义复述，再自评。评分即时进 FSRS 排程（云端即真相）。</p>
      <div class="gradeRow">${[[1,'忘了'],[2,'困难'],[3,'良好'],[4,'轻松']].map(([g,l]) =>
        `<button onclick="grade(${g},this)">${l}</button>`).join('')}</div>
      <p id="r" class="mt"></p>
      <script>async function grade(g,btn){
        const res=await fetch('/api/grade/'+encodeURIComponent(${JSON.stringify(sel.item_id)})+'/'+g,{method:'POST'});
        const j=await res.json();
        document.querySelectorAll('.gradeRow button').forEach(b=>b.classList.remove('picked'));btn.classList.add('picked');
        document.getElementById('r').textContent=j.duplicate?('今天已评过（事件 #'+j.id+'），未重复计。'):('已记录 → 下次复习 '+j.due_at+'（间隔 '+j.interval+' 天，证据态：'+j.evidence_state+'）');
      }</script></div>`;
  }
  return PAGE('/', body);
}

async function queuePage(env) {
  const { results } = await env.DB.prepare(
    `SELECT r.*, i.title, i.url FROM cn_reviews r LEFT JOIN cn_items i ON i.id = r.item_id ORDER BY r.due_at ASC LIMIT 100`).all();
  const rows = (results || []).map(r => `<tr><td>${esc((r.title || r.item_id).slice(0, 70))}</td>
    <td><span class="badge">${esc(r.evidence_state || '—')}</span></td>
    <td class="mt">${esc((r.due_at || '').slice(0, 10))}</td></tr>`).join('');
  return PAGE('/queue', `<div class="card"><h1>复习队列</h1>
    <table><tr><th>条目</th><th>证据态</th><th>下次复习</th></tr>${rows || '<tr><td colspan="3">队列为空——先在今天页学一篇并评分。</td></tr>'}</table></div>`);
}

async function radarPage(env) {
  const { results: srcs } = await env.DB.prepare('SELECT * FROM cn_sources ORDER BY board_id, id').all();
  const { results: counts } = await env.DB.prepare('SELECT board_id, COUNT(*) n FROM cn_items GROUP BY board_id').all();
  const cmap = Object.fromEntries((counts || []).map(c => [c.board_id, c.n]));
  const boards = [...REGISTRY.map(b => ({ id: b.board, name: b.name })), AGG_BOARD];
  let body = `<div class="card"><h1>前沿雷达</h1><p class="mt">全部板块的数据源都进入每日精选；下面是每个板块的信息源与状态。</p>
    <p class="mt">${boards.map(b => `<a href="#${b.id}">${esc(b.name)}</a>`).join(' · ')}</p></div>`;
  for (const b of boards) {
    const bs = (srcs || []).filter(s => s.board_id === b.id);
    body += `<div class="card" id="${b.id}"><h2>${esc(b.name)}<span class="badge ok">${cmap[b.id] || 0} 条</span></h2>`;
    if (bs.length) {
      body += `<h3>数据源（信息源 / 平台 / 网站）</h3><table><tr><th>来源</th><th>平台</th><th>健康</th></tr>`;
      body += bs.map(s => `<tr><td>${esc(s.name)}<div class="mt"><a href="${esc(s.website)}" rel="noopener">${esc(s.website)}</a></div></td>
        <td class="mt">${esc(s.platform)}${s.official ? '<span class="badge ok">官方</span>' : '<span class="badge">聚合</span>'}</td>
        <td>${s.health === 'active' ? '<span class="badge ok">正常</span>' : '<span class="badge info">' + esc(s.health) + '</span>'}</td></tr>`).join('');
      body += `</table>`;
    } else if (b.id === 'board5') body += `<p class="mt">聚合各板块，无独立来源。</p>`;
    const { results: items } = await env.DB.prepare(
      b.id === 'board5'
        ? `SELECT title, url, board_id FROM cn_items ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT 8`
        : `SELECT title, url, board_id FROM cn_items WHERE board_id=? ORDER BY COALESCE(published_at, fetched_at) DESC LIMIT 6`
    ).bind(...(b.id === 'board5' ? [] : [b.id])).all();
    if ((items || []).length) body += `<h3>最新条目</h3><ul class="mt">${items.map(it =>
      `<li><a href="${esc(it.url)}" rel="noopener">${esc(it.title.slice(0, 90))}</a></li>`).join('')}</ul>`;
    body += `</div>`;
  }
  return PAGE('/radar', body);
}

async function systemPage(env) {
  const { results: runs } = await env.DB.prepare('SELECT * FROM cn_run_log ORDER BY at DESC LIMIT 14').all();
  const rows = (runs || []).map(r => {
    const c = JSON.parse(r.counts_json || '{}');
    return `<tr><td class="mt">${esc(r.as_of_date)}</td><td><span class="badge">${esc(r.result)}</span></td>
      <td class="mt">arXiv ${c.arxiv || 0} · bio ${c.biorxiv || 0} · 板块流 ${c.feeds || 0} · 候选 ${c.candidates || 0}</td>
      <td class="mt">${esc(r.note || '')}</td></tr>`;
  }).join('');
  const total = await env.DB.prepare('SELECT COUNT(*) n FROM cn_items').first();
  return PAGE('/system', `<div class="card"><h1>系统与来源</h1>
    <p class="mt">整套系统跑在 Cloudflare（Workers + D1 + 每日 cron），不依赖任何本机。当前候选库 ${total ? total.n : 0} 条。</p>
    <table><tr><th>日期</th><th>结果</th><th>抓取/候选</th><th>说明</th></tr>${rows || '<tr><td colspan=4>尚无运行</td></tr>'}</table>
    <p style="margin-top:14px"><button onclick="run(this)">立即运行一次每日流水线</button> <span id="rr" class="mt"></span></p>
    <script>async function run(b){b.disabled=true;document.getElementById('rr').textContent='运行中…（抓取全网可能需十几秒）';
      const res=await fetch('/api/run',{method:'POST'});const j=await res.json();
      document.getElementById('rr').textContent='结果：'+j.result+'（'+JSON.stringify(j.counts)+'）';setTimeout(()=>location.reload(),1200);}</script></div>`);
}

// ───────────────────────── 入口 ─────────────────────────
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    try {
      if (request.method === 'POST' && p.startsWith('/api/grade/')) {
        const [, , , idEnc, gradeRaw] = p.split('/');
        const grade = parseInt(gradeRaw, 10);
        if (!idEnc || !(grade >= 1 && grade <= 4)) return Response.json({ error: 'bad request' }, { status: 422 });
        return Response.json(await gradeRecall(env, decodeURIComponent(idEnc), grade));
      }
      if (request.method === 'POST' && p === '/api/run') {
        return Response.json(await runDaily(env, 'manual'));
      }
      const html = p === '/queue' ? await queuePage(env)
        : p === '/radar' ? await radarPage(env)
        : p === '/system' ? await systemPage(env)
        : await todayPage(env);
      return new Response(html, { headers: { 'content-type': 'text/html; charset=utf-8' } });
    } catch (e) {
      return new Response('error: ' + e.message, { status: 500 });
    }
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runDaily(env, 'cron'));
  },
};
