# PFI_OS macOS Entry Apps

This directory contains the portable macOS launcher bundle for PFI_OS.

## Installed local entry points

The launcher is installed to:

```text
~/Desktop/PFI_OS.app
~/Downloads/PFI_OS.app
/Applications/PFI_OS.app
```

## Behavior

The launcher searches for the current local PFI_OS project path, then starts
local `StartPFIOS.command` through `/bin/zsh` without routing through
Terminal. If no local project is found, it fails closed with a local warning
instead of opening GitHub.

Set `PFI_OS_HOME` before launching if a future agent moves the local checkout.

## Reinstall

```bash
./scripts/installPFIOSEntryApps.sh
```
