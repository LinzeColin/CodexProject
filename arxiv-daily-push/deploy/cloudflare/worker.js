/**
 * ADP 云端镜像 Worker（R6）
 * - 只读镜像：今天学什么 / 队列 / 系统（D1，本机单向推送）
 * - 唯一可写：POST /grade → events_inbox（本机 `adp mirror pull` 回传并过 FSRS）
 * - 访问控制：owner key 的 sha256 哈希存于 D1 mirror_meta（明文只在本机
 *   data/authorization/cloud_owner_key.txt）；无 key 一律 401；Owner 首次带 ?key=
 *   访问后种 HttpOnly cookie。可再叠加 Cloudflare Access（见 RUNBOOK-R6）。
 *   轮换：本机重生成 key → adp mirror push 会同步新哈希。
 * - cron：刷新到期复习计数（失败不重试，本机心跳兜底）。
 */

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
<footer>云端为只读镜像+回传队列；主库与闭环在本机（断网时本机照常）。${extra}</footer>
</body></html>`;

async function sha256Hex(text) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

async function ownerKeyHash(env) {
  const row = await env.DB.prepare(
    "SELECT value FROM mirror_meta WHERE key='owner_key_sha256'").first();
  return row ? row.value : null;
}

async function presentedKey(request) {
  const url = new URL(request.url);
  const key = url.searchParams.get('key');
  if (key) return key;
  const cookie = request.headers.get('Cookie') || '';
  const match = cookie.match(/adpk=([A-Za-z0-9_-]+)/);
  return match ? match[1] : null;
}

async function authorized(request, env) {
  const expected = await ownerKeyHash(env);
  if (!expected) return { ok: false, configured: false };
  const key = await presentedKey(request);
  if (!key) return { ok: false, configured: true };
  const hash = await sha256Hex(key);
  return { ok: hash === expected, configured: true, key };
}

function deny() {
  return new Response(PAGE('未授权', '<div class="card"><h1>401 · 仅 Owner 可访问</h1><p>请使用带访问钥匙的专属链接打开（?key=…），钥匙在本机 data/authorization/cloud_owner_key.txt。</p></div>'),
    { status: 401, headers: { 'content-type': 'text/html; charset=utf-8' } });
}

function withCookie(resp, key) {
  if (key) {
    resp.headers.append('Set-Cookie',
      `adpk=${key}; Path=/; Max-Age=31536000; Secure; HttpOnly; SameSite=Lax`);
  }
  return resp;
}

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
    const auth = await authorized(request, env);
    if (!auth.configured) {
      return new Response('owner key not configured: run `adp mirror push` locally first',
        { status: 503 });
    }
    if (!auth.ok) return deny();

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

    let resp;
    if (url.pathname === '/queue') resp = new Response(await queuePage(env), { headers: { 'content-type': 'text/html; charset=utf-8' } });
    else if (url.pathname === '/system') resp = new Response(await systemPage(env), { headers: { 'content-type': 'text/html; charset=utf-8' } });
    else resp = new Response(await todayPage(env), { headers: { 'content-type': 'text/html; charset=utf-8' } });
    return withCookie(resp, auth.key || null);
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
