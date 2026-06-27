from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from backend.app.schemas.strategy_dsl import validate_strategy
from backend.app.services.agent_runtime import AUTO_PAPER_AGENT
from backend.app.services.backtest import run_buy_and_hold_fixture
from backend.app.services.approval_queue import ApprovalQueue
from backend.app.services.policy import GovernorPolicy
from backend.app.services.live_broker import FailClosedLiveBroker, LiveOrderIntent
from backend.app.services.paper_trading_loop import DEFAULT_REFRESH_INTERVAL_SECONDS, build_default_loop, latest_mark_prices
from backend.app.services.paper_broker import PaperBroker
from backend.app.services.phase6_owner_gate import DEFAULT_MAX_SAMPLE_AGE_SECONDS, DEFAULT_MAX_SAMPLE_GAP_SECONDS, build_phase6_owner_gate_status
from backend.app.services.strategy_iteration import run_strategy_tournament

router = APIRouter()

ROOT = Path(__file__).resolve().parents[3]
POLICY_PATH = ROOT / "configs" / "trading_governor_policy.yaml"
DATA_PATH = ROOT / "data" / "sample_prices.csv"
QUEUE_PATH = ROOT / "runtime" / "approval_queue.json"
PAPER_STATE_PATH = ROOT / "runtime" / "paper_portfolio.json"
PHASE6_EVIDENCE_ROOT = ROOT / "runtime" / "phase6_owner_gate_latest"
PHASE6_HISTORY_PATH = ROOT / "runtime" / "phase6_soak_history.jsonl"
LIVE_AUTHORIZATION_PATH = ROOT / "runtime" / "LIVE_AUTHORIZATION.json"


@router.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "mode": "research_paper_order_intent_review",
        "live_trading_enabled": False,
        "kill_switch_active": False,
        "refresh_interval_seconds": DEFAULT_REFRESH_INTERVAL_SECONDS,
    }


@router.get("/owner/summary")
def owner_summary() -> dict:
    queue = ApprovalQueue(QUEUE_PATH)
    queue_summary = queue.summary()
    return {
        "system_mode": "research_paper_order_intent_review",
        "strategies": {"research": 1, "paper": 1, "live_order_review": queue_summary["fresh_pending_count"]},
        "required_owner_actions": ["review_order_tickets"] if queue_summary["fresh_pending_count"] else [],
        "pending_order_tickets": queue_summary["fresh_pending_count"],
        "expired_order_tickets": queue_summary["expired_pending_count"],
    }


@router.post("/strategy/validate")
def strategy_validate(payload: dict) -> dict:
    strategy = validate_strategy(payload)
    return {"valid": True, "normalized_strategy": strategy.model_dump(mode="json"), "warnings": []}


@router.post("/backtest/run")
def backtest_run(payload: dict | None = None) -> dict:
    payload = payload or {}
    metrics = run_buy_and_hold_fixture(DATA_PATH, initial_capital=float(payload.get("initial_capital", 10000)))
    return {"run_id": "fixture_bt_001", "metrics": metrics}


@router.post("/paper/run-once")
def paper_run_once() -> dict:
    loop = build_default_loop(queue_path=QUEUE_PATH, paper_state_path=PAPER_STATE_PATH)
    return loop.run_once()


@router.get("/orders/approval-queue")
def approval_queue() -> dict:
    queue = ApprovalQueue(QUEUE_PATH)
    summary = queue.summary()
    return {
        "tickets": queue.latest_with_freshness(),
        "count": summary["fresh_pending_count"],
        "summary": summary,
    }


@router.get("/agent/status")
def agent_status() -> dict:
    queue = ApprovalQueue(QUEUE_PATH)
    queue_summary = queue.summary()
    return {
        "agent_id": "paper_trading_loop",
        "status": "ready",
        "refresh_interval_seconds": DEFAULT_REFRESH_INTERVAL_SECONDS,
        "capabilities": [
            "paper_trading",
            "risk_check",
            "approval_queue",
            "broker_ready_order_ticket",
        ],
        "pending_tickets": queue_summary["fresh_pending_count"],
        "expired_tickets": queue_summary["expired_pending_count"],
        "latest_ticket_created_at": queue_summary["latest_ticket_created_at"],
        "latest_fresh_ticket_created_at": queue_summary["latest_fresh_ticket_created_at"],
        "loop": AUTO_PAPER_AGENT.snapshot(),
    }


@router.get("/agent/loop/status")
def agent_loop_status() -> dict:
    return AUTO_PAPER_AGENT.snapshot()


@router.get("/paper/portfolio")
def paper_portfolio() -> dict:
    return PaperBroker.load(PAPER_STATE_PATH).portfolio_snapshot(latest_mark_prices(DATA_PATH))


@router.post("/strategy/tournament/run")
def strategy_tournament_run() -> dict:
    return run_strategy_tournament(DATA_PATH)


@router.get("/phase6/owner-gate/status")
def phase6_owner_gate_status() -> dict:
    return build_phase6_owner_gate_status(
        evidence_root=PHASE6_EVIDENCE_ROOT,
        history_path=PHASE6_HISTORY_PATH,
        max_sample_gap_seconds=DEFAULT_MAX_SAMPLE_GAP_SECONDS,
        max_sample_age_seconds=DEFAULT_MAX_SAMPLE_AGE_SECONDS,
        live_authorization_path=LIVE_AUTHORIZATION_PATH,
    )


@router.get("/dashboard/state")
def dashboard_state() -> dict:
    return {
        "health": health(),
        "owner_summary": owner_summary(),
        "agent_status": agent_status(),
        "paper_portfolio": paper_portfolio(),
        "strategy_tournament": strategy_tournament_run(),
        "approval_queue": approval_queue(),
        "phase6_owner_gate": phase6_owner_gate_status(),
    }


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> str:
    return """
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Alpha 交易驾驶舱</title>
  <style>
    :root { color-scheme: light; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
    body { margin: 0; background: #f5f6f3; color: #1d1f21; }
    header { padding: 18px 28px; border-bottom: 1px solid #d8ddd2; background: #ffffff; display: flex; justify-content: space-between; gap: 16px; align-items: center; position: sticky; top: 0; z-index: 2; }
    h1 { margin: 0; font-size: 22px; font-weight: 750; }
    h2 { margin: 0 0 12px; font-size: 15px; }
    main { padding: 20px 28px 28px; display: grid; gap: 16px; grid-template-columns: minmax(0, 1fr); }
    section { background: #ffffff; border: 1px solid #d8ddd2; border-radius: 8px; padding: 16px; }
    button { border: 1px solid #1d1f21; background: #1d1f21; color: #fff; border-radius: 6px; padding: 9px 12px; cursor: pointer; font-weight: 650; }
    button.secondary { background: #fff; color: #1d1f21; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th, td { padding: 9px 8px; border-bottom: 1px solid #eceee8; text-align: left; vertical-align: top; }
    th { color: #5c6258; font-size: 12px; text-transform: uppercase; letter-spacing: 0; }
    pre { white-space: pre-wrap; word-break: break-word; font-size: 12px; line-height: 1.45; margin: 0; }
    .status { font-size: 13px; color: #555; }
    .metric-grid { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); }
    .metric { border: 1px solid #eceee8; border-radius: 8px; padding: 12px; background: #fbfbf8; }
    .metric .label { color: #666d61; font-size: 12px; }
    .metric .value { font-size: 22px; font-weight: 760; margin-top: 5px; }
    .pill { display: inline-flex; border-radius: 999px; padding: 3px 8px; font-size: 12px; font-weight: 700; }
    .ok { background: #e6f5ec; color: #176c3a; }
    .warn { background: #fff3d6; color: #8a5b00; }
    .danger { background: #fde7e7; color: #9b1c1c; }
    .grid-two { display: grid; gap: 16px; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); }
    .muted { color: #6a7166; }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Alpha 交易驾驶舱</h1>
      <div class="status" id="lastUpdated">加载中</div>
    </div>
    <div>
      <button onclick="runCycle()">运行一次虚拟交易</button>
      <button class="secondary" onclick="loadState()">刷新</button>
    </div>
  </header>
  <main>
    <section>
      <h2>系统快照</h2>
      <div class="metric-grid" id="metrics"></div>
    </section>
    <section><h2>Phase 6 OWNER-GATE 状态</h2><div id="phase6"></div></section>
    <div class="grid-two">
      <section><h2>虚拟交易组合</h2><div id="portfolio"></div></section>
      <section><h2>Agent 运行状态</h2><div id="agent"></div></section>
    </div>
    <section><h2>策略锦标赛</h2><div id="tournament"></div></section>
    <section><h2>人工确认队列</h2><div id="queue"></div></section>
  </main>
  <script>
    function pill(text, kind) {
      return `<span class="pill ${kind}">${text}</span>`;
    }
    function metric(label, value) {
      return `<div class="metric"><div class="label">${label}</div><div class="value">${value}</div></div>`;
    }
    const STATUS_LABELS = {
      blocked_not_ready_for_owner_gate: '未达 OWNER-GATE',
      ready_for_owner_gate: '可进入 OWNER-GATE',
      pass: '通过',
      fail: '未通过',
      unknown: '未知',
      missing: '缺失',
      ready: '就绪',
      sleeping: '休眠中',
      completed: '已完成',
      filled: '已成交（虚拟）',
      pending_owner_approval: '待人工确认',
      fresh_pending_owner_approval: '新鲜，待人工确认',
      expired_owner_approval: '已过期',
      approved_for_owner_review: '风控通过，待确认',
      promote_to_paper: '晋级虚拟交易',
      fresh: '新鲜',
      expired: '已过期'
    };
    function statusText(value) {
      if (!value) return '无';
      return STATUS_LABELS[value] || value;
    }
    function formatHours(value) {
      return Number(value || 0).toFixed(4);
    }
    function renderMetrics(data) {
      const portfolio = data.paper_portfolio || {};
      const queue = data.approval_queue || {};
      const queueSummary = queue.summary || {};
      const health = data.health || {};
      const loop = (data.agent_status && data.agent_status.loop) || {};
      document.getElementById('metrics').innerHTML = [
        metric('Agent', pill(statusText(data.agent_status.status), 'ok')),
        metric('运行循环', pill(statusText(loop.status || 'unknown'), loop.error_count ? 'danger' : 'ok')),
        metric('虚拟总权益', Number(portfolio.total_equity || 0).toFixed(2)),
        metric('虚拟成交数', portfolio.trade_count || 0),
        metric('新鲜待确认', queueSummary.fresh_pending_count || queue.count || 0),
        metric('已过期工单', queueSummary.expired_pending_count || 0),
        metric('刷新间隔', `${health.refresh_interval_seconds || 300}s`)
      ].join('');
    }
    function renderPhase6(phase6) {
      const blockers = (phase6.blocking_conditions || []).join(', ') || '无';
      const statusKind = phase6.status === 'ready_for_owner_gate' ? 'ok' : 'warn';
      const freshKind = phase6.sampler_freshness_status === 'pass' ? 'ok' : 'danger';
      const liveKind = phase6.live_authorization_absent ? 'ok' : 'danger';
      document.getElementById('phase6').innerHTML = `
        <div class="metric-grid">
          ${metric('收口状态', pill(statusText(phase6.status || 'unknown'), statusKind))}
          ${metric('连续观察', `${formatHours(phase6.observed_hours)} / ${phase6.duration_hours_required || 48}h`)}
          ${metric('最新样本', pill(statusText(phase6.sampler_freshness_status || 'unknown'), freshKind))}
          ${metric('实盘授权文件', pill(phase6.live_authorization_absent ? '不存在' : '存在', liveKind))}
        </div>
        <table>
          <tbody>
            <tr><th>连续窗口</th><td>${phase6.window_start || '缺失'} → ${phase6.window_end || '缺失'}</td></tr>
            <tr><th>样本</th><td>总数 ${phase6.sample_count || 0}，连续 ${phase6.continuous_sample_count || 0}</td></tr>
            <tr><th>样本间隔</th><td>最大 ${phase6.max_observed_gap_seconds || 0}s，阈值 ${phase6.max_sample_gap_seconds || 900}s，gap ${phase6.gap_violation_count || 0}</td></tr>
            <tr><th>最新样本年龄</th><td>${phase6.latest_sample_age_seconds ?? 'n/a'}s / ${phase6.max_sample_age_seconds || 900}s</td></tr>
            <tr><th>Paper/Shadow 报告</th><td>${statusText(phase6.paper_shadow_status || 'missing')}</td></tr>
            <tr><th>Shadow Live 约束</th><td>${statusText(phase6.shadow_live_constraints_status || 'missing')}</td></tr>
            <tr><th>当前阻塞</th><td>${blockers}</td></tr>
          </tbody>
        </table>
      `;
    }
    function renderPortfolio(portfolio) {
      const positions = portfolio.positions || [];
      const rows = positions.map(row => `<tr><td>${row.symbol}</td><td>${row.quantity}</td><td>${row.mark_price}</td><td>${row.market_value}</td></tr>`).join('');
      document.getElementById('portfolio').innerHTML = `
        <div class="metric-grid">
          ${metric('现金', Number(portfolio.cash || 0).toFixed(2))}
          ${metric('持仓市值', Number(portfolio.positions_value || 0).toFixed(2))}
          ${metric('总权益', Number(portfolio.total_equity || 0).toFixed(2))}
        </div>
        <table><thead><tr><th>标的</th><th>数量</th><th>标记价</th><th>市值</th></tr></thead><tbody>${rows || '<tr><td colspan="4" class="muted">暂无虚拟持仓</td></tr>'}</tbody></table>
      `;
    }
    function renderAgent(agent) {
      const loop = agent.loop || {};
      const summary = loop.last_result_summary || {};
      const loopKind = loop.error_count ? 'danger' : (loop.task_running ? 'ok' : 'warn');
      document.getElementById('agent').innerHTML = `
        <table>
          <tbody>
            <tr><th>ID</th><td>${agent.agent_id}</td></tr>
            <tr><th>状态</th><td>${pill(statusText(agent.status), 'ok')}</td></tr>
            <tr><th>循环</th><td>${pill(statusText(loop.status || 'unknown'), loopKind)}</td></tr>
            <tr><th>运行次数</th><td>${loop.run_count || 0}</td></tr>
            <tr><th>刷新间隔</th><td>${agent.refresh_interval_seconds}s</td></tr>
            <tr><th>上次运行</th><td>${loop.last_run_completed_at || '尚未运行'}</td></tr>
            <tr><th>下次运行</th><td>${loop.next_run_at || '等待中'}</td></tr>
            <tr><th>最新工单</th><td>${agent.latest_ticket_created_at || '无'}</td></tr>
            <tr><th>最新新鲜工单</th><td>${agent.latest_fresh_ticket_created_at || '无'}</td></tr>
            <tr><th>过期工单</th><td>${agent.expired_tickets || 0}</td></tr>
            <tr><th>最新结果</th><td>${summary.intent_symbol || '无'} / ${statusText(summary.ticket_status)} / ${statusText(summary.paper_order_status)}</td></tr>
            <tr><th>错误</th><td>${loop.error_count || 0}${loop.last_error ? ': ' + loop.last_error : ''}</td></tr>
            <tr><th>能力</th><td>${(agent.capabilities || []).join(', ')}</td></tr>
          </tbody>
        </table>
      `;
    }
    function renderTournament(tournament) {
      const rows = (tournament.candidates || []).slice(0, 8).map(row => `
        <tr>
          <td>${row.strategy_id}</td><td>${row.symbol}</td><td>${row.lookback_days}</td>
          <td>${Number(row.total_return * 100).toFixed(2)}%</td><td>${Number(row.oos_return * 100).toFixed(2)}%</td>
          <td>${Number(row.hit_rate * 100).toFixed(2)}%</td><td>${row.validation_windows}</td>
          <td>${Number(row.max_drawdown * 100).toFixed(2)}%</td><td>${Number(row.score).toFixed(4)}</td><td>${statusText(row.decision)}</td>
        </tr>`).join('');
      document.getElementById('tournament').innerHTML = `
        <div class="status">当前优胜策略：${(tournament.winner && tournament.winner.strategy_id) || '无'}</div>
        <table><thead><tr><th>策略</th><th>标的</th><th>回看天数</th><th>收益</th><th>样本外收益</th><th>胜率</th><th>验证窗口</th><th>最大回撤</th><th>分数</th><th>决策</th></tr></thead><tbody>${rows}</tbody></table>
      `;
    }
    function renderQueue(queue) {
      const rows = (queue.tickets || []).map(ticket => {
        const payload = ticket.broker_payload || {};
        const risk = ticket.risk_check || {};
        return `<tr>
          <td>${ticket.ticket_id}</td><td>${statusText(ticket.actionability || ticket.status)}</td><td>${payload.symbol || ''}</td>
          <td>${payload.side || ''}</td><td>${payload.quantity || ''}</td>
          <td>${payload.estimated_price || ''}</td><td>${statusText(risk.status || 'unknown')}</td>
          <td>${statusText((ticket.freshness && ticket.freshness.status) || 'unknown')}</td>
          <td>${(ticket.freshness && ticket.freshness.seconds_until_expiry) ?? 'n/a'}</td>
        </tr>`;
      }).join('');
      document.getElementById('queue').innerHTML = `<table><thead><tr><th>工单</th><th>可操作状态</th><th>标的</th><th>方向</th><th>数量</th><th>价格</th><th>风控</th><th>新鲜度</th><th>剩余秒数</th></tr></thead><tbody>${rows || '<tr><td colspan="9" class="muted">暂无待确认工单</td></tr>'}</tbody></table>`;
    }
    async function loadState() {
      const response = await fetch('/dashboard/state');
      const data = await response.json();
      renderMetrics(data);
      renderPhase6(data.phase6_owner_gate || {});
      renderPortfolio(data.paper_portfolio || {});
      renderAgent(data.agent_status || {});
      renderTournament(data.strategy_tournament || {});
      renderQueue(data.approval_queue || {});
      document.getElementById('lastUpdated').textContent = '最后更新：' + new Date().toLocaleString();
    }
    async function runCycle() {
      await fetch('/paper/run-once', { method: 'POST' });
      await loadState();
    }
    loadState();
    setInterval(loadState, 300000);
  </script>
</body>
</html>
"""


@router.post("/live/order-intent")
def live_order_intent(payload: dict) -> dict:
    policy = GovernorPolicy.load(POLICY_PATH)
    broker = FailClosedLiveBroker()
    intent = LiveOrderIntent(
        idempotency_key=payload.get("idempotency_key", ""),
        symbol=payload.get("symbol", "SPY"),
        side=payload.get("side", "buy"),
        quantity=float(payload.get("quantity", 1)),
        notional_aud=float(payload.get("notional_aud", 999999)),
    )
    return broker.submit_order_intent(intent, policy, broker_health_ok=False)
