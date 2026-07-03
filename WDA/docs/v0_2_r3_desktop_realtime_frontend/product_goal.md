# Product Goal

WDA v0.2-R3 makes WDA usable as a normal local software system instead of a folder of scripts and Markdown outputs.

## User Goal

The owner should be able to double-click WDA, see the latest local analysis in Chinese, trigger an update, inspect failures, and open evidence-backed reports without typing terminal commands.

## Success Criteria

- Double-click entry exists under Downloads.
- FastAPI service starts locally on the new computer.
- Dashboard is Chinese, human-readable, and action-oriented.
- Manual update writes status, logs, dashboard snapshot, and report index.
- launchd scheduler template exists but is not loaded without user action.
- Repo-safe docs explain operation, recovery, and data boundaries.

## Non-goals

- No cloud deployment.
- No external drive access.
- No WeChat exporter execution in this sprint.
- No RAG/Web/Matrix buildout.
- No raw/private data in Git.
