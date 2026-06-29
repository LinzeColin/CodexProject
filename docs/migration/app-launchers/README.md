# App Launcher Snapshots

This directory contains read-only snapshots of the macOS launchers found on the
old Mac for migration handoff.

Included:

- `memory-atlas/`: `/Applications/Memory Atlas.app`
- `serenity-daily-analysis/`: `/Applications/Serenity 每日分析.app`

Only `Info.plist`, `PkgInfo`, and the text launcher scripts are included. Code
signatures, icons, and generated app bundle metadata are intentionally excluded.

Before installing on a new Mac, review and update any absolute paths inside the
launcher scripts so they point at the new checkout location.
