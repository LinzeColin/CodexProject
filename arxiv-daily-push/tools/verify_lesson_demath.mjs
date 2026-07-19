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
    wantGone: ['$H = 0.91$', '$1.0$', '$H = 0.15$'], wantKept: ['H = 0.91', '1.0-bit', 'H = 0.15'] },
  { name: '希腊字母与上下标', text: 'the $\\alpha$-phase decays as $x^2_i$ under $T_{c}$.',
    wantGone: ['$\\alpha$', '$x^2_i$', '$T_{c}$'], wantKept: ['x^2_i'] },
  { name: '金融货币绝不动(board-4)', text: 'the Fed raised $5 billion and later $10 billion in facilities.',
    wantGone: [], wantKept: ['$5 billion', '$10 billion'] },
  { name: '单个未配对 $ 不动', text: 'it costs $100 million overall.', wantGone: [], wantKept: ['$100 million'] },
];

let fail = 0;
console.log('抽取自:', WORKER);
for (const c of CASES) {
  const html = lessonHTML(mkLesson([c.text]));
  const badLeft = c.wantGone.filter(g => html.includes(g.replace(/&/g,'&amp;')));
  const missing = c.wantKept.filter(k => !html.includes(k));
  if (badLeft.length || missing.length) { fail++; console.log(`  ❌ [${c.name}] 裸残留=${JSON.stringify(badLeft)} 误删=${JSON.stringify(missing)}`); }
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

console.log(fail === 0 ? '\nPASS: 数学定界符剥净、货币保留,负控证明旧渲染保留裸 $。' : `\nFAIL: ${fail} 项`);
process.exit(fail === 0 ? 0 : 1);
