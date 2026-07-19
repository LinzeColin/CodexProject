#!/usr/bin/env node
// 载荷型再推导验证器：讲义渲染层剥内联 LaTeX 数学定界符($…$),且绝不动金融货币文本。
// 抽取【已部署】worker_cloud.js 的 esc+deMath+lessonHTML 实跑;负控:旧渲染(无 deMath)在同一夹具上
// 保留裸 $——证明夹具能判别、断言承重。跑法：node arxiv-daily-push/tools/verify_lesson_demath.mjs
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const WORKER = path.resolve(HERE, '..', 'deploy', 'cloudflare', 'worker_cloud.js');
const SRC = fs.readFileSync(WORKER, 'utf8');

function extract(anchorStart, anchorEnd) {
  const a = SRC.indexOf(anchorStart);
  const b = a < 0 ? -1 : SRC.indexOf(anchorEnd, a + anchorStart.length); // anchorEnd 从 a 之后找
  if (a < 0 || b < 0) throw new Error(`无法定位 ${anchorStart}..${anchorEnd}——锚点变了,改验证器别让它空过`);
  return SRC.slice(a, b);
}
// esc 与 deMath+lessonHTML 都从发货源抽取,不复刻
const escSrc = extract('const esc = ', '\n');                    // esc 是单行 const 箭头函数
const coreSrc = extract('const deMath', 'function itemListHTML');
// eslint-disable-next-line no-new-func
const { lessonHTML, deMath } = new Function(
  'PROVENANCE_NOTE', escSrc + '\n' + coreSrc + '\n return { lessonHTML, deMath };')('');

const mkLesson = texts => ({ sections_json: JSON.stringify([{ title: '证据与数字', sentences: texts.map(text => ({ text })) }]) });

const CASES = [
  { name: '线上实际观察(NRR):$H = 0.91$ bits', text: 'maintains high output entropy ($H = 0.91$ bits, near the $1.0$-bit maximum), while $H = 0.15$ collapses.',
    wantGone: ['$H = 0.91$', '$1.0$', '$H = 0.15$'], wantKept: ['H = 0.91', '1.0-bit', 'H = 0.15'], expectNoDollar: true },
  { name: '希腊字母与上下标', text: 'the $\\alpha$-phase decays as $x^2_i$ under $T_{c}$.',
    wantGone: ['$\\alpha$', '$x^2_i$', '$T_{c}$'], wantKept: ['x^2_i'], expectNoDollar: true },
  { name: '金融货币绝不动(board-4)', text: 'the Fed raised $5 billion and later $10 billion in facilities.',
    wantGone: [], wantKept: ['$5 billion', '$10 billion'] },
  { name: '单个未配对 $ 不动', text: 'it costs $100 million overall.', wantGone: [], wantKept: ['$100 million'] },
  { name: '标题面(线上实测 arxiv:1310.5162)', text: '$C1$-Genericity of Symplectic Diffeomorphisms and Lower Bounds',
    wantGone: ['$C1$'], wantKept: ['C1-Genericity'], expectNoDollar: true },
  { name: '不等式数学(线上实测——P18 首版启发式盲区;原始文本,由 escLike 统一转义)', text: 'for dimensions $0 < m < d$ the bound holds.',
    wantGone: ['$0 < m < d$'], wantKept: ['0 < m < d'], expectNoDollar: true },
  { name: '两美元额夹不等号(审查者对抗用例——散文有整词,收紧后货币必须保留)', text: 'prices moved from $5 < previous high and $9 later.',
    wantGone: [], wantKept: ['$5 <', '$9 later'] },
];

let fail = 0;
console.log('抽取自:', WORKER);
// escLike 镜像发货 esc 对 &<> 的转义:夹具一律写【原始文本】,由这里统一转义一次再匹配。
// (P18 R1 硬伤 D2:不等式夹具写成预转义形态又被二次转义,变成永不匹配的空转夹具——本结构性修复杜绝整类问题。)
const escLike = t => t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
for (const c of CASES) {
  const html = lessonHTML(mkLesson([c.text]));
  const badLeft = c.wantGone.filter(g => html.includes(escLike(g)));
  const missing = c.wantKept.filter(k => !html.includes(escLike(k)));
  const dollarLeak = c.expectNoDollar && html.includes('$');
  if (badLeft.length || missing.length || dollarLeak) { fail++; console.log(`  ❌ [${c.name}] 裸残留=${JSON.stringify(badLeft)} 误删=${JSON.stringify(missing)} 硬断言$泄漏=${!!dollarLeak}`); }
  else console.log(`  ✅ [${c.name}]`);
}
// 负控:旧渲染(esc(x.text) 无 deMath)必保留裸 $——证明夹具承重
{
  // 逐字复现修复前的句渲染:`<p>${esc(x.text)}</p>`
  const escOnly = new Function('t', escSrc + '\n return esc(t);');
  const t = CASES[0].text;
  const oldHtml = `<p>${escOnly(t)}</p>`;
  const stillHas = ['$H = 0.91$', '$1.0$'].every(g => oldHtml.includes(g));
  if (!stillHas) { fail++; console.log('  ❌ 负控失效:旧渲染本应保留裸 $ 却没有——夹具不判别,断言不承重'); }
  else console.log('     ↳ 负控成立:旧渲染(esc-only,无 deMath)在同一夹具保留裸 $H = 0.91$/$1.0$');
}
// 静态:发货源 lessonHTML 句子 + itemPage 摘要段都必须经 deMath(线上残留 3 处裸 $ 正是摘要段漏掉的教训)
if (!/esc\(deMath\(x\.text\)\)/.test(SRC)) { fail++; console.log('  ❌ 发货源 lessonHTML 未经 deMath 渲染句子'); }
else console.log('  ✅ 发货源 lessonHTML 句渲染走 esc(deMath(x.text))');
if (!/esc\(deMath\(item\.summary\)\)/.test(SRC)) { fail++; console.log('  ❌ 发货源 itemPage 摘要段未经 deMath——首版修复正是漏了它,线上残留 3 处裸 $'); }
else console.log('  ✅ 发货源 itemPage 摘要段走 esc(deMath(item.summary))');
// P18:标题面(线上实测 $C1$-Genericity 裸呈现于搜索/看板/条目 h1/浏览器 tab)。列表行 slice 必须在 deMath 之后。
const TITLE_PINS = [
  ['itemListHTML 列表行', /esc\(deMath\(it\.title\)\.slice\(0, 110\)\)/],
  ['radar 列表行(R1 前误标为 history)', /esc\(deMath\(it\.title\)\.slice\(0, 90\)\)/],
  ['history 列表行(真;R1 抓出漏修)', /esc\(deMath\(s\.title \|\| s\.item_id \|\| ''\)\.slice\(0, 70\)\)/],
  ['item/today 页 h1',    /esc\(deMath\(item\.title\)\)/],
  ['复习页 h1',           /esc\(deMath\(dueRow\.title\)\)/],
  ['浏览器 tab 标题(渲染点)', /esc\(deMath\(opts\.title\)\)/],
  ['itemPage tab 传参(slice 在 deMath 后,防孤 $)', /title: deMath\(item\.title\)\.slice\(0, 40\)/],
];
for (const [name, re] of TITLE_PINS) {
  if (!re.test(SRC)) { fail++; console.log(`  ❌ 发货源标题面未过 deMath: ${name}`); }
  else console.log(`  ✅ 标题面走 deMath: ${name}`);
}

console.log(fail === 0 ? '\nPASS: 数学定界符剥净、货币保留,负控证明旧渲染保留裸 $。' : `\nFAIL: ${fail} 项`);
process.exit(fail === 0 ? 0 : 1);
