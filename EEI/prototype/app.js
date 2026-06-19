const NS = 'http://www.w3.org/2000/svg';
const STORAGE_KEY = 'atlas-v42-prototype-state';
const companies = {
  nvidia: { name: 'NVIDIA', avatar: 'NV', industry: '半导体与 AI 基础设施', meta: '12 个重要变化', count: 12 },
  tsmc: { name: 'TSMC', avatar: 'TS', industry: '先进晶圆制造', meta: '8 个重要变化', count: 8 },
  asml: { name: 'ASML', avatar: 'AS', industry: '半导体设备', meta: '5 个重要变化', count: 5 },
  microsoft: { name: 'Microsoft', avatar: 'MS', industry: '云与 AI 平台', meta: '9 个重要变化', count: 9 },
  meta: { name: 'Meta', avatar: 'ME', industry: '互联网与 AI 基础设施', meta: '6 个重要变化', count: 6 }
};

const watchlistOrder = ['nvidia', 'tsmc', 'asml', 'microsoft', 'meta'];
const lenses = [
  ['empire', '商业全景'],
  ['supply', '供应链'],
  ['capital', '资金与交易'],
  ['control', '股权与控制'],
  ['policy', '政策与风险'],
  ['changes', '战略变化']
];

const defaultWeights = {
  supply: 28,
  strategy: 20,
  capital: 16,
  control: 12,
  policy: 10,
  technology: 8,
  recency: 6
};

const defaultThresholds = {
  minimumEdgeScore: 45,
  solidEvidence: 60,
  aggregationCount: 6,
  maxVisibleEdges: 40,
  staleHours: 72
};

const defaultVisual = {
  nodeScale: 100,
  edgeContrast: 92,
  labelDensity: 88,
  motion: true,
  haptic: true,
  autoNormalize: true
};

const datasets = {
  nvidia: {
    zones: [
      { id: 'upstream', x: 34, y: 150, w: 385, h: 320, title: '上游能力与关键投入', sub: 'IP / EDA · 设备 · 制造 · 存储 · 封装' },
      { id: 'core', x: 435, y: 150, w: 410, h: 320, title: 'NVIDIA 商业核心', sub: '平台 · 产品 · 软件 · 生态与基础设施', primary: true },
      { id: 'downstream', x: 861, y: 150, w: 385, h: 320, title: '下游渠道与需求', sub: '云平台 · 数据中心 · 行业客户 · 开发者生态' },
      { id: 'capital', x: 435, y: 28, w: 410, h: 105, title: '资本、治理与战略交易', sub: '投资 · 合作 · 并购 · 长期承诺' },
      { id: 'policy', x: 435, y: 488, w: 410, h: 125, title: '政策、能源与外部约束', sub: '出口管制 · 电力 · 地缘 · 政府政策' }
    ],
    nodes: [
      node('synopsys', 111, 212, 'Synopsys', 'EDA / IP', 'SY', 'technology', 76, 7, metrics(82,78,40,34,22,92,74)),
      node('cadence', 111, 294, 'Cadence', 'EDA / IP', 'CD', 'technology', 70, 6, metrics(76,74,35,30,20,90,70)),
      node('asml', 268, 188, 'ASML', '关键光刻设备', 'AS', 'supply', 91, 12, metrics(95,88,48,35,58,96,68)),
      node('tsmc', 274, 292, 'TSMC', '先进晶圆制造', 'TS', 'supply', 96, 18, metrics(98,96,68,46,72,97,82)),
      node('skhynix', 264, 397, 'SK hynix', '高带宽存储', 'SK', 'supply', 88, 10, metrics(92,86,60,30,42,91,84)),
      node('coherent', 113, 405, '光模块集群', '8 家关键节点', '08', 'supply', 67, 18, metrics(70,64,44,18,28,70,78)),
      node('nvidia', 640, 306, 'NVIDIA', '当前研究中心', 'NV', 'focus', 100, 42, metrics(100,100,100,100,100,100,100)),
      node('gpu', 518, 220, '加速计算', 'GPU / CPU / DPU', 'AI', 'business', 94, 14, metrics(86,98,78,70,32,95,90)),
      node('cuda', 516, 382, 'CUDA 生态', '软件与开发者锁定', 'CU', 'technology', 92, 20, metrics(64,98,52,55,24,96,91)),
      node('systems', 760, 219, 'AI 系统', 'DGX / NVL / 网络', 'DG', 'business', 89, 13, metrics(82,92,71,52,30,93,87)),
      node('ventures', 761, 381, '战略投资', '生态与资本连接', 'VC', 'capital', 78, 15, metrics(40,76,94,68,34,88,86)),
      node('microsoft', 1017, 188, 'Microsoft', '云平台与大客户', 'MS', 'customer', 92, 16, metrics(46,93,88,41,42,96,93)),
      node('aws', 1126, 278, 'AWS', '云平台与渠道', 'AW', 'customer', 87, 14, metrics(44,88,82,34,38,94,91)),
      node('meta', 1018, 362, 'Meta', 'AI 基础设施客户', 'ME', 'customer', 85, 12, metrics(42,86,84,30,36,92,89)),
      node('coreweave', 1124, 438, 'CoreWeave', '专用 AI 云', 'CW', 'capital', 81, 11, metrics(52,83,91,58,28,84,96)),
      node('enterprise', 1010, 447, '行业客户群', '汽车 / 医疗 / 工业', '23', 'customer', 74, 23, metrics(36,75,72,18,34,72,80)),
      node('export', 514, 545, '出口管制', '市场与产品约束', 'EX', 'policy', 88, 19, metrics(55,84,54,22,98,96,94)),
      node('energy', 643, 556, '能源与电网', '数据中心运营约束', 'EN', 'policy', 77, 15, metrics(68,72,60,18,86,81,88)),
      node('uspolicy', 770, 545, '产业政策', '补贴 / 许可 / 合规', 'US', 'policy', 79, 17, metrics(44,76,58,22,92,93,90)),
      node('softbank', 512, 78, 'SoftBank / ARM', '资本与架构生态', 'SB', 'capital', 74, 8, metrics(36,78,86,78,31,89,72)),
      node('mellanox', 640, 78, 'Mellanox', '并购形成的网络能力', 'MX', 'control', 84, 9, metrics(62,91,79,92,24,95,66)),
      node('partners', 768, 78, '生态投资组合', '18 个重点连接', '18', 'capital', 71, 18, metrics(38,72,88,61,28,74,85))
    ],
    edges: [
      edge('synopsys','gpu','芯片设计工具','technology',78,'reported'), edge('cadence','gpu','芯片设计工具','technology',72,'reported'),
      edge('asml','tsmc','光刻设备依赖','supply',94,'reported'), edge('tsmc','nvidia','先进制造与封装','supply',98,'reported'),
      edge('skhynix','nvidia','HBM 供应','supply',92,'reported'), edge('coherent','systems','高速互联组件','supply',68,'inferred'),
      edge('gpu','nvidia','核心产品平台','business',96,'reported'), edge('cuda','nvidia','软件生态与锁定','technology',94,'reported'),
      edge('nvidia','systems','系统级交付','business',90,'reported'), edge('nvidia','ventures','资本与生态扩张','capital',82,'reported'),
      edge('nvidia','microsoft','云部署与采购','customer',93,'reported'), edge('nvidia','aws','云渠道与实例','customer',89,'reported'),
      edge('nvidia','meta','大规模基础设施采购','customer',87,'reported'), edge('ventures','coreweave','投资与商业合作','capital',88,'reported'),
      edge('nvidia','enterprise','行业解决方案','customer',72,'inferred'), edge('export','nvidia','产品与市场限制','policy',91,'reported'),
      edge('energy','systems','算力扩张能源约束','policy',78,'inferred'), edge('uspolicy','nvidia','产业与合规影响','policy',82,'reported'),
      edge('softbank','nvidia','资本与架构关系','capital',74,'reported'), edge('mellanox','nvidia','并购控制关系','control',90,'reported'),
      edge('partners','ventures','战略投资组合','capital',73,'reported'), edge('tsmc','skhynix','先进封装协同','supply',75,'inferred'),
      edge('microsoft','coreweave','算力市场连接','capital',68,'inferred'), edge('aws','enterprise','云渠道触达','customer',66,'inferred')
    ]
  },
  tsmc: {
    zones: [
      { id: 'upstream', x: 34, y: 150, w: 385, h: 320, title: '设备、材料与工艺投入', sub: '光刻 · 刻蚀 · 沉积 · 化学品 · 硅片' },
      { id: 'core', x: 435, y: 150, w: 410, h: 320, title: 'TSMC 制造与产能网络', sub: '先进制程 · 成熟制程 · 封装 · 全球晶圆厂', primary: true },
      { id: 'downstream', x: 861, y: 150, w: 385, h: 320, title: '设计客户与终端需求', sub: 'AI · 移动 · 汽车 · 高性能计算' },
      { id: 'capital', x: 435, y: 28, w: 410, h: 105, title: '资本开支与全球扩产', sub: '台湾 · 美国 · 日本 · 欧洲' },
      { id: 'policy', x: 435, y: 488, w: 410, h: 125, title: '政策、能源与地缘约束', sub: '补贴 · 出口管制 · 电力 · 水资源' }
    ],
    nodes: [
      node('asml', 112, 190, 'ASML', 'EUV 光刻设备', 'AS', 'supply', 98, 16, metrics(100,96,70,34,74,98,80)),
      node('amat', 113, 282, 'Applied Materials', '沉积与工艺设备', 'AM', 'supply', 87, 12, metrics(90,85,52,26,48,94,76)),
      node('lam', 113, 382, 'Lam Research', '刻蚀与沉积', 'LR', 'supply', 86, 11, metrics(89,84,50,25,47,93,75)),
      node('materials', 280, 214, '材料与气体集群', '硅片 / 化学品 / 气体', '18', 'supply', 80, 18, metrics(83,80,46,16,55,78,74)),
      node('cadence', 282, 368, 'EDA / IP 生态', '设计流与工艺协同', 'IP', 'technology', 76, 14, metrics(70,79,38,20,34,85,72)),
      node('tsmc', 640, 306, 'TSMC', '当前研究中心', 'TS', 'focus', 100, 46, metrics(100,100,100,100,100,100,100)),
      node('advanced', 515, 220, '先进制程', '3nm / 2nm / GAA', '2N', 'business', 96, 15, metrics(98,96,86,70,72,97,92)),
      node('packaging', 515, 382, '先进封装', 'CoWoS / SoIC', 'PK', 'business', 94, 18, metrics(98,95,82,65,60,96,95)),
      node('globalfabs', 760, 220, '全球晶圆厂', '台湾 / 美国 / 日本', 'GF', 'business', 88, 19, metrics(86,90,91,62,84,94,86)),
      node('capacity', 760, 382, '产能分配', '客户与节点组合', 'CP', 'capital', 86, 13, metrics(90,88,88,72,54,86,90)),
      node('nvidia', 1013, 190, 'NVIDIA', 'AI 与高性能计算', 'NV', 'customer', 97, 18, metrics(86,98,88,35,62,97,93)),
      node('apple', 1125, 278, 'Apple', '移动与消费电子', 'AP', 'customer', 93, 17, metrics(78,94,84,32,44,96,86)),
      node('amd', 1013, 368, 'AMD', 'CPU / GPU 客户', 'AD', 'customer', 88, 12, metrics(76,90,74,26,38,94,88)),
      node('broadcom', 1124, 442, 'Broadcom', '网络与定制芯片', 'BC', 'customer', 84, 11, metrics(72,86,70,24,36,92,84)),
      node('automotive', 1014, 447, '汽车客户集群', '长期验证与成熟节点', '12', 'customer', 72, 12, metrics(64,73,58,18,42,76,68)),
      node('chips', 512, 544, '美国 CHIPS 激励', '扩产与本地化条件', 'US', 'policy', 88, 21, metrics(58,85,90,28,96,96,91)),
      node('taiwanpower', 640, 557, '台湾电力与水', '运营连续性约束', 'TW', 'policy', 84, 16, metrics(78,82,62,16,92,87,90)),
      node('export', 770, 544, '出口与技术管制', '客户与设备约束', 'EX', 'policy', 82, 18, metrics(66,80,52,18,94,94,93)),
      node('capex', 516, 78, '资本开支计划', '先进制程与封装扩张', 'CX', 'capital', 94, 22, metrics(84,96,98,42,56,96,94)),
      node('arizona', 640, 78, 'Arizona Fabs', '美国制造网络', 'AZ', 'capital', 90, 15, metrics(86,91,96,52,90,95,88)),
      node('japan', 768, 78, '日本与欧洲布局', '客户靠近与政策协同', 'JP', 'capital', 82, 14, metrics(76,84,88,46,86,91,82))
    ],
    edges: [
      edge('asml','advanced','EUV 关键设备','supply',98,'reported'), edge('amat','tsmc','制造设备','supply',88,'reported'),
      edge('lam','tsmc','刻蚀与沉积设备','supply',87,'reported'), edge('materials','tsmc','材料与气体','supply',82,'inferred'),
      edge('cadence','advanced','工艺设计协同','technology',77,'reported'), edge('advanced','tsmc','先进制造能力','business',97,'reported'),
      edge('packaging','tsmc','先进封装能力','business',95,'reported'), edge('tsmc','globalfabs','全球制造网络','business',90,'reported'),
      edge('tsmc','capacity','产能配置与承诺','capital',88,'reported'), edge('tsmc','nvidia','先进制造与封装','customer',98,'reported'),
      edge('tsmc','apple','芯片制造','customer',95,'reported'), edge('tsmc','amd','芯片制造','customer',90,'reported'),
      edge('tsmc','broadcom','芯片制造','customer',86,'reported'), edge('tsmc','automotive','成熟节点与长期供货','customer',73,'inferred'),
      edge('chips','arizona','补贴与本地化条件','policy',93,'reported'), edge('arizona','globalfabs','美国扩产','capital',92,'reported'),
      edge('taiwanpower','tsmc','能源与水资源约束','policy',86,'inferred'), edge('export','asml','设备与技术限制','policy',88,'reported'),
      edge('capex','tsmc','资本开支驱动','capital',96,'reported'), edge('japan','globalfabs','多地区扩产','capital',84,'reported'),
      edge('capacity','nvidia','先进产能分配','capital',88,'inferred'), edge('capacity','apple','先进产能分配','capital',86,'inferred')
    ]
  },
  asml: {
    zones: [
      { id: 'upstream', x: 34, y: 150, w: 385, h: 320, title: '超精密部件与材料', sub: '光学 · 光源 · 精密运动 · 计量与材料' },
      { id: 'core', x: 435, y: 150, w: 410, h: 320, title: 'ASML 技术与服务体系', sub: 'EUV · DUV · 计算光刻 · 服务网络', primary: true },
      { id: 'downstream', x: 861, y: 150, w: 385, h: 320, title: '晶圆厂客户与制程需求', sub: '逻辑 · 存储 · 先进制程 · 全球晶圆厂' },
      { id: 'capital', x: 435, y: 28, w: 410, h: 105, title: '研发投入与长期客户协同', sub: '研发 · 共同投资 · 交付承诺' },
      { id: 'policy', x: 435, y: 488, w: 410, h: 125, title: '出口许可与地缘约束', sub: '荷兰许可 · 美国规则 · 中国市场' }
    ],
    nodes: [
      node('zeiss', 111, 194, 'Carl Zeiss SMT', 'EUV 光学系统', 'CZ', 'supply', 100, 14, metrics(100,98,72,62,68,98,84)),
      node('trumpf', 112, 292, 'TRUMPF', '激光与光源部件', 'TR', 'supply', 91, 10, metrics(94,90,58,35,52,94,78)),
      node('vdl', 111, 393, '精密制造集群', '机械 / 运动 / 真空', '16', 'supply', 82, 16, metrics(86,82,48,22,42,80,76)),
      node('materials', 280, 234, '材料与子系统', '高纯材料与电子部件', '21', 'supply', 76, 21, metrics(78,76,42,16,38,72,74)),
      node('software', 282, 378, '计算与软件组件', '控制 / 仿真 / 计量', 'SW', 'technology', 84, 13, metrics(72,88,52,26,28,88,86)),
      node('asml', 640, 306, 'ASML', '当前研究中心', 'AS', 'focus', 100, 44, metrics(100,100,100,100,100,100,100)),
      node('euv', 515, 220, 'EUV 系统', '先进制程瓶颈能力', 'EU', 'business', 100, 19, metrics(100,100,96,70,88,99,92)),
      node('duv', 515, 382, 'DUV 系统', '成熟与先进制程基础', 'DU', 'business', 88, 14, metrics(88,86,76,54,62,96,70)),
      node('service', 760, 220, '装机与服务网络', '升级 / 维护 / 备件', 'SV', 'business', 93, 22, metrics(94,96,88,65,70,97,95)),
      node('rd', 760, 382, '研发与路线图', 'High-NA EUV', 'NA', 'capital', 96, 17, metrics(84,99,98,58,76,98,94)),
      node('tsmc', 1015, 188, 'TSMC', '先进逻辑客户', 'TS', 'customer', 100, 20, metrics(88,100,96,42,82,99,94)),
      node('samsung', 1123, 278, 'Samsung', '逻辑与存储客户', 'SS', 'customer', 92, 16, metrics(84,94,88,36,74,97,88)),
      node('intel', 1015, 368, 'Intel', '逻辑制造客户', 'IN', 'customer', 90, 15, metrics(82,92,90,34,80,96,90)),
      node('skhynix', 1124, 444, 'SK hynix', '存储制造客户', 'SK', 'customer', 84, 12, metrics(76,86,78,28,68,93,86)),
      node('chinafabs', 1014, 448, '中国晶圆厂群', '受许可限制市场', 'CN', 'customer', 73, 18, metrics(60,74,64,18,98,78,91)),
      node('nlpolicy', 512, 544, '荷兰出口许可', '设备交付与服务约束', 'NL', 'policy', 96, 22, metrics(62,94,70,18,100,98,96)),
      node('usrules', 640, 557, '美国技术规则', '跨境技术与市场影响', 'US', 'policy', 94, 20, metrics(58,92,68,18,100,97,95)),
      node('supplyrisk', 770, 544, '单点供应风险', '关键子系统集中', 'SR', 'policy', 90, 18, metrics(98,90,52,24,70,90,89)),
      node('highna', 514, 78, 'High-NA EUV', '下一代研发平台', 'HN', 'capital', 98, 17, metrics(94,100,99,64,80,98,96)),
      node('customerfund', 640, 78, '客户联合投入', '长期路线图协同', 'CF', 'capital', 86, 11, metrics(60,90,94,70,62,92,84)),
      node('capacity', 768, 78, '产能与交付扩张', '系统产量与服务能力', 'CP', 'capital', 90, 15, metrics(88,92,96,48,66,94,91))
    ],
    edges: [
      edge('zeiss','euv','关键光学系统','supply',100,'reported'), edge('trumpf','euv','激光光源能力','supply',94,'reported'),
      edge('vdl','asml','精密制造与装配','supply',84,'inferred'), edge('materials','asml','材料与电子子系统','supply',78,'inferred'),
      edge('software','asml','控制与计算组件','technology',86,'reported'), edge('euv','asml','核心产品平台','business',100,'reported'),
      edge('duv','asml','核心产品平台','business',90,'reported'), edge('asml','service','装机与全周期服务','business',95,'reported'),
      edge('asml','rd','研发与路线图投入','capital',97,'reported'), edge('asml','tsmc','设备交付与服务','customer',100,'reported'),
      edge('asml','samsung','设备交付与服务','customer',94,'reported'), edge('asml','intel','设备交付与服务','customer',93,'reported'),
      edge('asml','skhynix','设备交付与服务','customer',87,'reported'), edge('nlpolicy','asml','出口许可约束','policy',99,'reported'),
      edge('usrules','asml','技术规则影响','policy',96,'reported'), edge('supplyrisk','zeiss','关键子系统集中','policy',98,'reported'),
      edge('highna','rd','下一代研发','capital',99,'reported'), edge('customerfund','highna','客户路线图协同','capital',88,'reported'),
      edge('capacity','service','交付与服务扩张','capital',92,'reported'), edge('asml','chinafabs','受限市场服务','customer',76,'reported')
    ]
  }
};

datasets.microsoft = datasets.nvidia;
datasets.meta = datasets.nvidia;

function node(id, x, y, title, sub, avatar, type, baseScore, sources, components) {
  return { id, x, y, title, sub, avatar, type, baseScore, sources, components };
}
function edge(source, target, label, type, score, evidence) {
  return { source, target, label, type, score, evidence };
}
function metrics(supply, strategy, capital, control, policy, evidence, recency) {
  return { supply, strategy, capital, control, policy, technology: Math.round((strategy + evidence) / 2), recency, evidence };
}

const typeColors = {
  focus:'#172033', supply:'#2d6cdf', technology:'#7054d6', business:'#5c47c8', customer:'#0f8aa6',
  capital:'#c16a18', control:'#8c4fc1', policy:'#c14c43', risk:'#c14c43', group:'#77869a'
};
const viewAliases = {
  watchlist:'map', industries:'taxonomy', changes:'ops', evidence:'data', sync:'ops', calibration:'models'
};
const viewNames = {
  map:'商业版图', watchlist:'关注列表', industries:'行业', changes:'关键变化', data:'数据资产', evidence:'来源与证据',
  sync:'同步状态', taxonomy:'对象与范围', models:'模型与参数', calibration:'双周校准', architecture:'功能结构', delivery:'开发状态', ops:'操作记录', governance:'开发治理'
};
const defaultState = {
  focus:'nvidia', lens:'empire', view:'map', selected:null, selectedEdge:null, selectedTable:'relationships',
  history:['nvidia'], cursor:0, weights:{...defaultWeights}, thresholds:{...defaultThresholds}, visual:{...defaultVisual},
  graphScale:1, labels:true, mode:'network', modelTab:'formula', modelVersion:'v12.1', configVersion:12,
  draft:false, auditLog:[]
};
let state = loadState();
let toastTimer = null;
let pendingFocus = null;

function loadState(){
  try{
    const stored=JSON.parse(localStorage.getItem(STORAGE_KEY)||'null');
    if(!stored) return structuredClone(defaultState);
    return {...structuredClone(defaultState),...stored,
      weights:{...defaultWeights,...(stored.weights||{})},thresholds:{...defaultThresholds,...(stored.thresholds||{})},visual:{...defaultVisual,...(stored.visual||{})},
      history:Array.isArray(stored.history)&&stored.history.length?stored.history.filter(x=>companies[x]):['nvidia']};
  }catch(_){ return structuredClone(defaultState); }
}
function saveState(){ try{localStorage.setItem(STORAGE_KEY,JSON.stringify(state));}catch(_){} }
function svgEl(name,attrs={}){const el=document.createElementNS(NS,name);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,String(v)));return el;}
function clamp(v,min,max){return Math.max(min,Math.min(max,v));}
function escapeHtml(v=''){return String(v).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));}
function haptic(pattern=8){if(state.visual.haptic&&navigator.vibrate){try{navigator.vibrate(pattern)}catch(_){}}}
function showToast(message){
  const el=document.getElementById('toast'); if(!el) return; el.textContent=message; el.classList.add('show'); clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('show'),3100);
}
function currentDataset(){return datasets[state.focus]||datasets.nvidia;}
function currentCompany(){return companies[state.focus]||companies.nvidia;}
function weightedScore(n){
  const c=n.components||metrics(60,60,60,60,60,70,70), w=state.weights;
  const total=Object.values(w).reduce((a,b)=>a+Number(b||0),0)||100;
  const raw=(c.supply*w.supply+c.strategy*w.strategy+c.capital*w.capital+c.control*w.control+c.policy*w.policy+c.technology*w.technology+c.recency*w.recency)/total;
  return clamp(raw*(.5+.5*(c.evidence||70)/100),0,100);
}
function allowedEdge(e){
  const minimum=Number(state.thresholds.minimumEdgeScore||45); if(e.score<minimum) return false;
  if(state.lens==='supply') return ['supply','technology','business'].includes(e.type);
  if(state.lens==='capital') return ['capital','customer','control'].includes(e.type);
  if(state.lens==='control') return ['control','capital','business'].includes(e.type);
  if(state.lens==='policy') return ['policy','risk'].includes(e.type);
  if(state.lens==='changes') return e.score>=82||['capital','policy','risk'].includes(e.type);
  return true;
}
function filteredEdges(){return currentDataset().edges.filter(allowedEdge).sort((a,b)=>b.score-a.score).slice(0,Number(state.thresholds.maxVisibleEdges||40));}
function visibleIds(edges){const ids=new Set([state.focus]);edges.forEach(e=>{ids.add(e.source);ids.add(e.target)});return ids;}

function showView(requested,announce=true){
  const actual=viewAliases[requested]||requested;
  state.view=requested;
  document.querySelectorAll('[data-screen]').forEach(screen=>screen.classList.toggle('active',screen.dataset.screen===actual));
  document.querySelectorAll('.nav-item[data-view]').forEach(item=>item.classList.toggle('active',item.dataset.view===requested));
  renderBreadcrumbs(requested);
  if(actual==='data') renderData();
  if(actual==='models') renderModel();
  if(actual==='ops') renderOps();
  if(actual==='map') renderMap();
  if(requested==='industries') document.querySelectorAll('.catalog-item').forEach((x,i)=>x.classList.toggle('active',i===3));
  if(requested==='calibration'){state.modelTab='impact';renderModel();}
  if(announce && requested!==actual) showToast(`${viewNames[requested]}已在当前原型中聚合到“${viewNames[actual]}”工作区；生产版本将使用独立路由。`);
  saveState(); haptic(7);
}
function renderBreadcrumbs(requested=state.view){
  const wrap=document.getElementById('breadcrumbs'); if(!wrap) return;
  const c=currentCompany();
  wrap.innerHTML=`<button data-go-view="map">研究</button><span>›</span><button data-go-view="${escapeHtml(requested)}">${escapeHtml(viewNames[requested]||requested)}</button>${requested==='map'?`<span>›</span><strong>${escapeHtml(c.name)}</strong>`:''}`;
  wrap.querySelectorAll('[data-go-view]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.goView,false)));
}

function renderWatchlist(){
  const wrap=document.getElementById('watchlist'); if(!wrap) return;
  wrap.innerHTML=watchlistOrder.map(id=>{const c=companies[id];return `<button class="watch-item ${state.focus===id?'active':''}" data-focus="${id}"><span class="watch-avatar">${c.avatar}</span><span><strong class="watch-name">${escapeHtml(c.name)}</strong><small class="watch-meta">${escapeHtml(c.industry)}</small></span><span class="watch-alert">${c.count}</span></button>`}).join('');
  wrap.querySelectorAll('[data-focus]').forEach(b=>b.addEventListener('click',()=>setFocus(b.dataset.focus,true)));
}
function renderLensTabs(){
  const wrap=document.getElementById('lensTabs'); if(!wrap) return;
  wrap.innerHTML=lenses.map(([id,label])=>`<button class="lens-tab ${state.lens===id?'active':''}" data-lens="${id}">${label}</button>`).join('');
  wrap.querySelectorAll('[data-lens]').forEach(b=>b.addEventListener('click',()=>{state.lens=b.dataset.lens;state.selected=null;renderMap(true);haptic(7)}));
}
function setFocus(id,push=true){
  if(!companies[id]){showToast('该对象尚未进入演示数据集；生产版本将按同一逻辑查询并重绘。');return;}
  if(push){state.history=state.history.slice(0,state.cursor+1);if(state.history.at(-1)!==id)state.history.push(id);state.cursor=state.history.length-1;}
  state.focus=id;state.selected=null;state.selectedEdge=null;closeInspector();renderWatchlist();renderBreadcrumbs('map');
  const stage=document.getElementById('graphStage');stage?.classList.add('transitioning');
  setTimeout(()=>{renderMap(true);stage?.classList.remove('transitioning');stage?.classList.add('recentered');setTimeout(()=>stage?.classList.remove('recentered'),480)},150);
  saveState();haptic([10,28,12]);showToast(`研究中心已切换为 ${companies[id].name}；视角、模型、时间和筛选保持不变。`);
}
function goHistory(delta){const next=state.cursor+delta;if(next<0||next>=state.history.length)return;state.cursor=next;setFocus(state.history[next],false);}

function edgePath(a,b,index){
  const dx=b.x-a.x,dy=b.y-a.y;
  if(Math.abs(dx)>Math.abs(dy))return `M ${a.x} ${a.y} C ${a.x+dx*.34} ${a.y+((index%3)-1)*18}, ${a.x+dx*.68} ${b.y-((index%3)-1)*18}, ${b.x} ${b.y}`;
  return `M ${a.x} ${a.y} C ${a.x+25} ${a.y+dy*.35}, ${b.x-25} ${a.y+dy*.7}, ${b.x} ${b.y}`;
}
function midpoint(a,b,index){return{x:(a.x+b.x)/2,y:(a.y+b.y)/2+((index%3)-1)*8};}
function renderMap(pulse=false){
  renderWatchlist();renderLensTabs();renderBreadcrumbs('map');
  const c=currentCompany(),data=currentDataset(),edges=filteredEdges(),ids=visibleIds(edges),nodeMap=Object.fromEntries(data.nodes.map(n=>[n.id,n]));
  document.getElementById('focusTitle').textContent=c.name;document.getElementById('focusIndustry').textContent=c.industry;
  document.getElementById('visibleObjects').textContent=ids.size;document.getElementById('visibleRelations').textContent=edges.length;document.getElementById('sourceCount').textContent=data.nodes.filter(n=>ids.has(n.id)).reduce((a,n)=>a+n.sources,0);document.getElementById('dataVersion').textContent=state.modelVersion;
  document.getElementById('provenanceText').textContent=`${edges.length} 条关系 · ${data.nodes.filter(n=>ids.has(n.id)).reduce((a,n)=>a+n.sources,0)} 个来源 · 最近同步 18 分钟前`;
  document.getElementById('focusStatus').textContent=`证据覆盖 ${Math.round(edges.filter(e=>e.evidence==='reported').length/Math.max(1,edges.length)*100)}%`;
  const zoneLayer=document.getElementById('zoneLayer'),edgeLayer=document.getElementById('edgeLayer'),nodeLayer=document.getElementById('nodeLayer'),graph=document.getElementById('graph');
  zoneLayer.replaceChildren();edgeLayer.replaceChildren();nodeLayer.replaceChildren();
  data.zones.forEach(z=>{const g=svgEl('g');g.append(svgEl('rect',{x:z.x,y:z.y,width:z.w,height:z.h,class:'zone-shape'}));const t=svgEl('text',{x:z.x+16,y:z.y+23,class:'zone-title'});t.textContent=z.title;const st=svgEl('text',{x:z.x+16,y:z.y+41,class:'zone-subtitle'});st.textContent=z.sub;g.append(t,st);zoneLayer.append(g)});
  edges.forEach((e,i)=>{const a=nodeMap[e.source],b=nodeMap[e.target];if(!a||!b)return;const g=svgEl('g',{'data-edge':`${e.source}-${e.target}`,role:'button',tabindex:'0'});const selected=state.selected&&(e.source===state.selected||e.target===state.selected);let cls='edge-path';if(e.evidence!=='reported')cls+=' derived';if(e.type==='capital'||e.type==='control')cls+=' capital';if(e.type==='policy'||e.type==='risk')cls+=' policy';if(state.selected&&!selected)cls+=' dimmed';if(selected)cls+=' active';if(state.mode==='flow')cls+=' edge-flow';const path=svgEl('path',{d:edgePath(a,b,i),class:cls,style:`stroke-width:${1.0+e.score/68}`});path.addEventListener('click',ev=>{ev.stopPropagation();state.selected=null;state.selectedEdge=e;openEdgeInspector(e,a,b);renderMap()});g.append(path);if(state.labels){const m=midpoint(a,b,i),w=clamp(e.label.length*7+14,58,124);const lg=svgEl('g',{class:'edge-label-wrap'});lg.append(svgEl('rect',{x:m.x-w/2,y:m.y-9,width:w,height:18,class:'edge-label-bg'}));const txt=svgEl('text',{x:m.x,y:m.y,class:'edge-label'});txt.textContent=e.label;lg.append(txt);g.append(lg)}edgeLayer.append(g)});
  data.nodes.filter(n=>ids.has(n.id)).forEach(n=>nodeLayer.append(renderNode(n,pulse)));
  graph.style.transform=`scale(${state.graphScale})`;
  document.getElementById('graphStage').classList.toggle('hide-labels',!state.labels);
  document.querySelectorAll('.mode-button').forEach(b=>b.classList.toggle('active',b.dataset.mode===state.mode));
  saveState();
}
function renderNode(n,pulse){
  const focus=n.id===state.focus,selected=n.id===state.selected,score=Math.round(weightedScore(n)),w=focus?154:118,h=focus?70:52,x=n.x-w/2,y=n.y-h/2;
  const cls=['graph-node',focus?'focus':'',selected?'selected':'',n.type==='business'||n.type==='technology'?'business':'',n.type==='capital'||n.type==='control'?'capital':'',n.type==='policy'?'policy':'',n.type==='risk'?'risk':'',n.type==='group'?'group':''].filter(Boolean).join(' ');
  const g=svgEl('g',{class:cls,'data-node':n.id,role:'button',tabindex:'0','aria-label':`${n.title}，${n.sub}，重要度 ${score}`});
  g.append(svgEl('rect',{x,y,width:w,height:h,class:'node-card'}));
  const dot=svgEl('circle',{cx:x+15,cy:y+15,r:5,class:'node-type-dot',fill:typeColors[n.type]||'#567'});g.append(dot);
  const title=svgEl('text',{x:n.x,y:n.y-(focus?7:5),class:'node-title'});title.textContent=n.title;g.append(title);
  const sub=svgEl('text',{x:n.x,y:n.y+(focus?11:10),class:'node-sub'});sub.textContent=n.sub;g.append(sub);
  if(focus){g.append(svgEl('rect',{x:n.x-23,y:y+h-19,width:46,height:15,rx:8,class:'node-score-bg'}));const st=svgEl('text',{x:n.x,y:y+h-11,class:'node-score'});st.textContent=`${score} / 100`;g.append(st)}
  if(n.sources>=15&&!focus)g.append(svgEl('circle',{cx:x+w-8,cy:y+8,r:10,class:'node-change-ring'}));
  const select=ev=>{ev?.stopPropagation();state.selected=n.id;state.selectedEdge=null;openNodeInspector(n);renderMap();haptic(7)};
  g.addEventListener('click',select);g.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();select(ev)}});
  g.addEventListener('contextmenu',ev=>{ev.preventDefault();pendingFocus=n.id;const menu=document.getElementById('contextMenu');menu.style.left=`${Math.min(ev.clientX-222,window.innerWidth-450)}px`;menu.style.top=`${Math.min(ev.clientY-60,window.innerHeight-260)}px`;menu.classList.remove('hidden')});
  return g;
}
function openNodeInspector(n){
  const drawer=document.getElementById('inspectorDrawer');pendingFocus=n.id;document.getElementById('drawerType').textContent=n.id===state.focus?'当前研究中心':'公司 / 业务对象';document.getElementById('drawerTitle').textContent=n.title;
  const rels=currentDataset().edges.filter(e=>e.source===n.id||e.target===n.id).sort((a,b)=>b.score-a.score).slice(0,4);
  document.getElementById('drawerBody').innerHTML=`<section class="drawer-section"><h3>研究摘要</h3><p class="drawer-summary">${escapeHtml(n.sub)}。综合优先级 ${Math.round(weightedScore(n))}；当前可见 ${rels.length} 条关键关系，${n.sources} 个公开来源锚点。</p></section><section class="drawer-section"><h3>核心指标</h3><div class="drawer-metrics"><div class="drawer-metric"><strong>${Math.round(weightedScore(n))}</strong><small>研究优先级</small></div><div class="drawer-metric"><strong>${n.components.supply}</strong><small>供应关键性</small></div><div class="drawer-metric"><strong>${n.components.strategy}</strong><small>战略依赖</small></div><div class="drawer-metric"><strong>${n.components.evidence}%</strong><small>证据质量</small></div></div></section><section class="drawer-section"><h3>最重要连接</h3>${rels.map(e=>{const other=currentDataset().nodes.find(x=>x.id===(e.source===n.id?e.target:e.source));return `<div class="evidence-row"><span class="evidence-grade" style="background:${e.evidence==='reported'?'#16855b':'#6d4aff'}"></span><span><strong>${escapeHtml(other?.title||'相关对象')} · ${escapeHtml(e.label)}</strong><small>${e.evidence==='reported'?'公开披露':'多源推断'} · 关系重要度 ${e.score}</small></span><time>18h</time></div>`}).join('')}</section><section class="drawer-section"><h3>可追溯性</h3><p class="drawer-summary">实体 ID：${escapeHtml(n.id)}<br>模型版本：${state.modelVersion}<br>数据快照：2026.06.19.42</p></section>`;
  drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');
  document.getElementById('drawerFocusButton').disabled=n.id===state.focus;
}
function openEdgeInspector(e,a,b){
  const drawer=document.getElementById('inspectorDrawer');pendingFocus=b.id;document.getElementById('drawerType').textContent='关系';document.getElementById('drawerTitle').textContent=e.label;
  document.getElementById('drawerBody').innerHTML=`<section class="drawer-section"><h3>关系路径</h3><p class="drawer-summary"><strong>${escapeHtml(a.title)}</strong> → <strong>${escapeHtml(b.title)}</strong><br>${escapeHtml(e.label)}</p></section><section class="drawer-section"><h3>关系状态</h3><div class="drawer-metrics"><div class="drawer-metric"><strong>${e.score}</strong><small>重要度</small></div><div class="drawer-metric"><strong>${e.evidence==='reported'?'已披露':'多源推断'}</strong><small>证据状态</small></div><div class="drawer-metric"><strong>${relationshipLabel(e.type)}</strong><small>关系家族</small></div><div class="drawer-metric"><strong>18h</strong><small>最后核验</small></div></div></section><section class="drawer-section"><h3>模型解释</h3><p class="drawer-summary">adjusted_priority = raw_priority × evidence_quality_factor<br>当前使用 ${state.modelVersion}，所有参数可在“模型与参数”中查看和调整。</p></section>`;
  drawer.classList.add('open');drawer.setAttribute('aria-hidden','false');document.getElementById('drawerFocusButton').disabled=false;
}
function relationshipLabel(t){return({supply:'供应链与运营',technology:'技术、数据与IP',business:'集团与业务',customer:'商业依赖',capital:'资本与融资',control:'所有权与控制',policy:'政府与政策',risk:'政策与风险'})[t]||t;}
function closeInspector(){const d=document.getElementById('inspectorDrawer');d?.classList.remove('open');d?.setAttribute('aria-hidden','true');state.selected=null;state.selectedEdge=null;}

const tableDefs=[
  {id:'entities',label:'entities',rows:'2.46K',x:60,y:55,fields:[['entity_id','uuid','pk'],['canonical_name','text',''],['entity_type','enum',''],['industry_id','uuid','fk']]},
  {id:'relationships',label:'relationships',rows:'8.73K',x:340,y:42,fields:[['relationship_id','uuid','pk'],['subject_entity_id','uuid','fk'],['object_entity_id','uuid','fk'],['relationship_type','text',''],['valid_from','date','']]},
  {id:'evidence',label:'evidence_records',rows:'31.2K',x:650,y:62,fields:[['evidence_id','uuid','pk'],['relationship_id','uuid','fk'],['source_id','uuid','fk'],['evidence_state','enum',''],['observed_at','timestamptz','']]},
  {id:'events',label:'events',rows:'4.18K',x:90,y:310,fields:[['event_id','uuid','pk'],['entity_id','uuid','fk'],['event_type','text',''],['event_time','timestamptz','']]},
  {id:'scores',label:'score_snapshots',rows:'66.4K',x:380,y:330,fields:[['score_id','uuid','pk'],['object_id','uuid','fk'],['model_version','text',''],['score','numeric',''],['snapshot_id','uuid','fk']]},
  {id:'models',label:'model_config_versions',rows:'42',x:680,y:325,fields:[['config_version_id','uuid','pk'],['model_id','text',''],['parameters','jsonb',''],['status','enum',''],['activated_at','timestamptz','']]}
];
function renderData(){
  const tree=document.getElementById('schemaTree');if(!tree)return;
  tree.innerHTML=`<div class="schema-group open"><button class="schema-header"><span>核心事实</span><small>6</small></button><div class="schema-items">${tableDefs.map(t=>`<button class="table-link ${state.selectedTable===t.id?'active':''}" data-table="${t.id}"><span>${t.label}</span><small>${t.rows}</small></button>`).join('')}</div></div><div class="schema-group open"><button class="schema-header"><span>目录与治理</span><small>8</small></button><div class="schema-items"><button class="table-link"><span>relationship_types</span><small>52</small></button><button class="table-link"><span>supply_chain_stages</span><small>16</small></button><button class="table-link"><span>industry_taxonomy</span><small>26</small></button><button class="table-link"><span>company_catalog</span><small>140</small></button></div></div>`;
  tree.querySelectorAll('.schema-header').forEach(b=>b.addEventListener('click',()=>b.parentElement.classList.toggle('open')));tree.querySelectorAll('[data-table]').forEach(b=>b.addEventListener('click',()=>{state.selectedTable=b.dataset.table;renderData();haptic(6)}));
  const cards=document.getElementById('erdTables');cards.innerHTML=tableDefs.map(t=>`<article class="erd-card ${state.selectedTable===t.id?'active':''}" data-erd-table="${t.id}" style="left:${t.x}px;top:${t.y}px"><header><strong>${t.label}</strong><span>${t.rows}</span></header><div class="erd-fields">${t.fields.map(([n,typ,key])=>`<div class="erd-field"><i class="key-mark ${key}"></i><b>${n}</b><small>${typ}</small></div>`).join('')}</div></article>`).join('');
  cards.querySelectorAll('[data-erd-table]').forEach(c=>c.addEventListener('click',()=>{state.selectedTable=c.dataset.erdTable;renderData()}));
  drawErdLinks();renderTableDetail();
}
function drawErdLinks(){const svg=document.getElementById('erdEdges');if(!svg)return;svg.innerHTML='';const pairs=[['entities','relationships'],['relationships','evidence'],['entities','events'],['relationships','scores'],['models','scores']];pairs.forEach(([a,b])=>{const A=tableDefs.find(x=>x.id===a),B=tableDefs.find(x=>x.id===b);svg.append(svgEl('path',{d:`M ${A.x+154} ${A.y+56} C ${(A.x+B.x)/2+80} ${A.y+56}, ${(A.x+B.x)/2+80} ${B.y+56}, ${B.x} ${B.y+56}`,class:'erd-line'}))});}
function renderTableDetail(){const t=tableDefs.find(x=>x.id===state.selectedTable)||tableDefs[1],detail=document.getElementById('tableDetail');if(!detail)return;detail.innerHTML=`<div class="table-detail-head"><strong>${t.label}</strong><span>atlas_core · 演示事实表</span></div><div class="detail-stat-grid"><div><strong>${t.rows}</strong><small>记录</small></div><div><strong>99.4%</strong><small>质量通过</small></div><div><strong>18m</strong><small>新鲜度</small></div><div><strong>v42</strong><small>Schema</small></div></div><h3 class="column-list-title">字段</h3>${t.fields.map(([n,typ,key])=>`<div class="column-row"><span><strong>${n}</strong><small>${key==='pk'?'主键':key==='fk'?'外键':'业务字段'}</small></span><code>${typ}</code></div>`).join('')}`;}

const modelProfiles=[
  {id:'balanced',name:'综合研究优先级',sub:'默认均衡配置',color:'#2563eb'},
  {id:'supply',name:'供应链关键性',sub:'瓶颈与替代性',color:'#0f8aa6'},
  {id:'capital',name:'资本动量',sub:'融资、投资与并购',color:'#c25b13'},
  {id:'control',name:'控制影响力',sub:'持股、投票与治理',color:'#6d4aff'},
  {id:'policy',name:'政策暴露',sub:'监管、出口与补贴',color:'#c2413a'},
  {id:'evidence',name:'证据质量',sub:'可信度与冲突',color:'#16855b'}
];
const paramLabels={supply:'供应关键性',strategy:'战略依赖',capital:'资本动量',control:'控制影响',policy:'政策暴露',technology:'技术依赖',recency:'时间相关性'};
function renderModel(){
  document.getElementById('activeModelVersion').textContent=`Balanced · ${state.modelVersion}`;
  const list=document.getElementById('modelList');list.innerHTML=modelProfiles.map((m,i)=>`<button class="model-list-item ${i===0?'active':''}" data-profile="${m.id}"><span class="model-color" style="--model-color:${m.color}"></span><span><strong>${m.name}</strong><small>${m.sub}</small></span><em>${i===0?'生效':'可选'}</em></button>`).join('');
  list.querySelectorAll('[data-profile]').forEach(b=>b.addEventListener('click',()=>{list.querySelectorAll('.model-list-item').forEach(x=>x.classList.toggle('active',x===b));showToast(`已载入 ${b.querySelector('strong').textContent} 配置用于预览。`)}));
  document.querySelectorAll('[data-model-tab]').forEach(b=>b.classList.toggle('active',b.dataset.modelTab===state.modelTab));
  renderModelCanvas();renderParameterEditor();renderImpactBars();
}
function renderModelCanvas(){const wrap=document.getElementById('modelCanvas');if(!wrap)return;const tab=state.modelTab;
  if(tab==='formula')wrap.innerHTML=`<div class="formula-visual"><div class="formula-column">${Object.entries(paramLabels).slice(0,4).map(([k,v])=>`<div class="formula-node component" style="--node-accent:${typeColors[k==='supply'?'supply':k==='capital'?'capital':k==='policy'?'policy':'technology']}"><strong>${v}</strong><span>标准化分量 0–100</span><em>${state.weights[k]}%</em></div>`).join('')}</div><div class="formula-arrow"></div><div class="formula-column"><div class="formula-node output"><strong>综合研究优先级</strong><span>按权重聚合后乘以证据质量因子，并应用时间衰减。</span><em>${Math.round(Object.values(state.weights).reduce((a,b)=>a+b,0))}</em></div></div><div class="formula-arrow"></div><div class="formula-column"><div class="formula-node"><strong>图谱排序</strong><span>节点大小、关系显著度和 Top N</span></div><div class="formula-node"><strong>告警门槛</strong><span>重要变化与异常检测</span></div><div class="formula-node"><strong>可解释输出</strong><span>公式、输入、版本和证据</span></div></div><div class="formula-equation">priority = Σ(weightᵢ × normalized_componentᵢ) × (0.5 + 0.5 × evidence_quality) × recency_factor</div></div>`;
  else if(tab==='weights')wrap.innerHTML=`<div class="weight-visual">${Object.entries(paramLabels).map(([k,v])=>`<article class="weight-card"><header><strong>${v}</strong><b>${state.weights[k]}%</b></header><div class="weight-track"><i style="--p:${state.weights[k]*2.5}%"></i></div></article>`).join('')}</div>`;
  else if(tab==='thresholds')wrap.innerHTML=`<div class="threshold-visual">${[['minimumEdgeScore','关系入图门槛','#2563eb'],['solidEvidence','高可信证据门槛','#16855b'],['maxVisibleEdges','首屏边预算','#6d4aff'],['staleHours','数据过期小时','#c25b13'],['aggregationCount','聚合节点门槛','#0f8aa6'],['alertScore','变化告警门槛','#c2413a']].map(([k,v,c])=>{const val=state.thresholds[k]??(k==='alertScore'?78:50),pct=k==='maxVisibleEdges'?val/80*100:k==='staleHours'?val/168*100:val;return `<article class="threshold-card"><h3>${v}</h3><div class="dial" style="--dial-color:${c};--dial-p:${clamp(pct,5,100)}%"><strong>${val}</strong></div><p>修改后即时预览；发布时版本化并触发增量重算。</p></article>`}).join('')}</div>`;
  else if(tab==='time')wrap.innerHTML=`<div class="time-visual"><article class="decay-chart"><h3>事件时间衰减</h3><svg viewBox="0 0 360 150"><path d="M20 25 C90 42 140 82 330 130" fill="none" stroke="#2563eb" stroke-width="3"/><path d="M20 25 C150 30 235 52 330 80" fill="none" stroke="#6d4aff" stroke-width="3"/><line x1="20" y1="135" x2="335" y2="135" stroke="#cbd5e1"/><line x1="20" y1="15" x2="20" y2="135" stroke="#cbd5e1"/></svg></article><article class="decay-chart"><h3>默认半衰期</h3><div class="weight-visual"><article class="weight-card"><header><strong>新闻信号</strong><b>30天</b></header><div class="weight-track"><i style="--p:22%"></i></div></article><article class="weight-card"><header><strong>合同/资本</strong><b>365天</b></header><div class="weight-track"><i style="--p:68%"></i></div></article><article class="weight-card"><header><strong>控制关系</strong><b>730天</b></header><div class="weight-track"><i style="--p:94%"></i></div></article></div></article></div>`;
  else wrap.innerHTML=`<div class="impact-full"><article class="formula-node output"><strong>双周校准与影响预览</strong><span>比较当前模型与候选配置在覆盖率、稳定性、准确性、解释性和用户反馈上的差异。建议不会自动覆盖用户配置。</span><em>14d</em></article>${[['覆盖率',88,92],['供应链排序稳定性',82,86],['证据一致性',90,93],['告警精度',76,84],['图谱可读性',86,91]].map(([n,a,b])=>`<div class="impact-row"><strong>${n}</strong><div class="impact-pair"><i class="impact-before" style="--before:${a}%"></i><i class="impact-after" style="--after:${b}%"></i></div><span class="impact-delta">+${b-a}</span></div>`).join('')}</div>`;
}
function renderParameterEditor(){const wrap=document.getElementById('parameterEditor');if(!wrap)return;wrap.innerHTML=`<section class="parameter-section"><h3>综合权重</h3>${Object.entries(paramLabels).map(([k,v])=>parameterRow(k,v,state.weights[k],0,70,1,'%')).join('')}<div class="total-weight"><span>权重总和</span><strong id="weightTotal">${Object.values(state.weights).reduce((a,b)=>a+b,0)}%</strong></div></section><section class="parameter-section"><h3>门槛与图预算</h3>${parameterRow('minimumEdgeScore','关系入图门槛',state.thresholds.minimumEdgeScore,0,100,1,'')}${parameterRow('maxVisibleEdges','首屏最大关系',state.thresholds.maxVisibleEdges,10,80,1,'条')}${parameterRow('staleHours','过期提醒',state.thresholds.staleHours,1,168,1,'h')}</section><section class="parameter-section"><h3>配置文件</h3><div class="formula-card-small"><code>config/model_profiles/balanced-v2.json<br>config/thresholds/default-v2.json<br>models/model_registry.json</code><button id="exportModelConfig">导出当前 JSON 配置</button></div></section>`;
  wrap.querySelectorAll('input[type=range],input[type=number]').forEach(input=>input.addEventListener('input',()=>updateParameter(input)));
  document.getElementById('exportModelConfig')?.addEventListener('click',exportModelConfig);
}
function parameterRow(k,label,val,min,max,step,unit){return `<div class="parameter-row"><div class="parameter-label"><span>${label}</span><strong data-param-value="${k}">${val}${unit}</strong></div><div class="parameter-control"><input type="range" data-param="${k}" min="${min}" max="${max}" step="${step}" value="${val}" data-unit="${unit}"><input type="number" data-param-number="${k}" min="${min}" max="${max}" step="${step}" value="${val}"></div><div class="parameter-help">允许范围 ${min}–${max}${unit}；当前修改先进入草稿预览。</div></div>`;}
function updateParameter(input){const key=input.dataset.param||input.dataset.paramNumber,val=Number(input.value),isWeight=key in state.weights;if(isWeight)state.weights[key]=val;else state.thresholds[key]=val;const pair=input.dataset.param?document.querySelector(`[data-param-number="${key}"]`):document.querySelector(`[data-param="${key}"]`);if(pair)pair.value=val;const unit=document.querySelector(`[data-param="${key}"]`)?.dataset.unit||'';document.querySelector(`[data-param-value="${key}"]`).textContent=`${val}${unit}`;state.draft=true;document.getElementById('draftState').textContent='有未发布修改';document.getElementById('draftState').classList.add('changed');const total=document.getElementById('weightTotal');if(total)total.textContent=`${Object.values(state.weights).reduce((a,b)=>a+b,0)}%`;renderModelCanvas();renderImpactBars();saveState();haptic(4)}
function renderImpactBars(){const wrap=document.getElementById('impactBars');if(!wrap)return;const total=Object.values(state.weights).reduce((a,b)=>a+b,0)||100;const delta=(total-100);wrap.innerHTML=[['供应链瓶颈',72,clamp(72+state.weights.supply/5,0,100)],['资本事件',66,clamp(66+state.weights.capital/6,0,100)],['控制关系',58,clamp(58+state.weights.control/5,0,100)],['政策风险',61,clamp(61+state.weights.policy/4,0,100)]].map(([n,a,b])=>`<div class="impact-row"><strong>${n}</strong><div class="impact-pair"><i class="impact-before" style="--before:${a}%"></i><i class="impact-after" style="--after:${b}%"></i></div><span class="impact-delta ${b<a?'negative':''}">${b>=a?'+':''}${Math.round(b-a)}</span></div>`).join('');document.getElementById('previewSummary').textContent=`当前草稿将影响约 ${Math.round(8.73*(1+Math.abs(delta)/100)).toFixed(2)}M 条关系的排序和显示优先级`;}
function resetParameters(){state.weights={...defaultWeights};state.thresholds={...defaultThresholds};state.draft=false;document.getElementById('draftState').textContent='已恢复默认';renderModel();renderMap();showToast('参数已恢复默认值，尚未发布。')}
function exportModelConfig(){const payload={model_id:'balanced',version:state.modelVersion,weights:state.weights,thresholds:state.thresholds,generated_at:new Date().toISOString()};const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(payload,null,2)],{type:'application/json'}));a.download='atlas-model-config-v4.2.json';a.click();URL.revokeObjectURL(a.href);showToast('当前模型配置已导出为 JSON。')}
function applyModel(){const total=Object.values(state.weights).reduce((a,b)=>a+b,0);if(total!==100){showToast(`权重总和为 ${total}%，必须等于 100% 后才能发布。`);haptic([25,35,25]);return;}const reason=document.getElementById('changeReason').value.trim();if(!reason){showToast('请填写变更说明，便于审计和回滚。');return;}const overlay=document.getElementById('refreshOverlay'),bar=document.getElementById('refreshProgress'),message=document.getElementById('refreshMessage');overlay.classList.add('open');overlay.setAttribute('aria-hidden','false');const steps=[['校验公式、参数与阈值',18],['保存不可变配置版本',40],['增量重算受影响指标',68],['失效缓存并原子切换',88],['推送所有界面差异',100]];let i=0;const tick=()=>{message.textContent=steps[i][0];bar.style.width=`${steps[i][1]}%`;document.querySelectorAll('.refresh-steps span').forEach((x,j)=>x.classList.toggle('active',j<=Math.min(3,i)));if(i<steps.length-1){i++;setTimeout(tick,360)}else setTimeout(()=>{overlay.classList.remove('open');overlay.setAttribute('aria-hidden','true');state.configVersion++;state.modelVersion=`v12.${state.configVersion-11}`;state.draft=false;state.auditLog.unshift({time:new Date().toLocaleString('zh-CN'),title:'发布模型配置',detail:reason,version:state.modelVersion,status:'完成'});document.getElementById('draftState').textContent='已生效';document.getElementById('draftState').classList.remove('changed');document.getElementById('activeModelVersion').textContent=`Balanced · ${state.modelVersion}`;renderMap(true);renderOps();saveState();haptic([12,24,18]);showToast(`${state.modelVersion} 已生效；全体数据呈现已切换到同一模型快照。`)},420)};tick();}

function renderOps(){const jobs=document.getElementById('refreshJobs'),audit=document.getElementById('auditTimeline');if(!jobs||!audit)return;const jobRows=[['模型配置热刷新','完成','3.8s','刚刚'],['SEC filings 增量同步','完成','42.6s','18分钟前'],['关系物化视图重算','完成','8.2s','24分钟前'],['公司目录完整性检查','完成','1.1s','1小时前'],['供应链来源解析','警告','31.4s','2小时前']];jobs.innerHTML=jobRows.map(([n,s,d,t])=>`<div class="refresh-job"><span class="job-status ${s==='完成'?'success':'warning'}"></span><span><strong>${n}</strong><small>${t}</small></span><em>${d}</em><b>${s}</b></div>`).join('');const base=[{time:'2026/06/19 16:42',title:'v4.2 功能、模型与领域目录冻结',detail:'17个功能 · 52种关系 · 16个供应链阶段 · 140个研究对象',version:'v4.2',status:'已解决'},{time:'2026/06/19 16:10',title:'GitHub 文档备份与治理模板生成',detail:'CODEOWNERS、PR模板、Issue表单、目录完整性工作流',version:'v4.2',status:'模板完成'},{time:'2026/06/19 15:55',title:'交互原型更新',detail:'对象与范围、开发状态、参数在线修改与全局刷新',version:'v4.2',status:'已原型'},...state.auditLog];audit.innerHTML=base.map(x=>`<article class="audit-item"><time>${x.time}</time><span class="audit-dot"></span><div><strong>${x.title}</strong><p>${x.detail}</p><small>${x.version} · ${x.status}</small></div></article>`).join('');}

function bindEvents(){
  document.querySelectorAll('.nav-item[data-view]').forEach(b=>b.addEventListener('click',()=>showView(b.dataset.view)));
  document.getElementById('historyBack')?.addEventListener('click',()=>goHistory(-1));
  document.getElementById('closeInspector')?.addEventListener('click',()=>{closeInspector();renderMap()});
  document.getElementById('drawerFocusButton')?.addEventListener('click',()=>pendingFocus&&setFocus(pendingFocus,true));
  document.getElementById('setFocusAction')?.addEventListener('click',()=>{document.getElementById('contextMenu').classList.add('hidden');pendingFocus&&setFocus(pendingFocus,true)});
  document.getElementById('expandUpstreamAction')?.addEventListener('click',()=>{document.getElementById('contextMenu').classList.add('hidden');showToast('已展开一层上游关键关系；正式系统将按图预算增量加载。')});
  document.getElementById('expandDownstreamAction')?.addEventListener('click',()=>{document.getElementById('contextMenu').classList.add('hidden');showToast('已展开一层下游客户与市场关系。')});
  document.getElementById('pinAction')?.addEventListener('click',()=>{document.getElementById('contextMenu').classList.add('hidden');showToast('节点已固定，后续重绘将保持空间锚点。')});
  document.getElementById('graphStage')?.addEventListener('click',ev=>{if(ev.target.id==='graph'||ev.target.id==='graphStage'){closeInspector();document.getElementById('contextMenu').classList.add('hidden');renderMap()}});
  document.getElementById('fitGraph')?.addEventListener('click',()=>{state.graphScale=1;renderMap();haptic(5)});
  document.getElementById('zoomIn')?.addEventListener('click',()=>{state.graphScale=clamp(state.graphScale+.08,.76,1.28);renderMap()});
  document.getElementById('zoomOut')?.addEventListener('click',()=>{state.graphScale=clamp(state.graphScale-.08,.76,1.28);renderMap()});
  document.getElementById('toggleLabels')?.addEventListener('click',()=>{state.labels=!state.labels;renderMap()});
  document.querySelectorAll('.mode-button').forEach(b=>b.addEventListener('click',()=>{state.mode=b.dataset.mode;if(state.mode==='flow')state.lens='supply';if(state.mode==='timeline')state.lens='changes';renderMap(true);haptic(7)}));
  document.querySelectorAll('.filter-pill[data-filter]').forEach(b=>b.addEventListener('click',()=>{b.classList.toggle('active');showToast(`筛选“${b.textContent.trim()}”已更新当前图谱。`)}));
  document.getElementById('depthButton')?.addEventListener('click',ev=>{ev.target.textContent=ev.target.textContent.trim()==='1 层'?'2 层':'1 层';showToast('递归深度已更新，系统将按关系预算分批加载。')});
  document.getElementById('regionButton')?.addEventListener('click',ev=>{ev.target.textContent=ev.target.textContent.trim()==='全部地区'?'美国 / 亚洲':'全部地区'});
  document.getElementById('compareSnapshot')?.addEventListener('click',()=>showToast('已进入快照比较：新增、消失、增强和减弱关系将使用形状与动效双重编码。'));
  document.getElementById('openDataFromMap')?.addEventListener('click',()=>showView('data'));
  document.getElementById('dataPulse')?.addEventListener('click',()=>showView('sync'));
  document.getElementById('saveScene')?.addEventListener('click',()=>{saveState();showToast('当前主体、镜头、筛选、时间、模型和画布状态已保存。');haptic([8,18,12])});
  document.getElementById('addWatch')?.addEventListener('click',()=>showToast('新增 Watchlist：正式系统支持搜索、分组、优先级和提醒。'));
  document.getElementById('searchInput')?.addEventListener('keydown',ev=>{if(ev.key==='Enter'){const q=ev.currentTarget.value.trim().toLowerCase();const match=Object.entries(companies).find(([id,c])=>(id+c.name+c.industry).toLowerCase().includes(q));if(match){showView('map',false);setFocus(match[0],true)}else showToast('未在演示对象中找到；生产版本将搜索全部实体、关系与证据。')}});
  document.querySelectorAll('[data-model-tab]').forEach(b=>b.addEventListener('click',()=>{state.modelTab=b.dataset.modelTab;renderModel();haptic(6)}));
  document.getElementById('resetParameters')?.addEventListener('click',resetParameters);document.getElementById('applyModel')?.addEventListener('click',applyModel);document.getElementById('previewModel')?.addEventListener('click',()=>{state.draft=true;saveState();showToast('草稿已保存，不影响当前全局模型版本。')});
  document.getElementById('exportModelButton')?.addEventListener('click',exportModelConfig);
  document.getElementById('importModelButton')?.addEventListener('click',()=>showToast('正式系统导入 JSON 后先做 Schema 校验与影响 diff；原型仅展示流程，不写入本地文件。'));
  document.querySelectorAll('.catalog-item').forEach(item=>item.addEventListener('click',()=>{document.querySelectorAll('.catalog-item').forEach(x=>x.classList.toggle('active',x===item));haptic(6);showToast(`已切换到“${item.querySelector('strong').textContent}”目录；生产系统从版本化 CSV/JSON 实时读取。`)}));
  document.getElementById('exportCatalogs')?.addEventListener('click',()=>showToast('目录导出包含关系、供应链、行业、公司、业务、资本、模型与开发状态。'));
  document.addEventListener('keydown',ev=>{if(ev.key==='Escape'){closeInspector();document.getElementById('contextMenu')?.classList.add('hidden')}if((ev.metaKey||ev.ctrlKey)&&ev.key.toLowerCase()==='k'){ev.preventDefault();document.getElementById('searchInput')?.focus()}});
  document.addEventListener('pointerdown',ev=>{const b=ev.target.closest('button');if(!b)return;b.animate([{transform:'scale(1)'},{transform:'scale(.975)'},{transform:'scale(1)'}],{duration:150,easing:'cubic-bezier(.2,0,0,1)'})});
}

bindEvents();renderWatchlist();renderMap();renderData();renderModel();renderOps();showView(state.view||'map',false);
setTimeout(()=>showToast('Atlas v4.2 交互原型已就绪：示例数据、模型控制和开发治理使用同一目录基线。'),360);
