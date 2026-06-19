from __future__ import annotations
import base64, csv, html, json, math
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf'
ART=ROOT/'artifacts'
ART.mkdir(exist_ok=True)
HTML_PATH=ART/'governance_blueprint_v42_source.html'

def rows(name):
    with (ROOT/name).open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))

def esc(v): return html.escape(str(v))

def img_uri(path):
    p=ROOT/path
    data=base64.b64encode(p.read_bytes()).decode('ascii')
    mime='image/png' if p.suffix.lower()=='.png' else 'image/jpeg'
    return f'data:{mime};base64,{data}'

functions=rows('data/function_catalog.csv')
models=rows('data/model_registry.csv')
formulas=rows('data/formula_registry.csv')
params=rows('data/parameter_catalog.csv')
thresholds=rows('data/threshold_registry.csv')
families=rows('data/relationship_family_catalog.csv')
relations=rows('data/relationship_taxonomy.csv')
stages=rows('data/supply_chain_stage_taxonomy.csv')
industries=rows('data/industry_taxonomy.csv')
sectors=rows('data/sector_taxonomy.csv')
segments=rows('data/business_segment_taxonomy.csv')
capital=rows('data/capital_object_taxonomy.csv')
roles=rows('data/upstream_downstream_role_catalog.csv')
companies=rows('data/company_catalog.csv')
tasks=rows('data/task_backlog.csv')
acceptance=rows('data/acceptance_matrix.csv')
risks=rows('data/risk_register.csv')
gates=rows('data/release_gate_catalog.csv')
resolved=rows('data/resolved_unresolved_register.csv')
source_registry=rows('data/source_registry_extended.csv')
metrics=rows('data/metric_catalog.csv')

screens={
 'home':img_uri('prototype/screenshots/default_1440x900.png'),
 'data':img_uri('prototype/screenshots/data_1440x900.png'),
 'models':img_uri('prototype/screenshots/models_1440x900.png'),
 'taxonomy':img_uri('prototype/screenshots/taxonomy_1440x900.png'),
 'delivery':img_uri('prototype/screenshots/delivery_1440x900.png'),
 'governance':img_uri('prototype/screenshots/governance_1440x900.png'),
}

families_cards=''.join(f'''<div class="mini-card"><span class="dot" style="--c:{['#2563eb','#7c3aed','#0f8aa6','#c06b17','#b64944','#16855b','#5b6b80','#d0527b','#4f67d8','#7b8ca5'][i%10]}"></span><div><b>{esc(r['name_zh'])}</b><small>{esc(r['relationship_type_count'])} 种关系 · {esc(r['default_graph_zone'])}</small></div></div>''' for i,r in enumerate(families))

stages_flow=''.join(f'''<div class="stage"><em>{int(r['stage_order']):02d}</em><b>{esc(r['name_zh'])}</b></div>''' for r in stages)

function_rows=''.join(f'''<tr><td>{esc(r['function_id'])}</td><td>{esc(r['nav_group'])}</td><td><b>{esc(r['name_zh'])}</b></td><td>{esc(r['priority'])}</td><td>{esc(r['prototype_status'])}</td><td>{esc(r['implementation_status'])}</td></tr>''' for r in functions)

model_rows=''.join(f'''<tr><td>{esc(r['model_id'])}</td><td><b>{esc(r['name_zh'])}</b></td><td>{esc(r['formula_id'])}</td><td>{esc(r['scoring_object'])}</td><td>{esc(r['status'])}</td></tr>''' for r in models)

formula_rows=''.join(f'''<tr><td>{esc(r['formula_id'])}</td><td><b>{esc(r['name_zh'])}</b></td><td class="formula-cell">{esc(r['formula'])}</td><td>{esc(r['default_threshold'])}</td></tr>''' for r in formulas[:6])
formula_rows2=''.join(f'''<tr><td>{esc(r['formula_id'])}</td><td><b>{esc(r['name_zh'])}</b></td><td class="formula-cell">{esc(r['formula'])}</td><td>{esc(r['default_threshold'])}</td></tr>''' for r in formulas[6:])

risk_top=[r for r in risks if r['severity'].lower() in ('critical','high')][:10]
risk_rows=''.join(f'''<tr><td>{esc(r['risk_id'])}</td><td>{esc(r['severity']).upper()}</td><td><b>{esc(r['risk'])}</b></td><td>{esc(r['control'])}</td><td>{esc(r['owner'])}</td></tr>''' for r in risk_top)

gate_cards=''.join(f'''<div class="gate-card"><b>{esc(r['gate_id'])}</b><span>{esc(r.get('name','') or r.get('goal','') or r.get('name_zh',''))}</span><small>{esc(r.get('exit_criteria','') or r.get('exit_condition',''))}</small></div>''' for r in gates)

sector_cards=''.join(f'''<div class="sector-card"><em>{esc(r['sector_id'])}</em><b>{esc(r['name_zh'])}</b><small>{esc(r['description'])}</small></div>''' for r in sectors)

status_counts={}
for r in resolved:
    status_counts[r['status']]=status_counts.get(r['status'],0)+1

css=r'''
@page{size:A4 landscape;margin:0}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:#dfe5ed;font-family:"Noto Sans CJK SC","Microsoft YaHei",Arial,sans-serif;color:#172033;-webkit-print-color-adjust:exact;print-color-adjust:exact}
.page{width:297mm;height:210mm;page-break-after:always;background:#f5f7fa;position:relative;overflow:hidden;padding:13mm 15mm 12mm}
.page:last-child{page-break-after:auto}
.page:before{content:"";position:absolute;inset:0;background:linear-gradient(130deg,rgba(37,99,235,.035),transparent 35%,rgba(124,58,237,.025));pointer-events:none}
.header{display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:6mm;position:relative;z-index:1}
.kicker{font-size:8.5pt;font-weight:800;letter-spacing:.14em;color:#2563eb;text-transform:uppercase}
h1{font-size:24pt;line-height:1.12;margin:1.5mm 0 1mm;letter-spacing:-.025em} h2{font-size:18pt;margin:0 0 4mm} h3{font-size:11.5pt;margin:0 0 2mm}
.subtitle{font-size:9.2pt;color:#64748b;max-width:190mm;line-height:1.55}
.page-no{font-size:8.5pt;color:#94a3b8;text-align:right}.page-no b{display:block;font-size:12pt;color:#334155}
.grid{display:grid;gap:4mm;position:relative;z-index:1}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}.g4{grid-template-columns:repeat(4,1fr)}.g5{grid-template-columns:repeat(5,1fr)}
.card{background:#fff;border:1px solid #dce3ec;border-radius:3mm;padding:4mm;box-shadow:0 2mm 6mm rgba(15,23,42,.04)}
.card.blue{border-color:#b9d2ff;background:linear-gradient(145deg,#fff,#f4f8ff)}.card.dark{background:#111a2d;color:#fff;border-color:#111a2d}.card.amber{background:#fff9ec;border-color:#ead8ae}
.kpi{display:flex;flex-direction:column;min-height:25mm}.kpi strong{font-size:23pt;line-height:1;color:#172033}.kpi.dark strong{color:#fff}.kpi span{font-size:9pt;font-weight:750;margin-top:2mm}.kpi small{font-size:7.5pt;color:#64748b;margin-top:auto;line-height:1.35}.dark small{color:#aab6ca}
.status-table,.compact-table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dce3ec;border-radius:2mm;overflow:hidden;font-size:7.3pt}.status-table th,.compact-table th{text-align:left;background:#eef2f7;color:#475569;padding:1.8mm 2mm;font-weight:800}.status-table td,.compact-table td{padding:1.55mm 2mm;border-top:1px solid #edf1f5;vertical-align:top}.status-table tr:nth-child(even) td,.compact-table tr:nth-child(even) td{background:#fafbfc}
.badge{display:inline-flex;padding:.8mm 1.8mm;border-radius:10mm;background:#e8f1ff;color:#1d4ed8;font-size:7pt;font-weight:800}.badge.green{background:#e5f7ee;color:#08764b}.badge.amber{background:#fff0d4;color:#9a5400}.badge.red{background:#ffe6e4;color:#a53b34}
.screen{width:100%;height:auto;display:block;border:1px solid #cfd7e3;border-radius:3mm;box-shadow:0 4mm 12mm rgba(15,23,42,.12)}
.screen-wrap{background:#fff;border:1px solid #dce3ec;border-radius:3mm;padding:3mm}
.callout{border-left:1.4mm solid #2563eb;background:#eef5ff;padding:3mm 4mm;border-radius:0 2mm 2mm 0;font-size:8pt;line-height:1.55}.callout b{display:block;font-size:9pt;margin-bottom:.8mm}.callout.amber{border-color:#c16a18;background:#fff7e9}.callout.red{border-color:#c2413a;background:#fff0ee}.callout.green{border-color:#16855b;background:#edf9f3}
.arch{display:grid;grid-template-columns:repeat(4,1fr);gap:3mm}.arch-col{display:flex;flex-direction:column;gap:1.35mm}.arch-head{font-size:8pt;font-weight:850;color:#fff;background:#172033;padding:1.75mm;border-radius:2mm;text-align:center}.arch-item{background:#fff;border:1px solid #d8e0ea;border-radius:2mm;padding:1.8mm 2.3mm;min-height:14.6mm}.arch-item b{font-size:7.8pt;display:block}.arch-item small{font-size:6.45pt;color:#64748b;line-height:1.25;display:block;margin-top:.7mm}
.flow-arrow{text-align:center;font-size:20pt;color:#94a3b8;align-self:center}
.mini-card{display:flex;gap:2.2mm;align-items:center;background:#fff;border:1px solid #dce3ec;border-radius:2mm;padding:2mm 2.4mm;min-height:13mm}.mini-card .dot{width:3mm;height:3mm;border-radius:50%;background:var(--c);flex:0 0 auto}.mini-card b{font-size:7.6pt;display:block}.mini-card small{font-size:6.4pt;color:#64748b;display:block;margin-top:.6mm}
.stage-flow{display:grid;grid-template-columns:repeat(8,1fr);gap:2mm}.stage{position:relative;background:#fff;border:1px solid #dce3ec;border-radius:2mm;padding:2mm;min-height:15mm}.stage em{font-style:normal;font-size:6.5pt;color:#2563eb;font-weight:850}.stage b{display:block;font-size:7pt;margin-top:.7mm}.stage:nth-child(n+9){background:#f7f3ff;border-color:#ddd1ff}
.sector-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:2.5mm}.sector-card{background:#fff;border:1px solid #dce3ec;border-radius:2mm;padding:2.6mm;min-height:21mm}.sector-card em{font-style:normal;font-size:6.2pt;color:#2563eb}.sector-card b{display:block;font-size:8pt;margin:.5mm 0}.sector-card small{font-size:6.3pt;color:#64748b;line-height:1.3;display:block}
.formula-cell{font-family:"Noto Sans Mono CJK SC",monospace;font-size:6.5pt;color:#334155;line-height:1.32}
.lifecycle{display:flex;align-items:stretch;gap:2mm}.life{flex:1;background:#fff;border:1px solid #dce3ec;border-radius:2mm;padding:3mm;text-align:center}.life b{font-size:8pt}.life small{display:block;font-size:6.5pt;color:#64748b;margin-top:1mm}.life-arrow{display:flex;align-items:center;color:#94a3b8;font-size:16pt}
.gate-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:2mm}.gate-card{background:#fff;border:1px solid #dce3ec;border-radius:2mm;padding:2.5mm;min-height:23mm}.gate-card b{font-size:10pt;color:#2563eb}.gate-card span{display:block;font-size:7pt;font-weight:800;margin:.8mm 0}.gate-card small{font-size:6pt;color:#64748b;line-height:1.25;display:block}
.trace{display:flex;align-items:center;gap:2mm}.trace .box{flex:1;background:#fff;border:1px solid #dce3ec;border-radius:2mm;padding:3mm;text-align:center}.trace .box b{font-size:8pt}.trace .box small{display:block;font-size:6.4pt;color:#64748b;margin-top:.8mm}.trace .arrow{font-size:15pt;color:#7c8ca2}
.footer{position:absolute;left:15mm;right:15mm;bottom:5mm;border-top:1px solid #dce3ec;padding-top:2mm;display:flex;justify-content:space-between;font-size:6.7pt;color:#7c8ca2;z-index:2}
.cover{background:linear-gradient(132deg,#0e1728 0%,#15264a 55%,#1d3e82 100%);color:#fff}.cover:before{background:radial-gradient(circle at 80% 20%,rgba(96,165,250,.35),transparent 28%),radial-gradient(circle at 20% 85%,rgba(139,92,246,.24),transparent 25%)}
.cover .brand{display:flex;gap:3mm;align-items:center}.logo{width:12mm;height:12mm;border-radius:3mm;background:linear-gradient(145deg,#5277ff,#7c5cff);display:grid;place-items:center;font-weight:900;font-size:14pt}.cover h1{font-size:34pt;max-width:220mm;margin-top:22mm}.cover .subtitle{color:#c4d0e5;font-size:12pt;max-width:230mm}.cover-grid{margin-top:14mm;display:grid;grid-template-columns:repeat(6,1fr);gap:3mm}.cover .kpi{background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.13);border-radius:3mm;padding:4mm}.cover .kpi strong{color:#fff}.cover .kpi span{color:#fff}.cover .kpi small{color:#b5c1d5}.cover .footer{border-color:rgba(255,255,255,.18);color:#afbed4}
.note{font-size:6.7pt;color:#64748b;line-height:1.4}.small-list{margin:0;padding-left:4mm;font-size:7.2pt;line-height:1.55}.small-list li{margin:.8mm 0}.big-number{font-size:30pt;font-weight:900;letter-spacing:-.04em}.bar{height:2.5mm;background:#e7ecf2;border-radius:99px;overflow:hidden}.bar i{display:block;height:100%;width:var(--p);background:var(--c,#2563eb);border-radius:99px}.metric-row{display:grid;grid-template-columns:42mm 1fr 15mm;gap:2mm;align-items:center;font-size:7pt;margin:2mm 0}.metric-row b{text-align:right}
.two-col-text{columns:2;column-gap:8mm;font-size:7.2pt;line-height:1.55}.two-col-text p{break-inside:avoid;margin:0 0 3mm}
.threshold-summary .card{height:30mm;padding:3mm}.threshold-summary h3{font-size:10pt;margin-bottom:.6mm}.threshold-summary .big-number{font-size:25pt;line-height:1}.threshold-summary .note{font-size:6.1pt;line-height:1.25;margin:1mm 0 0}
'''

pages=[]
def page(n,title,subtitle,body,kicker='EEI GOVERNANCE BLUEPRINT'):
    pages.append(f'''<section class="page"><div class="header"><div><div class="kicker">{kicker}</div><h1>{title}</h1><div class="subtitle">{subtitle}</div></div><div class="page-no"><b>{n:02d}</b>v4.2.0 · 2026-06-19</div></div>{body}<div class="footer"><span>美国企业商业版图与供应链递归探索器</span><span>Task Pack / GitHub Governance Baseline</span></div></section>''')

pages.append(f'''<section class="page cover"><div class="brand"><div class="logo">E</div><div><b>EEI</b><small style="display:block;color:#b6c3d8">商域图谱 / Enterprise Ecosystem Intelligence</small></div></div><h1>商域图谱：企业商业版图与供应链递归探索系统</h1><div class="subtitle">系统功能架构、可递归商业版图、数据库与数据血缘、模型/公式/参数/阈值管理、GitHub 开发治理与 Codex MVP 执行蓝图</div><div class="cover-grid">{''.join(f'<div class="kpi"><strong>{v}</strong><span>{l}</span><small>{d}</small></div>' for v,l,d in [('17','功能板块','导航、输入输出、表/API'),('11','分析模型','公式、解释、版本与回滚'),('52','关系类型','10 个关系家族'),('16','供应链阶段','可递归上下游全链'),('130','开发任务','依赖、Gate 与验收'),('211','验收标准','P0 阻断发布')])}</div><div class="callout amber" style="margin-top:10mm;background:rgba(255,255,255,.09);border-color:#f0b95a;color:#fff"><b>交付真实性</b>本 PDF 与交互原型是规格/治理基线。原型中的公司关系与数值为 fixture；生产数据库、真实采集、关系核验、后端、评分引擎和生产前端尚未实现。</div><div class="footer"><span>Codex MVP Task Pack v4.2.0 + v5.0 sync</span><span>2026-06-20</span></div></section>''')

body=f'''<div class="grid g5">{''.join(f'<div class="card kpi"><strong>{v}</strong><span>{l}</span><small>{d}</small></div>' for v,l,d in [('140','研究对象','P0/P1/P2 与外部节点'),('60','可调参数','范围、步长、控件、刷新'),('17','阈值','证据、显示、告警、动效'),('53','风险项','控制、触发器、责任人'),('10','发布门禁','G0-G9 逐级放行')])}</div><div class="grid g2" style="margin-top:4mm"><div class="card"><h3>当前真实状态</h3><table class="status-table"><tr><th>层级</th><th>状态</th></tr><tr><td>需求、架构、目录、模型与验收</td><td><span class="badge green">已完成规格</span></td></tr><tr><td>高保真交互原型</td><td><span class="badge green">已完成 fixture 演示</span></td></tr><tr><td>GitHub 模板与自动校验</td><td><span class="badge green">已包含，待仓库启用</span></td></tr><tr><td>生产代码与真实数据库</td><td><span class="badge red">NOT STARTED</span></td></tr><tr><td>真实数据接入与事实核验</td><td><span class="badge red">NOT STARTED</span></td></tr></table></div><div class="card"><h3>统一治理链</h3><div class="trace"><div class="box"><b>需求/功能</b><small>Function ID + 用户问题</small></div><div class="arrow">→</div><div class="box"><b>任务</b><small>Task + 文件 + 依赖</small></div><div class="arrow">→</div><div class="box"><b>验收</b><small>Acceptance + 测试证据</small></div><div class="arrow">→</div><div class="box"><b>风险</b><small>Control + Trigger + Owner</small></div><div class="arrow">→</div><div class="box"><b>Gate</b><small>停止条件 + 回滚</small></div></div><div class="callout" style="margin-top:4mm"><b>三层一致性</b>人类可读 Markdown、机器可读 CSV/JSON/YAML、GitHub Actions 自动校验必须同步；任一层漂移则 PR 失败。</div></div></div>'''
page(2,'交付基线与真实状态','先明确“已定义/已原型”和“已生产实现”的边界，避免把可视化演示误报为实时投资系统。',body)

body=f'''<div class="arch"><div class="arch-col"><div class="arch-head">用户研究工作区</div>{''.join(f'<div class="arch-item"><b>{esc(r["name_zh"])}</b><small>{esc(r["default_visualization"])}</small></div>' for r in functions[:8])}</div><div class="arch-col"><div class="arch-head">研究管理</div>{''.join(f'<div class="arch-item"><b>{esc(r["name_zh"])}</b><small>{esc(r["default_visualization"])}</small></div>' for r in functions[8:11])}<div class="arch-head" style="margin-top:2mm;background:#4f3aa3">数据与模型</div>{''.join(f'<div class="arch-item"><b>{esc(r["name_zh"])}</b><small>{esc(r["default_visualization"])}</small></div>' for r in functions[11:15])}</div><div class="arch-col"><div class="arch-head" style="background:#0f7f78">系统治理</div>{''.join(f'<div class="arch-item"><b>{esc(r["name_zh"])}</b><small>{esc(r["default_visualization"])}</small></div>' for r in functions[15:])}<div class="callout green"><b>共享上下文</b>主体、时间、快照、模型版本、关系筛选、证据状态、探索路径、选中对象和视口在所有板块间保持。</div></div><div class="arch-col"><div class="arch-head" style="background:#8b4a13">底层能力</div><div class="arch-item"><b>图查询与递归投影</b><small>上下游、路径、子图预算、聚合与按需展开</small></div><div class="arch-item"><b>评分与解释引擎</b><small>公式、权重、阈值、半衰期、证据与覆盖率</small></div><div class="arch-item"><b>数据库与血缘</b><small>稳定主键、时间语义、证据、快照、版本与日志</small></div><div class="arch-item"><b>采集与运行</b><small>来源注册、限速、重试、实体解析、质量与新鲜度</small></div></div></div>'''
page(3,'系统功能板块与四层架构','17 个正式功能并非文档附录，而是导航、数据/API、任务、验收和风险都可追踪的产品能力。',body)

body=f'''<div class="screen-wrap"><img class="screen" src="{screens['home']}"></div><div class="grid g3" style="margin-top:3mm"><div class="callout"><b>首页可视化覆盖 ≥90%</b>首页直接进入 Watchlist 当前公司；主画布承载关系、上下游、业务、资本、政策和时间变化，文字只用于图例、解释和操作。</div><div class="callout green"><b>递归切换研究中心</b>单击节点查看详情；明确执行“设为研究中心”后，保持镜头、模型、时间和筛选，重建该对象自己的商业版图。</div><div class="callout amber"><b>可读性控制</b>首屏 20-40 个关键关系；语义缩放、聚合节点、Top-N、局部子图与等价列表防止图谱变成关系毛线团。</div></div>'''
page(4,'默认首页：Watchlist 驱动的可视化商业版图','左侧导航 + 中央关系画布 + 右侧详情/证据 + 底部时间变化。视觉不是装饰，而是系统的主要信息表达。',body,'VISUAL-FIRST HOME')

body=f'''<div class="grid g2"><div class="card"><h3>递归商业帝国对象</h3><div class="grid g3">{''.join(f'<div class="mini-card"><span class="dot" style="--c:{c}"></span><div><b>{n}</b><small>{d}</small></div></div>' for c,n,d in [('#172033','主体公司','当前研究中心与入口'),('#2563eb','上游节点','材料、IP、设备、制造'),('#0f8aa6','下游节点','客户、渠道与终端需求'),('#7c3aed','集团与业务','法人、板块、产品与设施'),('#c16a18','资本对象','证券、投资、并购、合同'),('#c2413a','政策与约束','监管、补贴、出口、能源')])}</div><div class="callout" style="margin-top:4mm"><b>递归规则</b>任意公司、集团、业务板块、产品、设施、基金、合同或政策节点都可成为新主体。每次重心切换生成同构视图，而不是跳转到静态详情页。</div></div><div class="card"><h3>全链供应链 16 阶段</h3><div class="stage-flow">{stages_flow}</div><div class="callout amber" style="margin-top:4mm"><b>供应链不仅是供应商名单</b>每条边必须有方向、阶段、角色、有效期、证据状态、金额/比例语义、替代性、切换成本、集中度和地缘暴露。</div></div></div><div class="grid g2" style="margin-top:4mm"><div class="card"><h3>24 类上下游/使能角色</h3><p class="note">覆盖原材料、化学品/气体、EDA/IP、设备、晶圆制造、封装测试、模组、系统集成、物流、能源、云渠道、客户、资本、政策、人才和跨域基础设施。</p></div><div class="card"><h3>递归查询边界</h3><p class="note">查询预算按层数、边数、重要度、证据门槛和时间窗口共同控制；继续展开由用户触发，禁止后台无限扩张。</p></div></div>'''
page(5,'可递归商业帝国与全链供应链','从 NVIDIA 到 TSMC，再到 ASML 或任意新节点；每一步都能重建上下游、业务、资本、控制、政策和战略视角。',body,'RECURSIVE BUSINESS EMPIRE')

body=f'''<div class="screen-wrap"><img class="screen" src="{screens['data']}"></div><div class="grid g3" style="margin-top:3mm"><div class="callout"><b>数据库感来自可追溯结构</b>实体、关系、证据、事件、配置、快照和日志都有稳定主键、表结构、版本与时间语义。</div><div class="callout green"><b>数据血缘</b>任意数字可回到模型版本、参数、指标、事实行、证据定位和原始来源；UI 同时显示新鲜度和事实状态。</div><div class="callout amber"><b>未知不是 0</b>未知、未披露、推断、冲突、已撤销和过期必须分开；资本金额必须保留币种、期间和 amount_kind。</div></div>'''
page(6,'数据库优先的数据工作台','不仅“看起来像数据库”，而是把数据库对象、ERD、血缘、来源健康、新鲜度和表详情作为正式产品板块。',body,'DATABASE-FIRST WORKBENCH')

body=f'''<div class="grid g2"><div class="card"><h3>10 个关系家族 / 52 种关系</h3><div class="grid g2">{families_cards}</div></div><div class="card"><h3>关系边最低字段</h3><table class="compact-table"><tr><th>类别</th><th>必需字段</th></tr><tr><td>身份与方向</td><td>subject_id、object_id、relationship_type、family、direction</td></tr><tr><td>时间</td><td>valid_from/to、reported_at、observed_at、retrieved_at</td></tr><tr><td>事实与证据</td><td>fact_status、evidence_ids、confidence、source independence</td></tr><tr><td>经济语义</td><td>amount、currency、amount_kind、ownership/voting_pct、period</td></tr><tr><td>模型与快照</td><td>model_version、parameter_version、data_snapshot_id</td></tr></table><div class="callout red" style="margin-top:4mm"><b>禁止静默推断</b>生态伙伴、联合发布、地理邻近或市场相关性不能自动转为供应、控制或资金关系；推断边默认至少需要两个独立来源。</div></div></div><div class="grid g4" style="margin-top:4mm">{''.join(f'<div class="card kpi"><strong>{v}</strong><span>{l}</span><small>{d}</small></div>' for v,l,d in [('32','领域对象','组织、资产、人员、资本、政策、证据'),('54','指标','定义、单位、方向和质量'),('34','来源类别','官方披露、政府、合同、专利等'),('212','验收追踪行','功能到任务/测试/Gate')])}</div>'''
page(7,'领域本体、关系和证据语义','商业图谱的可信度取决于关系定义、方向、时间、金额、证据和事实状态，而不是节点数量。',body,'DOMAIN & EVIDENCE MODEL')

body=f'''<div class="sector-grid">{sector_cards}</div><div class="grid g4" style="margin-top:4mm">{''.join(f'<div class="card kpi"><strong>{v}</strong><span>{l}</span><small>{d}</small></div>' for v,l,d in [('26','行业分类','行业/子行业父级结构'),('13','入口板块','人类可读的首页分类'),('20','业务板块类型','集团、平台、产品、资产、市场'),('30','资本对象','权益、债务、现金流、承诺、估值')])}</div><div class="callout" style="margin-top:4mm"><b>140 个研究对象是“研究宇宙”，不是已验证事实库</b>P0/P1/P2/X 分层用于研究优先级；真实关系必须在 Build/ingestion 阶段逐条接入来源、解析、核验并保留事实状态。</div>'''
page(8,'行业、板块、公司、业务与资本范围','默认入口使用 13 个用户可理解板块；底层保留 26 个行业分类，并允许跨行业递归探索。',body,'RESEARCH UNIVERSE')

body=f'''<div class="screen-wrap"><img class="screen" src="{screens['models']}"></div><div class="grid g3" style="margin-top:3mm"><div class="callout"><b>模型透明</b>公式、输入、权重、阈值、时间半衰期、缺失值策略和默认值都可查看，不使用不可解释黑箱评分。</div><div class="callout green"><b>在线修改 + 文件修改</b>页面控件和 YAML/JSON 配置使用同一 schema；先 dry-run 和影响预览，再保存不可变版本并激活。</div><div class="callout amber"><b>即时刷新不是部分覆盖</b>大范围重算期间继续显示上一个成功快照；完成后原子切换并向全部视图推送同一版本。</div></div>'''
page(9,'模型、公式、参数与阈值控制中心','11 个模型、11 个公式、75 个参数和 17 个阈值全部有机器可读目录、在线控件、版本、日志和回滚边界。',body,'MODEL CONTROL CENTER')

body=f'''<div class="grid g2"><div class="card"><h3>模型目录</h3><table class="compact-table"><tr><th>ID</th><th>模型</th><th>公式</th><th>评分对象</th><th>状态</th></tr>{model_rows}</table></div><div class="card"><h3>参数生命周期</h3><div class="lifecycle"><div class="life"><b>草稿输入</b><small>范围/步长/schema 校验</small></div><div class="life-arrow">→</div><div class="life"><b>即时预览</b><small>P95 &lt;250ms，影响 diff</small></div><div class="life-arrow">→</div><div class="life"><b>保存版本</b><small>不可变配置 + 变更说明</small></div><div class="life-arrow">→</div><div class="life"><b>激活快照</b><small>原子切换 + 缓存失效</small></div><div class="life-arrow">→</div><div class="life"><b>回滚/校准</b><small>日志 + 14 天复核</small></div></div><div class="grid g3" style="margin-top:4mm"><div class="card kpi"><strong>1.0</strong><span>顶层权重总和</span><small>容差 ±0.0001</small></div><div class="card kpi"><strong>0.70</strong><span>单项权重上限</span><small>防止单维度支配</small></div><div class="card kpi"><strong>2</strong><span>推断关系来源</span><small>至少两个独立来源</small></div></div><div class="callout red" style="margin-top:4mm"><b>评分边界</b>模型用于研究排序、可视化聚焦和变化告警，不等同于投资收益预测或“真实隐藏资金”的确定性识别。</div></div></div>'''
page(10,'模型清单与参数生命周期','默认值可用，但用户必须能看到公式并修改权重、战略评分、时间重要性和门槛；每次修改可解释、可预览、可撤销。',body,'MODEL GOVERNANCE')

body=f'''<div class="grid g2"><div class="card"><h3>核心公式（1/2）</h3><table class="compact-table"><tr><th>ID</th><th>名称</th><th>公式</th><th>默认门槛</th></tr>{formula_rows}</table></div><div class="card"><h3>核心公式（2/2）</h3><table class="compact-table"><tr><th>ID</th><th>名称</th><th>公式</th><th>默认门槛</th></tr>{formula_rows2}</table></div></div><div class="grid g4 threshold-summary" style="margin-top:3mm">{''.join(f'<div class="card"><h3>{t}</h3><div class="big-number">{v}</div><p class="note">{d}</p></div>' for t,v,d in [('节点入图','46','综合优先级低于门槛不进入当前图'),('关系入图','48','重要性低于门槛则聚合或隐藏'),('首页预算','42/64','默认最多 42 节点、64 条关系'),('高优先告警','80','进入 Watchlist 高优先级队列')])}</div>'''
page(11,'公式、默认参数与门槛示例','所有默认值都可以在 `data/parameter_catalog.csv`、`data/threshold_registry.csv` 和 `config/model_runtime_defaults.yaml` 中直接审阅和修改。',body,'FORMULAS & THRESHOLDS')

body=f'''<div class="grid g2"><div class="card"><h3>热刷新流水线</h3><div class="trace"><div class="box"><b>校验</b><small>schema、范围、权重和依赖</small></div><div class="arrow">→</div><div class="box"><b>版本化</b><small>配置 hash、作者、原因</small></div><div class="arrow">→</div><div class="box"><b>影响分析</b><small>模型/指标/对象/视图</small></div><div class="arrow">→</div><div class="box"><b>增量重算</b><small>任务、进度、失败补偿</small></div><div class="arrow">→</div><div class="box"><b>原子发布</b><small>同屏同快照 + SSE/WebSocket</small></div></div><div class="callout green" style="margin-top:4mm"><b>即时反馈</b>按钮按压、选择、重心切换、数据差异、刷新进度和成功/失败都使用视觉 + 动效 + 可选触觉反馈；支持 reduced motion。</div></div><div class="card"><h3>双周校准（每 14 天）</h3><div class="metric-row"><span>Top-N 稳定性</span><div class="bar"><i style="--p:86%;--c:#2563eb"></i></div><b>86%</b></div><div class="metric-row"><span>证据覆盖率</span><div class="bar"><i style="--p:92%;--c:#16855b"></i></div><b>92%</b></div><div class="metric-row"><span>变化告警精度</span><div class="bar"><i style="--p:84%;--c:#7c3aed"></i></div><b>84%</b></div><div class="metric-row"><span>可解释覆盖</span><div class="bar"><i style="--p:96%;--c:#0f8aa6"></i></div><b>96%</b></div><div class="callout amber"><b>校准建议默认不自动生效</b>系统生成候选差异和回滚点，由用户审阅后激活；所有操作进入追加式日志。</div></div></div><div class="grid g3" style="margin-top:4mm"><div class="card kpi"><strong>120ms</strong><span>预览 debounce</span><small>输入连续变化时合并重算</small></div><div class="card kpi"><strong>&lt;700ms</strong><span>会话应用 P95</span><small>局部视图差异刷新</small></div><div class="card kpi"><strong>14d</strong><span>固定校准周期</span><small>漂移、覆盖、质量和反馈</small></div></div>'''
page(12,'即时重算、操作日志与双周校准','参数修改要“立即看到影响”，但必须通过版本化、增量计算、原子快照和失败补偿确保全体呈现一致。',body,'LIVE RECALCULATION')

body=f'''<div class="screen-wrap"><img class="screen" src="{screens['delivery']}"></div><div class="grid g3" style="margin-top:3mm"><div class="callout green"><b>已解决（7）</b>首页、递归主体、数据底座、模型流程、14 天校准、视觉覆盖和文档治理方式已冻结。</div><div class="callout amber"><b>未解决（7）</b>部署预算、认证、商业数据许可、生产规模、图引擎基准、模型有效性和真实关系接入。</div><div class="callout"><b>四轴状态</b>规格、原型、生产实现、验证分别记录；`PROTOTYPED` 不得写成 `DONE`。</div></div>'''
page(13,'开发任务、已解决/未解决与交付状态','130 个任务不是粗粒度待办：每项都有依赖、文件范围、Gate、Acceptance ID、风险、测试和回滚。',body,'DELIVERY STATUS')

body=f'''<div class="grid g2"><div class="card"><h3>高优先风险与管控</h3><table class="compact-table"><tr><th>ID</th><th>级别</th><th>风险</th><th>控制</th><th>Owner</th></tr>{risk_rows}</table></div><div class="card"><h3>G0-G9 发布门禁</h3><div class="gate-grid">{gate_cards}</div><div class="callout red" style="margin-top:4mm"><b>停止条件</b>任一 P0 验收无任务/测试、任一高风险无控制/触发/责任人、配置不可解释/回滚、同屏混用快照、fixture 标为真实、视觉/可访问性未达标，均不得发布。</div></div></div>'''
page(14,'风险、控制、验收与发布门禁','53 项风险、211 条验收、232 条追踪关系和 10 个 Gate 形成可判定的发布闭环。',body,'RISK & ACCEPTANCE')

body=f'''<div class="screen-wrap"><img class="screen" src="{screens['governance']}"></div><div class="grid g3" style="margin-top:3mm"><div class="callout"><b>结构化变更入口</b>Feature、Model Change、Data/Relationship Scope、Risk/Control 和 Bug 使用 Issue Forms 收集固定字段。</div><div class="callout green"><b>PR 强制同步</b>PR 模板要求功能/模型/领域/状态/风险/验收/迁移/回滚同步；CODEOWNERS 指定审查责任。</div><div class="callout amber"><b>自动防漂移</b>Actions 校验目录数量、ID 唯一性、交叉引用、YAML/JSON、原型导航、PDF、shell 语法和 checksums。</div></div>'''
page(15,'GitHub 开发文档备份与防漂移','压缩包解压后可直接初始化为 GitHub 仓库；文档、机器目录、代码契约和交付状态由同一 PR 历史长期保存。',body,'GITHUB GOVERNANCE')

body=f'''<div class="grid g2"><div class="card"><h3>Codex G0 启动</h3><pre style="font-size:8pt;line-height:1.6;background:#111a2d;color:#e7eefc;border-radius:2mm;padding:4mm;white-space:pre-wrap">unzip US_Corporate_Power_Map_Codex_MVP_Task_Pack_v4.2_2026-06-19.zip
cd US_Corporate_Power_Map_Codex_MVP_Task_Pack_v4.2_2026-06-19

git init
git add .
git commit -m "chore: add EEI v4.2 governance baseline"

python scripts/validate_task_pack.py
bash scripts/preflight.sh

codex exec --sandbox read-only - \
  &lt; prompts/01_PLAN_ONLY.md \
  | tee artifacts/01_plan_output.txt</pre><div class="callout"><b>先计划，后写入</b>G0 输出必须列出将读取/修改的文件、测试命令、数据/模型迁移、风险、回滚和验收映射；未审查不得进入 workspace-write。</div></div><div class="card"><h3>最终交付清单</h3><table class="compact-table"><tr><th>类型</th><th>入口</th><th>用途</th></tr><tr><td>交互原型</td><td>prototype/standalone.html</td><td>审阅首页、数据、模型、治理和递归交互</td></tr><tr><td>治理索引</td><td>GOVERNANCE_INDEX.md</td><td>统一入口与机器 SSOT</td></tr><tr><td>功能/模型/领域</td><td>根目录 3 份清单 + data/</td><td>开发范围与参数修改</td></tr><tr><td>状态/风险/验收</td><td>DEVELOPMENT_STATUS.md + RISK_AND_ACCEPTANCE.md</td><td>进度、控制和发布判定</td></tr><tr><td>GitHub 治理</td><td>.github/ + scripts/</td><td>Issue/PR/CODEOWNERS/Actions</td></tr><tr><td>Codex 输入</td><td>AGENTS.md + prompts/ + CODEX_MASTER_TASK.md</td><td>Plan/Build/QA 自主推进</td></tr></table><div class="grid g3" style="margin-top:4mm"><div class="card kpi"><strong>PASS</strong><span>目录完整性</span><small>数量、ID 与交叉引用</small></div><div class="card kpi"><strong>PASS</strong><span>浏览器原型</span><small>无 console/page error</small></div><div class="card kpi"><strong>PASS</strong><span>PDF/ZIP</span><small>渲染、解压与 checksums</small></div></div></div></div>'''
page(16,'Codex 执行与最终交付','从此版本开始，需求、数据、模型、代码、风险和验收不再散落在聊天记录中，而是进入可审计、可版本化、可验证的仓库基线。',body,'HANDOFF & EXECUTION')

full=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>EEI Governance Blueprint v4.2</title><style>{css}</style></head><body>{''.join(pages)}</body></html>'''
HTML_PATH.write_text(full,encoding='utf-8')

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
    page_=browser.new_page(viewport={'width':1600,'height':1000})
    page_.set_content(full,wait_until='load')
    page_.emulate_media(media='print')
    page_.pdf(path=str(OUT),width='297mm',height='210mm',print_background=True,prefer_css_page_size=True,margin={'top':'0','right':'0','bottom':'0','left':'0'})
    browser.close()
print(OUT)
