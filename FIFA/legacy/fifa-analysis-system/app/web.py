from typing import Any, Dict


def dashboard_html() -> str:
    return """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>2026 FIFA World Cup 情报分析系统</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f4f6f8;
      --panel: #ffffff;
      --ink: #1b1f24;
      --muted: #667085;
      --line: #d8dee8;
      --accent: #0f766e;
      --accent-soft: #d9f4ef;
      --warn: #a15c00;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
    }
    header {
      padding: 24px 32px 18px;
      border-bottom: 1px solid var(--line);
      background: var(--panel);
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 20px;
    }
    h1 { margin: 0; font-size: 24px; line-height: 1.2; }
    .sub { margin-top: 6px; color: var(--muted); font-size: 14px; }
    main { padding: 24px 32px 40px; max-width: 1400px; margin: 0 auto; }
    .grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    .metric { color: var(--muted); font-size: 13px; }
    .value { font-size: 28px; font-weight: 700; margin-top: 6px; }
    .layout { display: grid; grid-template-columns: 1.2fr .8fr; gap: 14px; margin-top: 14px; }
    h2 { font-size: 16px; margin: 0 0 12px; }
    table { width: 100%; border-collapse: collapse; font-size: 14px; }
    th, td { text-align: left; padding: 10px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { color: var(--muted); font-weight: 600; font-size: 12px; }
    a { color: var(--accent); text-decoration: none; }
    button {
      border: 1px solid var(--accent);
      background: var(--accent);
      color: white;
      border-radius: 6px;
      padding: 9px 12px;
      font-weight: 650;
      cursor: pointer;
    }
    .ghost { background: white; color: var(--accent); }
    .actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .badge { display: inline-block; padding: 3px 8px; border-radius: 999px; background: var(--accent-soft); color: var(--accent); font-size: 12px; }
    .warning { color: var(--warn); font-size: 13px; margin-top: 10px; }
    @media (max-width: 900px) {
      header { padding: 18px; display: block; }
      main { padding: 18px; }
      .grid, .layout { grid-template-columns: 1fr; }
      .actions { margin-top: 14px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>2026 FIFA World Cup 情报分析系统</h1>
      <div class="sub">48 支球队 · 默认公开信息源 · 每 4 小时自动刷新 · 概率分析与报告生成</div>
    </div>
    <div class="actions">
      <button onclick="runRefresh()">立即刷新</button>
      <button class="ghost" onclick="location.href='/docs'">API 文档</button>
    </div>
  </header>
  <main>
    <section class="grid">
      <div class="panel"><div class="metric">参赛球队</div><div class="value" id="teams">-</div></div>
      <div class="panel"><div class="metric">启用信息源</div><div class="value" id="sources">-</div></div>
      <div class="panel"><div class="metric">入库新闻/情报</div><div class="value" id="articles">-</div></div>
      <div class="panel"><div class="metric">分析报告</div><div class="value" id="reports">-</div></div>
    </section>
    <section class="layout">
      <div class="panel">
        <h2>动态刷新状态</h2>
        <table>
          <tbody>
            <tr><th>运行状态</th><td id="refresh-running">-</td></tr>
            <tr><th>刷新频率</th><td id="refresh-interval">-</td></tr>
            <tr><th>最近刷新</th><td id="refresh-last">-</td></tr>
            <tr><th>下次刷新</th><td id="refresh-next">-</td></tr>
            <tr><th>刷新摘要</th><td id="refresh-summary">-</td></tr>
          </tbody>
        </table>
        <div class="warning">说明：系统会自动采集默认公开源。赔率/TAB 等平台数据只有在授权和条款允许时才会接入。</div>
      </div>
      <div class="panel">
        <h2>信息源</h2>
        <table>
          <thead><tr><th>名称</th><th>类型</th><th>状态</th></tr></thead>
          <tbody id="source-list"></tbody>
        </table>
      </div>
    </section>
    <section class="layout">
      <div class="panel">
        <h2>最新新闻/情报</h2>
        <table>
          <thead><tr><th>标题</th><th>来源</th><th>时间</th></tr></thead>
          <tbody id="article-list"></tbody>
        </table>
      </div>
      <div class="panel">
        <h2>最新报告</h2>
        <table>
          <thead><tr><th>报告</th><th>生成时间</th></tr></thead>
          <tbody id="report-list"></tbody>
        </table>
      </div>
    </section>
  </main>
  <script>
    async function getJson(url) {
      const res = await fetch(url);
      if (!res.ok) throw new Error(url + ' ' + res.status);
      return await res.json();
    }
    function text(value) { return value === null || value === undefined || value === '' ? '-' : value; }
    async function loadDashboard() {
      const [summary, refresh, sources, articles, reports] = await Promise.all([
        getJson('/api/dashboard'),
        getJson('/refresh/status'),
        getJson('/crawl-sources'),
        getJson('/news-articles'),
        getJson('/reports')
      ]);
      document.getElementById('teams').textContent = summary.teams_count;
      document.getElementById('sources').textContent = summary.enabled_sources_count;
      document.getElementById('articles').textContent = summary.news_articles_count;
      document.getElementById('reports').textContent = summary.reports_count;
      document.getElementById('refresh-running').innerHTML = refresh.running ? '<span class="badge">运行中</span>' : '<span class="badge">未运行</span>';
      document.getElementById('refresh-interval').textContent = refresh.interval_hours + ' 小时';
      document.getElementById('refresh-last').textContent = text(refresh.last_finished_at);
      document.getElementById('refresh-next').textContent = text(refresh.next_run_at);
      document.getElementById('refresh-summary').textContent = text(refresh.last_summary);
      document.getElementById('source-list').innerHTML = sources.slice(0, 8).map(s => `<tr><td>${s.name}</td><td>${s.source_type}</td><td>${s.enabled ? '启用' : '停用'}</td></tr>`).join('');
      document.getElementById('article-list').innerHTML = articles.slice(0, 10).map(a => `<tr><td>${a.url ? `<a href="${a.url}" target="_blank" rel="noreferrer">${a.title}</a>` : a.title}</td><td>${text(a.source)}</td><td>${text(a.published_at || a.created_at)}</td></tr>`).join('');
      document.getElementById('report-list').innerHTML = reports.slice(0, 10).map(r => `<tr><td><a href="/reports/${r.id}.md" target="_blank">${r.title}</a></td><td>${r.created_at}</td></tr>`).join('');
    }
    async function runRefresh() {
      await fetch('/refresh/run', { method: 'POST' });
      await loadDashboard();
    }
    loadDashboard();
    setInterval(loadDashboard, 60000);
  </script>
</body>
</html>"""


def dashboard_summary_payload(stats: Dict[str, Any]) -> Dict[str, Any]:
    return stats
