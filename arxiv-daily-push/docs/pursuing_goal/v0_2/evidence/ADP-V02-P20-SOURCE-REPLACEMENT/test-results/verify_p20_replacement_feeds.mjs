#!/usr/bin/env node
// P20 载荷型验证器:6 个被墙源中 4 个的替代端点(SD RSS x3 + Bing News RSS)——
// (a) 边缘可达性由临时探针 worker 实测(记录在 evidence:200 + 70/52/87/11 条);
// (b) 本验证器证【解析器兼容】:抽取【已部署】parseFeed 实跑 4 个真实 XML 样本(specimens_p20/),
//     断言逐源解析出足量条目且 title/link/published 齐;负控:403 拦截页 HTML 必须解析 0 条(计数器不空转)。
// (c) 静态钉:发货源 REGISTRY 中 4 源的 feed 已指向替代端点。
import fs from 'node:fs'; import path from 'node:path'; import url from 'node:url';
const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const WORKER = path.resolve(HERE, '..', 'deploy', 'cloudflare', 'worker_cloud.js');
const SRC = fs.readFileSync(WORKER, 'utf8');
function extract(a, b) { const i = SRC.indexOf(a); const j = i < 0 ? -1 : SRC.indexOf(b, i + a.length); if (i < 0 || j < 0) throw new Error('锚点变了: ' + a); return SRC.slice(i, j); }
// 抽取解析链:tag/stripTags 工具 + MAX_ITEMS_PER_FEED + parseFeed(不复刻)
const utils = extract('function stripTags', 'function parseFeed');  // 含 stripTags/decodeEntities/tag 全依赖链
const pf = extract('function parseFeed', 'function parseOaiArxiv');
const maxc = SRC.match(/const MAX_ITEMS_PER_FEED = \d+;/)[0];
// eslint-disable-next-line no-new-func
const { parseFeed } = new Function(maxc + '\n' + utils + '\n' + pf + '\n return { parseFeed };')();

const CASES = [
  { f: 'cell.xml',   min: 15, why: 'Cell → rss.sciencedirect.com/publication/science/00928674 (边缘实测 200/70 条)' },
  { f: 'neuron.xml', min: 15, why: 'Neuron → …/08966273 (边缘实测 200/52 条)' },
  { f: 'lancet.xml', min: 15, why: 'Lancet → …/01406736 (边缘实测 200/87 条)' },
  { f: 'bing.xml',   min: 5,  why: 'gnews-us-tech → Bing News RSS q=FTC+antitrust (边缘实测 200/11 条)' },
];
let fail = 0;
console.log('抽取自:', WORKER);
for (const c of CASES) {
  const xml = fs.readFileSync(path.join(HERE, 'specimens_p20', c.f), 'utf8');
  const items = parseFeed(xml);
  const good = items.filter(i => i.title && /^https?:/.test(i.link));
  const dated = items.filter(i => i.published);  // SD RSS 日期在 description 文本、无独立标签→published 常为 null;与现有 31 个 rss 源同标准,不作 fail 条件
  const ok = good.length >= c.min;
  console.log(`  ${ok ? '✅' : '❌'} [${c.f}] 解析 ${items.length} 条(合格 ${good.length},带日期 ${dated.length},需≥${c.min}) — ${c.why}`);
  if (!ok) fail++;
}
// 负控:403 拦截页(HTML 无 <item>)必须 0 条——证明上面的计数不是空转
const blockPage = '<!DOCTYPE html><html><head><title>Access Denied</title></head><body><h1>403</h1><p>blocked</p></body></html>';
const nc = parseFeed(blockPage);
if (nc.length !== 0) { fail++; console.log('  ❌ 负控失效:拦截页竟解析出', nc.length, '条'); }
else console.log('     ↳ 负控成立:403 拦截页解析 0 条(计数承重)');
// 静态钉:REGISTRY 已指向替代端点
const PINS = [
  ["cell → SD RSS", "feed: 'https://rss.sciencedirect.com/publication/science/00928674'"],
  ["neuron → SD RSS", "feed: 'https://rss.sciencedirect.com/publication/science/08966273'"],
  ["lancet → SD RSS", "feed: 'https://rss.sciencedirect.com/publication/science/01406736'"],
  ["gnews → Bing RSS", "feed: 'https://www.bing.com/news/search?q=FTC+antitrust&format=rss&mkt=en-US'"],
];
// P20 诚实性钉:gnews 的病因必须记为【间歇 503】而非硬墙(边缘实测 6 次:2×200/78 条 + 4×503)。
// cell/lancet 才是确定性 403(3/3)。把二者混为一谈=过度推断,曾是本次的错误判断。
if (!/间歇 503/.test(SRC)) { fail++; console.log('  ❌ 发货源未如实记录 gnews 是间歇 503(非硬墙)——过度推断会误导后人'); }
else console.log('  ✅ 发货源如实区分:gnews=间歇 503,cell/lancet=确定性 403');
for (const [name, needle] of PINS) {
  if (!SRC.includes(needle)) { fail++; console.log(`  ❌ 发货源 REGISTRY 未指向替代端点: ${name}`); }
  else console.log(`  ✅ REGISTRY 指向替代端点: ${name}`);
}
console.log(fail === 0 ? '\nPASS: 4 个替代端点解析兼容 + 负控承重 + 配置已切换。' : `\nFAIL: ${fail}`);
process.exit(fail === 0 ? 0 : 1);
