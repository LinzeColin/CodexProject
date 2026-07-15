/**
 * ADP 云端入口 Worker（R6 + Tunnel 直连）
 * - 首选：反向代理到 Cloudflare Tunnel（adp-origin → 本机 127.0.0.1:8787），
 *   手机打开 adp.linzezhang.com 即是完整六主题系统本体。
 * - 兜底：本机睡眠/隧道断开时自动回落只读镜像（D1，本机单向推送）+
 *   回传队列（POST /grade → events_inbox，本机 `adp mirror pull` 过 FSRS）。
 * - 访问控制：无（Owner 2026-07-15 指令取消钥匙登录）。页面公开可读；
 *   本机 webapp 对隧道来访只放行「浏览+主动回忆」（remote_guard），
 *   如需私有化，推荐在仪表盘叠加 Cloudflare Access（见 README R6 节）。
 *   /grade 仍有每讲义每 UTC 日 1 条的防重上限。
 * - cron：刷新到期复习计数（失败不重试，本机心跳兜底）。
 */

// Tunnel 入口主机名（无 Worker 路由，经边缘直达本机）。
// 注意：该 CNAME 记录尚待 Owner 在对话里点名确认后创建——创建前 fetch 必失败，
// 所有请求走下方镜像兜底（这正是设计的降级路径，不是故障）。
const ORIGIN = 'https://adp-origin.linzezhang.com';

async function proxyFullSystem(request, url) {
  const headers = new Headers(request.headers);
  headers.set('x-adp-edge', 'adp-mirror-worker'); // 溯源用；本机守卫认 cf-connecting-ip
  const resp = await fetch(ORIGIN + url.pathname + url.search, {
    method: request.method,
    headers,
    body: (request.method === 'GET' || request.method === 'HEAD') ? undefined : request.body,
    // 5s 权衡：本机离线且 DNS 在时边缘立刻回 530（不吃满超时）；超时只兜
    // 「connector 在线但源站黑洞」的罕见情形——太短会把慢首字节误降级到镜像。
    signal: AbortSignal.timeout(5000),
  });
  // 502/503/504=connector 在线但本机服务挂；52x/530=隧道断——都回落镜像。
  // 500/501 属应用自身错误，直透不掩盖。
  if (resp.status >= 502) throw new Error('origin unavailable: ' + resp.status);
  return resp;
}

const PAGE = (title, body, extra = '') => `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${title} · ADP 镜像</title>
<style>
body{margin:0;background:#f3eee1;color:#4a3d28;font:15px/1.9 -apple-system,"PingFang SC",sans-serif}
header{padding:12px 16px;background:#fdfaf2;border-bottom:1px solid #d8cfba;display:flex;gap:10px;align-items:center}
header b{color:#2f2618}
nav a{color:#8a5c16;text-decoration:none;margin-right:12px}
main{max-width:720px;margin:0 auto;padding:14px 14px 40px}
.card{background:#fdfaf2;border:1px solid #d8cfba;border-radius:10px;padding:14px 16px;margin:12px 0}
h1{font-size:19px;color:#2f2618}h2{font-size:16px;color:#2f2618}
.mt{color:#8b7a5c;font-size:12.5px}
.badge{display:inline-block;border:1px solid #d8cfba;border-radius:999px;padding:1px 9px;font-size:12px}
button{min-height:44px;padding:8px 16px;border-radius:10px;border:1px solid #d8cfba;background:#fdfaf2;font-size:14.5px}
table{width:100%;border-collapse:collapse;font-size:13.5px}
td,th{padding:6px 8px;border-bottom:1px solid #e7dfcc;text-align:left;vertical-align:top}
footer{padding:10px 16px;color:#8b7a5c;font-size:11.5px}
</style></head><body>
<header><b>ADP 镜像</b><nav><a href="/">今天</a><a href="/queue">队列</a><a href="/system">系统</a></nav></header>
<main>${body}</main>
<footer>镜像兜底页：本机在线时会自动直连完整系统；当前本机离线或隧道未连，仍可浏览与评分（回传队列）。${extra}</footer>
</body></html>`;

const esc = (s) => String(s ?? '').replace(/[&<>"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

async function todayPage(env) {
  const lesson = await env.DB.prepare(
    'SELECT * FROM lessons_mirror ORDER BY as_of_date DESC LIMIT 1').first();
  const sel = await env.DB.prepare(
    'SELECT * FROM selections_mirror ORDER BY as_of_date DESC, run_id DESC LIMIT 1').first();
  const meta = await env.DB.prepare(
    "SELECT value FROM mirror_meta WHERE key='pushed_at'").first();
  let body = '';
  if (sel) {
    body += `<div class="card"><h2>为什么今天选它</h2><p>${esc(sel.abstain ? sel.abstain_reason : sel.why)}</p>
      <p class="mt">决策日期 ${esc(sel.as_of_date)} · ${sel.abstain ? '今日弃权' : '总分 ' + Number(sel.score).toFixed(1)}</p></div>`;
  }
  if (lesson) {
    const sections = JSON.parse(lesson.sections_json);
    body += `<div class="card"><h1>${esc(lesson.doc_title)}</h1>
      <p class="mt">讲义 ${esc(lesson.id)} · ${esc(lesson.generator)} · <a href="${esc(lesson.canonical_url)}">原文</a></p>`;
    for (const [i, s] of sections.entries()) {
      body += `<h2>${i + 1}. ${esc(s.title)}</h2><p>${esc(s.body)}</p>`;
    }
    body += `</div><div class="card"><h2>主动回忆（回传本机）</h2>
      <p class="mt">先复述，再自评。评分写入回传队列，本机下次 run/pull 时过 FSRS 排程——发送/浏览不算学会。</p>
      <p style="display:flex;gap:8px;flex-wrap:wrap">
        ${[['1','忘了'],['2','困难'],['3','良好'],['4','轻松']].map(([g, label]) =>
          `<button onclick="grade('${esc(lesson.id)}',${g})">${label}</button>`).join('')}
      </p><p id="r" class="mt"></p>
      <script>async function grade(id,g){
        const res=await fetch('/grade/'+encodeURIComponent(id)+'/'+g,{method:'POST'});
        const j=await res.json();
        document.getElementById('r').textContent = j.duplicate
          ? '今天已评过，未重复入队（#'+j.id+'）'
          : '已入回传队列（#'+j.id+'），本机同步后生效';
      }</script></div>`;
  } else {
    body += '<div class="card"><p>镜像为空：先在本机执行 <code>adp mirror push</code>。</p></div>';
  }
  return PAGE('今天', body, meta ? `镜像推送时间：${esc(meta.value)}` : '尚未推送');
}

async function queuePage(env) {
  const { results } = await env.DB.prepare(
    'SELECT r.*, l.doc_title FROM review_mirror r LEFT JOIN lessons_mirror l ON l.id = r.item_id ORDER BY r.due_at').all();
  const rows = (results || []).map((r) =>
    `<tr><td>${esc((r.doc_title || r.item_id).slice(0, 60))}</td>
     <td><span class="badge">${esc(r.evidence_state || '—')}</span></td>
     <td class="mt">${esc(r.due_at || '—')}</td></tr>`).join('');
  return PAGE('队列', `<div class="card"><h1>学习队列（镜像）</h1>
    <table><tr><th>条目</th><th>证据态</th><th>到期</th></tr>${rows || '<tr><td colspan="3">空</td></tr>'}</table>
    <p class="mt">状态编辑请在本机进行（镜像只读）。</p></div>`);
}

async function systemPage(env) {
  const { results } = await env.DB.prepare(
    'SELECT * FROM manifests_mirror ORDER BY run_id DESC LIMIT 14').all();
  const inbox = await env.DB.prepare(
    'SELECT COUNT(*) AS n FROM events_inbox WHERE applied=0').first();
  const due = await env.DB.prepare(
    "SELECT value FROM mirror_meta WHERE key='due_count'").first();
  const rows = (results || []).map((m) =>
    `<tr><td class="mt">${esc(m.run_id)}</td><td><span class="badge">${esc(m.result)}</span></td>
     <td class="mt">${esc(m.trigger_kind)}</td><td class="mt">${esc(m.note || '')}</td></tr>`).join('');
  return PAGE('系统', `<div class="card"><h1>运行真相（镜像）</h1>
    <p class="mt">待回传评分 ${inbox ? inbox.n : 0} 条 · 云端到期提醒计数 ${due ? esc(due.value) : '—'}（cron 刷新，失败不重试，本机心跳兜底）</p>
    <table><tr><th>运行</th><th>结果</th><th>触发</th><th>说明</th></tr>${rows}</table></div>`);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    // 镜像兜底页的评分（只有镜像页会调用 /grade）：永不代理，直接入回传队列
    if (request.method === 'POST' && url.pathname.startsWith('/grade/')) {
      const [, , lessonId, gradeRaw] = url.pathname.split('/');
      const grade = parseInt(gradeRaw, 10);
      if (!lessonId || !(grade >= 1 && grade <= 4)) {
        return Response.json({ error: 'bad request' }, { status: 422 });
      }
      const today = new Date().toISOString().slice(0, 10);
      const dup = await env.DB.prepare(
        "SELECT id FROM events_inbox WHERE lesson_id=? AND substr(created_at,1,10)=?")
        .bind(decodeURIComponent(lessonId), today).first();
      if (dup) return Response.json({ queued: false, duplicate: true, id: dup.id });
      const res = await env.DB.prepare(
        'INSERT INTO events_inbox (lesson_id, grade, created_at) VALUES (?, ?, ?)')
        .bind(decodeURIComponent(lessonId), grade, new Date().toISOString()).run();
      return Response.json({ queued: true, duplicate: false, id: res.meta.last_row_id });
    }

    // 首选：完整系统直连（Tunnel → 本机 8787）；失败自动回落下方镜像
    try {
      return await proxyFullSystem(request, url);
    } catch (e) {
      if (url.pathname.startsWith('/api/')) {
        return Response.json(
          { error: '完整系统离线（本机睡眠或隧道未连）；稍后重试，或刷新页面用镜像评分' },
          { status: 503 });
      }
    }

    if (url.pathname === '/queue') return new Response(await queuePage(env), { headers: { 'content-type': 'text/html; charset=utf-8' } });
    if (url.pathname === '/system') return new Response(await systemPage(env), { headers: { 'content-type': 'text/html; charset=utf-8' } });
    if (url.pathname === '/') return new Response(await todayPage(env), { headers: { 'content-type': 'text/html; charset=utf-8' } });
    // 完整系统才有的页面（/radar /pilot /corrections /evidence…）：兜底时如实说明，不冒充
    return new Response(PAGE('离线', `<div class="card"><h1>该页面仅完整系统提供</h1>
      <p>本机离线或隧道未连，此页暂不可用。可先看 <a href="/">今天（镜像）</a>、<a href="/queue">队列</a> 或 <a href="/system">系统</a>。</p></div>`),
      { status: 503, headers: { 'content-type': 'text/html; charset=utf-8' } });
  },

  async scheduled(event, env) {
    // 复习提醒轻任务：统计镜像中已到期条目数，写入 mirror_meta（失败不重试）
    const now = new Date().toISOString();
    const due = await env.DB.prepare(
      'SELECT COUNT(*) AS n FROM review_mirror WHERE due_at IS NOT NULL AND due_at <= ?')
      .bind(now).first();
    await env.DB.batch([
      env.DB.prepare("INSERT OR REPLACE INTO mirror_meta (key, value) VALUES ('due_count', ?)")
        .bind(String(due ? due.n : 0)),
      env.DB.prepare("INSERT OR REPLACE INTO mirror_meta (key, value) VALUES ('due_checked_at', ?)")
        .bind(now),
    ]);
  },
};
