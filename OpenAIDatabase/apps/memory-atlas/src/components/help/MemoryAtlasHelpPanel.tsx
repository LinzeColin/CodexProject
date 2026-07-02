import { ArrowRight, X } from "lucide-react";
import type { ChineseUiCopy } from "../../i18n/types";
import type { ViewKey } from "../../types";

interface MemoryAtlasHelpPanelProps {
  copy: ChineseUiCopy["help"];
  open: boolean;
  onClose: () => void;
  onSelectView: (view: ViewKey) => void;
}

export function MemoryAtlasHelpPanel({ copy, open, onClose, onSelectView }: MemoryAtlasHelpPanelProps) {
  if (!open) return null;

  return (
    <div className="help-backdrop" data-memory-atlas-help-panel="stage0-phase2" role="presentation">
      <aside className="help-panel" aria-label={copy.panelTitle} data-three-minute-path="true">
        <div className="help-panel-heading">
          <div>
            <p className="eyebrow">Memory Atlas Help</p>
            <h2>{copy.panelTitle}</h2>
            <span>{copy.panelSubtitle}</span>
          </div>
          <button aria-label={copy.closeLabel} className="help-close-button" onClick={onClose} title={copy.closeLabel} type="button">
            <X size={18} />
          </button>
        </div>

        <section className="help-path-section" aria-label={copy.threeMinuteTitle}>
          <div className="panel-title-row">
            <h3>{copy.threeMinuteTitle}</h3>
            <span>3 min</span>
          </div>
          <ol className="help-path-list">
            {copy.threeMinutePath.map((step) => (
              <li key={`${step.minute}-${step.view}`}>
                <span className="help-minute">{step.minute}</span>
                <div>
                  <strong>{step.title}</strong>
                  <p>{step.description}</p>
                  <button onClick={() => onSelectView(step.view)} type="button">
                    <span>{step.actionLabel}</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="help-mode-section" aria-label={copy.modeTitle}>
          <div className="panel-title-row">
            <h3>{copy.modeTitle}</h3>
          </div>
          <div className="help-mode-grid">
            <article>
              <strong>{copy.modes.presentation.label}</strong>
              <p>{copy.modes.presentation.description}</p>
            </article>
            <article>
              <strong>{copy.modes.analysis.label}</strong>
              <p>{copy.modes.analysis.description}</p>
            </article>
          </div>
        </section>

        <section className="help-workflow-section" aria-label={copy.workflowTitle}>
          <div className="panel-title-row">
            <h3>{copy.workflowTitle}</h3>
          </div>
          <div className="help-workflow-list">
            {copy.workflowNotes.map((note) => (
              <article key={note.title}>
                <strong>{note.title}</strong>
                <p>{note.description}</p>
              </article>
            ))}
          </div>
        </section>

        <p className="help-footer-note">{copy.footerNote}</p>
      </aside>
    </div>
  );
}
