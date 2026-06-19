import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  ArrowLeft,
  CheckCircle2,
  CircleDot,
  Database,
  FileCheck2,
  GitBranch,
  ListChecks,
  Network,
  ShieldAlert
} from "lucide-react";
import { ACTIVE_ANALYSIS_CONTEXT } from "../analysis-contract";

type CsvRow = Record<string, string>;

type StatusLane = {
  key: string;
  label: string;
  count: number;
  description: string;
};

const dataRoot = resolve(process.cwd(), "../../data");
const githubDataRoot = "https://github.com/LinzeColin/CodexProject/blob/main/EEI/data";

function parseCsv(text: string): CsvRow[] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let quoted = false;
  const source = text.replace(/^\uFEFF/, "");

  for (let index = 0; index < source.length; index += 1) {
    const char = source[index];
    const next = source[index + 1];
    if (char === '"' && quoted && next === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") {
        index += 1;
      }
      row.push(field);
      if (row.some((value) => value.length > 0)) {
        rows.push(row);
      }
      row = [];
      field = "";
    } else {
      field += char;
    }
  }

  row.push(field);
  if (row.some((value) => value.length > 0)) {
    rows.push(row);
  }

  const [header, ...records] = rows;
  if (!header) return [];
  return records.map((record) =>
    Object.fromEntries(header.map((key, index) => [key, record[index] ?? ""]))
  );
}

function readCsv(path: string): CsvRow[] {
  return parseCsv(readFileSync(resolve(dataRoot, path), "utf8"));
}

function countRows(rows: CsvRow[], predicate: (row: CsvRow) => boolean) {
  return rows.filter(predicate).length;
}

export default function DevelopmentStatusPage() {
  const ledger = readCsv("development_status_ledger.csv");
  const tasks = readCsv("task_backlog.csv");
  const acceptance = readCsv("acceptance_matrix.csv");
  const traceability = readCsv("acceptance_traceability.csv");
  const risks = readCsv("risk_register.csv");
  const riskControls = readCsv("risk_control_traceability.csv");
  const gates = readCsv("release_gate_catalog.csv");

  const lanes: StatusLane[] = [
    {
      key: "resolved",
      label: "resolved",
      count: countRows(ledger, (row) =>
        ["CI_VALIDATED", "LOCAL_E2E_VALIDATED", "LOCAL_VALIDATED", "VALIDATED"].includes(
          row.validation_status
        )
      ),
      description: "validated implementation evidence exists"
    },
    {
      key: "prototyped",
      label: "prototyped",
      count: countRows(
        ledger,
        (row) => row.prototype_status === "DONE" && row.implementation_status !== "DONE"
      ),
      description: "prototype or UI contract exists before complete implementation"
    },
    {
      key: "specified",
      label: "specified",
      count: countRows(
        ledger,
        (row) => row.spec_status === "DONE" && row.implementation_status === "NOT_STARTED"
      ),
      description: "requirements are defined and implementation has not started"
    },
    {
      key: "not-started",
      label: "not started",
      count: countRows(tasks, (row) => row.status === "NOT STARTED"),
      description: "task backlog items with no product implementation"
    },
    {
      key: "blocked",
      label: "blocked",
      count: countRows(tasks, (row) => row.status === "BLOCKED"),
      description: "items stopped by an explicit unresolved blocker"
    },
    {
      key: "out-of-scope",
      label: "out-of-scope",
      count: countRows(tasks, (row) => row.gate === "Phase2" || row.priority === "P1"),
      description: "Phase 2 or P1 work excluded from the current P0 MVP path"
    }
  ];

  const doneAcceptance = countRows(acceptance, (row) => row.status === "DONE");
  const openRisks = risks.filter((row) => row.status === "OPEN");
  const currentGate = gates.find((row) => row.status === "IN PROGRESS") ?? gates[0];
  const recentTasks = tasks.filter((row) => row.status !== "NOT STARTED").slice(-12).reverse();
  const acceptanceEvidence = traceability
    .filter((row) => row.status === "DONE")
    .slice(-12)
    .reverse();

  return (
    <main
      className="statusWorkspace"
      data-active-data-snapshot={ACTIVE_ANALYSIS_CONTEXT.dataSnapshot}
      data-active-model-version={ACTIVE_ANALYSIS_CONTEXT.modelVersion}
      data-active-profile-version={ACTIVE_ANALYSIS_CONTEXT.profileVersion}
      data-active-score-snapshot={ACTIVE_ANALYSIS_CONTEXT.scoreSnapshot}
      data-active-time={ACTIVE_ANALYSIS_CONTEXT.defaultAsOf}
      data-analysis-contract={ACTIVE_ANALYSIS_CONTEXT.contractVersion}
      data-testid="development-status-screen"
    >
      <aside className="navRail" aria-label="主导航">
        <div className="brandMark" aria-label="商域图谱">
          <span className="brandGlyph">E</span>
          <span>
            <strong>商域图谱</strong>
            <small>EEI</small>
          </span>
        </div>
        <nav aria-label="主导航">
          <a className="navItem" href="/" title="商业版图">
            <Network size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>商业版图</span>
          </a>
        </nav>
        <div className="systemNav" aria-label="系统模块">
          <span className="navGroupLabel">系统模块</span>
          <a className="navItem" href="/objects-scope" title="对象与范围">
            <Database size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>对象与范围</span>
          </a>
          <a
            aria-current="page"
            className="navItem active"
            data-testid="development-status-nav-active"
            href="/development-status"
            title="开发状态"
          >
            <ListChecks size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>开发状态</span>
          </a>
        </div>
      </aside>

      <section className="statusMain" aria-label="开发状态">
        <header className="statusHeader">
          <div>
            <p className="eyebrow">Development Status</p>
            <h1>开发状态</h1>
            <p className="subjectSubtitle">Resolved work, open scope, acceptance evidence and risk controls.</p>
          </div>
          <a className="returnLink" href="/">
            <ArrowLeft size={16} aria-hidden="true" />
            <span>商业版图</span>
          </a>
        </header>

        <section className="statusSummary" aria-label="状态摘要">
          <div data-testid="status-current-gate">
            <dt>Release phase</dt>
            <dd>
              {currentGate.gate_id} / {currentGate.status}
            </dd>
          </div>
          <div>
            <dt>Tasks</dt>
            <dd data-testid="status-task-count">{tasks.length}</dd>
          </div>
          <div>
            <dt>Acceptance done</dt>
            <dd data-testid="status-acceptance-done">{doneAcceptance}</dd>
          </div>
          <div>
            <dt>Open risks</dt>
            <dd data-testid="status-open-risks">{openRisks.length}</dd>
          </div>
        </section>

        <section className="statusLanes" aria-label="状态分类" data-testid="status-lanes">
          {lanes.map((lane) => (
            <article data-testid={`status-lane-${lane.key}`} key={lane.key}>
              <CircleDot size={18} aria-hidden="true" />
              <span>{lane.label}</span>
              <strong>{lane.count}</strong>
              <small>{lane.description}</small>
            </article>
          ))}
        </section>

        <section className="evidenceLinks" data-testid="status-linked-evidence">
          <a data-testid="status-link-tasks" href={`${githubDataRoot}/task_backlog.csv`}>
            <ListChecks size={16} aria-hidden="true" />
            <span>tasks</span>
          </a>
          <a data-testid="status-link-risks" href={`${githubDataRoot}/risk_register.csv`}>
            <ShieldAlert size={16} aria-hidden="true" />
            <span>risks</span>
          </a>
          <a
            data-testid="status-link-controls"
            href={`${githubDataRoot}/risk_control_traceability.csv`}
          >
            <GitBranch size={16} aria-hidden="true" />
            <span>controls</span>
          </a>
          <a
            data-testid="status-link-acceptance"
            href={`${githubDataRoot}/acceptance_traceability.csv`}
          >
            <FileCheck2 size={16} aria-hidden="true" />
            <span>acceptance evidence</span>
          </a>
        </section>

        <section className="statusPanels">
          <article data-testid="status-ledger-panel">
            <header>
              <CheckCircle2 size={18} aria-hidden="true" />
              <h2>Function Status</h2>
            </header>
            <div className="statusTable">
              {ledger.slice(0, 12).map((row) => (
                <div data-testid={`status-ledger-${row.item_id}`} key={row.item_id}>
                  <strong>{row.item_id}</strong>
                  <span>{row.name}</span>
                  <em>{row.implementation_status}</em>
                  <small>{row.validation_status}</small>
                </div>
              ))}
            </div>
          </article>

          <article data-testid="status-task-panel">
            <header>
              <ListChecks size={18} aria-hidden="true" />
              <h2>Recent Task Evidence</h2>
            </header>
            <div className="statusTable">
              {recentTasks.map((row) => (
                <div data-testid={`status-task-${row.task_id}`} key={row.task_id}>
                  <strong>{row.task_id}</strong>
                  <span>{row.title}</span>
                  <em>{row.gate}</em>
                  <small>{row.status}</small>
                </div>
              ))}
            </div>
          </article>

          <article data-testid="status-acceptance-panel">
            <header>
              <FileCheck2 size={18} aria-hidden="true" />
              <h2>Acceptance Evidence</h2>
            </header>
            <div className="statusTable">
              {acceptanceEvidence.map((row) => (
                <div data-testid={`status-acceptance-${row.acceptance_id}`} key={row.trace_id}>
                  <strong>{row.acceptance_id}</strong>
                  <span>{row.evidence_path}</span>
                  <em>{row.test_type}</em>
                  <small>{row.status}</small>
                </div>
              ))}
            </div>
          </article>

          <article data-testid="status-risk-control-panel">
            <header>
              <ShieldAlert size={18} aria-hidden="true" />
              <h2>Risk Controls</h2>
            </header>
            <div className="statusTable">
              {openRisks.slice(0, 8).map((risk) => {
                const linkedControl = riskControls.find((row) => row.risk_id === risk.risk_id);
                return (
                  <div data-testid={`status-risk-${risk.risk_id}`} key={risk.risk_id}>
                    <strong>{risk.risk_id}</strong>
                    <span>{risk.control}</span>
                    <em>{risk.severity}</em>
                    <small>{linkedControl?.acceptance_ids || risk.status}</small>
                  </div>
                );
              })}
            </div>
          </article>
        </section>
      </section>
    </main>
  );
}
