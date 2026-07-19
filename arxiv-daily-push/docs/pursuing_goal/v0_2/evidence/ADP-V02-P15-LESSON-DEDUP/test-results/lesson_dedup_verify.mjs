#!/usr/bin/env node
// 载荷型再推导验证器：抽取【已部署】worker_cloud.js 的 splitSentences+buildLesson 实跑，
// 证明修复后【同一句摘要绝不在多个讲义段落逐字重复】；并用【负控】证明该断言承重——
// pre-fix 旧逻辑在同一夹具上必然产生跨段重复。跑法：node arxiv-daily-push/tools/verify_lesson_dedup.mjs
// 退出 0=全过；非 0=失败(附原因)。不改数据、不联网、纯函数验证。
import fs from 'node:fs';
import path from 'node:path';
import url from 'node:url';

const HERE = path.dirname(url.fileURLToPath(import.meta.url));
const WORKER = path.resolve(HERE, '..', 'deploy', 'cloudflare', 'worker_cloud.js');
const BOARD_NAMES = { 1: '板块一', 2: '板块二', 3: '板块三', 4: '板块四' };

// —— 抽取【线上真实代码】：从 splitSentences 到 makeLesson 之间(含 buildLesson)，绝不复刻 ——
function loadShipped() {
  const src = fs.readFileSync(WORKER, 'utf8');
  const start = src.indexOf('function splitSentences');
  const end = src.indexOf('async function makeLesson');
  if (start < 0 || end < 0 || end <= start) throw new Error('无法在 worker 中定位 splitSentences..makeLesson 区间——锚点变了，改验证器别让它空过');
  const slice = src.slice(start, end);
  // eslint-disable-next-line no-new-func
  const factory = new Function('BOARD_NAMES', slice + '\n return { buildLesson, splitSentences };');
  return factory(BOARD_NAMES);
}

// —— 负控参照：P-DEDUP 之前的 buildLesson。取句逻辑(sents/numeric/limits/各段 slice)逐字保留旧版；
// 回退串换成 fb-* 占位、跨领域生成串缩短——两者都非摘要原句,crossSectionDupes 只数原句,对判别零影响。 ——
function buildLessonPreFix(it, splitSentences) {
  const sents = splitSentences(it.summary);
  const cats = (it.categories || '').split(',').filter(Boolean);
  const numeric = sents.filter(s => /\d/.test(s));
  const limits = sents.filter(s => /(however|but|limit|only|fail|不足|局限|但|然而|仅)/i.test(s));
  const sec = (title, arr, fallback) => ({ title, sentences: (arr.length ? arr : [fallback]).slice(0, 4).map(text => ({ text })) });
  return [
    sec('人话版', sents.slice(0, 2), `本文标题：${it.title}。摘要过短，请点原文精读。`),
    sec('领域脉络', cats.length ? [`本文类目：${cats.slice(0, 5).join('、')}，属于其所在研究脉络的最新进展。`] : sents.slice(2, 3), `来源板块：${BOARD_NAMES[it.board_id] || it.board_id}。`),
    sec('机制拆解', sents.slice(2, 5), 'fb-机制'),
    sec('证据与数字', numeric.slice(0, 3), 'fb-证据'),
    sec('反例与边界', limits, 'fb-反例'),
    sec('跨领域连接与意外收获', cats.length >= 2 ? [`横跨 ${cats.length} 个类目`] : [], 'fb-跨'),
    sec('可复用方法', [], 'fb-复用'),
    sec('术语表', [], 'fb-术语'),
  ];
}

// 找出【一句摘要文本出现在 >=2 个段落】的跨段重复(生成串/回退串各段唯一，不会误判)。
function crossSectionDupes(sections, abstractSents) {
  const setAbs = new Set(abstractSents);
  const seen = new Map(); // text -> [titles]
  for (const sec of sections) {
    for (const { text } of sec.sentences) {
      if (!setAbs.has(text)) continue; // 只看摘要原句，忽略生成/回退串
      if (!seen.has(text)) seen.set(text, []);
      seen.get(text).push(sec.title);
    }
  }
  return [...seen.entries()].filter(([, titles]) => titles.length >= 2)
    .map(([text, titles]) => ({ text: text.slice(0, 60) + '…', sections: titles }));
}

// —— 夹具 ——
const FIXTURES = [
  {
    name: 'INTSD(线上实际观察到重复的那篇)',
    it: {
      title: 'Benchmarking Nighttime Traffic Sign Recognition', board_id: 1, categories: 'cs.CV,cs.CY',
      summary: 'Traffic signboards are vital for road safety and intelligent transportation systems. Yet, recognizing traffic signs at night remains underexplored due to the scarcity of real-world public datasets capturing low-light degradations and distractor classes. Existing benchmarks are predominantly daytime and do not reflect challenges such as headlight glare, motion blur, sensor noise, and vandalized or ambiguous signage. To address these gaps, we introduce INTSD, a large-scale nighttime traffic sign dataset collected across diverse regions of India. INTSD contains street-level images spanning 41 traffic signboard classes, multiple distractor categories, and varied lighting and weather conditions, designed to support both detection and fine-grained classification under nighttime scenarios. Additionally, we present LENS-Net, a strong baseline that integrates an adaptive illumination-aware detector with a multimodal classifier.',
    },
    expectPreFixDup: true, // 旧逻辑必在此产生重复(数字句落在 slice(2,5))
  },
  {
    name: 'cats 为空(领域脉络回退到 sents[2:3] 与机制拆解重叠)',
    it: {
      title: 'No categories case', board_id: 2, categories: '',
      summary: 'This paper studies a system. The second sentence sets context here. The third sentence describes the core mechanism in detail. A fourth sentence adds more method description. A fifth closes it out cleanly.',
    },
    expectPreFixDup: true, // 旧逻辑：领域脉络=sents[2:3]、机制拆解=sents[2:5] → sents[2] 重复
  },
  {
    name: '数字句在开头(人话版与证据与数字重叠)',
    it: {
      title: 'Numeric in intro', board_id: 3, categories: 'stat.ML',
      summary: 'We evaluate across 5 datasets in this work. The context sentence follows without numbers here. Then a mechanism sentence with no digits at all. Another plain method sentence continues. Final wrap up sentence here.',
    },
    expectPreFixDup: true, // 旧逻辑：人话版=sents[0:2] 含数字句、证据与数字=numeric 也含它 → 重复
  },
];

// —— 执行 ——
let fail = 0;
const { buildLesson, splitSentences } = loadShipped();
console.log('抽取自:', WORKER);
for (const fx of FIXTURES) {
  const abs = splitSentences(fx.it.summary);
  const now = buildLesson(fx.it);
  const pre = buildLessonPreFix(fx.it, splitSentences);
  const dupNow = crossSectionDupes(now, abs);
  const dupPre = crossSectionDupes(pre, abs);
  const okNow = dupNow.length === 0;
  const okNC = fx.expectPreFixDup ? dupPre.length > 0 : true; // 负控：旧逻辑应产生重复
  if (!okNow) { fail++; console.log(`  ❌ [${fx.name}] 修复后仍有跨段重复:`, JSON.stringify(dupNow)); }
  else console.log(`  ✅ [${fx.name}] 修复后无跨段重复`);
  if (!okNC) { fail++; console.log(`  ❌ [${fx.name}] 负控失效：旧逻辑本应产生重复却没有——夹具不判别，断言不承重`); }
  else if (fx.expectPreFixDup) console.log(`     ↳ 负控成立：旧逻辑在此确产生重复 ${JSON.stringify(dupPre.map(d => d.sections))}`);
}
console.log(fail === 0 ? '\nPASS: 修复消除全部跨段重复，且负控证明断言承重。' : `\nFAIL: ${fail} 项`);
process.exit(fail === 0 ? 0 : 1);
