/**
 * ADP 云端原生 Worker（Owner 2026-07-15 指令：网页即主体，整套系统跑在 Cloudflare，
 * 不再依赖 Mac）。一个 Worker + 一个 D1 完成五环节：抓取 → 选择 → 讲义 → 主动回忆 → FSRS 排程。
 * cron 每日跑流水线；页面直接读写 D1；主动回忆评分即时进 FSRS（无回传队列，云端即真相）。
 *
 * Stage 1：数据基座 + 流水线 + today 页。Stage 2：六主题全 UI。Stage 3：切 adp.linzezhang.com。
 */

// Build identity (ADP-S1-P01-T010): read-only /build.json + footer build id. No secret.
// build_id/source_sha256 are a self-excluding hash: reset both values back to their
// zero-placeholders ('0'*12 and '0'*64) and sha256 the file to reproduce source_sha256.
const BUILD = { build_id: 'd1dfcb3b7447', source_sha256: 'd1dfcb3b744711d4716ca1a8c6b2b856f9fa83f134eb1e05fd5d7e9fb181ee3a', schema_version: 'cn_v0_3', built_at: '2026-07-17' };

// ── S3-P03-T040 Board 3 官方视图 A0 canary 切换（Owner S3 Exit 已批准 A0 晋级）──
// 默认关 = 部署即基线（生产 Board 3 与六主题不变）。开=Board 3 只把 A0 官方原文作默认证据、媒体降为 discovery。
// 回滚 = 置 false 一次部署。非破坏性 canary 端点 /api/a0-canary 实抓 gov.cn 政策验证官方证据率，不写生产。
const BOARD3_A0_ONLY = false;
const A0_OFFICIAL_SOURCE_IDS = new Set(['gov-cn-policy', 'gov-cn-fagui', 'stats-gov', 'ndrc-gov', 'cac-gov', 'nda-gov']);
// Board 3 A0 准入：源为央级 .gov.cn 官方 或 A0 白名单 source_id 才作官方证据；否则（媒体）降为 discovery（不作证据）。
function a0Board3Eligible(it) {
  if (it.board_id !== 'board3') return true;                 // 只门控 Board 3
  if (A0_OFFICIAL_SOURCE_IDS.has(it.source_id)) return true;
  const w = (it.website || it.url || '');
  try { return new URL(/^https?:/.test(w) ? w : 'https://' + w).hostname.endsWith('.gov.cn'); } catch (e) { return false; }
}

// ── S2-P01-T022 不可变原始证据 R2 双写（SHADOW；feature flag 默认关=部署即基线；DIR-007 免费档硬预算内）──
const RAW_DUALWRITE = true;  // S2-P01-T023 SHADOW 开启：cron/run 抓取后旁路双写 R2（预算硬停内） // 默认关；开=抓取成功后旁路把原始字节写 R2（不改发布主链）
// DIR-007 R2 免费档硬顶：Storage 10GB/月、Class A(写/list)1e6/月、Class B(读/head)1e7/月；写前预算硬停（guard 0.9）。
const R2_BUDGET = { storageBytes: 10 * 1024 * 1024 * 1024, classAPerMonth: 1000000, classBPerMonth: 10000000, guardFrac: 0.9 };
async function sha256Hex(bytes) { const d = await crypto.subtle.digest('SHA-256', bytes); return Array.from(new Uint8Array(d)).map(b => b.toString(16).padStart(2, '0')).join(''); }
function rawExt(mime) { return ({ 'text/html': '.html', 'application/pdf': '.pdf', 'application/xml': '.xml', 'text/xml': '.xml', 'application/json': '.json', 'text/plain': '.txt' })[mime] || ''; }
function sniffMime(bytes) { const h = new TextDecoder('ascii').decode(bytes.slice(0, 16)).replace(/^\s+/, ''); if (h.slice(0, 5).toLowerCase() === '%pdf-') return 'application/pdf'; if (h[0] === '<') return 'text/html'; if (h[0] === '{' || h[0] === '[') return 'application/json'; return 'application/octet-stream'; }
function rawKey(sourceId, sha, mime) { if (!/^[a-z0-9][a-z0-9_-]*$/.test(sourceId || '')) throw new Error('bad source_id'); const k = `raw/${sourceId}/v1/${sha.slice(0, 2)}/${sha.slice(2, 4)}/${sha}${rawExt(mime)}`; if (/token|apikey|password|secret|[?&](q|key|token)=|@|%40/i.test(k)) throw new Error('key pii'); return k; }
function r2Month() { const d = new Date(); return `${d.getUTCFullYear()}${String(d.getUTCMonth() + 1).padStart(2, '0')}`; }
async function r2Usage(env, mo) { const r = await env.DB.prepare('SELECT key,value FROM cn_meta WHERE key IN (?,?,?)').bind(`r2_${mo}_ca`, `r2_${mo}_cb`, `r2_${mo}_bytes`).all(); const u = { ca: 0, cb: 0, bytes: 0 }; for (const row of (r.results || [])) { if (row.key.endsWith('_ca')) u.ca = +row.value; else if (row.key.endsWith('_cb')) u.cb = +row.value; else if (row.key.endsWith('_bytes')) u.bytes = +row.value; } return u; }
async function r2Bump(env, mo, dCa, dCb, dBytes) { const set = async (suf, dv) => { if (!dv) return; await env.DB.prepare('INSERT INTO cn_meta(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=CAST(value AS INTEGER)+?').bind(`r2_${mo}_${suf}`, String(dv), dv).run(); }; await set('ca', dCa); await set('cb', dCb); await set('bytes', dBytes); }
// 每次 run 的双写上限（T023 发现：naive per-feed 双写会超免费档 Worker 子请求上限~50/请求 -> 静默丢失；
// 上限 + 单次 run 只读一次预算，控制子请求，7 日靠 cron 累积）。模块级状态每请求重置。
let _rawWrites = 0; let _rawUsage = null; const RAW_MAX_PER_RUN = 3;
// content-addressed 幂等写：HEAD 存在则跳过；预算硬停 + 每 run 上限；idempotent D1 行。返回 {key,wrote,deduped,over_budget,skipped}。
async function dualWriteArtifact(env, sourceId, url, buf) {
  if (_rawWrites >= RAW_MAX_PER_RUN) return { skipped: 'per_run_cap' };
  const bytes = new Uint8Array(buf); const mime = sniffMime(bytes); const sha = await sha256Hex(bytes); const key = rawKey(sourceId, sha, mime);
  const mo = r2Month(); if (!_rawUsage) _rawUsage = await r2Usage(env, mo); // 每 run 只读一次预算，省子请求
  const head = await env.RAW.head(key); if (head) return { key, deduped: true, wrote: false }; // Class B
  if (_rawUsage.ca + _rawWrites + 1 > R2_BUDGET.classAPerMonth * R2_BUDGET.guardFrac || _rawUsage.bytes + bytes.length > R2_BUDGET.storageBytes * R2_BUDGET.guardFrac) return { key, wrote: false, over_budget: true };
  await env.RAW.put(key, buf, { httpMetadata: { contentType: mime } }); _rawWrites++;
  await env.DB.prepare('INSERT INTO cn_artifacts(object_key,sha256,source_id,url,mime,content_length,compression,content_version,created_at) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(object_key) DO NOTHING').bind(key, sha, sourceId, url, mime, bytes.length, 'none', 'v1', new Date().toISOString()).run();
  await r2Bump(env, mo, 1, 1, bytes.length); // Class A(put) + Class B(head) + bytes
  return { key, wrote: true, deduped: false };
}

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
    // Google News 从数据中心 IP 被拦（429/403），换为可从云端抓的官方/主流媒体 RSS
    { id: 'people-politics', name: '人民网 · 时政（政策/政府）', platform: 'people.com.cn 官方 RSS', website: 'http://politics.people.com.cn', method: 'rss', feed: 'http://www.people.com.cn/rss/politics.xml', official: 1, cadence: '每日' },
    { id: 'people-finance', name: '人民网 · 经济与财经政策', platform: 'people.com.cn 官方 RSS', website: 'http://finance.people.com.cn', method: 'rss', feed: 'http://www.people.com.cn/rss/finance.xml', official: 1, cadence: '每日' },
    { id: 'chinanews-scroll', name: '中国新闻网 · 滚动新闻', platform: 'chinanews.com.cn 官方 RSS', website: 'https://www.chinanews.com.cn', method: 'rss', feed: 'https://www.chinanews.com.cn/rss/scroll-news.xml', official: 0, cadence: '每日' },
    { id: 'sina-china-focus', name: '新浪 · 国内焦点', platform: 'sina.com.cn 官方 RSS', website: 'https://news.sina.com.cn/china', method: 'rss', feed: 'https://rss.sina.com.cn/news/china/focus15.xml', official: 0, cadence: '每日' },
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
const FEED_PER_BOARD = 4;       // 每板每次抓取的 feed 数（按最久未抓取优先）——保证每板都有覆盖
const BATCH_CHUNK = 80;         // 每个 D1 batch 的语句数上限
function chunk(arr, n) { const o = []; for (let i = 0; i < arr.length; i += n) o.push(arr.slice(i, i + n)); return o; }

// ───────────────────────── 工具 ─────────────────────────
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
// href 安全化：只允许 http/https（外部 feed 的 url 已在入库时过滤，这里是渲染侧纵深防御，防 javascript:/data:）
const safeHref = (u) => /^https?:\/\//i.test(String(u || '')) ? esc(u) : '#';
// 在 <script> 内嵌字符串时转义 </，防 </script> 提前闭合
const jsStr = (s) => JSON.stringify(s).replace(/</g, '\\u003c');
const nowISO = () => new Date().toISOString();
const dayISO = (d = new Date()) => d.toISOString().slice(0, 10);
// 本地日（用户在 UTC+8，中国标准时）：streak 与「每日一评」防重按用户的一天分桶，而非 UTC
const LOCAL_OFFSET_H = 8;
const localDay = (iso = nowISO()) => new Date(Date.parse(iso) + LOCAL_OFFSET_H * 3600e3).toISOString().slice(0, 10);
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

// 字符集感知抓取：按 XML 声明选 TextDecoder（gb2312/gbk→gb18030），防中文源乱码
async function fetchFeedText(url, env, sourceId) {
  const r = await fetch(url, { headers: { 'User-Agent': UA }, signal: AbortSignal.timeout(15000) });
  if (!r.ok) throw new Error('http ' + r.status);
  const buf = await r.arrayBuffer();
  // S2-P01-T022 SHADOW 双写：抓取成功后旁路存原始字节（flag 默认关；从不影响解析/发布，出错吞掉）
  if (RAW_DUALWRITE && env && env.RAW && sourceId) { try { await dualWriteArtifact(env, sourceId, url, buf); } catch (e) { } }
  const head = new TextDecoder('ascii').decode(buf.slice(0, 200));
  const m = head.match(/encoding="([^"]+)"/i);
  let enc = (m ? m[1] : 'utf-8').toLowerCase();
  if (enc === 'gb2312' || enc === 'gbk') enc = 'gb18030';
  try { return new TextDecoder(enc).decode(buf); } catch { return new TextDecoder('utf-8').decode(buf); }
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
  // 清理注册表已移除的旧源（及其条目），避免雷达页残留（如换掉的 Google News）
  const ids = REGISTRY.flatMap(b => b.sources.map(s => s.id));
  const ph = ids.map(() => '?').join(',');
  stmts.push(env.DB.prepare(`DELETE FROM cn_sources WHERE id NOT IN (${ph})`).bind(...ids));
  // 保护被选择/复习引用的条目，避免删出悬空外键（today/queue 页会 join 到 null）
  stmts.push(env.DB.prepare(
    `DELETE FROM cn_items WHERE kind='feed' AND source_id NOT IN (${ph})
       AND id NOT IN (SELECT item_id FROM cn_reviews)
       AND id NOT IN (SELECT item_id FROM cn_selections WHERE item_id IS NOT NULL)`).bind(...ids));
  await env.DB.batch(stmts);
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

  // 读取所有 feed 源的健康与上次抓取时间（一次查询）
  const { results: srcHealth } = await env.DB.prepare('SELECT id, health, consecutive_failures, last_fetch FROM cn_sources').all();
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
  // 每板取最久未抓取的 FEED_PER_BOARD 个（新源 last_fetch 空排最前）——保证每个板块每次都有覆盖。
  // 自愈：已停用的源在停用 3 天后重新纳入重试（防板块三因源被临时封而永久变黑）。
  const eligible = feeds.filter(f => {
    const h = hmap[f.s.id];
    if (h?.health !== 'disabled_auto') return true;
    return !h.last_fetch || (Date.now() - Date.parse(h.last_fetch)) > 3 * 864e5;
  });
  const byBoard = {};
  for (const f of eligible) (byBoard[f.b] ||= []).push(f);
  const rotated = [];
  for (const bid in byBoard) {
    byBoard[bid].sort((a, b) => (hmap[a.s.id]?.last_fetch || '').localeCompare(hmap[b.s.id]?.last_fetch || ''));
    rotated.push(...byBoard[bid].slice(0, FEED_PER_BOARD));
  }
  const settled = await Promise.allSettled(rotated.map(f =>
    fetchFeedText(f.s.feed, env, f.s.id).then(xml => ({ f, items: parseFeed(xml) }))));
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
  // 每板保留上限——但保护被复习/精选/讲义引用的条目，否则复习卡变孤儿（待复习计数虚高、详情页 404）
  await env.DB.prepare(
    `DELETE FROM cn_items WHERE id IN (
       SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY board_id ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC) rn FROM cn_items) WHERE rn > ?)
     AND id NOT IN (SELECT item_id FROM cn_reviews)
     AND id NOT IN (SELECT item_id FROM cn_selections WHERE item_id IS NOT NULL)
     AND id NOT IN (SELECT item_id FROM cn_lessons)`
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
    evidence: item.official ? 1 : (/^https?:\/\//.test(item.url) ? 0.7 : 0.3),  // 官方源 http/https 同等（板块三是 http）
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
     WHERE COALESCE(i.published_at, i.fetched_at) >= ? ORDER BY COALESCE(i.published_at, i.fetched_at) DESC, i.id DESC LIMIT 1200`
  ).bind(cutoff).all();
  counts.candidates = (items || []).length;
  // 近期板块分布（多样性上下文）
  const { results: recentSel } = await env.DB.prepare(
    'SELECT board_id FROM cn_selections WHERE abstain=0 ORDER BY as_of_date DESC LIMIT 14').all();
  const recentBoards = {}; for (const r of (recentSel || [])) recentBoards[r.board_id] = (recentBoards[r.board_id] || 0) + 1 / 14;
  const ctx = { now: Date.now(), recentBoards, seenSources: new Set((recentSel || []).map(r => r.board_id)) };

  let best = null;
  for (const it of (items || [])) {
    if (BOARD3_A0_ONLY && !a0Board3Eligible(it)) continue;   // T040: Board 3 A0 门 —— 媒体不作证据（降 discovery）
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
  const today = localDay();  // 「每日一评」按用户本地日
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
  _rawWrites = 0; _rawUsage = null; // T023：每次 run 重置双写上限/预算快照（模块级状态在暖 isolate 会跨请求残留）
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

// ───────────────────────── UI（六主题设计语言，从 base.html 移植） ─────────────────────────
const NAV = [['/', '今天'], ['/review', '复习'], ['/radar', '前沿雷达'], ['/system', '系统']];
const FAVICON = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="82" font-size="82">📚</text></svg>');
const META_DESC = 'ADP 前沿学习——每日跨全领域 arXiv 与顶级期刊、政策、科技金融精选一篇，配讲义、主动回忆与 FSRS 间隔复习，整套系统跑在 Cloudflare。';
const THEME_OPTIONS = [['warm', '暖纸学习'], ['minimal', '简约专注'], ['fresh', '清新干净'], ['techno', '炫技'], ['cosmos', '宇宙星河'], ['forest', '森林河流']];
// 首屏 hero 设计语言（v1.1 §首屏与导航结构；video=整屏视频，dash=知识体征仪表盘），仅今天页出现
const HERO_CSS = `
.hero{display:none;position:relative;overflow:hidden;margin:0;z-index:5}
:root[data-hero="video"] .hero-video{display:block}
:root[data-hero="dash"] .hero-cosmic{display:block}
.hero-video{height:74vh;min-height:420px}
:root[data-theme="techno"] .hero-video{height:80vh}
:root[data-theme="forest"] .hero-video{height:72vh}
.hero-video video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.hero-video .mask{position:absolute;inset:0}
:root[data-theme="minimal"] .hero-video .mask{background:linear-gradient(180deg,rgba(0,42,59,.5),rgba(0,42,59,.18) 45%,rgba(0,42,59,.95))}
:root[data-theme="techno"] .hero-video .mask{background:linear-gradient(180deg,rgba(143,176,217,.35),rgba(143,176,217,.05) 45%,#8fb0d9)}
:root[data-theme="forest"] .hero-video .mask{background:linear-gradient(180deg,rgba(251,250,247,1),rgba(251,250,247,.78) 30%,rgba(251,250,247,.6) 60%,rgba(251,250,247,1))}
.hero-inner{position:relative;z-index:2;height:100%;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 8vw;gap:14px}
:root[data-nav="sidebar"] .hero-video .hero-inner{padding-left:calc(216px + 4vw)}
.hero .eyebrow{letter-spacing:.3em;text-transform:uppercase;font-size:12px;color:var(--mt)}
:root[data-theme="minimal"] .hero .eyebrow{color:rgba(255,255,255,.75)}
:root[data-theme="forest"] .hero .eyebrow{color:#6F6F6F}
.hero .display{margin:0;font-family:var(--font-display);font-weight:var(--display-weight);font-style:var(--display-style);font-size:clamp(30px,7vw,72px);line-height:1.02;letter-spacing:var(--display-ls);max-width:18em;color:var(--ink)}
:root[data-theme="minimal"] .hero .display{color:#fff}
:root[data-theme="techno"] .hero .display{color:#0f2038;line-height:.92}
:root[data-theme="forest"] .hero .display{color:#000}
.hero .sub{max-width:620px;font-size:15px;line-height:1.7;color:var(--tx);margin:0}
:root[data-theme="minimal"] .hero .sub{color:rgba(255,255,255,.72)}
:root[data-theme="forest"] .hero .sub{color:#4c4c48}
:root[data-theme="techno"] .hero .sub{color:#243b58}
.hero .cta{display:inline-flex;align-items:center;gap:8px;padding:12px 26px;border-radius:999px;text-decoration:none;font-size:15px;border:1px solid var(--bd);color:var(--ink)}
:root[data-theme="minimal"] .hero .cta{color:#fff;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.28);backdrop-filter:blur(5px)}
:root[data-theme="techno"] .hero .cta{color:#10233c;background:rgba(255,255,255,.5);border:1px solid rgba(255,255,255,.7);backdrop-filter:blur(20px)}
:root[data-theme="forest"] .hero .cta{color:#fff;background:#000;border:1px solid #000}
.fr{opacity:0;transform:translateY(18px);animation:frise .8s cubic-bezier(.2,.7,.2,1) forwards}
.fr.d1{animation-delay:.1s}.fr.d2{animation-delay:.28s}.fr.d3{animation-delay:.46s}
.bw{display:inline-block;opacity:0;filter:blur(10px);transform:translateY(24px);animation:bwin .9s cubic-bezier(.16,.8,.26,1) forwards}
@keyframes bwin{50%{filter:blur(5px);transform:translateY(-3px);opacity:.7}to{filter:blur(0);transform:none;opacity:1}}
/* 宇宙星河：知识体征仪表盘 */
.hero-cosmic{max-width:880px;margin:0 auto;padding:22px 16px 4px}
.cosmic-live{display:flex;align-items:center;gap:10px;padding:0 2px 12px}
.cosmic-live .dot{width:7px;height:7px;background:#63d1a2;border-radius:50%;box-shadow:0 0 8px rgba(99,209,162,.8);animation:pulse 2.4s infinite}
@keyframes pulse{50%{opacity:.35}}
.dash{border:1px solid var(--hairline);background:rgba(9,14,27,.5);backdrop-filter:blur(10px);display:grid;grid-template-columns:200px 1fr 1.2fr}
.dash>div{padding:16px;border-right:1px solid var(--hairline)}
.dash>div:last-child{border-right:none}
.gauge{display:flex;flex-direction:column;align-items:center;gap:6px;text-align:center}
.gauge .num{font-family:'Space Grotesk',var(--font-body);font-variant-numeric:tabular-nums;font-size:32px;font-weight:700;color:var(--ink);letter-spacing:-.02em}
.vitals-d{display:grid;grid-template-columns:1fr 1fr 1fr;gap:0;align-content:center}
.vitals-d>div{padding:4px 8px;border-left:1px solid var(--hairline)}
.vitals-d>div:first-child{border-left:none}
.vitals-d .v{font-family:'Space Grotesk',var(--font-body);font-variant-numeric:tabular-nums;font-size:20px;color:var(--ink)}
.sparkline{width:100%;height:70px;margin-top:6px}
.cosmic-rule{border:none;border-top:1px solid var(--hairline);margin:14px 0 0}
@media(max-width:780px){.dash{grid-template-columns:1fr}.dash>div{border-right:none;border-bottom:1px solid var(--hairline)}:root[data-nav="sidebar"] .hero-video .hero-inner{padding-left:8vw}.hero-video{height:64vh;min-height:360px}}
`;
const CSS = `
/* 六组主题令牌（颜色/圆角/字体/玻璃），由 data-theme 驱动 */
:root,[data-theme="warm"]{--bg:#f3eee1;--pn:#fdfaf2;--ink:#2f2618;--tx:#4a3d28;--mt:#8b7a5c;--ac:#8a5c16;--warn:#a4462c;--bd:#d8cfba;--ok:#4f6f3a;--radius:3px;--radius-lg:12px;--pill:3px;--font-body:'Noto Sans SC',-apple-system,sans-serif;--font-display:'Noto Serif SC',serif;--display-weight:900;--display-style:normal;--display-ls:-0.02em;--glass-bg:var(--pn);--glass-blur:0px;--hairline:var(--bd);--shadow:0 1px 3px rgba(47,38,24,.08)}
[data-theme="minimal"]{--bg:#002a3b;--pn:rgba(255,255,255,.045);--ink:#f4f7f9;--tx:#c9d6dc;--mt:#a5a5ad;--ac:#e8f1f5;--warn:#ff9b7a;--bd:rgba(255,255,255,.14);--ok:#8fd0b8;--radius:999px;--radius-lg:18px;--pill:999px;--font-body:'Noto Sans SC',-apple-system,sans-serif;--font-display:'Instrument Serif','Noto Serif SC',serif;--display-weight:400;--display-style:normal;--display-ls:-0.03em;--glass-bg:rgba(255,255,255,.045);--glass-blur:5px;--hairline:rgba(255,255,255,.12);--shadow:0 18px 50px rgba(0,10,16,.45)}
[data-theme="fresh"]{--bg:#eef6f2;--pn:#fff;--ink:#0d3b2e;--tx:#2a5748;--mt:#5e8a7d;--ac:#0c8f6f;--warn:#c4552f;--bd:#d7e8e0;--ok:#0c8f6f;--radius:14px;--radius-lg:22px;--pill:999px;--font-body:'Noto Sans SC',-apple-system,sans-serif;--font-display:'Noto Sans SC',sans-serif;--display-weight:700;--display-style:normal;--display-ls:-0.01em;--glass-bg:#fff;--glass-blur:0px;--hairline:#d7e8e0;--shadow:0 10px 30px rgba(12,84,64,.10)}
[data-theme="techno"]{--bg:#8fb0d9;--pn:rgba(255,255,255,.16);--ink:#10233c;--tx:#243b58;--mt:#4a6488;--ac:#10233c;--warn:#b34a2e;--bd:rgba(255,255,255,.45);--ok:#1d6f5c;--radius:9999px;--radius-lg:26px;--pill:9999px;--font-body:'Noto Sans SC',-apple-system,sans-serif;--font-display:'Instrument Serif','Noto Serif SC',serif;--display-weight:400;--display-style:italic;--display-ls:-0.04em;--glass-bg:rgba(255,255,255,.16);--glass-blur:4px;--hairline:rgba(255,255,255,.4);--shadow:0 16px 44px rgba(28,52,94,.22)}
[data-theme="cosmos"]{--bg:#060913;--pn:rgba(9,14,27,.58);--ink:#e8eeff;--tx:#b9c6e4;--mt:#6e7ba3;--ac:#89AACC;--warn:#ff8f6b;--bd:rgba(137,170,204,.22);--ok:#63d1a2;--radius:0px;--radius-lg:0px;--pill:0px;--font-body:'Space Grotesk','Noto Sans SC',sans-serif;--font-display:'Space Grotesk','Noto Sans SC',sans-serif;--display-weight:700;--display-style:normal;--display-ls:-0.03em;--glass-bg:rgba(9,14,27,.58);--glass-blur:10px;--hairline:rgba(137,170,204,.22);--shadow:0 0 8px rgba(137,170,204,.18)}
[data-theme="forest"]{--bg:#fbfaf7;--pn:#fff;--ink:#000;--tx:#4c4c48;--mt:#6F6F6F;--ac:#2e7d5b;--warn:#a4462c;--bd:#e4e1d8;--ok:#2e7d5b;--radius:999px;--radius-lg:18px;--pill:999px;--font-body:'Noto Sans SC',-apple-system,sans-serif;--font-display:'Instrument Serif','Noto Serif SC',serif;--display-weight:400;--display-style:normal;--display-ls:-0.025em;--glass-bg:#fff;--glass-blur:0px;--hairline:#e4e1d8;--shadow:0 8px 26px rgba(30,40,30,.08)}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.9 var(--font-body);transition:background .3s,color .3s}
a{color:var(--ac);text-decoration:none}
h1,h2,h3{color:var(--ink);line-height:1.5;font-family:var(--font-display);font-weight:var(--display-weight);font-style:var(--display-style);letter-spacing:var(--display-ls)}
h1{font-size:22px;margin:.2em 0}h2{font-size:17px}h3{font-size:15px;margin:14px 0 4px;color:var(--ac)}
.mt{color:var(--mt);font-size:13px}
main{max-width:760px;margin:0 auto;padding:18px 18px 60px}
.card{background:var(--glass-bg);backdrop-filter:blur(var(--glass-blur));border:1px solid var(--hairline);border-radius:var(--radius-lg);padding:16px 18px;margin:14px 0;box-shadow:var(--shadow);overflow-wrap:break-word}
.badge{display:inline-block;border:1px solid var(--hairline);border-radius:999px;padding:1px 10px;font-size:12px;margin-left:6px;color:var(--mt)}
.badge.ok{color:var(--ok);border-color:var(--ok)}
button{min-height:44px;padding:9px 17px;border-radius:var(--pill);border:1px solid var(--bd);background:var(--glass-bg);font-size:15px;color:var(--tx);cursor:pointer;font-family:var(--font-body)}
button.picked{background:var(--ac);color:var(--bg);border-color:var(--ac)}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{padding:7px 8px;border-bottom:1px solid var(--hairline);text-align:left;vertical-align:top}
.gradeRow{display:flex;gap:8px;flex-wrap:wrap;margin-top:8px}
/* T079 移动端溢出防线（360/390/430 宽）：媒体不溢出 + 数据密集表格局部横滚（不产生全页横向滚动；不动主题/动效层） */
main img,main svg,main video{max-width:100%}
@media(max-width:520px){table{display:block;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch}}
/* T080 组件状态矩阵（按下/禁用/加载/成功/错误/聚焦/撤销）：点击即时反馈——:active 于 pointerdown 触发（<16ms），
   transition 仅 80ms，反馈在 100ms 内可见；不新增 @keyframes、不动主题/动效层。 */
button{transition:transform .08s ease,background .15s ease,border-color .15s ease,opacity .15s ease}
button:active{transform:translateY(1px)}
button:disabled,button[aria-disabled="true"]{opacity:.5;cursor:not-allowed;transform:none}
button[aria-busy="true"]{opacity:.7;cursor:progress;pointer-events:none}
button:focus-visible,a:focus-visible,select:focus-visible{outline:2px solid var(--ac);outline-offset:2px}
button.undo{border-color:var(--warn);color:var(--warn)}
[data-state="ok"]{color:var(--ok)}[data-state="err"]{color:var(--warn)}
select#theme{min-height:38px;border-radius:var(--pill);border:1px solid var(--bd);background:var(--glass-bg);color:var(--tx);padding:6px 12px;font-size:13.5px;margin-left:auto}
/* 页头 */
header.top{position:relative;z-index:30;display:flex;align-items:center;gap:14px;padding:12px 20px;border-bottom:1px solid var(--hairline);background:var(--glass-bg);backdrop-filter:blur(var(--glass-blur));flex-wrap:wrap}
header.top b{color:var(--ink);font-size:17px;font-family:var(--font-display);font-style:var(--display-style);letter-spacing:var(--display-ls)}
/* 三种导航（结构开关 body[data-nav]） */
nav.nav-top,nav.nav-side,nav.nav-dock{display:none}
nav.nav-top{justify-content:center;gap:6px;padding:8px 12px}nav.nav-top a{padding:6px 16px;border-radius:var(--pill)}
nav.nav-top a.active{background:var(--ac);color:var(--bg)}
:root[data-nav="topbar"] nav.nav-top{display:flex;flex:1}
nav.nav-side{position:fixed;left:0;top:0;bottom:0;width:216px;padding:18px 12px;border-right:1px solid var(--hairline);background:var(--glass-bg);backdrop-filter:blur(var(--glass-blur));overflow:auto}
nav.nav-side a{display:block;padding:8px 14px;margin:3px 0;border-radius:var(--pill);border-left:3px solid transparent;white-space:nowrap}
nav.nav-side a.active{border-left-color:var(--ac);color:var(--ac);background:var(--bg)}
[data-theme="forest"] nav.nav-side a{border-left:none}[data-theme="forest"] nav.nav-side a.active{background:#000;color:#fff}
:root[data-nav="sidebar"] nav.nav-side{display:block}
:root[data-nav="sidebar"] main,:root[data-nav="sidebar"] header.top{margin-left:216px}
nav.nav-dock{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);gap:4px;padding:6px;border:1px solid var(--hairline);border-radius:999px;background:var(--glass-bg);backdrop-filter:blur(8px);z-index:40;box-shadow:var(--shadow)}
nav.nav-dock a{padding:7px 15px;border-radius:var(--pill);font-size:13.5px}
nav.nav-dock a.active{background:var(--ac);color:var(--bg)}
:root[data-nav="dock"] nav.nav-dock{display:flex}:root[data-nav="dock"] footer.receipt{padding-bottom:92px}
/* 深色主题让原生下拉/表单用暗色配色（否则选项在浅色弹层上几乎看不清） */
:root[data-theme="minimal"],:root[data-theme="cosmos"]{color-scheme:dark}
:root[data-theme="warm"],:root[data-theme="fresh"],:root[data-theme="forest"],:root[data-theme="techno"]{color-scheme:light}
@media(max-width:640px){nav.nav-side{display:none!important}:root[data-nav] main,:root[data-nav] header.top{margin-left:0!important}:root[data-nav="sidebar"] nav.nav-top{display:flex;flex:1}}
footer.receipt{max-width:760px;margin:0 auto;padding:14px 18px 48px;color:var(--mt);font-size:12px}
.searchbox input{min-height:38px;border-radius:var(--pill);border:1px solid var(--bd);background:var(--glass-bg);color:var(--tx);padding:6px 14px;font-size:13.5px;width:150px;font-family:var(--font-body)}
.vitals{display:flex;flex-wrap:wrap;gap:10px}
.vital{flex:1;min-width:88px;text-align:center;padding:8px 6px;border:1px solid var(--hairline);border-radius:var(--radius-lg)}
.vital .n{font-family:var(--font-display);font-size:22px;color:var(--ink);line-height:1.2}
.vital .l{font-size:11.5px;color:var(--mt)}
.itemrow{display:flex;gap:10px;align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--hairline)}
.itemrow:last-child{border-bottom:none}
.itemrow .body{flex:1;min-width:0}
.btn-sm{min-height:34px;padding:5px 12px;font-size:13px;white-space:nowrap}
.pill-link{display:inline-block;font-size:12.5px;border:1px solid var(--hairline);border-radius:999px;padding:2px 11px;margin:2px 4px 2px 0;color:var(--ac)}
.reveal{border:1px dashed var(--hairline);border-radius:var(--radius-lg);padding:12px 14px;margin-top:10px;background:var(--bg)}
.deep-btn{display:inline-flex;align-items:center;gap:6px;min-height:38px;padding:8px 16px;border-radius:var(--pill);border:1px solid var(--ac);background:var(--ac);color:var(--bg);font-size:14px;font-weight:600;margin:6px 6px 2px 0;text-decoration:none}
.deep-btn.ghost{background:transparent;color:var(--ac)}
.deep-btn:hover{opacity:.9}
/* ── 每主题氛围动效层（从 base.html 移植并大幅加强可见度；纯 CSS/SVG，无外部依赖，CSP 安全） ── */
main{position:relative;z-index:1}
nav.nav-side{z-index:20}
footer.receipt{position:relative;z-index:1}
.fx{position:fixed;inset:0;pointer-events:none;z-index:0;display:none;overflow:hidden}
:root[data-fx="cosmos"] .fx-cosmos{display:block}
:root[data-fx="techno"] .fx-techno{display:block}
:root[data-fx="minimal"] .fx-minimal{display:block}
/* 宇宙星河：明亮银河（星云辉光常驻在屏 + 极光光带扫动 + 密集亮星闪烁 + 高频流星），卡片调透让银河透出 */
.fx-cosmos{background:radial-gradient(58% 42% at 22% 18%,rgba(78,133,191,.42),transparent 70%),radial-gradient(56% 44% at 84% 78%,rgba(122,92,201,.40),transparent 70%),radial-gradient(52% 40% at 62% 48%,rgba(45,127,142,.26),transparent 72%)}
:root[data-theme="cosmos"] .card{background:rgba(9,14,27,.40)}
.fx-cosmos .band{position:absolute;left:-25%;top:-8%;width:150%;height:64%;background:conic-gradient(from 130deg at 50% 50%,rgba(137,170,204,0),rgba(122,92,201,.32),rgba(78,133,191,.28),rgba(99,209,162,.22),rgba(137,170,204,0));filter:blur(46px);transform:rotate(-10deg);animation:banddrift 22s ease-in-out infinite alternate}
@keyframes banddrift{to{transform:rotate(-3deg) translateX(9%) translateY(6%)}}
.fx-cosmos .neb{position:absolute;width:54vw;height:54vw;border-radius:50%;filter:blur(60px);opacity:.6;animation:nebfloat 28s ease-in-out infinite alternate}
.fx-cosmos .neb.blue{background:#4E85BF;top:-8vw;right:-4vw}
.fx-cosmos .neb.violet{background:#7a5cc9;bottom:-10vw;left:-6vw;animation-duration:36s}
.fx-cosmos .neb.teal{background:#2d7f8e;top:40%;left:44%;width:36vw;height:36vw;opacity:.42;animation-duration:32s}
@keyframes nebfloat{to{transform:translate(6vw,-4vw) scale(1.14)}}
.fx-cosmos .stars{position:absolute;inset:0;background-repeat:repeat;background-image:radial-gradient(1.6px 1.6px at 20px 30px,#fff 60%,transparent 61%),radial-gradient(1.4px 1.4px at 92px 68px,rgba(210,225,255,.95) 60%,transparent 61%),radial-gradient(2.2px 2.2px at 150px 120px,#fff 60%,transparent 61%),radial-gradient(1.4px 1.4px at 60px 160px,rgba(200,220,255,.9) 60%,transparent 61%),radial-gradient(1.8px 1.8px at 190px 40px,#fff 60%,transparent 61%);background-size:200px 200px}
.fx-cosmos .stars.near{background-size:300px 300px;animation:twinkle 3.4s ease-in-out infinite alternate}
@keyframes twinkle{from{opacity:1}to{opacity:.35}}
.fx-cosmos .meteor{position:absolute;top:8%;left:-12%;width:200px;height:2px;background:linear-gradient(90deg,#fff,rgba(255,255,255,.5),transparent);box-shadow:0 0 7px #fff;transform:rotate(18deg);opacity:0;animation:meteor 6s linear infinite}
@keyframes meteor{0%,82%{opacity:0;transform:translate(0,0) rotate(18deg)}84%{opacity:1}100%{opacity:0;transform:translate(112vw,56vh) rotate(18deg)}}
/* 简约专注：海面顶光 + 移动光柱 + 海底暗角 */
.fx-minimal{background:radial-gradient(120vw 62vh at 50% -12vh,rgba(163,214,235,.30),transparent 62%)}
.fx-minimal .toplight{position:absolute;left:50%;top:-28vh;width:78vw;height:92vh;transform:translateX(-50%) rotate(6deg);background:linear-gradient(180deg,rgba(185,228,247,.32),transparent 72%);filter:blur(22px);animation:shaft 11s ease-in-out infinite alternate}
@keyframes shaft{to{transform:translateX(-40%) rotate(-5deg)}}
.fx-minimal .vignette{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 118%,rgba(0,10,18,.6),transparent 58%)}
/* 炫技：白色流体云漂移（更大更明显） */
.fx-techno .cloud{position:absolute;width:72vw;height:34vw;border-radius:50%;background:radial-gradient(closest-side,rgba(255,255,255,.92),transparent 70%);filter:blur(24px);animation:clouddrift 15s ease-in-out infinite alternate}
.fx-techno .cloud.c2{top:40%;left:44%;width:58vw;animation-duration:12s;opacity:.85}
.fx-techno .cloud.c3{top:66%;left:-14%;width:66vw;animation-duration:19s;opacity:.72}
@keyframes clouddrift{to{transform:translateX(15vw) translateY(-4vw)}}
/* 森林河流：水带 + 坡地（更高更明显，缓慢起伏） */
:root[data-theme="forest"] .waterband{height:6px;border-radius:999px;margin:2px 0 12px;background:linear-gradient(90deg,#2e7d5b,#3c7ea0);opacity:.85}
.forest-slopes{display:none;position:fixed;bottom:0;left:0;right:0;height:210px;pointer-events:none;z-index:0;animation:sway 14s ease-in-out infinite alternate}
:root[data-theme="forest"] .forest-slopes{display:block}
.forest-slopes svg{width:100%;height:100%;display:block}
@keyframes sway{to{transform:translateX(-3%)}}
/* 卡片入场：淡入上移 */
.card{animation:frise .5s cubic-bezier(.2,.7,.2,1) both}
@keyframes frise{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}.fr,.bw{opacity:1!important;transform:none!important;filter:none!important}}
${HERO_CSS}
`;
const navActive = (h, page) => h === '/' ? page === '/' : page.startsWith(h);
const navLinks = (cls, page) => `<nav class="${cls}" aria-label="主导航">${NAV.map(([h, t]) => `<a href="${h}"${navActive(h, page) ? ' class="active" aria-current="page"' : ''}>${t}</a>`).join('')}</nav>`;
// 主题-导航映射 + 安全读写（storage 被禁时不抛）；HEAD_INIT 在首绘前定主题防闪烁
const THEME_NAV = { warm: 'sidebar', minimal: 'topbar', fresh: 'topbar', techno: 'dock', cosmos: 'dock', forest: 'sidebar' };
// 每主题氛围动效层开关（cosmos 银河 / techno 流云 / minimal 海面光；forest 坡地由 data-theme 驱动）
const THEME_FX = { warm: 'none', minimal: 'minimal', fresh: 'none', techno: 'techno', cosmos: 'cosmos', forest: 'none' };
// 首屏结构（今天页顶部，按主题切 DOM）：video=整屏对标视频，dash=知识体征仪表盘，none=无首屏（v1.1 规范）
const THEME_HERO = { warm: 'none', minimal: 'video', fresh: 'none', techno: 'video', cosmos: 'dash', forest: 'video' };
// 视频自托管在 Worker 静态资产（同源 /media/*.mp4；从 v1.1 §视频资产的对标原视频压制为 720p 无音轨 web loop，
// 存进 deploy/cloudflare/assets/media/），彻底摆脱外部 CloudFront 依赖（原 NOVA/宇宙星河那条已 403 失效，故 cosmos 用仪表盘无视频）。
const HERO_VIDEO = {
  minimal: '/media/velorah.mp4',   // Velorah（简约专注）
  techno: '/media/voyage.mp4',     // Space Voyage（炫技）
  forest: '/media/aethera.mp4',    // Aethera（森林河流）
};
// 首绘前在 <html> 上定 data-theme + data-nav，颜色与导航结构都无闪烁（storage 被禁时安全回退）
const HEAD_INIT = `<script>(function(){try{var m=${JSON.stringify(THEME_NAV)},fx=${JSON.stringify(THEME_FX)},hr=${JSON.stringify(THEME_HERO)};var s=localStorage.getItem('adp-theme');if(!Object.prototype.hasOwnProperty.call(m,s))s='warm';
var r=document.documentElement;r.setAttribute('data-theme',s);r.setAttribute('data-nav',m[s]);r.setAttribute('data-fx',fx[s]||'none');r.setAttribute('data-hero',hr[s]||'none');}catch(e){}})();</script>`;
const THEME_JS = `
var THEMES=${JSON.stringify(THEME_NAV)};
var THEMEFX=${JSON.stringify(THEME_FX)};
var THEMEHERO=${JSON.stringify(THEME_HERO)};
var HEROVIDEO=${JSON.stringify(HERO_VIDEO)};
var reducedMotion=false;try{reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;}catch(e){}
function lsGet(k){try{return localStorage.getItem(k)}catch(e){return null}}
function lsSet(k,v){try{localStorage.setItem(k,v)}catch(e){}}
function isTheme(n){return Object.prototype.hasOwnProperty.call(THEMES,n);}
function applyTheme(n){if(!isTheme(n))n='warm';var r=document.documentElement;r.setAttribute('data-theme',n);r.setAttribute('data-nav',THEMES[n]);r.setAttribute('data-fx',THEMEFX[n]||'none');
var hasHero=document.querySelector('.hero-video,.hero-cosmic');r.setAttribute('data-hero',hasHero?(THEMEHERO[n]||'none'):'none');lsSet('adp-theme',n);
syncHeroVideo(n);if(n==='techno')blurTextIn();if(n==='cosmos')animateGauge();
var m=document.querySelector('meta[name=theme-color]');if(m){m.content=getComputedStyle(r).getPropertyValue('--bg').trim();}}
// 视频首屏实现红线（v1.1 §实现红线）：src 由 JS 赋值、muted/loop 显式布尔、play().catch，未静音会被自动播放策略拦成冻结首帧
function syncHeroVideo(n){var v=document.getElementById('heroVideo');if(!v)return;var url=HEROVIDEO[n];
var want=document.documentElement.getAttribute('data-hero')==='video'&&url&&!reducedMotion;
if(want){if(v.dataset.current!==url){v.muted=true;v.loop=true;v.playsInline=true;v.autoplay=true;v.src=url;v.dataset.current=url;v.oncanplay=function(){v.play().catch(function(){});};}v.play().catch(function(){});}
else{try{v.pause();}catch(e){}if(!url){v.removeAttribute('src');v.dataset.current='';try{v.load();}catch(e){}}}}
function blurTextIn(){var ws=document.querySelectorAll('.hero .display .bw');for(var i=0;i<ws.length;i++){(function(w,i){w.style.animation='none';void w.offsetWidth;w.style.animation='';w.style.animationDelay=(i*0.045)+'s';})(ws[i],i);}}
function animateGauge(){var num=document.getElementById('gaugeNum'),arc=document.getElementById('gaugeArc');if(!num)return;
var target=parseFloat(num.dataset.value||'0'),maxv=parseFloat(num.dataset.max||'104'),circ=2*Math.PI*54;
function settle(){num.textContent=String(Math.round(target)).padStart(3,'0');if(arc)arc.style.strokeDashoffset=circ*(1-(target/maxv)*0.75);}
if(reducedMotion||document.visibilityState!=='visible'){settle();return;}
var start=null;function step(ts){if(!start)start=ts;var p=Math.min(1,(ts-start)/1200);var val=target*(0.5-Math.cos(Math.PI*p)/2);num.textContent=String(Math.round(val)).padStart(3,'0');if(arc)arc.style.strokeDashoffset=circ*(1-(val/maxv)*0.75);if(p<1)requestAnimationFrame(step);}
requestAnimationFrame(step);setTimeout(settle,1500);}
(function(){var s=lsGet('adp-theme');if(!isTheme(s))s='warm';var sel=document.getElementById('theme');if(sel){sel.value=s;sel.onchange=function(){applyTheme(sel.value);};}applyTheme(s);})();
`;
// 氛围动效层（固定背景，aria-hidden，纯 CSS/SVG 驱动；仅当前主题对应层显示）
const FX_LAYERS = `<div class="fx fx-cosmos" aria-hidden="true"><div class="band"></div><div class="neb blue"></div><div class="neb violet"></div><div class="neb teal"></div><div class="stars"></div><div class="stars near"></div><div class="meteor"></div></div><div class="fx fx-minimal" aria-hidden="true"><div class="toplight"></div><div class="vignette"></div></div><div class="fx fx-techno" aria-hidden="true"><div class="cloud" style="top:6%;left:-10%"></div><div class="cloud c2"></div><div class="cloud c3"></div></div><div class="forest-slopes" aria-hidden="true"><svg viewBox="0 0 1440 120" preserveAspectRatio="none"><path d="M0,120 L0,70 Q360,10 720,64 T1440,52 L1440,120 Z" fill="#2e7d5b" opacity="0.16"/><path d="M0,120 L0,96 Q480,44 900,92 T1440,84 L1440,120 Z" fill="#3c7ea0" opacity="0.14"/></svg></div>`;
const PAGE = (page, body, opts = {}) => `<!doctype html><html lang="zh-CN" data-theme="warm" data-nav="sidebar" data-fx="none" data-hero="none"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${opts.title ? esc(opts.title) + ' · ' : ''}ADP 前沿学习</title>
<meta name="description" content="${esc(META_DESC)}">
<meta name="theme-color" content="#f3eee1">
<meta property="og:title" content="ADP 前沿学习"><meta property="og:description" content="${esc(META_DESC)}"><meta property="og:type" content="website">
<link rel="icon" href="${FAVICON}">
<style>${CSS}</style>${HEAD_INIT}</head>
<body>
${FX_LAYERS}
${navLinks('nav-side', page)}
<header class="top"><b><a href="/" style="color:inherit">ADP 前沿学习</a></b>${navLinks('nav-top', page)}
<form action="/search" method="get" class="searchbox" role="search"><input name="q" placeholder="搜索条目…" aria-label="搜索" value="${esc(opts.q || '')}"></form>
<select id="theme" aria-label="主题">${THEME_OPTIONS.map(([v, t]) => `<option value="${v}">${t}</option>`).join('')}</select></header>
${opts.hero || ''}
<main>${body}</main>
${navLinks('nav-dock', page)}
<footer class="receipt">整套系统运行在 Cloudflare（抓取·选择·讲义·回忆·排程都在云端）；每日 cron 自动更新，不依赖任何本机。 · <a href="/history">往期精选</a> · <a href="/build.json" style="color:inherit" title="运行版本">build ${BUILD.build_id}</a></footer>
<script>${THEME_JS}</script>
</body></html>`;

// ───────────────────────── 首屏 hero（v1.1：video 整屏视频 / dash 知识体征仪表盘） ─────────────────────────
function blurChars(text) {
  return [...String(text)].map(c => c === ' ' ? ' ' : `<span class="bw">${esc(c)}</span>`).join('');
}
function sparkSVG(scores) {
  const max = 104, n = scores.length;
  if (!n) return '';
  const xy = (i, s) => [n === 1 ? 50 : (i / (n - 1)) * 100, 38 - Math.max(0, Math.min(1, s / max)) * 34];
  const line = scores.map((s, i) => xy(i, s).map(z => z.toFixed(1)).join(',')).join(' ');
  const dots = scores.map((s, i) => { const [x, y] = xy(i, s); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="1.7" fill="${s <= 0 ? 'var(--mt)' : 'var(--ac)'}"/>`; }).join('');
  return `<polyline points="${line}" fill="none" stroke="var(--ac)" stroke-width="1.5" vector-effect="non-scaling-stroke"/>${dots}`;
}
function heroSection(sel, item, v, spark) {
  const abstain = !sel || sel.abstain;
  const eyebrow = abstain ? '今日弃权 · 宁缺毋滥' : (BOARD_NAMES[sel.board_id] || '每日前沿');
  const title = (abstain ? '今天没有达标的精选' : (item ? item.title : '今日精选')).slice(0, 46);
  const sub = ((abstain ? (sel && sel.abstain_reason) : (sel && sel.why)) || '').slice(0, 100);
  const score = sel && sel.score != null ? Number(sel.score) : 0;
  const circ = 2 * Math.PI * 54;
  const video = `<section class="hero hero-video" aria-label="今日首屏">
    <video id="heroVideo" muted loop playsinline preload="auto" aria-hidden="true"></video>
    <div class="mask"></div>
    <div class="hero-inner">
      <div class="eyebrow fr d1">${esc(eyebrow)}</div>
      <h1 class="display">${blurChars(title)}</h1>
      <p class="sub fr d3">${esc(sub)}</p>
      <a class="cta fr d3" href="#todaymain">开始学习 ↓</a>
    </div>
  </section>`;
  const dash = `<section class="hero hero-cosmic" aria-label="今日知识体征">
    <div class="cosmic-live"><span class="dot"></span><span class="microlabel">LIVE · 今日知识体征</span></div>
    <div class="dash">
      <div class="gauge">
        <svg width="128" height="128" viewBox="0 0 128 128" aria-hidden="true">
          <defs><linearGradient id="gg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#89AACC"/><stop offset="1" stop-color="#4E85BF"/></linearGradient></defs>
          <circle cx="64" cy="64" r="54" fill="none" stroke="var(--hairline)" stroke-width="8"/>
          <circle id="gaugeArc" cx="64" cy="64" r="54" fill="none" stroke="url(#gg)" stroke-width="8" stroke-linecap="round" stroke-dasharray="${circ.toFixed(1)}" stroke-dashoffset="${circ.toFixed(1)}" transform="rotate(135 64 64)" style="filter:drop-shadow(0 0 6px rgba(137,170,204,.5))"/>
        </svg>
        <div class="num" id="gaugeNum" data-value="${score}" data-max="104">000</div>
        <div class="microlabel">${abstain ? '最高分 / 104' : '今日精选分 / 104'}</div>
      </div>
      <div class="vitals-d">
        <div><div class="v">${v.streak}</div><div class="microlabel">STREAK</div></div>
        <div><div class="v">${v.retention != null ? v.retention + '%' : '—'}</div><div class="microlabel">RETENTION</div></div>
        <div><div class="v">${v.due}</div><div class="microlabel">REVIEW DEBT</div></div>
      </div>
      <div><div class="microlabel">近 ${spark.length} 次精选分</div><svg class="sparkline" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true">${sparkSVG(spark)}</svg></div>
    </div>
    <hr class="cosmic-rule">
  </section>`;
  return video + dash;
}

async function todayPage(env) {
  const v = await computeVitals(env);
  const sel = await env.DB.prepare('SELECT * FROM cn_selections ORDER BY as_of_date DESC LIMIT 1').first();
  const { results: recent } = await env.DB.prepare('SELECT score, abstain FROM cn_selections ORDER BY as_of_date DESC LIMIT 7').all();
  const spark = (recent || []).map(r => r.abstain ? 0 : (r.score || 0)).reverse();
  if (!sel) return PAGE('/', vitalsCard(v) + `<div class="card"><h1>还没有内容</h1><p class="mt">每日流水线尚未运行。可在 <a href="/system">系统页</a> 手动触发一次。</p></div>`);
  const item = sel.abstain ? null : await env.DB.prepare('SELECT * FROM cn_items WHERE id=?').bind(sel.item_id).first();
  const hero = heroSection(sel, item, v, spark);
  if (sel.abstain) return PAGE('/', `<span id="todaymain"></span>` + vitalsCard(v) + `<div class="card"><h1>今日弃权</h1><p>${esc(sel.abstain_reason)}</p><p class="mt">决策日期 ${esc(sel.as_of_date)}——宁缺毋滥。可去 <a href="/radar">雷达</a> 挑条目「学这个」，或看 <a href="/history">往期</a>。</p></div>`, { hero });
  const lesson = await env.DB.prepare('SELECT * FROM cn_lessons WHERE item_id=? ORDER BY created_at DESC LIMIT 1').bind(sel.item_id).first();
  const review = await env.DB.prepare('SELECT * FROM cn_reviews WHERE item_id=?').bind(sel.item_id).first();
  let body = `<span id="todaymain"></span>` + vitalsCard(v) + `<div class="card"><h2>为什么今天选它</h2><p>${esc(sel.why)}</p>
    <p class="mt">决策日期 ${esc(sel.as_of_date)} · ${esc(BOARD_NAMES[sel.board_id] || sel.board_id || '')}${review ? ' · 证据态 ' + esc(review.evidence_state) : ''}</p></div>`;
  if (item) {
    body += `<div class="card"><h1>${esc(item.title)}</h1>
      <p class="mt">${esc(item.authors || '')}${item.categories ? ' · ' + esc(item.categories) : ''} · <a href="${safeHref(item.url)}" rel="noopener">原文</a></p>
      <p style="margin:4px 0 2px">${deepDiveBtn(item)}</p>`;
    if (lesson) for (const [i, s] of JSON.parse(lesson.sections_json).entries())
      body += `<h3>${i + 1}. ${esc(s.title)}</h3>${(s.sentences || []).map(x => `<p>${esc(x.text)}</p>`).join('')}`;
    body += `</div><div class="card"><h2>主动回忆</h2>
      <p class="mt">先合上讲义复述，再自评。评分即时进 FSRS 排程（云端即真相）。</p>
      <div class="gradeRow">${[[1,'忘了'],[2,'困难'],[3,'良好'],[4,'轻松']].map(([g,l]) =>
        `<button onclick="grade(${g},this)">${l}</button>`).join('')}</div>
      <p id="r" class="mt"></p>
      <script>var _grading=false,_pend=null;
        function grade(g,btn){if(_grading)return;_grading=true;var row=document.querySelectorAll('.gradeRow button'),r=document.getElementById('r');
          row.forEach(function(b){b.classList.remove('picked');b.disabled=true;});btn.classList.add('picked');r.removeAttribute('data-state');var left=4;
          function draw(){r.innerHTML='已选「'+btn.textContent+'」，<b>'+left+'</b>s 后记录　<button type="button" class="btn-sm undo" onclick="gradeUndo()">撤销</button>';}
          draw();_pend=setInterval(function(){left--;if(left<=0){clearInterval(_pend);_pend=null;gradeCommit(g,btn);}else draw();},1000);}
        function gradeUndo(){if(_pend){clearInterval(_pend);_pend=null;}document.querySelectorAll('.gradeRow button').forEach(function(b){b.classList.remove('picked');b.disabled=false;});
          var r=document.getElementById('r');r.setAttribute('data-state','');r.textContent='已撤销，未记录。';_grading=false;}
        async function gradeCommit(g,btn){var r=document.getElementById('r');btn.setAttribute('aria-busy','true');r.textContent='记录中…';
          try{var res=await fetch('/api/grade/'+encodeURIComponent(${jsStr(sel.item_id)})+'/'+g,{method:'POST'});if(!res.ok)throw new Error(res.status);var j=await res.json();
            btn.removeAttribute('aria-busy');r.setAttribute('data-state','ok');
            r.textContent=j.duplicate?('今天已评过（事件 #'+j.id+'），未重复计。'):('已记录 → 下次复习 '+j.due_at+'（间隔 '+j.interval+' 天，证据态：'+j.evidence_state+'）');
          }catch(e){btn.removeAttribute('aria-busy');r.setAttribute('data-state','err');r.textContent='记录失败，请重试。';
            document.querySelectorAll('.gradeRow button').forEach(function(b){b.disabled=false;});_grading=false;}}
      </script></div>`;
  }
  return PAGE('/', body, { hero });
}

async function radarPage(env) {
  const { results: srcs } = await env.DB.prepare('SELECT * FROM cn_sources ORDER BY board_id, id').all();
  const { results: counts } = await env.DB.prepare('SELECT board_id, COUNT(*) n FROM cn_items GROUP BY board_id').all();
  const cmap = Object.fromEntries((counts || []).map(c => [c.board_id, c.n]));
  cmap.board5 = Object.values(cmap).reduce((a, b) => a + b, 0);  // 板块五=聚合，计数为各板之和
  const boards = [...REGISTRY.map(b => ({ id: b.board, name: b.name })), AGG_BOARD];
  let body = `<div class="card"><h1>前沿雷达</h1><p class="mt">全部板块的数据源都进入每日精选；下面是每个板块的信息源与状态。</p>
    <p class="mt">${boards.map(b => `<a href="#${b.id}">${esc(b.name)}</a>`).join(' · ')}</p></div>`;
  for (const b of boards) {
    const bs = (srcs || []).filter(s => s.board_id === b.id);
    body += `<div class="card" id="${b.id}"><h2>${esc(b.name)}<span class="badge ok">${cmap[b.id] || 0} 条</span></h2>`;
    if (bs.length) {
      body += `<h3>数据源（信息源 / 平台 / 网站）</h3><table><tr><th>来源</th><th>平台</th><th>健康</th></tr>`;
      body += bs.map(s => `<tr><td>${esc(s.name)}<div class="mt"><a href="${safeHref(s.website)}" rel="noopener">${esc(s.website)}</a></div></td>
        <td class="mt">${esc(s.platform)}${s.official ? '<span class="badge ok">官方</span>' : '<span class="badge">聚合</span>'}</td>
        <td>${s.health === 'active' ? '<span class="badge ok">正常</span>' : '<span class="badge info">' + esc(s.health) + '</span>'}</td></tr>`).join('');
      body += `</table>`;
    } else if (b.id === 'board5') body += `<p class="mt">聚合各板块，无独立来源。</p>`;
    const { results: items } = await env.DB.prepare(
      b.id === 'board5'
        ? `SELECT id, title, url, board_id FROM cn_items ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 8`
        : `SELECT id, title, url, board_id FROM cn_items WHERE board_id=? ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT 6`
    ).bind(...(b.id === 'board5' ? [] : [b.id])).all();
    if ((items || []).length) body += `<h3>最新条目</h3><ul class="mt">${items.map(it =>
      `<li><a href="/item/${encodeURIComponent(it.id)}">${esc(it.title.slice(0, 90))}</a></li>`).join('')}</ul>`;
    body += `<p style="margin-top:8px"><a class="pill-link" href="/board/${b.id}">查看全部 ${cmap[b.id] || 0} 条 →</a></p></div>`;
  }
  return PAGE('/radar', body, { title: '前沿雷达' });
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
    <script>async function run(b){b.disabled=true;b.setAttribute('aria-busy','true');var rr=document.getElementById('rr');rr.removeAttribute('data-state');rr.textContent='运行中…（抓取全网可能需十几秒）';
      try{const res=await fetch('/api/run',{method:'POST'});if(!res.ok)throw new Error(res.status);const j=await res.json();
        b.removeAttribute('aria-busy');rr.setAttribute('data-state','ok');rr.textContent='结果：'+j.result+'（'+JSON.stringify(j.counts)+'）';setTimeout(()=>location.reload(),1200);
      }catch(e){b.removeAttribute('aria-busy');b.disabled=false;rr.setAttribute('data-state','err');rr.textContent='运行失败，请重试。';}}</script></div>`);
}

// ───────────────────────── 学习数据 / 复用组件 ─────────────────────────
async function computeVitals(env) {
  const now = nowISO(), today = localDay();
  const q = (sql, ...b) => env.DB.prepare(sql).bind(...b).first();
  // 只算 item 仍存在的到期卡（防孤儿卡把待复习计数撑高，与 /review 的 INNER JOIN 一致）
  const [due, learned, mastered, reviews, ret] = await Promise.all([
    q("SELECT COUNT(*) n FROM cn_reviews r WHERE r.due_at IS NOT NULL AND r.due_at<=? AND r.reps>0 AND EXISTS(SELECT 1 FROM cn_items i WHERE i.id=r.item_id)", now),
    q("SELECT COUNT(*) n FROM cn_reviews WHERE reps>0"),
    q("SELECT COUNT(*) n FROM cn_reviews WHERE evidence_state='已掌握'"),
    q("SELECT COUNT(*) n FROM cn_events WHERE kind='grade'"),
    q("SELECT AVG(CASE WHEN last_grade>=3 THEN 1.0 ELSE 0 END) r FROM cn_reviews WHERE last_grade IS NOT NULL"),
  ]);
  // streak 按用户本地日分桶（拉原始时间戳在 JS 里换算，避免 UTC 跨日误清零）
  const { results: evs } = await env.DB.prepare(
    "SELECT at FROM cn_events WHERE kind='grade' ORDER BY at DESC LIMIT 400").all();
  const set = new Set((evs || []).map(x => localDay(x.at)));
  let streak = 0, cur = new Date(today + 'T00:00:00Z');
  if (!set.has(today)) cur = new Date(cur.getTime() - 864e5);  // 今天没学则从昨天起算，不清零
  while (set.has(cur.toISOString().slice(0, 10))) { streak++; cur = new Date(cur.getTime() - 864e5); }
  return { due: due?.n || 0, learned: learned?.n || 0, mastered: mastered?.n || 0,
           reviews: reviews?.n || 0, retention: ret?.r != null ? Math.round(ret.r * 100) : null, streak };
}
function vitalsCard(v) {
  const cell = (n, l) => `<div class="vital"><div class="n">${n}</div><div class="l">${l}</div></div>`;
  return `<div class="card"><h2>学习数据</h2><div class="vitals">
    ${cell(v.streak, '连续天数')}${cell(v.due, '待复习')}${cell(v.mastered, '已掌握')}${cell(v.learned, '学习中')}${cell(v.retention != null ? v.retention + '%' : '—', '回忆达标率')}</div>
    ${v.due > 0 ? `<p style="margin-top:10px"><a class="pill-link" href="/review">开始复习（${v.due} 项到期）→</a></p>` : ''}</div>`;
}
const STUDY_JS = `<script>async function study(btn){btn.disabled=true;var o=btn.textContent;btn.textContent='加入中…';
try{var res=await fetch('/api/study/'+encodeURIComponent(btn.dataset.id),{method:'POST'});var j=await res.json();
btn.textContent=j.already?'已在队列':'已加入复习';}catch(e){btn.textContent='失败';btn.disabled=false;}}</script>`;
// ───────────────────────── ChatGPT 深度追问（带上当前条目，让 ChatGPT 联网深搜 + 深度思考 + 给 surprise） ─────────────────────────
const CHATGPT_URL = 'https://chatgpt.com/';
function deepDivePrompt(item) {
  const L = ['请对下面这份研究内容做一次「联网深度检索 + 深度思考」的顶级专业讲解。', '', '【标题】' + (item.title || '')];
  if (item.authors) L.push('【作者】' + item.authors);
  if (item.categories) L.push('【类目】' + item.categories);
  if (item.url) L.push('【原文】' + item.url);
  if (item.summary) L.push('【摘要】' + String(item.summary).slice(0, 600));
  L.push('', '我的要求：',
    '1. 先联网深度搜索：遍历相关论文、权威综述、官方资料与最新进展，交叉验证，并附可核查来源链接。',
    '2. 再深度思考：讲清它要解决的真问题、核心方法与关键假设、真正的创新点，以及局限与争议。',
    '3. 面向一个想彻底学懂的人，做详细、专业、全面、有深度的讲解，复杂处配恰当类比。',
    '4. 给我一些 surprise：意料之外的关联、反直觉的结论、以及大多数人会忽略的角度。',
    '5. 结尾给「若要继续深入，接下来该读什么 / 做什么」的清单。');
  return L.join('\n');
}
function deepDiveTopicPrompt(q) {
  return ['请围绕下面这个主题做一次「联网深度检索 + 深度思考」的专业讲解：', '', '【主题】' + q, '',
    '要求：联网遍历权威来源并交叉验证、附可核查链接；讲清来龙去脉、核心概念、最新进展与争议；面向想学懂的人做详细全面有深度的讲解、复杂处用类比；给我一些意料之外的 surprise；结尾给继续深入的阅读/行动清单。'].join('\n');
}
// hints=search 提示 ChatGPT 预选联网搜索（被忽略也无妨，提示词已明确要求联网深搜）
const chatgptHref = (prompt) => CHATGPT_URL + '?hints=search&q=' + encodeURIComponent(prompt);
function deepDiveBtn(item, label) {
  return `<a class="deep-btn" href="${esc(chatgptHref(deepDivePrompt(item)))}" target="_blank" rel="noopener noreferrer" title="把这条的信息带到 ChatGPT，让它联网深搜 + 深度讲解并给你一些 surprise">🔮 ${esc(label || '让 ChatGPT 全网深度追问')}</a>`;
}
function lessonHTML(lesson) {
  if (!lesson) return '';
  return JSON.parse(lesson.sections_json).map((s, i) =>
    `<h3>${i + 1}. ${esc(s.title)}</h3>${(s.sentences || []).map(x => `<p>${esc(x.text)}</p>`).join('')}`).join('');
}
function itemListHTML(items, { study = true } = {}) {
  if (!items.length) return '<p class="mt">暂无条目。</p>';
  return items.map(it => `<div class="itemrow"><div class="body">
    <a href="/item/${encodeURIComponent(it.id)}">${esc(it.title.slice(0, 110))}</a>
    <div class="mt">${esc(BOARD_NAMES[it.board_id] || it.board_id || '')}${it.published_at ? ' · ' + esc(it.published_at.slice(0, 10)) : ''} · <a href="${safeHref(it.url)}" rel="noopener">原文</a></div>
    </div>${study ? `<button class="btn-sm" data-id="${esc(it.id)}" onclick="study(this)">学这个</button>` : ''}</div>`).join('');
}
// 可复用的主动回忆评分组件（reveal 内容 + 四档评分 + 脚本）
function graderHTML(itemId, revealInner, nextHref) {
  return `<div class="card"><h2>主动回忆</h2>
    <p class="mt">先合上内容自己复述，再点「显示」核对，然后如实自评。评分即时进 FSRS 排程。</p>
    <button class="btn-sm" id="revealBtn" onclick="document.getElementById('revealBox').hidden=false;this.hidden=true">显示答案/讲义</button>
    <div class="reveal" id="revealBox" hidden>${revealInner || '<p class="mt">该条目暂无讲义，请点原文精读后自评。</p>'}</div>
    <div class="gradeRow">${[[1, '忘了'], [2, '困难'], [3, '良好'], [4, '轻松']].map(([g, l]) =>
      `<button onclick="grade(${g},this)" aria-label="评分：${l}">${l}</button>`).join('')}</div>
    <p id="r" class="mt" role="status"></p>
    <script>var _grading=false,_pend=null;
      function grade(g,btn){if(_grading)return;_grading=true;var row=document.querySelectorAll('.gradeRow button'),r=document.getElementById('r');
        row.forEach(function(b){b.classList.remove('picked');b.disabled=true;});btn.classList.add('picked');r.removeAttribute('data-state');var left=4;
        function draw(){r.innerHTML='已选「'+btn.textContent+'」，<b>'+left+'</b>s 后记录　<button type="button" class="btn-sm undo" onclick="gradeUndo()">撤销</button>';}
        draw();_pend=setInterval(function(){left--;if(left<=0){clearInterval(_pend);_pend=null;gradeCommit(g,btn);}else draw();},1000);}
      function gradeUndo(){if(_pend){clearInterval(_pend);_pend=null;}document.querySelectorAll('.gradeRow button').forEach(function(b){b.classList.remove('picked');b.disabled=false;});
        var r=document.getElementById('r');r.setAttribute('data-state','');r.textContent='已撤销，未记录。';_grading=false;}
      async function gradeCommit(g,btn){var r=document.getElementById('r');btn.setAttribute('aria-busy','true');r.textContent='记录中…';
        try{var res=await fetch('/api/grade/'+encodeURIComponent(${jsStr(itemId)})+'/'+g,{method:'POST'});if(!res.ok)throw new Error(res.status);var j=await res.json();
          btn.removeAttribute('aria-busy');r.setAttribute('data-state','ok');
          r.textContent=j.duplicate?('今天已评过（事件 #'+j.id+'），未重复计。'):('已记录 → 下次复习 '+j.due_at+'（间隔 '+j.interval+' 天，证据态：'+j.evidence_state+'）');
          ${nextHref ? `setTimeout(function(){location.href=${jsStr(nextHref)}},900);` : ''}}catch(e){btn.removeAttribute('aria-busy');r.setAttribute('data-state','err');r.textContent='记录失败，请重试。';
          document.querySelectorAll('.gradeRow button').forEach(function(b){b.disabled=false;});_grading=false;}}
    </script></div>`;
}

// ───────────────────────── 复习会话 /review ─────────────────────────
async function reviewPage(env) {
  const now = nowISO();
  const v = await computeVitals(env);
  const dueRow = await env.DB.prepare(
    "SELECT r.*, i.title, i.summary, i.url FROM cn_reviews r JOIN cn_items i ON i.id=r.item_id WHERE r.due_at<=? AND r.reps>0 ORDER BY r.due_at ASC LIMIT 1").bind(now).first();
  let body = vitalsCard(v);
  if (dueRow) {
    const lesson = await env.DB.prepare("SELECT * FROM cn_lessons WHERE item_id=? ORDER BY created_at DESC LIMIT 1").bind(dueRow.item_id).first();
    const reveal = lesson ? lessonHTML(lesson) : `<p>${esc((dueRow.summary || '').slice(0, 500))}</p>`;
    body += `<div class="card"><p class="mt">还有 ${v.due} 项到期</p><h1>${esc(dueRow.title)}</h1>
      <p class="mt"><a href="${safeHref(dueRow.url)}" rel="noopener">原文</a> · <a href="/item/${encodeURIComponent(dueRow.item_id)}">详情</a></p>
      <p style="margin:4px 0 0">${deepDiveBtn(dueRow)}</p></div>`;
    body += graderHTML(dueRow.item_id, reveal, '/review');
  } else {
    body += `<div class="card"><h1>复习完成 🎉</h1><p class="mt">当前没有到期的复习项。去 <a href="/">今天</a> 学一篇，或在 <a href="/radar">雷达</a> / 搜索里挑条目「学这个」加入队列。</p></div>`;
  }
  const { results: queue } = await env.DB.prepare(
    "SELECT r.due_at, r.evidence_state, i.title, i.id item_id FROM cn_reviews r LEFT JOIN cn_items i ON i.id=r.item_id WHERE r.reps>0 ORDER BY r.due_at ASC LIMIT 60").all();
  const rows = (queue || []).map(r => `<tr><td><a href="/item/${encodeURIComponent(r.item_id || '')}">${esc((r.title || r.item_id || '').slice(0, 64))}</a></td>
    <td><span class="badge">${esc(r.evidence_state || '—')}</span></td><td class="mt">${esc((r.due_at || '').slice(0, 10))}</td></tr>`).join('');
  body += `<div class="card"><h2>复习队列</h2><table><tr><th>条目</th><th>证据态</th><th>下次复习</th></tr>${rows || '<tr><td colspan=3>队列为空。</td></tr>'}</table></div>`;
  return PAGE('/review', body, { title: '复习' });
}

// ───────────────────────── 板块浏览 /board/:id ─────────────────────────
async function boardPage(env, boardId, offset) {
  const board = REGISTRY.find(b => b.board === boardId) || (boardId === 'board5' ? AGG_BOARD : null);
  if (!board) return null;
  const name = board.name || BOARD_NAMES[boardId];
  const PAGE_SIZE = 50;
  const { results: items } = await (boardId === 'board5'
    ? env.DB.prepare("SELECT * FROM cn_items ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT ? OFFSET ?").bind(PAGE_SIZE + 1, offset)
    : env.DB.prepare("SELECT * FROM cn_items WHERE board_id=? ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT ? OFFSET ?").bind(boardId, PAGE_SIZE + 1, offset)).all();
  const more = (items || []).length > PAGE_SIZE;
  const shown = (items || []).slice(0, PAGE_SIZE);
  let body = `<div class="card"><h1>${esc(name)}</h1><p class="mt"><a href="/radar">← 前沿雷达</a></p>
    ${itemListHTML(shown)}
    <p style="margin-top:12px">${offset > 0 ? `<a class="pill-link" href="/board/${boardId}?offset=${Math.max(0, offset - PAGE_SIZE)}">← 上一页</a>` : ''}
    ${more ? `<a class="pill-link" href="/board/${boardId}?offset=${offset + PAGE_SIZE}">下一页 →</a>` : ''}</p></div>`;
  return PAGE('/radar', body + STUDY_JS, { title: name });
}

// ───────────────────────── 搜索 /search ─────────────────────────
async function searchPage(env, q) {
  q = (q || '').trim().slice(0, 80);
  let body = `<div class="card"><h1>搜索</h1><p class="mt">在候选库标题与摘要里搜索。</p>`;
  if (q) {
    const like = '%' + q.replace(/[\\%_]/g, m => '\\' + m) + '%';  // 先转义 \ 本身（ESCAPE 字符），再转义 % _
    const { results } = await env.DB.prepare(
      "SELECT * FROM cn_items WHERE title LIKE ?1 ESCAPE '\\' OR summary LIKE ?1 ESCAPE '\\' ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 40").bind(like).all();
    body += `<p class="mt">「${esc(q)}」找到 ${(results || []).length} 条${(results || []).length === 40 ? '（仅显示前 40）' : ''}</p>
      <p style="margin:2px 0 6px"><a class="deep-btn ghost" href="${esc(chatgptHref(deepDiveTopicPrompt(q)))}" target="_blank" rel="noopener noreferrer">🔮 让 ChatGPT 全网深度检索这个主题</a></p>
      ${itemListHTML(results || [])}`;
  } else body += '<p class="mt">在右上角搜索框输入关键词。</p>';
  body += '</div>';
  return PAGE('/search', body + STUDY_JS, { title: '搜索' + (q ? '：' + q : ''), q });
}

// ───────────────────────── 往期精选 /history ─────────────────────────
async function historyPage(env) {
  const { results } = await env.DB.prepare(
    "SELECT s.*, i.title FROM cn_selections s LEFT JOIN cn_items i ON i.id=s.item_id ORDER BY s.as_of_date DESC LIMIT 40").all();
  const rows = (results || []).map(s => s.abstain
    ? `<tr><td class="mt">${esc(s.as_of_date)}</td><td colspan=2><span class="badge info">弃权</span> ${esc((s.abstain_reason || '').slice(0, 60))}</td></tr>`
    : `<tr><td class="mt">${esc(s.as_of_date)}</td><td><a href="/item/${encodeURIComponent(s.item_id || '')}">${esc((s.title || s.item_id || '').slice(0, 70))}</a></td>
       <td class="mt">${esc(BOARD_NAMES[s.board_id] || '')} · ${s.score != null ? Number(s.score).toFixed(0) : '—'}</td></tr>`).join('');
  return PAGE('/history', `<div class="card"><h1>往期精选</h1>
    <table><tr><th>日期</th><th>标题</th><th>板块·分</th></tr>${rows || '<tr><td colspan=3>暂无。</td></tr>'}</table></div>`, { title: '往期精选' });
}

// ───────────────────────── 条目详情 /item/:id ─────────────────────────
async function itemPage(env, id) {
  const item = await env.DB.prepare("SELECT * FROM cn_items WHERE id=?").bind(id).first();
  if (!item) return null;
  const lesson = await env.DB.prepare("SELECT * FROM cn_lessons WHERE item_id=? ORDER BY created_at DESC LIMIT 1").bind(id).first();
  const review = await env.DB.prepare("SELECT * FROM cn_reviews WHERE item_id=?").bind(id).first();
  let body = `<div class="card"><p class="mt"><a href="/board/${esc(item.board_id)}">← ${esc(BOARD_NAMES[item.board_id] || item.board_id)}</a></p>
    <h1>${esc(item.title)}</h1>
    <p class="mt">${esc(item.authors || '')}${item.categories ? ' · ' + esc(item.categories) : ''}${item.published_at ? ' · ' + esc(item.published_at.slice(0, 10)) : ''} · <a href="${safeHref(item.url)}" rel="noopener">原文</a>${review ? ' · 证据态 ' + esc(review.evidence_state) : ''}</p>
    ${item.summary ? `<p>${esc(item.summary)}</p>` : ''}
    ${review ? '' : `<button class="btn-sm" data-id="${esc(item.id)}" onclick="study(this)">加入复习队列</button>`}
    <p style="margin:8px 0 0">${deepDiveBtn(item)}</p></div>`;
  if (lesson) body += `<div class="card"><h2>讲义</h2>${lessonHTML(lesson)}</div>`;
  if (review) body += graderHTML(item.id, lesson ? lessonHTML(lesson) : `<p>${esc((item.summary || '').slice(0, 500))}</p>`, null);
  return PAGE('/', body + STUDY_JS, { title: item.title.slice(0, 40) });
}

async function studyItem(env, id) {
  const item = await env.DB.prepare("SELECT id FROM cn_items WHERE id=?").bind(id).first();
  if (!item) return { error: 'not found', status: 404 };
  const existing = await env.DB.prepare("SELECT item_id FROM cn_reviews WHERE item_id=?").bind(id).first();
  if (existing) return { already: true };
  await scheduleNewCard(env, id);
  // 建卡后 reps=0；给它一次即时可复习（今天到期），让「学这个」立刻能进复习流
  await env.DB.prepare("UPDATE cn_reviews SET reps=1, evidence_state='学习中', last_review=?, due_at=? WHERE item_id=? AND reps=0")
    .bind(nowISO(), nowISO(), id).run();
  return { ok: true };
}

function notFoundPage() {
  return PAGE('/', `<div class="card"><h1>页面不存在</h1><p class="mt">没找到这个页面。回 <a href="/">今天</a> 看看。</p></div>`, { title: '404' });
}

// ───────────────────────── 入口 ─────────────────────────
const SEC_HEADERS = {
  'x-content-type-options': 'nosniff',
  'referrer-policy': 'strict-origin-when-cross-origin',
  'content-security-policy': "default-src 'self'; img-src 'self' data:; media-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
};
// ───────────────────────── T081 RUM / Core Web Vitals（按 theme/route/device/network 分段）─────────────────────────
// NOT_DEPLOYED：客户端在 router 层注入（不改 PAGE 壳/主题/动效层的任何合同哈希）；端点写新表 cn_rum，不动既有生产数据。
// 采集 LCP/CLS/INP（INP 用最大交互时延近似），随页面隐藏 sendBeacon。达标判定在离线查询工具里做，且无数据不声称达标。
const RUM_ENABLED = true;              // 采集开关（部署后生效；关=不注入客户端脚本、端点 202 忽略）
const RUM_SAMPLE = 1;                  // 采样率 [0,1]（DIR-007 预算：可下调以降 D1 写入）
const RUM_METRICS = { LCP: [0, 120000], INP: [0, 60000], CLS: [0, 100] };   // 每指标合理量程（毫秒 / 无量纲）
const RUM_THEMES = ['warm', 'minimal', 'fresh', 'techno', 'cosmos', 'forest'];
const RUM_DEVICES = ['mobile', 'tablet', 'desktop'];
const RUM_JS = `(function(){try{if(!('PerformanceObserver' in window))return;
var sent={},d={LCP:null,CLS:0,INP:0};
function route(){var p=location.pathname;if(p==='/'||p==='/today')return'today';if(p==='/review'||p==='/queue')return'review';if(p.indexOf('/item/')===0)return'item';if(p.indexOf('/board/')===0)return'board';var s=p.replace('/','').split('/')[0];return s||'today';}
function device(){var w=innerWidth||document.documentElement.clientWidth;return w<600?'mobile':(w<1024?'tablet':'desktop');}
function net(){var c=navigator.connection;return(c&&c.effectiveType)||'unknown';}
function obs(t,cb,thr){try{var o=new PerformanceObserver(function(l){l.getEntries().forEach(cb);});var opt={type:t,buffered:true};if(thr)opt.durationThreshold=thr;o.observe(opt);}catch(e){}}
obs('largest-contentful-paint',function(e){d.LCP=e.renderTime||e.startTime;});
obs('layout-shift',function(e){if(!e.hadRecentInput)d.CLS+=e.value;});
obs('event',function(e){if(e.duration>d.INP)d.INP=e.duration;},40);
function send(m,v){if(v==null||!isFinite(v)||sent[m])return;sent[m]=1;try{navigator.sendBeacon('/api/rum',JSON.stringify({metric:m,value:Math.round(v*1000)/1000,theme:document.documentElement.getAttribute('data-theme')||'warm',route:route(),device:device(),network:net()}));}catch(e){}}
function flush(){send('LCP',d.LCP);send('CLS',d.CLS);send('INP',d.INP);}
addEventListener('visibilitychange',function(){if(document.visibilityState==='hidden')flush();});
addEventListener('pagehide',flush);
}catch(e){}})();`;
// pure validate + sample (roll passed in so it is deterministic/testable; endpoint passes Math.random())
function rumIngest(payload, roll) {
  if (!RUM_ENABLED) return { ok: false, reason: 'disabled' };
  if (!payload || typeof payload !== 'object') return { ok: false, reason: 'bad_payload' };
  const rng = RUM_METRICS[payload.metric];
  if (!rng) return { ok: false, reason: 'bad_metric' };
  const v = Number(payload.value);
  if (!isFinite(v) || v < rng[0] || v > rng[1]) return { ok: false, reason: 'bad_value' };
  if (!(roll <= RUM_SAMPLE)) return { ok: false, reason: 'sampled_out' };
  const theme = RUM_THEMES.indexOf(payload.theme) >= 0 ? payload.theme : 'other';
  const device = RUM_DEVICES.indexOf(payload.device) >= 0 ? payload.device : 'other';
  const route = (String(payload.route || 'other').slice(0, 32).replace(/[^a-zA-Z0-9_-]/g, '')) || 'other';
  const network = (String(payload.network || 'unknown').slice(0, 16).replace(/[^a-zA-Z0-9_.-]/g, '')) || 'unknown';
  return { ok: true, row: { metric: payload.metric, value: v, theme, device, route, network } };
}

// ───────────────────────── T082 环境动效性能（不改可见时视觉语义）─────────────────────────
// router 层注入（不碰任何主题/动效合同哈希）：①页面隐藏/后台→暂停环境动效（省 CPU/电，离屏零渲染）；
// ②低端设备（内存/核数低或省流量）→ 降级最重的环境层（meteor/band 隐藏、星云简化），但前景（按钮反馈）不消失。
// 唯一改动合同的是 @keyframes meteor（left/top→transform，屏幕路径等价、GPU 合成），走 T078 approved-change。
// selectors use the cosmos-unique leaf classes (meteor/band/neb, not theme-prefixed ambience selectors) so
// this script's text can never be mis-parsed as a CSS rule by the T077 contract extractor.
const FX_PERF_JS = `(function(){try{var q=function(s){return document.querySelectorAll(s);};
function run(on){q('.fx *').forEach(function(e){e.style.animationPlayState=on?'':'paused';});}
document.addEventListener('visibilitychange',function(){run(document.visibilityState==='visible');});
if(document.visibilityState!=='visible')run(false);
var dm=navigator.deviceMemory,hc=navigator.hardwareConcurrency,sd=navigator.connection&&navigator.connection.saveData;
if((dm&&dm<=4)||(hc&&hc<=4)||sd){document.documentElement.setAttribute('data-fx-lite','1');
q('.meteor,.band').forEach(function(e){e.style.display='none';});
q('.neb').forEach(function(e){e.style.filter='blur(28px)';e.style.opacity='.4';});}
}catch(e){}})();`;

const htmlResp = (html, status = 200) => new Response(html.replace('</body>', '<script>' + FX_PERF_JS + (RUM_ENABLED ? RUM_JS : '') + '</script></body>'), {
  // no-store（不是 no-cache）：这些浏览器对 no-cache 仍会缓存并不重新校验，导致用户一直看到旧页面、拿不到新部署。
  // no-store 强制每次都重新拉取，保证改动即时生效。
  status, headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store, must-revalidate', ...SEC_HEADERS },
});
const jsonResp = (obj, status = 200) => new Response(JSON.stringify(obj), {
  status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store', ...SEC_HEADERS },
});

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const p = url.pathname;
    try {
      if (p === '/favicon.ico') return new Response('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y="82" font-size="82">📚</text></svg>', { headers: { 'content-type': 'image/svg+xml', 'cache-control': 'public, max-age=86400' } });
      if (p === '/robots.txt') return new Response('User-agent: *\nDisallow:\n', { headers: { 'content-type': 'text/plain' } });
      if (p === '/build.json') return jsonResp(BUILD);
      if (p === '/api/a0-canary') {
        // S3-P03-T040 非破坏性 canary：实抓 gov.cn 政策原文（1 子请求）→ 应用 Board 3 A0 门 → 报告官方证据率。
        // 不写生产（只读预览）。回滚 = BOARD3_A0_ONLY=false 一次部署。
        let official = [];
        try {
          const r = await fetch('https://www.gov.cn/zhengce/xxgk/', { headers: { 'user-agent': UA }, cf: { cacheTtl: 300 } });
          const h = await r.text();
          const re = /href="(https?:\/\/[^"]*\/zhengce\/content\/[^"]+\.htm)"[^>]*>([^<]{6,80})/g; let m;
          const seen = new Set();
          while ((m = re.exec(h)) && official.length < 8) {
            if (seen.has(m[1])) continue; seen.add(m[1]);
            const d = /\/(\d{4})-(\d{1,2})\/(\d{1,2})\//.exec(m[1]);
            official.push({ source_id: 'gov-cn-policy', board_id: 'board3', title: m[2].trim(), url: m[1],
                            date: d ? `${d[1]}-${String(+d[2]).padStart(2, '0')}-${String(+d[3]).padStart(2, '0')}` : null,
                            a0_eligible: a0Board3Eligible({ board_id: 'board3', source_id: 'gov-cn-policy', url: m[1] }) });
          }
        } catch (e) { official = []; }
        const { results: b3media } = await env.DB.prepare(
          "SELECT id,source_id,title,url FROM cn_items WHERE board_id='board3' ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 200").all();
        const mediaDemoted = (b3media || []).filter(it => !a0Board3Eligible(it)).length;
        const officialEligible = official.filter(o => o.a0_eligible).length;
        return jsonResp({
          canary: 'board3_a0_view', flag_state: BOARD3_A0_ONLY ? 'ON' : 'OFF (production unchanged)',
          non_destructive: true, note: 'reads live gov.cn policy + current DB; writes nothing to production',
          official_original_items_found: official.length, official_eligible: officialEligible,
          board3_media_in_db: (b3media || []).length, board3_media_demoted_to_discovery: mediaDemoted,
          official_evidence_rate: official.length ? (officialEligible / official.length) : null,
          media_evidence_rate_under_gate: 0,
          sample_official: official.slice(0, 3),
          rollback: 'set BOARD3_A0_ONLY=false and redeploy (one deploy); flag currently ' + (BOARD3_A0_ONLY ? 'ON' : 'OFF'),
          owner_gate: 'S3 Exit approved A0 promotion; full flip pending A0 adapters wired to worker + real 14-day shadow (DIR-007 budgeted)',
        });
      }

      if (request.method === 'POST') {
        if (p.startsWith('/api/grade/')) {
          const [, , , idEnc, gradeRaw] = p.split('/');
          const grade = parseInt(gradeRaw, 10);
          if (!idEnc || !(grade >= 1 && grade <= 4)) return jsonResp({ error: 'bad request' }, 422);
          return jsonResp(await gradeRecall(env, decodeURIComponent(idEnc), grade));
        }
        if (p.startsWith('/api/study/')) {
          const id = decodeURIComponent(p.slice('/api/study/'.length));
          if (!id) return jsonResp({ error: 'bad request' }, 422);
          const r = await studyItem(env, id);
          return jsonResp(r, r.status || 200);
        }
        if (p === '/api/raw-selftest') {
          // S2-P01-T022 验收：写同一测试字节两次 -> 第二次 deduped（幂等）；返回预算用量。不受 RAW_DUALWRITE 全局 flag 限制（显式管理端验证）。
          if (!env.RAW) return jsonResp({ error: 'R2 binding RAW missing' }, 503);
          _rawWrites = 0; _rawUsage = null; // 每次 selftest 重置上限计数，保证验证可复现
          const bytes = new TextEncoder().encode('ADP-RAW-SELFTEST ' + '<html>immutable evidence dualwrite idempotency check</html>');
          const buf = bytes.buffer.slice(bytes.byteOffset, bytes.byteOffset + bytes.byteLength);
          const a = await dualWriteArtifact(env, 'selftest', 'https://adp.linzezhang.com/api/raw-selftest', buf);
          const b = await dualWriteArtifact(env, 'selftest', 'https://adp.linzezhang.com/api/raw-selftest', buf);
          const u = await r2Usage(env, r2Month());
          return jsonResp({ first: a, second: b, idempotent: (b.deduped === true && a.key === b.key), budget_usage_month: u, budget_limits: { classA: R2_BUDGET.classAPerMonth, classB: R2_BUDGET.classBPerMonth, storageBytes: R2_BUDGET.storageBytes } });
        }
        if (p === '/api/run') return jsonResp(await runDaily(env, 'manual'));
        if (p === '/api/rum') {
          // T081 RUM/CWV 采集端点：验证+采样后写 cn_rum（新表，不动既有生产数据）。忽略即 202（beacon 无需重试）。
          let payload = null; try { payload = await request.json(); } catch (e) { payload = null; }
          const res = rumIngest(payload, Math.random());
          if (!res.ok) return jsonResp({ ignored: res.reason }, ['bad_payload', 'bad_metric', 'bad_value'].includes(res.reason) ? 422 : 202);
          await env.DB.prepare('CREATE TABLE IF NOT EXISTS cn_rum (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, metric TEXT, value REAL, theme TEXT, route TEXT, device TEXT, network TEXT, build_id TEXT)').run();
          await env.DB.prepare('INSERT INTO cn_rum (ts,metric,value,theme,route,device,network,build_id) VALUES (?,?,?,?,?,?,?,?)')
            .bind(nowISO(), res.row.metric, res.row.value, res.row.theme, res.row.route, res.row.device, res.row.network, BUILD.build_id).run();
          return jsonResp({ ok: true }, 202);
        }
        return jsonResp({ error: 'not found' }, 404);
      }

      let html, status = 200;
      if (p === '/' || p === '/today') html = await todayPage(env);
      else if (p === '/review' || p === '/queue') html = await reviewPage(env);
      else if (p === '/radar') html = await radarPage(env);
      else if (p === '/system') html = await systemPage(env);
      else if (p === '/history') html = await historyPage(env);
      else if (p === '/search') html = await searchPage(env, url.searchParams.get('q') || '');
      else if (p.startsWith('/board/')) html = await boardPage(env, p.slice('/board/'.length), Math.max(0, parseInt(url.searchParams.get('offset') || '0', 10) || 0));
      else if (p.startsWith('/item/')) html = await itemPage(env, decodeURIComponent(p.slice('/item/'.length)));
      else html = null;
      if (html === null) { html = notFoundPage(); status = 404; }
      return htmlResp(html, status);
    } catch (e) {
      return htmlResp(PAGE('/', `<div class="card"><h1>出错了</h1><p class="mt">${esc(e.message || 'error')}——刷新或回 <a href="/">今天</a>。</p></div>`, { title: '错误' }), 500);
    }
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(runDaily(env, 'cron'));
  },
};
