# EVA_OS macOS Entry Apps

This directory contains the portable macOS launcher bundle for EVA_OS.

## Installed local entry points

The launcher is installed to:

```text
~/Desktop/EVA_OS.app
~/Downloads/EVA_OS.app
/Applications/EVA_OS.app
```

## Behavior

The launcher searches for the current local EVA_OS project path, then starts
local `StartQuantLab.command` through `/bin/zsh` without routing through
Terminal. If no local project is found, it fails closed with a local warning
instead of opening GitHub.

Set `EVA_OS_HOME` before launching if a future agent moves the local checkout.

## Reinstall

```bash
./scripts/installEVAOSEntryApps.sh
```
