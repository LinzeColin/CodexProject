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
const BUILD = { build_id: 'dc91b5b221d0', source_sha256: 'dc91b5b221d00a80d2ed67f059cb4404d9afc7dbecbed2ec4bdde148c863a606', schema_version: 'cn_v0_3', built_at: '2026-07-17' };

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
    // ── S3 A0 官方原文（P04 接入每日 cron）──
    // 只接入「边缘可达 + 静态可解析」的官方源；不可达的诚实地不接（见 known_gaps）：
    //   gov-cn-fagui 列表页 HTTP 403（拦截）；nda-gov 仅 193 字节 JS 跳转空壳（S3 适配器已标 live_blocked=True）。
    { id: 'gov-cn-policy', name: '国务院 · 政策文件（官方原文）', platform: '中国政府网 gov.cn', website: 'https://www.gov.cn', method: 'a0', list: 'https://www.gov.cn/zhengce/xxgk/', official: 1, cadence: '每日' },
    { id: 'stats-gov', name: '国家统计局 · 最新发布（官方原文）', platform: 'stats.gov.cn', website: 'https://www.stats.gov.cn', method: 'a0', list: 'https://www.stats.gov.cn/sj/zxfb/', official: 1, cadence: '每日' },
    { id: 'cac-gov', name: '中央网信办（官方原文）', platform: 'cac.gov.cn', website: 'https://www.cac.gov.cn', method: 'a0', list: 'https://www.cac.gov.cn/', official: 1, cadence: '每日' },
    { id: 'ndrc-gov', name: '国家发改委 · 政策发布（官方原文）', platform: 'ndrc.gov.cn', website: 'https://www.ndrc.gov.cn', method: 'a0', list: 'https://www.ndrc.gov.cn/xxgk/', official: 1, cadence: '每日' },
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
const OPENALEX_WORKS = 'https://api.openalex.org/works';   // T063 研究元数据
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

  // A0 官方原文（board3）：与 RSS 同样的健康/自动停用/自愈纪律，独立小额子请求预算。
  const a0all = [];
  for (const b of REGISTRY) for (const s of b.sources) if (s.method === 'a0') a0all.push({ b: b.board, s });
  const a0eligible = a0all.filter(f => {
    const h = hmap[f.s.id];
    if (h?.health !== 'disabled_auto') return true;
    return !h.last_fetch || (Date.now() - Date.parse(h.last_fetch)) > 3 * 864e5;
  });
  a0eligible.sort((a, b) => (hmap[a.s.id]?.last_fetch || '').localeCompare(hmap[b.s.id]?.last_fetch || ''));
  const a0run = a0eligible.slice(0, A0_PER_RUN);
  const a0settled = await Promise.allSettled(a0run.map(f =>
    fetchFeedText(f.s.list, env, f.s.id).then(html => ({ f, items: parseA0(html, f.s.id) }))));
  let a0New = 0;
  for (let i = 0; i < a0run.length; i++) {
    const res = a0settled[i], f = a0run[i];
    if (res.status === 'fulfilled') {
      for (const it of res.value.items) {
        itemStmts.push(itemStmt(env, { id: 'a0:' + await sha1(f.s.id + '|' + it.url), board: f.b, source: f.s.id,
          kind: 'official', title: it.title, url: it.url, summary: '', categories: '', authors: '', published: it.published }));
        a0New++;
      }
      healthStmts.push(healthStmt(env, f.s.id, res.value.items.length > 0, hmap[f.s.id]?.consecutive_failures));
      if (!res.value.items.length) counts.degraded.push('a0:' + f.s.id + ':parsed0');
    } else {
      counts.degraded.push('a0:' + f.s.id);
      healthStmts.push(healthStmt(env, f.s.id, false, hmap[f.s.id]?.consecutive_failures));
    }
  }
  counts.a0_official = a0New;
  counts.a0_fetched = a0run.length;

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

// ───────────────────────── A0 官方原文抓取（S3 适配器接入生产 cron；board3） ─────────────────────────
// 只从列表页抽「链接 + 标题 + 日期」，不抓正文（每源 1 子请求，DIR-007 预算）。
// 日期只在能从 URL 真实读出时才给；新版 gov.cn /content/YYYYMM/ 只有年月没有日 → published_at 留空，绝不编造。
const A0_PER_RUN = 4;               // 每次 cron 最多抓的 A0 源数（覆盖全部 4 个源）。
// DIR-007 子请求核算（外部 fetch/次 cron）：arxiv 2 + biorxiv 1 + RSS 13 + A0 4 = 20，上限 50。
// D1/R2 属 internal services，另有 1000/次 的独立额度，不与这 50 混算。
const pad2 = (n) => String(+n).padStart(2, '0');
const A0_SOURCES = {
  'gov-cn-policy': {
    // 钉住 host：否则 gov.cn 列表页上的站外链接会被当作「官方原文」入库（a0Board3Eligible 按 source_id 放行，不再校验 host）。
    match: /^https:\/\/www\.gov\.cn\/zhengce\/content\/[^"']+\.htm$/,
    resolve: (u) => u,
    // 旧版 /2019-04/15/ 有完整日期；新版 /202607/ 只有年月 → null（不编造「日」）
    date: (u) => { const m = /\/(\d{4})-(\d{1,2})\/(\d{1,2})\//.exec(u); return m ? `${m[1]}-${pad2(m[2])}-${pad2(m[3])}` : null; },
  },
  'stats-gov': {
    match: /^\.\/\d{6}\/t\d{8}_\d+\.html$/,
    resolve: (u) => 'https://www.stats.gov.cn/sj/zxfb/' + u.slice(2),
    date: (u) => { const m = /t(\d{4})(\d{2})(\d{2})_/.exec(u); return m ? `${m[1]}-${m[2]}-${m[3]}` : null; },
  },
  'ndrc-gov': {
    // 发改委自有政策原文：./zcfb/tz/202607/t20260716_1406539.html（与 stats 同为 t{YYYYMMDD}_ 形态）
    match: /^\.\/[a-z/]+\/\d{6}\/t\d{8}_\d+\.html$/,
    resolve: (u) => 'https://www.ndrc.gov.cn/xxgk/' + u.slice(2),
    date: (u) => { const m = /t(\d{4})(\d{2})(\d{2})_/.exec(u); return m ? `${m[1]}-${m[2]}-${m[3]}` : null; },
  },
  'cac-gov': {
    match: /^\/\/www\.cac\.gov\.cn\/\d{4}-\d{2}\/\d{2}\/c_\d+\.htm$/,
    resolve: (u) => 'https:' + u,
    date: (u) => { const m = /\/(\d{4})-(\d{2})\/(\d{2})\//.exec(u); return m ? `${m[1]}-${m[2]}-${m[3]}` : null; },
  },
};
// 从列表页 HTML 解析 A0 条目：title 优先取 title 属性（stats 用单引号），否则取链接文字；
// 去重按解析后 URL；标题过短（如 cac 的「全文」跳转链）直接丢弃而不是入库垃圾。
function parseA0(html, sourceId) {
  const cfg = A0_SOURCES[sourceId];
  if (!cfg) return [];
  const out = [], seen = new Set();
  // 有界量词 + 不要求闭合 </a>（取到下一个 < 为止）→ 线性时间：未闭合 <a 洪水不会二次回溯（ReDoS）。
  const re = /<a\s([^>]{0,400})>([^<]{0,200})/g;
  let m;
  while ((m = re.exec(html)) && out.length < MAX_ITEMS_PER_FEED) {
    const attrs = m[1];
    const hm = /href=["']([^"']+)["']/.exec(attrs);
    if (!hm) continue;
    const href = hm[1].trim();
    if (!cfg.match.test(href)) continue;
    const url = cfg.resolve(href);
    if (seen.has(url)) continue;                       // 同一 href 常因响应式布局重复出现
    const t = /title=["']([^"']+)["']/.exec(attrs);
    const title = decodeEntities(stripTags(t ? t[1] : m[2]));   // 复用既有 helper（含实体解码）
    if (title.length < 6) continue;                    // 「全文」这类跳转链无有效标题 → 不入库
    seen.add(url);
    out.push({ title, url, published: cfg.date(href) });
  }
  return out;
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

// ───────────────────────── 关键事实卡（S1-P03-T016 确定性 Factsheet；缺失即空，绝不编造） ─────────────────────────
// 从条目已有字段（title/url/summary/categories/authors/published_at）确定性抽取稳定事实。
// 端口自 tools/extract_factsheet.py：不臆造，抽不到就不显示。纯展示层，不改数据/流水线。
const FS_DOI_RE = /10\.\d{4,9}\/[^\s"'<>]+/;
const FS_DOCNUM_RE = /[一-龥A-Za-z]{0,8}[〔[（(]\s*20\d{2}\s*[〕\]）)]\s*第?\s*\d+\s*号|第\s*\d+\s*号(?:令|公告)?/;
const FS_UNIT_RE = /\d[\d,.]{0,39}\s*(?:%|％|个百分点|亿元|万元|亿美元|亿|万|bps|个基点|美元|元)/g;  // {0,39}=有界量词→线性时间（数字串永不超 40 字符），防 ReDoS 二次回溯
function fsFirst(re, ...texts) { for (const t of texts) { if (!t) continue; const m = String(t).match(re); if (m) return m[0].trim(); } return null; }
function fsUnits(...texts) { const out = []; for (const t of texts) { if (!t) continue; const mm = String(t).match(FS_UNIT_RE); if (mm) for (const u of mm) { const v = u.trim(); if (!out.includes(v)) out.push(v); } } return out; }
function factsheet(item) {
  const board = item.board_id;
  // 输入长度兜底：确保抽取正则在请求路径恒为线性时间（防 ReDoS 二次回溯）；入库已截断，这里再本地保证。
  const title = (item.title || '').slice(0, 500), summary = (item.summary || '').slice(0, 2000);
  const facts = [];
  const date = (item.published_at || '').slice(0, 10);
  if (date) facts.push(['日期', date]);
  const doi = fsFirst(FS_DOI_RE, item.id, item.url, summary);
  if ((board === 'board1' || board === 'board2') && doi) facts.push(['DOI', doi.replace(/[).,;]+$/, '')]);
  if (board === 'board3') { const dn = fsFirst(FS_DOCNUM_RE, title, summary); if (dn) facts.push(['文号', dn]); }
  if (board === 'board3' || board === 'board4') { const u = fsUnits(title, summary); if (u.length) facts.push(['关键数字', u.slice(0, 3).join('、')]); }
  const auth = (item.authors || '').split(/[;；]/).map(a => a.trim()).filter(Boolean);
  if (auth.length > 1) facts.push(['作者', auth.length + ' 位']);
  return facts;
}
// ───────────────────────── T063 研究元数据（OpenAlex） ─────────────────────────
const META_PER_RUN = 12;      // 每次 cron 补多少条 —— ★单条查询：1 个 DOI = 1 个外部子请求★。
                              // ★DIR-007★：cron 现用 20/50，故 20+12 = 32/50，留 18 个余量。
                              // 为什么不是批量：P08 原本用 /works?filter=doi:a|b|c 一次查 50 个（只花 1 个子请求），
                              // 但那条路【在生产上是死的】—— 从 Cloudflare 边缘实测 429 ×3/3
                              // （Insufficient budget…，retry-after≈13 小时，mailto 不解决）：
                              // OpenAlex 按 IP 计预算，而 Workers 出口是共享数据中心 IP，预算早被耗尽。
                              // 同一边缘上单条 /works/doi:X 是 200 ×3/3。实测 12 条并行：2302ms、0 次 429。
                              // 代价如实记：约 600 条候选按 12/晚 要约 50 晚补完（批量原本 12 晚）——
                              // 但 12 条/晚 > 0 条/永远，而后者正是现在生产上的真实状态。
const META_SCAN = 200;        // 单板单次扫描的读取上限。★真正兜住这张表的是 KEEP_PER_BOARD=300 的保留策略★，
                              // 不是这个 LIMIT —— LIMIT 限的是返回行数，不是扫描量（复核 F2 纠正的假前提）。
const META_RETRY_DAYS = 7;    // 查过但没查到的，7 天后再试一次（新预印本可能还没被索引）
const META_FETCH_TIMEOUT_MS = 8000;   // 单条查询的超时。边缘实测单条 0.8–1.7s、12 条并行 2.3s，
                              // 故 8s 给足余量；上限的意义是【一个挂住的连接不许卡死 cron】——
                              // enrichMeta 跑在 selectDaily 之前，元数据是增强，不许拖垮当日精选。
const META_UA_MAILTO = 'adp@linzezhang.com';   // OpenAlex polite pool：带 mailto 才有稳定配额
const OA_LABEL = { gold: '金色OA', green: '绿色OA', hybrid: '混合OA', bronze: '青铜OA', diamond: '钻石OA' };
// ★metadata adapters★：只从【既有 id/url】确定性地解析 DOI；解析不出就返回 null —— 不猜、不构造。
// 每条正则都是线性的（无嵌套量词、无回溯陷阱），且都实测过真实线上 URL 形态。
function metaDoi(it) {
  const id = String(it && it.id || ''), url = String(it && it.url || '');
  let m;
  if ((m = /^arxiv:(\d{4}\.\d{4,5})/.exec(id))) return '10.48550/arxiv.' + m[1];
  if ((m = /arxiv\.org\/abs\/(\d{4}\.\d{4,5})/.exec(url))) return '10.48550/arxiv.' + m[1];
  if ((m = /^(?:biorxiv|medrxiv):(10\.\d{4,9}\/[^\s]{1,80})$/.exec(id))) return m[1];
  if ((m = /(?:biorxiv|medrxiv)\.org\/content\/(10\.\d{4,9}\/[0-9.]{1,40})/.exec(url))) return m[1];
  if ((m = /nature\.com\/articles\/([a-z]\d{5,6}-\d{3}-\d{4,6}-[a-z0-9]{1,3})/.exec(url))) return '10.1038/' + m[1];
  if ((m = /elifesciences\.org\/articles\/(\d{4,7})/.exec(url))) return '10.7554/elife.' + m[1];
  if ((m = /\/doi\/(?:full\/|abs\/|pdf\/)?(10\.\d{4,9}\/[^?#\s]{1,80})/.exec(url))) return metaNotAsset(m[1]);
  if ((m = /[?&]id=(10\.\d{4,9}\/[^&#\s]{1,80})/.exec(url))) return metaNotAsset(m[1]);
  return null;
}
// 附件链接（PLOS 的 article/file?id=<doi>.PDF 等）里的「DOI」其实是资源名，不是作品 DOI。
// 复核指出原实现会返回 10.1371/journal.pbio.3003906.PDF —— 那是**猜**。抽不准就弃权。
function metaNotAsset(doi) { return /\.(?:pdf|xml|docx?|zip|csv|tiff?|png|jpe?g|s\d{3})$/i.test(doi) ? null : doi; }
// OpenAlex 回给的 doi 是全 URL 且【小写化】的（NEJMoa2512275 -> nejmoa2512275），
// 故请求侧与响应侧必须用同一个小写裸 DOI 做键，否则整批都对不上（实测坑）。
const metaKey = d => String(d || '').toLowerCase().replace(/^https?:\/\/(?:dx\.)?doi\.org\//, '').trim();
async function metaTables(env) {
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS cn_item_meta (item_id TEXT PRIMARY KEY, doi TEXT, oa_id TEXT, work_type TEXT, is_preprint INTEGER, venue TEXT, venue_type TEXT, cited_by INTEGER, oa_status TEXT, pub_year INTEGER, authors_n INTEGER, found INTEGER NOT NULL DEFAULT 0, enriched_at TEXT NOT NULL)').run();
}
// 一次 cron 补一批。★任何失败都只降级、不抛★ —— 验收明写「增强失败不阻塞原始论文」。
async function enrichMeta(env, counts) {
  try {
    await metaTables(env);
    // 条目被 prune 掉后其元数据行是孤儿（复核指出该表只增不减）。按主键反查删除，不用 join。
    // ★必须无条件执行★：一旦放到「有新条目要补」的分支里，稳态（全部补完）下就永远不跑，
    // 而稳态恰恰就是孤儿堆积的时候 —— 我的第一版就是这么写的，被自己的测试当场抓到。
    await env.DB.prepare('DELETE FROM cn_item_meta WHERE NOT EXISTS (SELECT 1 FROM cn_items i WHERE i.id = cn_item_meta.item_id)').run();
    const cutoff = new Date(Date.now() - META_RETRY_DAYS * 864e5).toISOString();
    // ★一板一查，不用 board_id IN (...)★ —— 复核实测：IN (两个值) 会让计划**放弃**
    // idx_cn_items_board_recency (board_id, COALESCE(published_at,fetched_at) DESC, id DESC)，
    // 退化成 idx_cn_items_board + USE TEMP B-TREE FOR ORDER BY，即**先全排序再 LIMIT**：
    // LIMIT 限的是**返回行数，不是扫描量**。单值等值时索引自带顺序，无需临时 B 树。
    // （我原注释写的「行数有界」是**假前提**：真正兜住它的是 KEEP_PER_BOARD=300 的保留策略，
    //   board1+board2 合计约 600 行；不是这个 LIMIT。依据必须是真的，哪怕结论一样。）
    const q = board => env.DB.prepare(
      `SELECT id, url FROM cn_items WHERE board_id = ?1
         AND NOT EXISTS (SELECT 1 FROM cn_item_meta m WHERE m.item_id = cn_items.id AND (m.found = 1 OR m.enriched_at >= ?2))
       ORDER BY COALESCE(published_at, fetched_at) DESC, id DESC LIMIT ?3`).bind(board, cutoff, META_SCAN);
    const parts = await env.DB.batch([q('board1'), q('board2')]);
    const results = [].concat(...parts.map(p => (p && p.results) || []));
    // ★dedup rules★：多个条目可能解析到同一个 DOI（同一篇论文经不同 feed 进来）。
    // 按 DOI 归并成一个查询键，再把结果【广播回每个】条目 —— 既不重复计子请求，也不漏条目。
    const byDoi = new Map();
    for (const it of (results || [])) {
      const doi = metaKey(metaDoi(it));
      if (!doi) continue;
      if (!byDoi.has(doi)) byDoi.set(doi, []);
      byDoi.get(doi).push(it.id);
      if (byDoi.size >= META_PER_RUN) break;   // 子请求预算：一个 DOI 一个子请求
    }
    if (!byDoi.size) return;
    const dois = [...byDoi.keys()];
    // ★单条查询，并行★。每个 DOI 一个子请求（预算见 META_PER_RUN）。
    // 单条端点回的是【规范记录】，故 P08 的「同一 DOI 多条 work、最后一条赢、被引数会错」
    // （复核 F3：arxiv:1506.01497 回 2 条 18240/6274）随之消失 —— 不再需要响应侧去重。
    // 截断判定也一并删除：单条查询没有分页，不存在截断。
    // 复核 #7：select= 里必须带 id —— P10 的立论是「单条端点回的是【规范记录】」，
    // 而被丢掉的恰恰是那条规范记录的【身份】，oa_id 会恒为 NULL。带上它。
    const SEL = encodeURIComponent('id,doi,type,primary_location,cited_by_count,open_access,publication_year');
    const settled = await Promise.all(dois.map(async (doi) => {
      // 复核 #5：DOI 必须 URL 编码（P08 本来有，P10 第一版把它改回归了）。
      // OpenAlex 对畸形 DOI 回 404 —— 与「真的没收录」【无法区分】→ 会给真论文写 found=0。
      // 可达字符集是真的：biorxiv/medrxiv 的 id 形态允许 [^\s]{1,80}，/doi/ 形态允许 & 与 %。
      const u = OPENALEX_WORKS + '/doi:' + encodeURIComponent(doi) + '?mailto=' + encodeURIComponent(META_UA_MAILTO) + '&select=' + SEL;
      try {
        // 复核 #4：必须有超时。worker 别处都用 AbortSignal.timeout(15000/20000)，这里原本没有。
        // Promise.all 会等满 12 个 —— 一个挂住的连接会卡死 cron，而且是在 selectDaily 之前，
        // 即为了补元数据把【当日精选】搞没。元数据是增强，不许拖垮正事。
        const r = await fetch(u, { headers: { 'User-Agent': 'adp-cloud (mailto:' + META_UA_MAILTO + ')' },
                                   cf: { cacheTtl: 3600 }, signal: AbortSignal.timeout(META_FETCH_TIMEOUT_MS) });
        if (r.status === 404) return { doi, miss: true };          // 未收录：干净的 404 → 可以写 found=0
        if (!r.ok) return { doi, err: 'http' + r.status };         // 429/5xx：不知道，绝不写 found=0
        return { doi, work: await r.json() };
      } catch (e) { return { doi, err: e.name };  }                // 超时/网络异常同样是「不知道」
    }));
    const best = new Map();
    const errKinds = new Map();
    let errs = 0;
    for (const s of settled) {
      if (s.work) best.set(s.doi, s.work);
      else if (s.err) { errs++; errKinds.set(s.err, (errKinds.get(s.err) || 0) + 1); }   // 未知 → 向安全侧倒
    }
    // 复核 #8：★把状态码留住★。P08 推的是 meta:http429，P10 第一版抹成了 meta:err12 ——
    // 而 429 正是让 P08 隐形整整一轮的那个信号。厂商行为随时可能变（单实体 GET 现在不吃 filter= 的预算，
    // 那是【没写进文档的】行为），一旦复发，抹掉状态码会让它【很难被看见】。
    for (const [k, n] of errKinds) counts.degraded.push('meta:' + k + (n > 1 ? 'x' + n : ''));
    if (errs === dois.length) return;                              // 全挂：什么都别写
    const now = nowISO(), stmts = [], hit = new Set();
    const unknown = new Set(settled.filter(s => s.err).map(s => s.doi));
    for (const [key, w] of best) {
      const ids = byDoi.get(key);
      hit.add(key);
      const srcObj = (w.primary_location && w.primary_location.source) || {};
      const venueType = srcObj.type || null;
      // ★预印本/期刊不混淆★：OpenAlex 的 type=preprint 或载体 type=repository 即预印本。
      // ★两个条件必须是「或」，不是「且」★：复核实测 eLife 是 type=preprint 但 source.type=journal
      // （eLife 的 Reviewed Preprint 模式），arXiv/bioRxiv/medRxiv 则是 preprint+repository。
      // 我原先写的「实测全部命中 preprint+repository」是**假的**，结论侥幸没错而已 —— 依据不能是假的。
      const isPre = (w.type === 'preprint' || venueType === 'repository') ? 1 : 0;
      for (const id of ids) {
        stmts.push(env.DB.prepare(
          `INSERT INTO cn_item_meta (item_id,doi,oa_id,work_type,is_preprint,venue,venue_type,cited_by,oa_status,pub_year,authors_n,found,enriched_at)
           VALUES (?1,?2,?3,?4,?5,?6,?7,?8,?9,?10,?11,1,?12)
           ON CONFLICT(item_id) DO UPDATE SET doi=excluded.doi, oa_id=excluded.oa_id, work_type=excluded.work_type,
             is_preprint=excluded.is_preprint, venue=excluded.venue, venue_type=excluded.venue_type,
             cited_by=excluded.cited_by, oa_status=excluded.oa_status, pub_year=excluded.pub_year,
             authors_n=excluded.authors_n, found=1, enriched_at=excluded.enriched_at`)
          .bind(id, key, String(w.id || '').slice(0, 64) || null, String(w.type || '').slice(0, 32) || null, isPre,
                String(srcObj.display_name || '').slice(0, 120) || null, venueType ? String(venueType).slice(0, 32) : null,
                Number(w.cited_by_count) || 0, String((w.open_access && w.open_access.oa_status) || '').slice(0, 16) || null,
                Number(w.publication_year) || null, null, now));
      }
    }
    // 只给【确知未收录】的（HTTP 404）写 found=0，避免每晚重查同一批查不到的；META_RETRY_DAYS 后重试。
    // ★「不知道」（429/5xx/异常）绝不写 found=0★ —— 那等于把我们自己的失败栽赃成「OpenAlex 查不到」，
    // 而被误判的条目会随窗口下沉、几乎永不重试。未知一律留白，下次再来。
    for (const [doi, ids] of byDoi) {
      if (hit.has(doi) || unknown.has(doi)) continue;
      for (const id of ids) stmts.push(env.DB.prepare(
        'INSERT INTO cn_item_meta (item_id,doi,found,enriched_at) VALUES (?1,?2,0,?3) ON CONFLICT(item_id) DO UPDATE SET enriched_at=excluded.enriched_at')
        .bind(id, doi, now));
    }
    if (stmts.length) await env.DB.batch(stmts);
    counts.meta = { requested: byDoi.size, matched: hit.size, unknown: unknown.size || undefined };
  } catch (e) {
    // 降级即可：原始论文本来就在库里，元数据只是增强。绝不让它把 cron 带崩。
    counts.degraded.push('meta:' + e.name);
  }
}
// 给一批条目挂上元数据（只挂 found=1 的）。同样【绝不抛】。
async function attachMeta(env, items) {
  try {
    const list = (items || []).filter(Boolean);
    const ids = list.map(i => i.id).filter(Boolean);
    if (!ids.length) return items;
    const map = new Map();
    for (let i = 0; i < ids.length; i += 50) {          // 分块：别去顶 SQLite 的绑定变量上限
      const part = ids.slice(i, i + 50);
      const { results } = await env.DB.prepare(
        'SELECT * FROM cn_item_meta WHERE found=1 AND item_id IN (' + part.map((_, k) => '?' + (k + 1)).join(',') + ')')
        .bind(...part).all();
      for (const r of (results || [])) map.set(r.item_id, r);
    }
    for (const it of list) if (map.has(it.id)) it._meta = map.get(it.id);
  } catch (e) { /* 增强失败不阻塞原始论文：静默降级，页面照常渲染 */ }
  return items;
}
// ★只如实转述 OpenAlex 的口径，不加解释、不声称「研究论文」★（见文件头：Nature 新闻同样是 article）。
function metaFacts(meta) {
  if (!meta) return [];
  const out = [];
  if (meta.venue) out.push([meta.is_preprint ? '预印本' : '发表于', String(meta.venue)]);
  if (Number(meta.cited_by) > 0) out.push(['被引', Number(meta.cited_by) + ' 次']);
  const oa = meta.oa_status;
  if (oa && oa !== 'closed') out.push(['开放获取', OA_LABEL[oa] || String(oa)]);
  return out;
}
function factsheetHTML(item) {
  // 日期在各卡片元信息行已展示，展示层去重（factsheet() 仍保留 date 以忠实于 schema）。
  const facts = factsheet(item).filter(([k]) => k !== '日期');
  // T063：研究元数据来自【第三方 OpenAlex】，与「确定性抽取自原文」不是一回事，
  // 故用不同的 title 标注出处 —— 证据来源不能混为一谈。
  const meta = metaFacts(item && item._meta);
  if (!facts.length && !meta.length) return '';
  const b = (cls, title) => ([k, v]) => `<span class="badge${cls}" title="${title}">${esc(k)}：${esc(v)}</span>`;
  return `<p class="mt" style="margin-top:6px">${facts.map(b('', '确定性抽取自原文字段·缺失即空')).join('')}${meta.map(b(' ok', 'OpenAlex 研究元数据·第三方来源·非原文抽取')).join('')}</p>`;
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
      await enrichMeta(env, counts);   // T063：+1 个外部子请求（一批 50 条 DOI）；失败只降级
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
const NAV = [['/', '今天'], ['/review', '复习'], ['/radar', '前沿雷达'], ['/watchlist', '关注'], ['/library', '知识库'], ['/system', '系统']];
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
  await attachMeta(env, [item]);
  const hero = heroSection(sel, item, v, spark);
  if (sel.abstain) return PAGE('/', `<span id="todaymain"></span>` + vitalsCard(v) + `<div class="card"><h1>今日弃权</h1><p>${esc(sel.abstain_reason)}</p><p class="mt">决策日期 ${esc(sel.as_of_date)}——宁缺毋滥。可去 <a href="/radar">雷达</a> 挑条目「学这个」，或看 <a href="/history">往期</a>。</p></div>`, { hero });
  const lesson = await env.DB.prepare('SELECT * FROM cn_lessons WHERE item_id=? ORDER BY created_at DESC LIMIT 1').bind(sel.item_id).first();
  const review = await env.DB.prepare('SELECT * FROM cn_reviews WHERE item_id=?').bind(sel.item_id).first();
  let body = `<span id="todaymain"></span>` + vitalsCard(v) + `<div class="card"><h2>为什么今天选它</h2><p>${esc(sel.why)}</p>
    <p class="mt">决策日期 ${esc(sel.as_of_date)} · ${esc(BOARD_NAMES[sel.board_id] || sel.board_id || '')}${review ? ' · 证据态 ' + esc(review.evidence_state) : ''}</p></div>`;
  if (item) {
    body += `<div class="card"><h1>${esc(item.title)}</h1>
      <p class="mt">${esc(item.authors || '')}${item.categories ? ' · ' + esc(item.categories) : ''} · <a href="${safeHref(item.url)}" rel="noopener">原文</a></p>
      ${factsheetHTML(item)}
      <p style="margin:4px 0 2px">${deepDiveBtn(item)}</p>`;
    if (lesson) body += lessonHTML(lesson);   // T084 用中心化 lessonHTML（带证据/推断 provenance 标注）
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

// ───────────────────────── T043 覆盖与缺口（Source-Year-Month） ─────────────────────────
const COVERAGE_START = '2016-01';   // 「2016+ 可恢复历史」这条硬约束的起点
// ★判定是穷尽且确定的，且【刻意没有】source_not_yet_active★
// v0_1 的 gap_detector 会从「我们抓到的条目」反推源的起始月，于是把「我们没回填」误报成
// 「那时这个源还不存在」——对 arXiv/Nature/NEJM/PNAS/bioRxiv 全是假话（实测 3665/3937 格 = 93%）。
// 没有独立证据就不许下这个判断。默认 not_backfilled 是【可证的事实】：我们确实没回填过。
const COV_REASON = {
  covered: '有条目',
  not_backfilled: '未回填（我们没抓过这一段，不是这个源当时不存在）',
};
function covMonths(start, end) {
  const out = [];
  let [y, m] = start.split('-').map(Number);
  const [ey, em] = end.split('-').map(Number);
  while (y < ey || (y === ey && m <= em)) {
    out.push(y + '-' + String(m).padStart(2, '0'));
    if (++m > 12) { m = 1; y++; }
  }
  return out;
}
// ★DIR-007 实测（rows_read 才是 D1 计量的量，不是结果行数）★
//   聚合查询：rows_read=1694（≈ 2 × 表大小 847；全表扫 + USE TEMP B-TREE FOR GROUP BY），结果行 69
//   登记查询：rows_read=74，结果行 37
//   合计约 1768 行 / 每次 /system 访问 → D1 免费档 5M 行/天 ≈ 2800 次访问/天。
// 两句诚实话：
//  1. 结果行 69 不是成本，rows_read 才是。原注释写「行数 = 不同 (source,month) 组合数」说的是
//     【结果行】，读的人会当成开销 —— 那是误导（复核指出）。
//  2. 这是【全表扫，且随 cn_items 线性增长】：substr(COALESCE(...)) 不可索引，GROUP BY 全表本就要扫完。
//     今天 KEEP_PER_BOARD=300 把表压在约 847 行，故无压力；若将来真做 2016+ 回填把表撑大，
//     每次 /system 访问的开销会跟着涨 —— 到那时必须改成物化/缓存，别等它咬人。
async function coverageGrid(env) {
  const now = new Date();
  const end = now.getUTCFullYear() + '-' + String(now.getUTCMonth() + 1).padStart(2, '0');
  const months = covMonths(COVERAGE_START, end);
  // ★源清单必须来自 cn_sources（登记表），不能来自 cn_items（我们碰巧抓到的东西）★
  // 第一版从 cn_items 推源清单 → 【一条都没抓到的源直接从网格里消失】：线上 cn_sources=37、
  // 有条目的仅 31 → 6 个源 × 127 月 = 762 格【既无 count 也无解释】，当场违反 T043 的
  // 「0 个静默未解释空洞」。而「一条都没抓到的源」恰恰是缺口检测最该喊出来的东西
  // （stats-gov 就是其中之一 —— P04 亲手接进来的 A0 官方源）。
  // ★这和 v0_1 的错是同一个谬误★：v0_1 从条目反推「源的起始月」→ 没数据＝「那时源还不存在」；
  // 我从条目反推「源的清单」→ 没数据＝「这个源不存在」。同一个错，从时间轴挪到源轴。
  // 在一根轴上修好、又在另一根轴上犯一遍 —— 写在这里，因为下一个人还会想这么写。
  const [regRes, aggRes] = await env.DB.batch([
    env.DB.prepare('SELECT id, board_id, name, health FROM cn_sources ORDER BY board_id, id'),
    env.DB.prepare("SELECT source_id, substr(COALESCE(published_at,fetched_at),1,7) mo, COUNT(*) n" +
                   " FROM cn_items GROUP BY source_id, mo"),
  ]);
  const registry = (regRes && regRes.results) || [];
  const counts = new Map();
  for (const r of ((aggRes && aggRes.results) || [])) {
    counts.set(r.source_id + '|' + r.mo, (counts.get(r.source_id + '|' + r.mo) || 0) + r.n);
  }
  const per = [];
  let covered = 0, notBackfilled = 0;
  for (const s of registry) {
    let c = 0, items = 0, first = null, last = null;
    for (const mo of months) {
      const n = counts.get(s.id + '|' + mo) || 0;
      if (n > 0) { c++; items += n; if (!first) first = mo; last = mo; covered++; }
      else notBackfilled++;
    }
    per.push({ source_id: s.id, board_id: s.board_id || '', health: s.health || '', months_covered: c,
               items, first, last, months_missing: months.length - c });
  }
  const cells = months.length * per.length;
  return {
    scope_start: COVERAGE_START, scope_end: end, months: months.length, cells,
    covered, not_backfilled: notBackfilled,
    sources_in_registry: per.length,
    sources_with_items: per.filter(x => x.items > 0).length,
    sources_never_ingested: per.filter(x => x.items === 0).map(x => x.source_id),
    // ★抓取失败 ≠ 未回填★：cn_sources.health 已经把「抓过但失败了」记下来了（run_log 里也有
    // degraded: ["a0:stats-gov"] 这样的记录）—— 系统一直是诚实的，只是没人去看。
    // 但★绝不用今天的 health 去解释 2016 年的格子★：一个源今天挂了，不能证明它 2016 年没内容。
    // 那正是本批开头抓到的谬误（拿手头的数据去解释它管不着的时段）。故 health 只作【来源级】的
    // 运维事实呈现，不下沉成 per-cell 的历史解释。
    sources_unhealthy: per.filter(x => x.health && x.health !== 'active')
                          .map(x => ({ id: x.source_id, health: x.health })),
    // ★这里【不】导出 unexplained: 0★ —— 它是恒真的字面量，任何改动都推翻不了它，
    // 拿它当「全面」的证据就是自欺（复核 BLOCK-4）。真正该看的是 coverage_pct（债务）
    // 与 sources_in_registry / sources_with_items 的差（有没有整个源被漏掉）。
    coverage_pct: cells ? Math.round((covered / cells) * 1000) / 10 : 0,
    per_source: per,
  };
}
function coverageHTML(g) {
  const rows = g.per_source.map(s => `<tr><td class="mt">${esc(s.source_id)}</td>
    <td class="mt">${esc(BOARD_NAMES[s.board_id] || s.board_id || '')}</td>
    <td class="mt">${s.items}</td>
    <td class="mt">${s.months_covered} / ${g.months}</td>
    <td class="mt">${s.first ? esc(s.first) + ' … ' + esc(s.last) : '—'}</td></tr>`).join('');
  return `<div class="card" style="margin-top:14px"><h2>覆盖与缺口（${esc(g.scope_start)} 起）</h2>
    <p class="mt">把「全面」从<b>来源数量</b>变成<b>可见的时间覆盖</b>：登记在册 ${g.sources_in_registry} 个来源 × ${g.months} 个月 = ${g.cells} 格（其中 ${g.sources_with_items} 个源真的抓到过东西）。
      <span class="badge ok">有条目 ${g.covered}</span>
      <span class="badge">未回填 ${g.not_backfilled}</span>
      —— 时间覆盖率 <b>${g.coverage_pct}%</b>。
      ${g.sources_never_ingested.length ? `<span class="badge">★从未抓到过任何条目的源：<b>${g.sources_never_ingested.length}</b> 个（${esc(g.sources_never_ingested.join('、'))}）★</span>` : ''}
      ${g.sources_unhealthy.length ? `<span class="badge">抓取异常：<b>${g.sources_unhealthy.length}</b> 个（${esc(g.sources_unhealthy.map(x => x.id + '：' + x.health).join('、'))}）</span>` : ''}</p>
    <p class="mt">「未回填」与「抓取失败」<b>不是一回事</b>：上面这些源<b>抓过、但失败了</b>（health 已记在册，
      每日运行日志里也有 degraded 记录）。<b>但本页不会拿今天的 health 去解释 2016 年的空格</b>——
      一个源今天挂了，证明不了它 2016 年没内容。那正是本页开头拒绝的那种「拿手头数据解释它管不着的时段」。</p>
    <p class="mt">★这就是当前的<b>覆盖债务</b>：${g.coverage_pct}% 意味着 ${g.scope_start} 以来的绝大多数月份<b>我们从没抓过</b>。
      这里<b>不写</b>「那时这个源还不存在」——除非有独立证据，否则那是<b>假话</b>：
      arXiv 自 1991 年、Nature 自 1869 年就在了，空着只因<b>我们没有回填</b>。缺口是真的，写清楚比藏起来强。</p>
    <table><tr><th>来源</th><th>板块</th><th>条目</th><th>覆盖月数</th><th>已覆盖区间</th></tr>${rows || '<tr><td colspan=5>尚无来源</td></tr>'}</table></div>`;
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
  let covHTML = '';
  try { covHTML = coverageHTML(await coverageGrid(env)); }
  catch (e) { covHTML = ''; }   // 覆盖视图坏了不许把 /system 带下线（与 P08 attachMeta 同一条纪律）
  return PAGE('/system', `<div class="card"><h1>系统与来源</h1>
    <p class="mt">整套系统跑在 Cloudflare（Workers + D1 + 每日 cron），不依赖任何本机。当前候选库 ${total ? total.n : 0} 条。</p>
    <table><tr><th>日期</th><th>结果</th><th>抓取/候选</th><th>说明</th></tr>${rows || '<tr><td colspan=4>尚无运行</td></tr>'}</table>
      </div>${covHTML}<div class="card">
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
// T084 证据/推断区分：讲义是「依据原文自动生成的结构化推断」，与「原文（证据）」明确区分，避免读者误把推断当原文。
const PROVENANCE_NOTE = '<p class="mt"><span class="badge">讲义·推断</span> 依据「原文」自动生成的结构化摘要（推断），非原文表述；以原文为准。</p>';
function lessonHTML(lesson) {
  if (!lesson) return '';
  return PROVENANCE_NOTE + JSON.parse(lesson.sections_json).map((s, i) =>
    `<h3>${i + 1}. ${esc(s.title)}</h3>${(s.sentences || []).map(x => `<p>${esc(x.text)}</p>`).join('')}`).join('');
}
function itemListHTML(items, { study = true } = {}) {
  if (!items.length) return '<p class="mt">暂无条目。</p>';
  return items.map(it => `<div class="itemrow"><div class="body">
    <a href="/item/${encodeURIComponent(it.id)}">${esc(it.title.slice(0, 110))}</a>
    <div class="mt">${esc(BOARD_NAMES[it.board_id] || it.board_id || '')}${it.published_at ? ' · ' + esc(it.published_at.slice(0, 10)) : ''} · <a href="${safeHref(it.url)}" rel="noopener">原文</a></div>
    ${factsheetHTML(it)}
    </div>${study ? `<button class="btn-sm" data-id="${esc(it.id)}" onclick="study(this)">学这个</button>` : ''}</div>`).join('');
}
// 可复用的主动回忆评分组件（reveal 内容 + 四档评分 + 脚本）
function graderHTML(itemId, revealInner, nextHref) {
  return `<div class="card"><h2>主动回忆</h2>
    <p class="mt">先合上内容自己复述，再点「显示」核对，然后如实自评。评分即时进 FSRS 排程。</p>
    <button class="btn-sm" id="revealBtn" aria-controls="revealBox" onclick="var b=document.getElementById('revealBox');b.hidden=false;this.hidden=true;b.focus();">显示答案/讲义</button>
    <div class="reveal" id="revealBox" tabindex="-1" hidden>${revealInner || '<p class="mt">该条目暂无讲义，请点原文精读后自评。</p>'}</div>
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

// ───────────────────────── 关注 /watchlist（S5-P04-T066 的诚实子集；只读线上数据 + 两张小表） ─────────────────────────
// T066 的 facet 是 {topic,agency,region,entity,doc_number} 且靠 T026 content_hash 判「实质变化」。
// 线上 cn_items 没有这些 facet 字段，S2 版本层也未上线。因此本实现只交付线上数据真能支撑的：
//   doc_number —— 用 P01 的确定性抽取器从 title/summary 真实抽出后精确匹配（board3 官方原文标题常带文号）
//   board      —— cn_items.board_id 真字段，精确匹配
//   keyword    —— 标题/摘要子串；★这不是 T066 的 facet，是 ADP-V02 追加★
// 变化判定只做「新条目」；「已入库条目的内容实质变化」需要 T026 content_hash，未上线 → 不做、不声称。
const WATCH_FACETS = ['doc_number', 'board', 'keyword'];
const WATCH_MAX = 20;                 // 关注条数上限
const WATCH_SCAN = 1000;              // 一次共享扫描读取的条目上限（硬上限）
const WATCH_WINDOW_DAYS = 30;         // 只看最近 N 天 —— 关注要的就是「新条目」
// ★DIR-007 双重有界 + 单遍扫描（两者都是实测换来的）★
// 1) 行数：候选查询必须「时间窗 + LIMIT」双重有界。只用 LIKE+LIMIT 时，匹配不到会为凑满 LIMIT
//    走完整个索引（真实 schema 5 万行实测 25.0ms）。加时间窗后计划变为
//    SEARCH cn_items USING INDEX idx_cn_items_recency (<expr>>?)（索引范围定位），无匹配也仅 1.51ms。
// 2) CPU：必须「一遍扫描对所有关注」而不是「每条关注扫一遍」。FS_DOCNUM_RE 在中文正文上约
//    0.041ms/行（[一-龥A-Za-z]{0,8} 使 V8 在每个汉字位置都无法跳过；英文约 0.05ms/1000 行），
//    每条关注各跑一遍时 100CJK/900EN 实测 4.17ms/条 → ×20 = 83ms，而 Workers 免费档 CPU 限额是
//    10ms/次 → 约 3 条文号关注就打爆。故：共享一次窗口扫描，每条目只抽一次文号，并用 '号' 预筛
//    （FS_DOCNUM_RE 的每种形态都必然含 '号'，英文正文则完全没有）。这同时把行读取量也降了 ×20。
//    这与 T066 的循环结构一致：for it in items: for w in watches。
const watchCutoff = () => new Date(Date.now() - WATCH_WINDOW_DAYS * 864e5).toISOString().slice(0, 10);
async function watchTables(env) {
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS cn_watchlist (id TEXT PRIMARY KEY, facet TEXT NOT NULL, value TEXT NOT NULL, created_at TEXT NOT NULL)').run();
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS cn_watch_seen (watch_id TEXT NOT NULL, item_id TEXT NOT NULL, at TEXT NOT NULL, PRIMARY KEY (watch_id, item_id))').run();
}
// 单条关注是否命中某条目。
// ★内层循环里不得有「只与条目有关」或「只与关注有关」的计算★ —— 它们会被乘以 (条目数 × 关注数)。
// doc（该条目只抽一次的文号）与 hay（该条目只拼一次的小写正文）由调用方按条目预计算；
// w._nv（关注值的归一化/小写形式）由调用方按关注预计算。
function watchMatches(it, w, doc, hay) {
  if (w.facet === 'board') return it.board_id === w.value;          // 真字段，精确
  if (w.facet === 'doc_number') return !!doc && doc.includes(w._nv); // 与 P03 同口径
  return hay.includes(w._nv);                                        // keyword：ADP-V02 追加，非 T066 facet
}
// 一次共享扫描 → 对所有关注求未读。返回 Map(watch_id -> 未读条目[])。
async function watchDigest(env, watches) {
  const out = new Map(watches.map(w => [w.id, []]));
  if (!watches.length) return out;
  const { results: items } = await env.DB.prepare(
    'SELECT * FROM cn_items WHERE COALESCE(published_at,fetched_at) >= ?1 ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT ?2')
    .bind(watchCutoff(), WATCH_SCAN).all();
  const rows = items || [];
  // 每条目只抽一次文号，且只对可能含文号的行跑正则（'号' 预筛）
  const docs = new Map();
  if (watches.some(w => w.facet === 'doc_number')) {
    for (const it of rows) {
      if (((it.title || '') + (it.summary || '')).indexOf('号') < 0) continue;
      // 与 factsheet()/itemIdentifiers() 同约定：抽取前先给输入长度兜底（请求路径线性时间的纵深防御）
      const dn = fsFirst(FS_DOCNUM_RE, (it.title || '').slice(0, 500), (it.summary || '').slice(0, 2000));
      if (dn) docs.set(it.id, normIdent(dn));
    }
  }
  const seen = new Map();
  for (const w of watches) {
    // ★不设 LIMIT、不排序★。曾经写成 ORDER BY at DESC LIMIT N，前提是「窗口 <= WATCH_SCAN 条，
    // 故最近的若干次已读必然覆盖窗口」—— 这个前提是错的：WATCH_SCAN 限的是**读取量**，不是窗口。
    // 30 天窗口在线上约 1.5 万条，已读集会超过任何 N；一旦截断，被截掉的是**最早 ack** 的行，
    // 而未来日期的条目（政策生效日）会永远排在候选第 1 位、其 ack 时间却会老化出界 → 重复通知，
    // 恰好重开了下面按窗口剪枝所要堵的那个洞。有界性由剪枝保证，不能靠一个会静默牺牲正确性的 LIMIT。
    // 无 ORDER BY 亦使计划回到 SEARCH cn_watch_seen USING COVERING INDEX (watch_id=?)。
    const { results: s } = await env.DB.prepare(
      'SELECT item_id FROM cn_watch_seen WHERE watch_id=?1').bind(w.id).all();
    seen.set(w.id, new Set((s || []).map(r => r.item_id)));
    w._nv = w.facet === 'doc_number' ? normIdent(w.value) : String(w.value).toLowerCase();  // 每条关注只算一次
  }
  const needHay = watches.some(w => w.facet === 'keyword');   // 与上面 docs 的守卫对齐：没有就别算
  for (const it of rows) {                       // T066 的循环序：先条目，再关注
    const doc = docs.get(it.id);
    const hay = needHay ? ((it.title || '') + ' ' + (it.summary || '')).toLowerCase() : '';  // ★每条目只拼一次★
    for (const w of watches) {
      if (seen.get(w.id).has(it.id)) continue;
      if (watchMatches(it, w, doc, hay)) out.get(w.id).push(it);
    }
  }
  return out;
}
async function watchlistPage(env) {
  await watchTables(env);
  const { results: watches } = await env.DB.prepare(
    'SELECT * FROM cn_watchlist ORDER BY created_at DESC LIMIT ?1').bind(WATCH_MAX).all();
  const facetLabel = { doc_number: '文号', board: '板块', keyword: '关键词' };
  let body = `<div class="card"><h1>关注</h1>
    <p class="mt">盯住一个<b>文号</b>、<b>板块</b>或<b>关键词</b>；有<b>新条目</b>时这里会列出来，点「标记已读」后不再重复出现。</p>
    <p class="mt" style="font-size:12px">只读线上已入库的内容，不新增抓取；每条关注只看<b>最近 ${WATCH_WINDOW_DAYS} 天</b>内、最多 ${WATCH_SCAN} 条。<b>只检测新条目</b>——已入库条目的内容改动检测需要尚未上线的版本层，故不做也不声称。</p>
    <form method="POST" action="/api/watch/add" style="margin-top:10px">
      <select name="facet" aria-label="关注类型">
        <option value="doc_number">文号（如 国发〔2026〕12号）</option>
        <option value="board">板块</option>
        <option value="keyword">关键词</option>
      </select>
      <input name="value" placeholder="要关注的内容" maxlength="80" required style="min-width:220px">
      <button class="btn-sm" type="submit">添加关注</button>
    </form>
    <p class="mt" style="font-size:12px">板块可填：${REGISTRY.map(b => esc(b.board) + '=' + esc(b.name)).join('、')}</p>
  </div>`;
  if (!(watches || []).length) {
    body += '<div class="card"><p class="mt">还没有关注项。添加一个文号或板块试试。</p></div>';
    return PAGE('/watchlist', body, { title: '关注' });
  }
  const digest = await watchDigest(env, watches);
  for (const w of watches) {
    const unseen = digest.get(w.id) || [];
    body += `<div class="card"><h2>${esc(facetLabel[w.facet] || w.facet)}：${esc(w.value)}
      <span class="badge${unseen.length ? '' : ' ok'}">${unseen.length ? unseen.length + ' 条新' : '无新'}</span></h2>
      <div class="mt">
        <form method="POST" action="/api/watch/ack/${encodeURIComponent(w.id)}" style="display:inline">
          <button class="btn-sm" type="submit"${unseen.length ? '' : ' disabled'}>标记已读</button></form>
        <form method="POST" action="/api/watch/del/${encodeURIComponent(w.id)}" style="display:inline">
          <button class="btn-sm" type="submit">删除关注</button></form>
      </div>
      ${unseen.length ? itemListHTML(await attachMeta(env, unseen.slice(0, 20))) : '<p class="mt">暂无新条目。</p>'}
      ${unseen.length > 20 ? `<p class="mt">仅显示前 20 条（共 ${unseen.length} 条新）。</p>` : ''}
    </div>`;
  }
  return PAGE('/watchlist', body + STUDY_JS, { title: '关注' });
}

// ───────────────────────── 知识库 /library（S5-P04-T067 Library 上线；只读视图） ─────────────────────────
// 数据只来自线上 cn_reviews ⨝ cn_items（你学过/在复习的条目）。不新增表、不改流水线。
// 诚实边界：T067 的「笔记」与「全 provenance 导出」需要 version/license 等 S2 版本层字段，
// 那一层尚未上线；此处只交付可如实呈现的部分，不臆造 provenance，也不做会被 T067 拒绝的残缺导出。
const LIB_PAGE_SIZE = 100;
async function libraryPage(env, params) {
  const board = (params.get('board') || '').slice(0, 12);
  const state = (params.get('state') || '').slice(0, 12);
  const { results: stats } = await env.DB.prepare(
    `SELECT i.board_id AS b, r.evidence_state AS s, COUNT(*) AS n
     FROM cn_reviews r CROSS JOIN cn_items i ON i.id = r.item_id GROUP BY i.board_id, r.evidence_state`).all();
  const total = (stats || []).reduce((a, x) => a + (x.n || 0), 0);
  const byState = {}, byBoard = {};
  for (const x of (stats || [])) {
    const s = x.s || '—';
    byState[s] = (byState[s] || 0) + (x.n || 0);
    byBoard[x.b] = (byBoard[x.b] || 0) + (x.n || 0);
  }
  const { results: rows } = await env.DB.prepare(
    `SELECT i.*, r.evidence_state, r.due_at, r.reps, r.lapses, r.last_review
     FROM cn_reviews r CROSS JOIN cn_items i ON i.id = r.item_id
     WHERE (?1 = '' OR i.board_id = ?1) AND (?2 = '' OR r.evidence_state = ?2)
     ORDER BY COALESCE(r.last_review, r.due_at) DESC, i.id DESC LIMIT ?3`).bind(board, state, LIB_PAGE_SIZE).all();
  const qs = (b, s) => {
    const p = [b ? 'board=' + encodeURIComponent(b) : '', s ? 'state=' + encodeURIComponent(s) : ''].filter(Boolean);
    return '/library' + (p.length ? '?' + p.join('&') : '');
  };
  const chip = (label, n, href, on) =>
    `<a class="pill-link" href="${href}"${on ? ' aria-current="page"' : ''}>${esc(label)} ${n}</a>`;
  let body = `<div class="card"><h1>知识库</h1>
    <p class="mt">你学过／在复习的全部条目——证据态、复习进度与原文出处都在这里。共 <b>${total}</b> 条。</p>
    <p style="margin:8px 0 2px">${chip('全部', total, qs('', ''), !board && !state)}${Object.keys(byBoard).sort().map(b =>
      chip(BOARD_NAMES[b] || b, byBoard[b], qs(b, state), board === b)).join('')}</p>
    <p style="margin:2px 0 0">${Object.keys(byState).filter(s => s !== '—').sort().map(s =>
      chip(s, byState[s], qs(board, s), state === s)).join('')}</p></div>`;
  await attachMeta(env, rows || []);
  const list = (rows || []).map(it => `<div class="itemrow"><div class="body">
    <a href="/item/${encodeURIComponent(it.id)}">${esc((it.title || '').slice(0, 110))}</a>
    <div class="mt">${esc(BOARD_NAMES[it.board_id] || it.board_id || '')}${it.published_at ? ' · ' + esc(String(it.published_at).slice(0, 10)) : ''} · <a href="${safeHref(it.url)}" rel="noopener">原文</a><span class="badge">${esc(it.evidence_state || '—')}</span><span class="badge">复习 ${Number(it.reps) || 0} 次</span>${it.due_at ? `<span class="badge">下次 ${esc(String(it.due_at).slice(0, 10))}</span>` : ''}</div>
    ${factsheetHTML(it)}
    </div></div>`).join('');
  body += `<div class="card">${list || '<p class="mt">知识库还是空的。去 <a href="/">今天</a> 学一篇，或在 <a href="/radar">雷达</a>／<a href="/search">搜索</a> 里点「学这个」。</p>'}
    ${(rows || []).length >= LIB_PAGE_SIZE ? `<p class="mt">仅显示最近 ${LIB_PAGE_SIZE} 条。</p>` : ''}</div>`;
  return PAGE('/library', body, { title: '知识库' });
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
  await attachMeta(env, shown);
  let body = `<div class="card"><h1>${esc(name)}</h1><p class="mt"><a href="/radar">← 前沿雷达</a></p>
    ${itemListHTML(shown)}
    <p style="margin-top:12px">${offset > 0 ? `<a class="pill-link" href="/board/${boardId}?offset=${Math.max(0, offset - PAGE_SIZE)}">← 上一页</a>` : ''}
    ${more ? `<a class="pill-link" href="/board/${boardId}?offset=${offset + PAGE_SIZE}">下一页 →</a>` : ''}</p></div>`;
  return PAGE('/radar', body + STUDY_JS, { title: name });
}

// ───────────────────────── 搜索 /search ─────────────────────────
// 标识符归一化（T060 _norm_id 语义）：去空白（含全角）+ ASCII 大小写折叠；DOI 大小写不敏感。
function normIdent(s) { return (s || '').replace(/　/g, ' ').replace(/\s+/g, '').toLowerCase(); }
// 从条目已有字段抽标识符（跨板块，用于检索排序；沿用 P01 的输入上界，保持线性时间）
function itemIdentifiers(it) {
  const out = [];
  const doi = fsFirst(FS_DOI_RE, it.id, it.url, (it.summary || '').slice(0, 2000));
  if (doi) out.push(doi.replace(/[).,;]+$/, ''));
  const dn = fsFirst(FS_DOCNUM_RE, (it.title || '').slice(0, 500), (it.summary || '').slice(0, 2000));
  if (dn) out.push(dn);
  return out;
}
const SEARCH_LIMIT = 40;
async function searchPage(env, params) {
  const q = (params.get('q') || '').trim().slice(0, 80);
  const board = (params.get('board') || '').slice(0, 12);
  const from = (params.get('from') || '').slice(0, 10);
  const to = (params.get('to') || '').slice(0, 10);
  const boardOpts = REGISTRY.map(b => b.board);
  const bSel = boardOpts.includes(board) ? board : '';           // 白名单，未知板块视为不筛选
  const dateOk = (s) => /^\d{4}-\d{2}-\d{2}$/.test(s) ? s : '';  // 只接受 YYYY-MM-DD
  const f = dateOk(from), t = dateOk(to);

  const filters = `<form method="get" action="/search" style="margin:8px 0 2px">
    <input type="hidden" name="q" value="${esc(q)}">
    <label class="mt">板块 <select name="board"><option value="">全部</option>${boardOpts.map(b =>
      `<option value="${esc(b)}"${bSel === b ? ' selected' : ''}>${esc(BOARD_NAMES[b] || b)}</option>`).join('')}</select></label>
    <label class="mt">起 <input type="date" name="from" value="${esc(f)}"></label>
    <label class="mt">止 <input type="date" name="to" value="${esc(t)}"></label>
    <button class="btn-sm" type="submit">筛选</button>
    ${(bSel || f || t) ? `<a class="pill-link" href="/search?q=${encodeURIComponent(q)}">清除筛选</a>` : ''}
  </form>`;

  let body = `<div class="card"><h1>搜索</h1>
    <p class="mt">在候选库的标题、摘要、链接与 ID 中检索；可按板块与日期范围筛选。若查询出现在某条的文号／DOI 这类标识符里，该条会被置顶。</p>
    ${filters}`;
  if (q) {
    const like = '%' + q.replace(/[\\%_]/g, m => '\\' + m) + '%';
    // 检索面必须与 itemIdentifiers 的抽取面一致：bioRxiv/medRxiv 的 DOI 只存在于 id/url，不在 title/summary。
    // LIKE %x% 本就不可走索引，加这两列不改变查询计划（已用 EXPLAIN QUERY PLAN 复验同计划）。
    const where = ["(title LIKE ?1 ESCAPE '\\' OR summary LIKE ?1 ESCAPE '\\' OR id LIKE ?1 ESCAPE '\\' OR url LIKE ?1 ESCAPE '\\')"];
    const binds = [like];
    if (bSel) { binds.push(bSel); where.push(`board_id = ?${binds.length}`); }
    if (f) { binds.push(f); where.push(`COALESCE(published_at, fetched_at) >= ?${binds.length}`); }
    if (t) { binds.push(t); where.push(`COALESCE(published_at, fetched_at) <= ?${binds.length}`); }
    binds.push(SEARCH_LIMIT);
    // 列名为代码字面量，全部取值均为绑定参数（无拼接注入面）；给出 board 时可走 idx_cn_items_board_recency
    const sql = `SELECT * FROM cn_items WHERE ${where.join(' AND ')} ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT ?${binds.length}`;
    let { results } = await env.DB.prepare(sql).bind(...binds).all();
    results = results || [];
    // T060 精确优先：查询形如标识符时，把归一化后精确命中的条目排到最前（对已取回的 <=40 行做，零额外 DB 成本）
    const nq = normIdent(q);
    const identLike = /^10\.\d{4,9}\//.test(q.trim()) || FS_DOCNUM_RE.test(q);
    let exactCount = 0;
    if (identLike && results.length) {
      const hit = [], rest = [];
      for (const it of results) {
        // 可证语义：查询出现在该行抽出的标识符里（而非正文别处）。用 includes 容忍抽取吞入的前缀
        // （如「转发国发〔2026〕12号」）；但这只证明标识符文本匹配，不声称该行就是官方原件。
        (itemIdentifiers(it).some(v => normIdent(v).includes(nq)) ? hit : rest).push(it);
      }
      exactCount = hit.length;
      results = hit.concat(rest);
    }
    const note = [bSel ? BOARD_NAMES[bSel] || bSel : '', f ? '起 ' + f : '', t ? '止 ' + t : ''].filter(Boolean).join(' · ');
    await attachMeta(env, results);
    body += `<p class="mt">「${esc(q)}」找到 ${results.length} 条${results.length === SEARCH_LIMIT ? '（仅显示最近 40）' : ''}${note ? '｜筛选：' + esc(note) : ''}${exactCount ? `｜<span class="badge ok">标识符匹配 ${exactCount} 条已置顶</span>` : ''}</p>
      <p style="margin:2px 0 6px"><a class="deep-btn ghost" href="${esc(chatgptHref(deepDiveTopicPrompt(q)))}" target="_blank" rel="noopener noreferrer">🔮 让 ChatGPT 全网深度检索这个主题</a></p>
      ${itemListHTML(results)}`;
  } else body += '<p class="mt">在右上角搜索框输入关键词，或用上面的板块／日期筛选。</p>';
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
  await attachMeta(env, [item]);
  let body = `<div class="card"><p class="mt"><a href="/board/${esc(item.board_id)}">← ${esc(BOARD_NAMES[item.board_id] || item.board_id)}</a></p>
    <h1>${esc(item.title)}</h1>
    <p class="mt">${esc(item.authors || '')}${item.categories ? ' · ' + esc(item.categories) : ''}${item.published_at ? ' · ' + esc(item.published_at.slice(0, 10)) : ''} · <a href="${safeHref(item.url)}" rel="noopener">原文</a>${review ? ' · 证据态 ' + esc(review.evidence_state) : ''}</p>
    ${factsheetHTML(item)}
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
        // S3-P03-T040 canary，P04 升级：用与生产 cron 同一个 parseA0 解析器逐源实测边缘可达性与产出，
        // 不再用重复的内联正则（旧正则只认 /YYYY-MM/DD/ 旧链接形态，所以只吐 2019/2020 老文件）。
        // 只读：不写任何生产数据。
        const probes = [];
        for (const b of REGISTRY) for (const s of b.sources) {
          if (s.method !== 'a0') continue;
          let rec = { source_id: s.id, list: s.list, reachable: false, parsed: 0, with_date: 0, error: null, sample: [] };
          try {
            // sourceId=null 关掉 fetchFeedText 的 R2 双写旁路（其内部 `&& sourceId` 守卫），
            // 否则这个「只读」端点会真写 R2+D1（未鉴权 → 任何人可烧 DIR-007 预算）——复核抓到的真实缺陷。
            const html = await fetchFeedText(s.list, env, null);
            const items = parseA0(html, s.id);
            rec.reachable = true;
            rec.parsed = items.length;
            rec.with_date = items.filter(i => i.published).length;
            rec.sample = items.slice(0, 2).map(i => ({ title: i.title.slice(0, 60), url: i.url, published: i.published,
              a0_eligible: a0Board3Eligible({ board_id: 'board3', source_id: s.id, url: i.url }) }));
          } catch (e) { rec.error = String(e && e.name || e).slice(0, 60); }
          probes.push(rec);
        }
        const { results: b3 } = await env.DB.prepare(
          // 必须选出 board_id：a0Board3Eligible 首行是 `if (it.board_id !== 'board3') return true`，
          // 漏选会让每一行都恒真通过 → 把 105 条媒体误报成「官方 A0」并谎称 safe_to_flip（T040 原版同样漏选，其 media_demoted:0 是空跑）。
          "SELECT id,board_id,source_id,title,url,kind FROM cn_items WHERE board_id='board3' ORDER BY COALESCE(published_at,fetched_at) DESC, id DESC LIMIT 400").all();
        const inDbOfficial = (b3 || []).filter(it => a0Board3Eligible(it)).length;
        const inDbMedia = (b3 || []).length - inDbOfficial;
        const parsedTotal = probes.reduce((a, p) => a + p.parsed, 0);
        return jsonResp({
          canary: 'board3_a0_view', flag_state: BOARD3_A0_ONLY ? 'ON' : 'OFF (media still counts as evidence)',
          non_destructive: true, note: 'probes each A0 source live from the edge with the SAME parser the cron uses; writes nothing',
          a0_sources_probed: probes.length,
          a0_sources_reachable: probes.filter(p => p.reachable && p.parsed > 0).length,
          a0_items_parsed_now: parsedTotal,
          probes,
          board3_in_db_total: (b3 || []).length,
          board3_in_db_official_a0: inDbOfficial,
          board3_in_db_media: inDbMedia,
          // 翻开关的前提：库里真的有 A0 官方原文，否则 board3 会被清空
          safe_to_flip_flag: inDbOfficial > 0,
          flip_precondition: 'BOARD3_A0_ONLY=true demotes media to discovery; flipping while board3_in_db_official_a0 == 0 would EMPTY board 3',
          rollback: 'set BOARD3_A0_ONLY=false and redeploy (one deploy); flag currently ' + (BOARD3_A0_ONLY ? 'ON' : 'OFF'),
          not_wired_honestly: {
            'gov-cn-fagui': 'listing returns HTTP 403 (blocked) - not ingested',
            'nda-gov': 'listing returns a ~193-byte JS-redirect stub (S3 adapter already marks live_blocked=true) - not ingested',
          },
        });
      }

      if (request.method === 'POST') {
        if (p === '/api/watch/add' || p.startsWith('/api/watch/ack/') || p.startsWith('/api/watch/del/')) {
          await watchTables(env);
          if (p === '/api/watch/add') {
            const form = await request.formData();
            const facet = String(form.get('facet') || '');
            const value = String(form.get('value') || '').trim().slice(0, 80);
            if (!WATCH_FACETS.includes(facet) || !value) return jsonResp({ error: 'bad facet or value' }, 422);
            const { results: cnt } = await env.DB.prepare('SELECT COUNT(*) n FROM cn_watchlist').all();
            if ((cnt?.[0]?.n || 0) >= WATCH_MAX) return jsonResp({ error: 'watch limit reached', limit: WATCH_MAX }, 422);
            const id = 'w:' + (await sha1(facet + '|' + value)).slice(0, 12);
            await env.DB.prepare('INSERT INTO cn_watchlist (id,facet,value,created_at) VALUES (?,?,?,?) ON CONFLICT(id) DO NOTHING')
              .bind(id, facet, value, nowISO()).run();
            return Response.redirect(new URL('/watchlist', request.url).toString(), 303);
          }
          const wid = decodeURIComponent(p.split('/')[4] || '');
          if (!wid) return jsonResp({ error: 'bad watch id' }, 422);
          if (p.startsWith('/api/watch/del/')) {
            await env.DB.batch([
              env.DB.prepare('DELETE FROM cn_watchlist WHERE id=?').bind(wid),
              env.DB.prepare('DELETE FROM cn_watch_seen WHERE watch_id=?').bind(wid),
            ]);
            return Response.redirect(new URL('/watchlist', request.url).toString(), 303);
          }
          // ack：把当前未读全部记为已读 —— 之后再访问该关注为零新条目（T066 的可重入性质）
          const w = await env.DB.prepare('SELECT * FROM cn_watchlist WHERE id=?').bind(wid).first();
          if (!w) return jsonResp({ error: 'not found' }, 404);
          const unseen = (await watchDigest(env, [w])).get(w.id) || [];
          const now = nowISO();
          const stmts = unseen.map(it => env.DB.prepare(
            'INSERT INTO cn_watch_seen (watch_id,item_id,at) VALUES (?,?,?) ON CONFLICT(watch_id,item_id) DO NOTHING')
            .bind(wid, it.id, now));
          // 剪枝：删掉「其条目已不在窗口内」的已读行 —— 窗口外的条目永不再成为候选，其已读行是死重量。
          // ★按条目自身的窗口归属判定，而不是按 ack 时间★：ack 时间剪枝在 published_at 为未来日期时
          // 有洞（政策生效日就是真实例子）—— 已读行被剪掉而条目仍在窗口内 → 会重复通知。
          // 相关子查询按主键查 cn_items，不做 join（避免 D1 无 ANALYZE 时的 join 顺序问题）。
          stmts.push(env.DB.prepare(
            'DELETE FROM cn_watch_seen WHERE watch_id=?1 AND NOT EXISTS (SELECT 1 FROM cn_items i WHERE i.id=cn_watch_seen.item_id AND COALESCE(i.published_at,i.fetched_at) >= ?2)')
            .bind(wid, watchCutoff()));
          await env.DB.batch(stmts);
          return Response.redirect(new URL('/watchlist', request.url).toString(), 303);
        }
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
      else if (p === '/watchlist') html = await watchlistPage(env);
      else if (p === '/library') html = await libraryPage(env, url.searchParams);
      else if (p === '/history') html = await historyPage(env);
      else if (p === '/search') html = await searchPage(env, url.searchParams);
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
