import { RotateCcw, SearchX } from "lucide-react";

interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  className?: string;
  dataState: string;
  onAction?: () => void;
}

export function EmptyState({ actionLabel, className = "", dataState, description, onAction, title }: EmptyStateProps) {
  return (
    <div className={`empty-state ${className}`.trim()} data-memory-atlas-empty-state={dataState} role="status">
      <SearchX size={24} />
      <strong>{title}</strong>
      <p>{description}</p>
      {actionLabel && onAction ? (
        <button onClick={onAction} type="button">
          <RotateCcw size={15} />
          <span>{actionLabel}</span>
        </button>
      ) : null}
    </div>
  );
}
