# PFI macOS Entry Apps

This directory contains the portable macOS launcher bundle for PFI.

## Installed local entry points

The launcher is installed to:

```text
~/Desktop/PFI.app
~/Downloads/PFI.app
/Applications/PFI.app
```

## Behavior

The launcher searches for the current local PFI project path, then starts
local `StartPFI.command` through `/bin/zsh` without routing through
Terminal. If no local project is found, it fails closed with a local warning
instead of opening GitHub.

Set `PFI_HOME` before launching if a future agent moves the local checkout.

## Reinstall

```bash
./scripts/installPFIEntryApps.sh
```
