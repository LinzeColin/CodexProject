import { CalendarDays, Crosshair, Download, Play, RefreshCw, Save } from "lucide-react";
import type { ComponentType, ReactNode } from "react";
import type { ViewKey } from "../../types";
import { COMMAND_WORKFLOW_VERSION, CommandExecutionState, CommandPaletteCommand, CommandPaletteModel, S12P1CommandId, S12_P3_CHATGPT_DEEP_EXPLORE_VERSION } from "../../shared/atlas/constants";
import { INITIAL_COMMAND_EXECUTION_STATE } from "../../shared/atlas/runtimeConfig";
import { MachineFieldDetails } from "../../shared/ui/display";



export function CommandPalettePanel({
  execution,
  model,
  onExecuteCommand,
  onNavigateView,
  ownerDailyEntry,
  selectedCommandId,
  onSelectCommand,
}: {
  execution: CommandExecutionState;
  model: CommandPaletteModel;
  onExecuteCommand: (command: CommandPaletteCommand) => void;
  onNavigateView: (view: ViewKey) => void;
  ownerDailyEntry: ReactNode;
  selectedCommandId: S12P1CommandId;
  onSelectCommand: (command: CommandPaletteCommand) => void;
}) {
  const selectedCommand = model.commands.find((command) => command.id === selectedCommandId) ?? model.commands[0];
  const selectedExecution = execution.commandId === selectedCommand.id ? execution : INITIAL_COMMAND_EXECUTION_STATE;
  return (
    <section
      className="command-palette"
      aria-label="Memory Atlas 命令面板"
      data-s12-p1-command-palette={model.version}
      data-s12-p1-command-count={model.commands.length}
      data-s12-p1-personalization-targets={model.personalizationTargets.join(",")}
      data-s12-p1-safety-boundary="S12 dry-run: No automatic send; No raw mutation; No proposal apply execution"
      data-s12-p3-chatgpt-deep-explore={S12_P3_CHATGPT_DEEP_EXPLORE_VERSION}
      data-s12-p3-chatgpt-deep-explore-command="chatgpt_deep_explore"
      data-r3-command-workflows={COMMAND_WORKFLOW_VERSION}
      data-r3-execution-status={selectedExecution.status}
      data-r3-write-scope="Application Support installed source copy; redacted sync and derived outputs only; no canonical repo mutation"
    >
      <div className="command-palette-heading">
        <div className="command-palette-heading-copy">
          <p className="eyebrow">快捷操作</p>
          <h2>接下来可以做什么</h2>
          <span>{model.commands.length} 个可选动作</span>
        </div>
        {ownerDailyEntry}
      </div>
      <div className="command-palette-grid">
        {model.commands.map((command) => {
          const Icon = commandPaletteIcon(command.id);
          return (
            <button
              className={command.id === selectedCommand.id ? "command-palette-action active" : "command-palette-action"}
              data-s12-p1-command-id={command.id}
              disabled={execution.status === "running"}
              key={command.id}
              onClick={() => onSelectCommand(command)}
              title={command.description}
              type="button"
            >
              <Icon size={18} />
              <span>{command.label}</span>
              <small>{command.status}</small>
            </button>
          );
        })}
      </div>
      <div className="command-palette-detail">
        <div className="command-palette-detail-copy">
          <strong>{selectedCommand.label}</strong>
          <p>{selectedCommand.description}</p>
        </div>
        <button
          className="command-execute-button"
          data-r3-command-execute={selectedCommand.id}
          disabled={execution.status === "running"}
          onClick={() => onExecuteCommand(selectedCommand)}
          type="button"
        >
          {selectedExecution.status === "running" ? <RefreshCw aria-hidden="true" className="command-running-icon" size={15} /> : <Play aria-hidden="true" size={15} />}
          <span>{selectedExecution.status === "running" ? "正在执行" : "执行此操作"}</span>
        </button>
      </div>
      {selectedExecution.status !== "idle" ? (
        <div
          aria-live="polite"
          className={`command-result command-result-${selectedExecution.status}`}
          data-r3-command-result={selectedCommand.id}
          data-r3-command-result-status={selectedExecution.status}
          role="status"
        >
          <strong>{selectedExecution.title}</strong>
          <p>{selectedExecution.message}</p>
          {selectedExecution.inputHint ? <code>{selectedExecution.inputHint}</code> : null}
          {selectedExecution.outputs.length > 0 ? (
            <ul>
              {selectedExecution.outputs.map((output) => <li key={output}><code>{output}</code></li>)}
            </ul>
          ) : null}
          {selectedExecution.fallbackUrl ? (
            <a href={selectedExecution.fallbackUrl} rel="noreferrer" target="_blank">
              {selectedExecution.status === "local_required" ? "打开本地 Memory Atlas" : "打开 ChatGPT 预填充页面"}
            </a>
          ) : null}
          {selectedExecution.navigationView ? (
            <button
              className="command-result-action"
              data-r3-command-navigate={selectedExecution.navigationView}
              onClick={() => onNavigateView(selectedExecution.navigationView as ViewKey)}
              type="button"
            >
              查看总结
            </button>
          ) : null}
        </div>
      ) : null}
      <MachineFieldDetails title="运行边界与技术详情" className="command-technical-details">
        <div className="command-palette-technical-content">
          <small>{selectedCommand.humanAction}</small>
          <code>{selectedCommand.dryRunCommand}</code>
          <div className="command-palette-safety">
            <span>No automatic send</span>
            <span>No silent send</span>
            <span>No canonical repo mutation</span>
            <span>Application Support source copy only</span>
            <span>No proposal apply execution</span>
            <span>No cookie/token/secret export</span>
            <span>ChatGPT / Codex / other agent personalization prompt</span>
            <span>prefill_only / auto_submit</span>
          </div>
        </div>
      </MachineFieldDetails>
    </section>
  );
}



export function commandPaletteIcon(commandId: S12P1CommandId): ComponentType<{ size?: number }> {
  if (commandId === "sync_chatgpt") return RefreshCw;
  if (commandId === "sync_codex") return Download;
  if (commandId === "generate_weekly_report") return CalendarDays;
  if (commandId === "view_pending_proposals") return Save;
  if (commandId === "chatgpt_deep_explore") return Crosshair;
  return Crosshair;
}
