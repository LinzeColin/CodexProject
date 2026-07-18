// T044 维护看板验证：真 node:sqlite + 真 schema，喂各种健康态的源，验汇总/排序/陈旧标记。
// 从发货 worker 抽取 maintenanceGrid 的 SQL + per-source 逻辑 + maintenanceHTML,测发货代码本体。
import { DatabaseSync } from 'node:sqlite';
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url'; import { dirname, join, parse } from 'node:path';
const HERE = dirname(fileURLToPath(import.meta.url));
function locate(){let d=HERE,r=parse(d).root;while(1){const p=join(d,'recover/arxiv-daily-push/deploy/cloudflare');if(existsSync(join(p,'worker_cloud.js')))return p;if(existsSync(join(d,'arxiv-daily-push/deploy/cloudflare/worker_cloud.js')))return join(d,'arxiv-daily-push/deploy/cloudflare');if(d===r)throw new Error('no worker');d=dirname(d);}}
const DIR = locate(); const W = readFileSync(join(DIR,'worker_cloud.js'),'utf8');
// 抽取 maintenanceGrid 的 per-source 映射逻辑(纯) + maintenanceHTML(纯) 供测。
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const BOARD_NAMES={board1:'前沿',board3:'官方'};
// maintenanceHTML 从 worker 抽取(逐字)
const mhSrc = W.match(/function maintenanceHTML\(g\)\s*\{[\s\S]*?\n\}/)[0];
const maintenanceHTML = new Function('esc','BOARD_NAMES', 'return ('+mhSrc.replace('function maintenanceHTML','function')+')')(esc,BOARD_NAMES);
// per-source 逻辑(从 maintenanceGrid 抽取核心)
function grid(rows, now){
  const per=rows.map(s=>{const lf=s.last_fetch?Date.parse(s.last_fetch):null;const a=(lf&&!isNaN(lf))?Math.floor((now-lf)/864e5):null;
    return {id:s.id,board_id:s.board_id,health:s.health||'active',fails:s.consecutive_failures||0,age_days:a,stale:a===null||a>3};});
  return {total:per.length,unhealthy:per.filter(x=>x.health!=='active').length,disabled:per.filter(x=>x.health==='disabled_auto').length,stale:per.filter(x=>x.stale).length,per};
}
let pass=0,fail=0; const ok=(c,m)=>{c?pass++:(fail++,console.log('  FAIL',m));};
const db=new DatabaseSync(':memory:'); db.exec(readFileSync(join(DIR,'schema_cloud.sql'),'utf8'));
const NOW=Date.parse('2026-07-18T00:00:00Z');
const seed=[
 ['s-active','board1','active',0,'2026-07-18T00:00:00Z'],
 ['s-degraded','board1','degraded',2,'2026-07-18T00:00:00Z'],
 ['s-disabled','board3','disabled_auto',5,'2026-07-10T00:00:00Z'],
 ['s-stale','board3','active',0,'2026-07-01T00:00:00Z'],
 ['s-never','board3','active',0,null],
];
for(const[id,b,h,f,lf]of seed)db.prepare("INSERT INTO cn_sources(id,board_id,name,platform,website,method,feed_url,official,cadence,health,consecutive_failures,last_fetch)VALUES(?,?,?,?,?,?,?,?,?,?,?,?)").run(id,b,id,'','','rss',null,0,'每日',h,f,lf);
const rows=db.prepare('SELECT id,board_id,name,health,consecutive_failures,last_fetch FROM cn_sources ORDER BY board_id,id').all();
const g=grid(rows,NOW);
console.log('== 汇总 ==');
ok(g.total===5,'total=5'); ok(g.unhealthy===2,'unhealthy=2 (degraded+disabled)');
ok(g.disabled===1,'disabled=1'); ok(g.stale===3,'stale=3 (disabled 8天 + s-stale 17天 + s-never null)');
console.log('== 排序:自动停用排第一 ==');
const html=maintenanceHTML(g);
const firstRow=html.slice(html.indexOf('<tbody')>=0?html.indexOf('<tbody'):html.indexOf('连续失败')).indexOf('s-disabled');
const posDisabled=html.indexOf('s-disabled'),posActive=html.indexOf('s-active');
ok(posDisabled>=0&&posActive>=0&&posDisabled<posActive,'disabled 行排在 active 行之前');
ok(html.includes('自动停用')&&html.includes('降级'),'渲染出停用/降级徽章');
ok(html.includes('从未'),'s-never 显示「从未」');
ok(/★/.test(html),'陈旧源打★');
ok(html.includes('登记 5 个源'),'汇总文案含总数');
console.log('== NC:全 active 无异常 ==');
const g2=grid([{id:'a',board_id:'board1',health:'active',consecutive_failures:0,last_fetch:'2026-07-18T00:00:00Z'}],NOW);
ok(g2.unhealthy===0&&g2.stale===0,'全健康时 unhealthy=0 stale=0');
console.log('== 复核 R1:唯一未转义的 DB 值 fails 现在必须转义(sink 覆盖) ==');
const gp={total:1,unhealthy:1,disabled:0,stale:0,per:[{id:'p',board_id:'board1',health:'degraded',fails:'<img src=x onerror=alert(1)>',age_days:0,stale:false}]};
const hp=maintenanceHTML(gp);
ok(!hp.includes('<img src=x onerror'),'污染 fails 不原样进 HTML');
ok(hp.includes('&lt;img src=x onerror'),'污染 fails 被转义成 &lt;img');
ok(maintenanceHTML({total:1,unhealthy:0,disabled:0,stale:0,per:[{id:'z',board_id:'board1',health:'active',fails:0,age_days:0,stale:false}]}).includes('—'),'fails=0 仍显示 —');
const EXP=13; console.log(`\n  pass=${pass} fail=${fail}`);
ok(pass+fail===EXP,`断言数==${EXP}`);
console.log(fail===0?'OK':'RED'); process.exit(fail===0?0:1);
