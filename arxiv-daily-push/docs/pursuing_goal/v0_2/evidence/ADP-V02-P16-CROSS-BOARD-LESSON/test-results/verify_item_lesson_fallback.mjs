#!/usr/bin/env node
// 载荷型再推导验证器：证明【每个板块每个条目都有可读讲义】——item/复习页无存储讲义时确定性现算
// buildLesson,而非旧行为的空盒 `<p></p>`。抽取【已部署】worker_cloud.js 的 splitSentences+buildLesson
// 实跑;负控：逐字复现旧的 reveal 选取逻辑,证明它对【无摘要且无存储讲义】的板块二/三/四条目产出空盒。
// 跑法：node arxiv-daily-push/tools/verify_item_lesson_fallback.mjs   退出 0=全过。不改数据、不联网。
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const WORKER = path.resolve(HERE, '..', 'deploy', 'cloudflare', 'worker_cloud.js');
const BOARD_NAMES = { 1: '板块一', 2: '板块二', 3: '板块三', 4: '板块四' };
const SRC = fs.readFileSync(WORKER, 'utf8');

function loadShipped() {
  const start = SRC.indexOf('function splitSentences');
  const end = SRC.indexOf('async function makeLesson');
  if (start < 0 || end < 0 || end <= start) throw new Error('无法定位 splitSentences..makeLesson——锚点变了,改验证器别让它空过');
  // eslint-disable-next-line no-new-func
  return new Function('BOARD_NAMES', SRC.slice(start, end) + '\n return { buildLesson, splitSentences };')(BOARD_NAMES);
}

// 现网 reveal 选取：新(现算回退) vs 旧(空盒)。lessonHTML 用不到,这里只判「内容是否为空」。
function newRevealNonEmpty(stored, item, buildLesson) {
  const lesson = stored || { sections_json: JSON.stringify(buildLesson(item)) };
  const secs = JSON.parse(lesson.sections_json);
  // 八段每段至少一句(含回退)→ 现算讲义永不空
  return secs.length === 8 && secs.every(s => s.sentences && s.sentences.length >= 1);
}
function oldRevealInner(stored, item) {
  // 逐字复现修复前 itemPage/reviewPage 的三元选取(stored 存在才渲染,否则退摘要 500 字)
  return stored ? '<<lessonHTML>>' : `<p>${(item.summary || '').slice(0, 500)}</p>`;
}

const { buildLesson } = loadShipped();
const FIXTURES = [
  { name: 'board3 政策(无摘要,如国务院批复)', it: { title: '国务院关于《扩大消费"十五五"规划》的批复', board_id: 3, categories: '', summary: '' }, emptyOld: true },
  { name: 'board2 期刊(无摘要)',            it: { title: 'Exogenous creatine promotes tumor metastasis', board_id: 2, categories: '', summary: '' }, emptyOld: true },
  { name: 'board1 arXiv(正常摘要)',         it: { title: 'NRR-Core', board_id: 1, categories: 'cs.CL,cs.AI', summary: 'Systems that optimize a single output risk losing ambiguity. With incomplete context, interpretations compress prematurely. We specify NRR as an interface. It reports H = 0.91 bits in a synthetic task.' }, emptyOld: false },
];

let fail = 0;
console.log('抽取自:', WORKER);
for (const fx of FIXTURES) {
  // 1) 修复后:无存储讲义也非空(八段齐、每段有句)
  const okNew = newRevealNonEmpty(null, fx.it, buildLesson);
  // 2) 负控:旧逻辑对无摘要条目产出空盒 `<p></p>`
  const oldInner = oldRevealInner(null, fx.it);
  const oldEmpty = oldInner === '<p></p>';
  if (!okNew) { fail++; console.log(`  ❌ [${fx.name}] 修复后现算讲义仍空/不足八段`); }
  else console.log(`  ✅ [${fx.name}] 修复后现算八段讲义非空`);
  if (fx.emptyOld) {
    if (!oldEmpty) { fail++; console.log(`  ❌ [${fx.name}] 负控失效:旧逻辑本应产空盒却没有(${oldInner.slice(0,40)})——夹具不判别,修复无意义`); }
    else console.log(`     ↳ 负控成立:旧逻辑此条产出空盒 <p></p>（正是线上观察到的缺陷）`);
  }
}
// 3) 静态:发货源 itemPage 与 reviewPage 都必须有现算回退,否则某一页仍空
const fallbackCount = (SRC.match(/stored \|\| \{ sections_json: JSON\.stringify\(buildLesson\(/g) || []).length;
if (fallbackCount < 2) { fail++; console.log(`  ❌ 发货源现算回退只出现 ${fallbackCount} 次(应 >=2: itemPage + reviewPage)`); }
else console.log(`  ✅ 发货源 itemPage+reviewPage 均有现算回退(${fallbackCount} 处)`);

console.log(fail === 0 ? '\nPASS: 每板块每条目都有非空讲义,负控证明旧逻辑对无摘要条目产空盒。' : `\nFAIL: ${fail} 项`);
process.exit(fail === 0 ? 0 : 1);
