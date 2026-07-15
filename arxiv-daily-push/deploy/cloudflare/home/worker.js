/**
 * home.linzezhang.com —— Owner 个人主页（极简静态枢纽）。
 * 设计原则：干净整洁（Owner 指令）；无外部资源；明暗自适应；系统入口一目了然。
 */

const HTML = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Linze Zhang</title>
<meta name="color-scheme" content="light dark">
<meta name="robots" content="noindex">
<style>
:root{color-scheme:light dark;--bg:#faf9f6;--fg:#1c1b18;--mt:#8a8578;--line:#e6e2d8;--card:#ffffff;--accent:#8a5c16}
@media (prefers-color-scheme: dark){
  :root{--bg:#0e1014;--fg:#e8e6e1;--mt:#8b8fa0;--line:#23262e;--card:#151820;--accent:#d9b36a}
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:16px/1.8 -apple-system,"PingFang SC","Noto Sans SC",sans-serif;
  min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px}
main{width:100%;max-width:640px}
h1{font-size:28px;margin:0 0 4px;letter-spacing:.5px}
.sub{color:var(--mt);margin:0 0 36px;font-size:14.5px}
.card{display:block;background:var(--card);border:1px solid var(--line);border-radius:14px;
  padding:20px 22px;margin:14px 0;
  transition:transform .15s ease,border-color .15s ease}
.card:hover{transform:translateY(-2px);border-color:var(--accent)}
.card b{font-size:17px}
.card > a.title{color:var(--fg);text-decoration:none;display:block}
.card p{margin:6px 0 0;color:var(--mt);font-size:14px}
.boards{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;line-height:1.4}
.boards a{font-size:12.5px;color:var(--accent);text-decoration:none;
  border:1px solid var(--line);border-radius:999px;padding:4px 12px;white-space:nowrap}
.boards a:hover{border-color:var(--accent)}
footer{margin-top:40px;color:var(--mt);font-size:12px}
</style></head><body>
<main>
  <h1>Linze Zhang</h1>
  <p class="sub">个人系统入口</p>

  <div class="card">
    <a class="title" href="https://adp.linzezhang.com">
      <b>ADP · 前沿学习</b>
      <p>每日一篇精选 · 主动回忆 · 间隔复习 —— 五板块前沿雷达</p>
    </a>
    <div class="boards">
      <a href="https://adp.linzezhang.com/radar#board1">一 · 研究前沿</a>
      <a href="https://adp.linzezhang.com/radar#board2">二 · 顶级期刊</a>
      <a href="https://adp.linzezhang.com/radar#board3">三 · 中国政策法规</a>
      <a href="https://adp.linzezhang.com/radar#board4">四 · 美国科技金融</a>
      <a href="https://adp.linzezhang.com/radar#board5">五 · 跨板块总览</a>
    </div>
  </div>

  <footer>home.linzezhang.com</footer>
</main>
</body></html>`;

export default {
  async fetch(request) {
    const path = new URL(request.url).pathname;
    if (path === '/favicon.ico' || path === '/robots.txt') {
      return new Response(path === '/robots.txt' ? 'User-agent: *\nDisallow:\n' : null,
        { status: path === '/robots.txt' ? 200 : 204,
          headers: { 'content-type': 'text/plain; charset=utf-8' } });
    }
    return new Response(HTML, {
      headers: { 'content-type': 'text/html; charset=utf-8',
                 'cache-control': 'public, max-age=300' },
    });
  },
};
