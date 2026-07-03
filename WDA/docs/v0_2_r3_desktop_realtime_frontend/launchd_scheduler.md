# launchd Scheduler

## Script

`WDA/scripts/install_wda_launch_agent.sh` writes:

```text
~/Library/LaunchAgents/com.linze.wda.v0_2_r3.update.plist
```

Default interval:

```text
86400 seconds
```

The plist runs:

```text
WDA/scripts/wda_app_update.sh
```

## Install Modes

Write plist only:

```bash
WDA/scripts/install_wda_launch_agent.sh
```

Write and load:

```bash
WDA/scripts/install_wda_launch_agent.sh --load
```

Uninstall:

```bash
WDA/scripts/uninstall_wda_launch_agent.sh
```

## Boundary

The scheduler does not run WeChat exporter tools and does not access external drives. It refreshes the local R3 runtime from the existing v0.2-R2 workspace.
