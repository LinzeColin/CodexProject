import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  ArrowLeft,
  Boxes,
  Building2,
  CircleDollarSign,
  Database,
  Download,
  FileJson,
  GitBranch,
  ListChecks,
  Network,
  PackageSearch,
  Rows3,
  ShieldCheck
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { ACTIVE_ANALYSIS_CONTEXT } from "../analysis-contract";

type CsvRow = Record<string, string>;

type CatalogSpec = {
  key: string;
  title: string;
  path: string;
  primaryKey: string;
  nameField: string;
  definition: string;
  icon: LucideIcon;
  coverageKey: string;
};

type CatalogView = CatalogSpec & {
  rows: CsvRow[];
};

const dataRoot = resolve(process.cwd(), "../../data");

const catalogSpecs: CatalogSpec[] = [
  {
    key: "relationship-family",
    title: "关系家族",
    path: "relationship_family_catalog.csv",
    primaryKey: "family_key",
    nameField: "name_zh",
    definition: "Ten top-level relationship families used to classify enterprise ecosystem edges.",
    icon: GitBranch,
    coverageKey: "relationship_families"
  },
  {
    key: "relationship",
    title: "关系类型",
    path: "relationship_taxonomy.csv",
    primaryKey: "relationship_type",
    nameField: "relationship_type",
    definition: "Fifty-two machine-readable relationship types with family, direction and definition.",
    icon: Network,
    coverageKey: "relationship_types"
  },
  {
    key: "upstream-downstream-role",
    title: "上下游角色",
    path: "upstream_downstream_role_catalog.csv",
    primaryKey: "role_id",
    nameField: "name_zh",
    definition: "Recursive upstream and downstream roles for supplier, customer and ecosystem traversal.",
    icon: Rows3,
    coverageKey: "upstream_downstream_roles"
  },
  {
    key: "supply-chain-stage",
    title: "供应链阶段",
    path: "supply_chain_stage_taxonomy.csv",
    primaryKey: "stage_id",
    nameField: "name_zh",
    definition: "Sixteen ordered supply-chain stages from critical minerals to customers.",
    icon: PackageSearch,
    coverageKey: "supply_chain_stages"
  },
  {
    key: "industry",
    title: "行业分类",
    path: "industry_taxonomy.csv",
    primaryKey: "industry_id",
    nameField: "name_zh",
    definition: "Industry taxonomy with parent and child rows for multi-label company membership.",
    icon: Building2,
    coverageKey: "industries"
  },
  {
    key: "sector",
    title: "行业板块",
    path: "sector_taxonomy.csv",
    primaryKey: "sector_id",
    nameField: "name_zh",
    definition: "Sector grouping layer used to scan industry landscapes and power systems.",
    icon: Boxes,
    coverageKey: "sectors"
  },
  {
    key: "business-segment",
    title: "业务板块",
    path: "business_segment_taxonomy.csv",
    primaryKey: "segment_id",
    nameField: "name_zh",
    definition: "Business segment objects for group structure, product lines and revenue views.",
    icon: Boxes,
    coverageKey: "business_segments"
  },
  {
    key: "capital-object",
    title: "资本对象",
    path: "capital_object_taxonomy.csv",
    primaryKey: "capital_object_id",
    nameField: "name_zh",
    definition: "Capital objects with amount semantics and aggregation rules.",
    icon: CircleDollarSign,
    coverageKey: "capital_objects"
  },
  {
    key: "domain-object",
    title: "领域对象",
    path: "domain_object_catalog.csv",
    primaryKey: "object_type_id",
    nameField: "name_zh",
    definition: "Domain object scope for entities, relationships, evidence, models and user state.",
    icon: ShieldCheck,
    coverageKey: "domain_objects"
  },
  {
    key: "company",
    title: "公司目录",
    path: "company_catalog.csv",
    primaryKey: "company_id",
    nameField: "canonical_name",
    definition: "Research universe company catalog with P0/P1/P2 targets and global context nodes.",
    icon: Building2,
    coverageKey: "companies"
  }
];

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

function readCatalog(spec: CatalogSpec): CatalogView {
  const rows = parseCsv(readFileSync(resolve(dataRoot, spec.path), "utf8"));
  return { ...spec, rows };
}

function sampleDefinition(row: CsvRow) {
  return (
    row.definition ||
    row.description ||
    row.examples ||
    row.research_scope ||
    row.scope ||
    row.amount_semantics ||
    row.relationship_mode ||
    row.industry_or_power_system ||
    "Canonical scope row"
  );
}

export default function ObjectsScopePage() {
  const catalogs = catalogSpecs.map(readCatalog);
  const totalRows = catalogs.reduce((sum, catalog) => sum + catalog.rows.length, 0);

  return (
    <main
      className="catalogWorkspace"
      data-active-data-snapshot={ACTIVE_ANALYSIS_CONTEXT.dataSnapshot}
      data-active-model-version={ACTIVE_ANALYSIS_CONTEXT.modelVersion}
      data-active-profile-version={ACTIVE_ANALYSIS_CONTEXT.profileVersion}
      data-active-score-snapshot={ACTIVE_ANALYSIS_CONTEXT.scoreSnapshot}
      data-active-time={ACTIVE_ANALYSIS_CONTEXT.defaultAsOf}
      data-analysis-contract={ACTIVE_ANALYSIS_CONTEXT.contractVersion}
      data-catalog-version="v4.2.0"
      data-testid="objects-scope-screen"
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
          <a
            aria-current="page"
            className="navItem active"
            data-testid="objects-scope-nav-active"
            href="/objects-scope"
            title="对象与范围"
          >
            <Database size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>对象与范围</span>
          </a>
          <a
            className="navItem"
            data-testid="development-status-nav-link"
            href="/development-status"
            title="开发状态"
          >
            <ListChecks size={18} strokeWidth={1.8} aria-hidden="true" />
            <span>开发状态</span>
          </a>
        </div>
      </aside>

      <section className="objectScopeMain" aria-label="对象与范围">
        <header className="objectScopeHeader">
          <div>
            <p className="eyebrow">Objects and Scope</p>
            <h1>对象与范围</h1>
            <p className="subjectSubtitle">Canonical catalogs, coverage counts and export links.</p>
          </div>
          <a className="returnLink" href="/">
            <ArrowLeft size={16} aria-hidden="true" />
            <span>商业版图</span>
          </a>
        </header>

        <section className="scopeSummary" aria-label="覆盖摘要">
          <div>
            <dt>Catalogs</dt>
            <dd data-testid="object-scope-catalog-count">{catalogs.length}</dd>
          </div>
          <div>
            <dt>Total rows</dt>
            <dd data-testid="object-scope-total-rows">{totalRows}</dd>
          </div>
          <div>
            <dt>Acceptance</dt>
            <dd>A169 / A170</dd>
          </div>
          <div>
            <dt>Exports</dt>
            <dd>JSON + CSV</dd>
          </div>
        </section>

        <section className="coverageGrid" aria-label="对象范围覆盖">
          {catalogs.map((catalog) => {
            const Icon = catalog.icon;
            return (
              <div
                className="coverageCell"
                data-testid={`object-scope-coverage-${catalog.coverageKey}`}
                key={catalog.key}
              >
                <Icon size={18} aria-hidden="true" />
                <span>{catalog.title}</span>
                <strong>{catalog.rows.length}</strong>
              </div>
            );
          })}
        </section>

        <section className="catalogMatrix" aria-label="目录定义与导出">
          {catalogs.map((catalog) => {
            const Icon = catalog.icon;
            const sampleRows = catalog.rows.slice(0, 3);
            return (
              <article
                className="catalogTile"
                data-testid={`object-scope-catalog-${catalog.key}`}
                key={catalog.key}
              >
                <header>
                  <Icon size={20} aria-hidden="true" />
                  <div>
                    <h2>{catalog.title}</h2>
                    <p data-testid={`object-scope-definition-${catalog.key}`}>
                      {catalog.definition}
                    </p>
                  </div>
                  <strong>{catalog.rows.length}</strong>
                </header>
                <dl className="catalogMeta">
                  <div>
                    <dt>Primary key</dt>
                    <dd>{catalog.primaryKey}</dd>
                  </div>
                  <div>
                    <dt>Source</dt>
                    <dd>data/{catalog.path}</dd>
                  </div>
                </dl>
                <ul className="definitionList">
                  {sampleRows.map((row) => (
                    <li key={row[catalog.primaryKey]}>
                      <strong>{row[catalog.nameField] || row[catalog.primaryKey]}</strong>
                      <span>{sampleDefinition(row)}</span>
                    </li>
                  ))}
                </ul>
                <div className="exportLinks" aria-label={`${catalog.title} export links`}>
                  <a
                    data-testid={`object-scope-export-${catalog.key}-json`}
                    href={`/v1/catalogs/${catalog.key}`}
                  >
                    <FileJson size={15} aria-hidden="true" />
                    <span>JSON</span>
                  </a>
                  <a
                    data-testid={`object-scope-export-${catalog.key}-csv`}
                    href={`/v1/catalogs/${catalog.key}?format=csv`}
                  >
                    <Download size={15} aria-hidden="true" />
                    <span>CSV</span>
                  </a>
                </div>
              </article>
            );
          })}
        </section>
      </section>
    </main>
  );
}
