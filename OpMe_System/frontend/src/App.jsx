import {
  Activity,
  AlertTriangle,
  BarChart3,
  Download,
  FileText,
  Gauge,
  LayoutDashboard,
  RefreshCcw,
  Settings,
  ShieldCheck,
  Wrench
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import ChartPanel from "./components/ChartPanel.jsx";
import ModuleForm from "./components/ModuleForm.jsx";
import {
  createCase,
  getDashboardSummary,
  getModelSettings,
  listCases,
  regenerateReport,
  reportDownloadUrl,
  saveModelSettings
} from "./lib/api.js";

const NAV = [
  ["dashboard", "总览", LayoutDashboard],
  ["dynamic", "动态调测窑", Gauge],
  ["fault", "故障诊断", AlertTriangle],
  ["gear", "齿圈修复", ShieldCheck],
  ["machining", "机械加工", Wrench],
  ["reports", "报告中心", FileText],
  ["settings", "模型设置", Settings]
];

const RISK_LABELS = {
  normal: "正常",
  warning: "预警",
  critical: "严重"
};

export default function App() {
  const [active, setActive] = useState("dashboard");
  const [role, setRole] = useState("engineer");
  const [summary, setSummary] = useState(null);
  const [cases, setCases] = useState([]);
  const [models, setModels] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");

  async function refreshAll() {
    const [nextSummary, nextCases, nextModels] = await Promise.all([getDashboardSummary(), listCases(), getModelSettings()]);
    setSummary(nextSummary);
    setCases(nextCases);
    setModels(nextModels);
    if (!selectedCase && nextCases.length > 0) setSelectedCase(nextCases[0]);
  }

  useEffect(() => {
    refreshAll().catch((error) => setNotice(error.message));
  }, []);

  const moduleCases = useMemo(() => cases.filter((item) => item.module === active), [cases, active]);
  const currentCase = active === "dashboard" || active === "reports" || active === "settings" ? selectedCase : moduleCases[0] || selectedCase;

  async function submitCase(payload) {
    setBusy(true);
    setNotice("");
    try {
      const created = await createCase(payload);
      setSelectedCase(created);
      await refreshAll();
      setNotice(`已生成案例 #${created.id} 和 PDF 报告。`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function handleRegenerate(caseId) {
    setBusy(true);
    try {
      await regenerateReport(caseId);
      await refreshAll();
      setNotice(`案例 #${caseId} 的 PDF 已重新生成。`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function saveModels() {
    setBusy(true);
    try {
      const saved = await saveModelSettings(models);
      setModels(saved);
      await refreshAll();
      setNotice("模型配置已保存；未填写密钥时继续使用离线规则。");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-mark">KM</div>
          <div>
            <h1>武汉开明</h1>
            <p>智能工业运维助手</p>
          </div>
        </div>
        <nav className="nav-list">
          {NAV.map(([key, label, Icon]) => (
            <button key={key} className={active === key ? "nav-item nav-item--active" : "nav-item"} onClick={() => setActive(key)} type="button">
              <Icon size={18} />
              <span>{label}</span>
            </button>
          ))}
        </nav>
      </aside>

      <section className="main-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Web + PDF 运维控制台</p>
            <h2>{NAV.find(([key]) => key === active)?.[1] || "总览"}</h2>
          </div>
          <div className="topbar-actions">
            <div className="role-switch" aria-label="角色切换">
              {[
                ["admin", "管理员"],
                ["engineer", "工程师"],
                ["viewer", "只读"]
              ].map(([key, label]) => (
                <button key={key} className={role === key ? "selected" : ""} onClick={() => setRole(key)} type="button">
                  {label}
                </button>
              ))}
            </div>
            <button className="icon-button" type="button" onClick={() => refreshAll()} title="刷新">
              <RefreshCcw size={18} />
            </button>
          </div>
        </header>

        {notice && <div className="notice">{notice}</div>}

        {active === "dashboard" && <Dashboard summary={summary} cases={cases} onSelect={setSelectedCase} />}
        {["dynamic", "fault", "gear", "machining"].includes(active) && (
          <Workbench module={active} currentCase={currentCase} onSubmit={submitCase} busy={busy || role === "viewer"} />
        )}
        {active === "reports" && <Reports cases={cases} busy={busy} onRegenerate={handleRegenerate} />}
        {active === "settings" && (
          <SettingsPage models={models} setModels={setModels} onSave={saveModels} busy={busy || role === "viewer"} />
        )}
      </section>
    </main>
  );
}

function Dashboard({ summary, cases, onSelect }) {
  const riskData = summary?.risk_distribution || { normal: 0, warning: 0, critical: 0 };
  const moduleData = summary?.module_distribution || {};
  return (
    <div className="content-stack">
      <section className="kpi-grid">
        <Kpi title="案例总数" value={summary?.total_cases ?? 0} tone="teal" />
        <Kpi title="PDF覆盖率" value={`${summary?.kpis?.pdf_coverage ?? 0}%`} tone="blue" />
        <Kpi title="预警案例" value={summary?.kpis?.warning_cases ?? 0} tone="amber" />
        <Kpi title="严重案例" value={summary?.kpis?.critical_cases ?? 0} tone="red" />
      </section>
      <section className="dashboard-grid">
        <div className="ops-panel">
          <div className="section-title">
            <h3>风险分布</h3>
            <Activity size={18} />
          </div>
          <div className="risk-bars">
            {Object.entries(riskData).map(([key, value]) => (
              <div key={key} className={`risk-row risk-row--${key}`}>
                <span>{RISK_LABELS[key] || key}</span>
                <div>
                  <i style={{ width: `${Math.min(100, value * 24)}%` }} />
                </div>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
        </div>
        <div className="ops-panel">
          <div className="section-title">
            <h3>模块覆盖</h3>
            <BarChart3 size={18} />
          </div>
          <div className="module-tags">
            {Object.entries(moduleData).map(([key, value]) => (
              <button key={key} type="button" onClick={() => onSelect(cases.find((item) => item.module === key))}>
                <span>{key}</span>
                <strong>{value}</strong>
              </button>
            ))}
            {Object.keys(moduleData).length === 0 && <p>暂无案例，先进入模块生成样例报告。</p>}
          </div>
        </div>
      </section>
      <CaseTable cases={summary?.recent_cases || []} onSelect={onSelect} />
    </div>
  );
}

function Kpi({ title, value, tone }) {
  return (
    <div className={`kpi kpi--${tone}`}>
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Workbench({ module, currentCase, onSubmit, busy }) {
  const visualizations = currentCase?.module === module ? currentCase.result.visualizations : [];
  return (
    <div className="content-stack">
      <ModuleForm module={module} onSubmit={onSubmit} busy={busy} />
      {currentCase?.module === module && (
        <section className="analysis-summary">
          <div>
            <p className="eyebrow">案例 #{currentCase.id}</p>
            <h3>{currentCase.result.title}</h3>
            <p>{currentCase.result.summary}</p>
          </div>
          <div className={`risk-chip risk-chip--${currentCase.result.risk_level}`}>{RISK_LABELS[currentCase.result.risk_level]}</div>
          {currentCase.report_status === "ready" && (
            <a className="secondary-button" href={reportDownloadUrl(currentCase.id)} target="_blank" rel="noreferrer">
              <Download size={18} />
              <span>下载PDF</span>
            </a>
          )}
        </section>
      )}
      <section className="chart-grid">
        {visualizations.map((viz) => (
          <ChartPanel key={viz.id} visualization={viz} />
        ))}
        {visualizations.length === 0 && <div className="empty-state">提交样例后会显示趋势、矩阵、风险仪表和工艺流程图。</div>}
      </section>
    </div>
  );
}

function CaseTable({ cases, onSelect }) {
  return (
    <section className="ops-panel">
      <div className="section-title">
        <h3>最近案例</h3>
        <FileText size={18} />
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>编号</th>
              <th>模块</th>
              <th>标题</th>
              <th>风险</th>
              <th>报告</th>
              <th>时间</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((item) => (
              <tr key={item.id} onClick={() => onSelect(item)}>
                <td>#{item.id}</td>
                <td>{item.module}</td>
                <td>{item.title}</td>
                <td>
                  <span className={`risk-chip risk-chip--${item.risk_level}`}>{RISK_LABELS[item.risk_level]}</span>
                </td>
                <td>{item.report_status}</td>
                <td>{new Date(item.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {cases.length === 0 && (
              <tr>
                <td colSpan="6">暂无案例</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function Reports({ cases, busy, onRegenerate }) {
  return (
    <section className="ops-panel">
      <div className="section-title">
        <h3>PDF 报告中心</h3>
        <FileText size={18} />
      </div>
      <div className="report-list">
        {cases.map((item) => (
          <article key={item.id} className="report-item">
            <div>
              <strong>#{item.id} {item.result.title}</strong>
              <p>{item.result.summary}</p>
            </div>
            <span className={`risk-chip risk-chip--${item.result.risk_level}`}>{RISK_LABELS[item.result.risk_level]}</span>
            <button className="secondary-button" type="button" disabled={busy} onClick={() => onRegenerate(item.id)}>
              <RefreshCcw size={16} />
              <span>重生成</span>
            </button>
            {item.report_status === "ready" ? (
              <a className="primary-button" href={reportDownloadUrl(item.id)} target="_blank" rel="noreferrer">
                <Download size={16} />
                <span>下载</span>
              </a>
            ) : (
              <span className="muted">{item.report_status}</span>
            )}
          </article>
        ))}
        {cases.length === 0 && <div className="empty-state">暂无报告。</div>}
      </div>
    </section>
  );
}

function SettingsPage({ models, setModels, onSave, busy }) {
  function change(index, key, value) {
    setModels((current) => current.map((item, itemIndex) => (itemIndex === index ? { ...item, [key]: value } : item)));
  }

  return (
    <section className="ops-panel">
      <div className="section-title">
        <h3>模型路由设置</h3>
        <Settings size={18} />
      </div>
      <div className="settings-grid">
        {models.map((model, index) => (
          <article key={model.provider} className="model-row">
            <div className="model-provider">
              <strong>{model.provider}</strong>
              <label>
                <input type="checkbox" checked={model.enabled} onChange={(event) => change(index, "enabled", event.target.checked)} />
                启用
              </label>
            </div>
            <label>
              <span>Base URL</span>
              <input value={model.base_url} onChange={(event) => change(index, "base_url", event.target.value)} />
            </label>
            <label>
              <span>模型</span>
              <input value={model.model} onChange={(event) => change(index, "model", event.target.value)} />
            </label>
            <label>
              <span>API Key</span>
              <input type="password" value={model.api_key || ""} onChange={(event) => change(index, "api_key", event.target.value)} />
            </label>
            <label>
              <span>优先级</span>
              <input type="number" value={model.priority} onChange={(event) => change(index, "priority", Number(event.target.value))} />
            </label>
          </article>
        ))}
      </div>
      <button className="primary-button settings-save" type="button" disabled={busy} onClick={onSave}>
        <ShieldCheck size={18} />
        <span>保存配置</span>
      </button>
    </section>
  );
}

