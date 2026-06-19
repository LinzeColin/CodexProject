"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  CircleDollarSign,
  Factory,
  Landmark,
  Network,
  Route
} from "lucide-react";

type IndustryKey = "semiconductors" | "ai-cloud" | "energy";

type Stage = {
  key: string;
  label: string;
  role: string;
  entities: string[];
};

type CrossLink = {
  target: IndustryKey;
  label: string;
  reason: string;
};

type IndustryLandscape = {
  key: IndustryKey;
  name: string;
  taxonomy: string;
  summary: string;
  subindustries: string[];
  stages: Stage[];
  topEntities: string[];
  bottlenecks: string[];
  capital: string[];
  policy: string[];
  changes: string[];
  crossLinks: CrossLink[];
};

const landscapes: Record<IndustryKey, IndustryLandscape> = {
  semiconductors: {
    key: "semiconductors",
    name: "Semiconductors",
    taxonomy: "taxonomy-v4.2",
    summary: "Design, equipment, manufacturing, packaging, system integration and AI demand.",
    subindustries: ["AI accelerators", "EDA and IP", "Foundry", "Advanced packaging", "Equipment"],
    stages: [
      {
        key: "design",
        label: "Design / IP",
        role: "platform control",
        entities: ["NVIDIA", "AMD", "Arm"]
      },
      {
        key: "equipment",
        label: "Equipment",
        role: "production bottleneck",
        entities: ["ASML", "Applied Materials", "Lam Research"]
      },
      {
        key: "foundry",
        label: "Manufacturing",
        role: "wafer capacity",
        entities: ["TSMC", "Intel Foundry", "GlobalFoundries"]
      },
      {
        key: "packaging",
        label: "Advanced packaging",
        role: "AI scaling constraint",
        entities: ["TSMC CoWoS", "Amkor", "ASE"]
      },
      {
        key: "systems",
        label: "Systems",
        role: "route to market",
        entities: ["Dell", "HPE", "Supermicro"]
      },
      {
        key: "customers",
        label: "Cloud and AI customers",
        role: "demand concentration",
        entities: ["Microsoft", "Amazon", "CoreWeave"]
      }
    ],
    topEntities: ["NVIDIA", "TSMC", "ASML", "AMD", "Broadcom", "Intel"],
    bottlenecks: ["EUV exposure capacity", "Advanced packaging queues", "HBM supply", "Export-control scope"],
    capital: ["Foundry capex", "GPU cloud financing", "Customer prepayments", "Strategic minority stakes"],
    policy: ["CHIPS incentives", "Export controls", "Antitrust platform review", "Taiwan geopolitical risk"],
    changes: ["Packaging demand moved into material-change queue", "AI cloud customers added cross-industry pressure"],
    crossLinks: [
      {
        target: "ai-cloud",
        label: "AI cloud infrastructure",
        reason: "GPU demand and cloud financing create downstream dependency"
      },
      {
        target: "energy",
        label: "Power and data-center energy",
        reason: "AI data-center load shifts semiconductor demand into energy constraints"
      }
    ]
  },
  "ai-cloud": {
    key: "ai-cloud",
    name: "AI cloud infrastructure",
    taxonomy: "taxonomy-v4.2",
    summary: "GPU capacity, data-center campuses, cloud customers, integrators and financing loops.",
    subindustries: ["GPU cloud", "Hyperscale cloud", "AI factories", "Systems integration"],
    stages: [
      { key: "chips", label: "Accelerators", role: "compute input", entities: ["NVIDIA", "AMD"] },
      { key: "systems", label: "AI systems", role: "rack integration", entities: ["Dell", "HPE", "ODM partners"] },
      { key: "datacenter", label: "Data centers", role: "capacity host", entities: ["CoreWeave", "Oracle", "AWS"] },
      { key: "software", label: "Platforms", role: "developer demand", entities: ["OpenAI", "Anthropic", "Palantir"] },
      { key: "customers", label: "Enterprise customers", role: "vertical demand", entities: ["Finance", "Defense", "Healthcare"] }
    ],
    topEntities: ["Microsoft", "Amazon", "CoreWeave", "Oracle", "OpenAI", "Anthropic"],
    bottlenecks: ["GPU-backed debt concentration", "Power interconnection queue", "Long-term cloud commitments"],
    capital: ["GPU-secured debt", "Cloud credits", "Strategic model-lab investments"],
    policy: ["AI safety procurement", "Cloud concentration review", "Government contract controls"],
    changes: ["Customer-demand path changed", "Capital commitments linked back to semiconductor suppliers"],
    crossLinks: [
      {
        target: "semiconductors",
        label: "Semiconductors",
        reason: "AI cloud capacity depends on accelerator and packaging supply"
      },
      {
        target: "energy",
        label: "Power and data-center energy",
        reason: "Cloud expansion depends on power availability and grid timing"
      }
    ]
  },
  energy: {
    key: "energy",
    name: "Power and data-center energy",
    taxonomy: "taxonomy-v4.2",
    summary: "Generation, grid interconnection, power contracts and AI data-center load growth.",
    subindustries: ["Nuclear", "Gas generation", "Grid equipment", "Data-center power"],
    stages: [
      { key: "generation", label: "Generation", role: "power source", entities: ["Constellation", "NextEra", "Vistra"] },
      { key: "grid", label: "Grid", role: "interconnection", entities: ["GE Vernova", "Duke Energy"] },
      { key: "contracts", label: "Power contracts", role: "load commitment", entities: ["Hyperscalers", "GPU clouds"] },
      { key: "facilities", label: "AI campuses", role: "demand sink", entities: ["Data-center campuses", "Colocation"] },
      { key: "customers", label: "Compute demand", role: "downstream pressure", entities: ["AI cloud", "Semiconductors"] }
    ],
    topEntities: ["Constellation", "NextEra", "Vistra", "GE Vernova", "Duke Energy"],
    bottlenecks: ["Interconnection queue", "Firm power availability", "Cooling and site constraints"],
    capital: ["Utility capex", "Power purchase agreements", "Infrastructure debt"],
    policy: ["Rate-base approval", "Reliability rules", "Clean-power credits"],
    changes: ["AI data-center load added cross-industry pressure", "Energy path flagged as semiconductor constraint"],
    crossLinks: [
      {
        target: "semiconductors",
        label: "Semiconductors",
        reason: "Energy availability constrains AI accelerator deployment"
      },
      {
        target: "ai-cloud",
        label: "AI cloud infrastructure",
        reason: "Cloud data-center capacity creates incremental power demand"
      }
    ]
  }
};

const orderedIndustryKeys: IndustryKey[] = ["semiconductors", "ai-cloud", "energy"];

export default function IndustriesPage() {
  const [activeKey, setActiveKey] = useState<IndustryKey>("semiconductors");
  const [path, setPath] = useState<IndustryKey[]>(["semiconductors"]);
  const active = landscapes[activeKey];
  const pathLabel = useMemo(() => path.map((key) => landscapes[key].name).join(" -> "), [path]);

  function switchIndustry(nextKey: IndustryKey) {
    setActiveKey(nextKey);
    setPath((current) => (current[current.length - 1] === nextKey ? current : [...current, nextKey]));
  }

  return (
    <main className="industryWorkspace" data-testid="industry-landscape-page">
      <aside className="industryRail" aria-label="行业切换">
        <a className="backLink" href="/">
          <Route size={16} aria-hidden="true" />
          <span>商业版图</span>
        </a>
        {orderedIndustryKeys.map((key) => (
          <button
            aria-current={key === activeKey ? "page" : undefined}
            className={key === activeKey ? "industrySwitch active" : "industrySwitch"}
            data-testid={`industry-switch-${key}`}
            key={key}
            onClick={() => switchIndustry(key)}
            type="button"
          >
            <Network size={16} aria-hidden="true" />
            <span>{landscapes[key].name}</span>
          </button>
        ))}
      </aside>

      <section className="industryMain" data-information-workspace="industry-landscape">
        <header className="industryHero">
          <div>
            <p className="eyebrow">Industry Landscape</p>
            <h1 data-testid="industry-title">{active.name}</h1>
            <p>{active.summary}</p>
          </div>
          <div className="industryMeta" data-testid="industry-taxonomy">
            <span>{active.taxonomy}</span>
            <span>Fixture projection</span>
          </div>
        </header>

        <div className="industryPath" data-testid="cross-industry-notice">
          <strong>Cross-industry path</strong>
          <span>{pathLabel}</span>
        </div>

        <section
          aria-label="行业价值链"
          className="industryChain"
          data-testid="industry-chain-stages"
          data-visual-surface="industry-chain"
        >
          {active.stages.map((stage, index) => (
            <article
              className="industryStage"
              data-testid={`industry-stage-${stage.key}`}
              key={stage.key}
            >
              <header>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h2>{stage.label}</h2>
              </header>
              <p>{stage.role}</p>
              <ul>
                {stage.entities.map((entity) => (
                  <li key={entity}>{entity}</li>
                ))}
              </ul>
            </article>
          ))}
        </section>

        <section className="industrySummaryGrid">
          <article data-testid="industry-subindustries">
            <h2>Subindustries</h2>
            <ul>
              {active.subindustries.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article data-testid="industry-entities">
            <h2>Entities</h2>
            <ul>
              {active.topEntities.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article data-testid="industry-bottlenecks">
            <h2>Bottlenecks</h2>
            <ul>
              {active.bottlenecks.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article data-testid="industry-capital">
            <h2>
              <CircleDollarSign size={16} aria-hidden="true" />
              Capital
            </h2>
            <ul>
              {active.capital.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article data-testid="industry-policy">
            <h2>
              <Landmark size={16} aria-hidden="true" />
              Policy
            </h2>
            <ul>
              {active.policy.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
          <article data-testid="industry-changes">
            <h2>
              <Activity size={16} aria-hidden="true" />
              Changes
            </h2>
            <ul>
              {active.changes.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          </article>
        </section>

        <section className="crossIndustry" data-testid="cross-industry-links">
          <header>
            <Factory size={18} aria-hidden="true" />
            <h2>Cross-industry navigation</h2>
          </header>
          <div>
            {active.crossLinks.map((link) => (
              <button
                data-testid={`cross-industry-${link.target}`}
                key={link.target}
                onClick={() => switchIndustry(link.target)}
                type="button"
              >
                <span>{link.label}</span>
                <small>{link.reason}</small>
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
