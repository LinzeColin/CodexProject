import { AlertTriangle, RotateCcw } from "lucide-react";

interface ErrorStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  className?: string;
  compact?: boolean;
  dataState: string;
  details?: string;
  onAction?: () => void;
}

export function ErrorState({
  actionLabel,
  className = "",
  compact = false,
  dataState,
  description,
  details,
  onAction,
  title,
}: ErrorStateProps) {
  return (
    <div
      className={`error-state${compact ? " compact" : ""} ${className}`.trim()}
      data-memory-atlas-error-state={dataState}
      role="alert"
    >
      <AlertTriangle size={compact ? 18 : 24} />
      <div>
        <strong>{title}</strong>
        <p>{description}</p>
        {details ? <small>{details}</small> : null}
      </div>
      {actionLabel && onAction ? (
        <button onClick={onAction} type="button">
          <RotateCcw size={15} />
          <span>{actionLabel}</span>
        </button>
      ) : null}
    </div>
  );
}
