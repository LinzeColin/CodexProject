# App Launcher Spec

## Installed Local Entries

- `/Users/linzezhang/Downloads/WDA.app`
- `/Users/linzezhang/Downloads/WDA.command`

Both entries execute:

```bash
/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/WDA/WDA/scripts/wda_app_start.sh
```

## Startup Behavior

1. Ensure local runtime folders exist.
2. Ensure local runtime venv exists.
3. Install FastAPI/Uvicorn dependencies into the local runtime venv only if missing.
4. Initialize R3 status.
5. Start the local service in a detached process.
6. Open `http://127.0.0.1:18730/`.

## Stop Behavior

`WDA/scripts/wda_app_stop.sh` reads the runtime PID file and stops the service if it is running.

## Evidence

Local entries were installed and verified by listing:

```text
/Users/linzezhang/Downloads/WDA.app
/Users/linzezhang/Downloads/WDA.command
```
