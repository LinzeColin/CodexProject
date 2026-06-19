# PFI-001 Reproducible Environment

Version: PFI-001 / v0.2

PFI OS separates installation from runtime. Startup, status, verification, and
gate commands must not install or upgrade dependencies. They resolve an already
prepared Python environment and fail with a clear remediation command when the
environment is missing.

## Canonical Runtime

- Python version file: `.python-version`
- Dependency lock: `requirements.lock`
- Install command: `scripts/installLockedEnv.sh`
- Runtime resolver: `scripts/pfiRuntime.sh`

## Clean Install

```bash
cd "$PFI_OS_HOME"
scripts/installLockedEnv.sh
```

The installer creates `.venv`, installs `requirements.lock`, installs the local
package with `--no-deps`, verifies app/test dependencies, and writes
`.venv/.pfi_os_app_ready`.

For clean-install proof without touching the default `.venv`, use:

```bash
PFI_VENV_DIR=/tmp/pfi_os_clean_env scripts/installLockedEnv.sh
```

## Offline Warm Start

After the locked environment exists, startup must perform no dependency
installation:

```bash
PFI_UI_V2=1 scripts/startPFIOS.sh
```

If dependencies are missing, runtime commands exit with remediation text instead
of invoking `pip`.

## Gate Commands

```bash
scripts/pfiGate.sh fast
scripts/pfiGate.sh target
scripts/pfiGate.sh full
scripts/pfiGate.sh release
```

- `fast`: syntax/product-contract/reproducible-env/secret scan.
- `target`: current PFI-001 plus Web Shell target contract tests.
- `full`: full local test script plus secret scan.
- `release`: explicit heavy release gate plus secret scan.

## Artifact Policy

Test artifacts must not contain secrets, private holdings, account screenshots,
raw local logs, runtime SQLite databases, or private absolute paths. Public Git
may contain sanitized summaries, fixtures, contracts, and deterministic test
evidence.
