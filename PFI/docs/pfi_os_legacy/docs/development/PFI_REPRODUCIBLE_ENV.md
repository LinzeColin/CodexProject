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

## PR/CI Evidence

PFI_OS is stored as a subdirectory of `LinzeColin/CodexProject`, so the
GitHub Actions workflow that actually runs on pull requests must live at the
repository root:

```text
.github/workflows/pfi-os-smoke.yml
```

The root workflow uses `working-directory: PFI_OS`, installs
`PFI_OS/requirements.lock`, runs `scripts/pfiGate.sh target`, and then runs
`scripts/pfiCiInjectedFailureProof.sh`.

The injected-failure proof creates a temporary Git repository with a tracked
fake API key and asserts that `scripts/secretScan.sh` fails with
`injected_secret.txt:openai_key`. If the secret scan ever accepts the injected
secret, CI fails.

Observed PR/CI proof on PR #2:

- Commit: `9ed86b6dc43e769242db18d6b7bd60c1a7a538a8`
- Workflow: `PFI_OS Smoke`
- Run id: `27856494975`
- Run number: `2`
- Conclusion: `success`
- Successful proof steps:
  - `Run PFI target gate`
  - `Prove injected failure is blocked`

## Artifact Policy

Test artifacts must not contain secrets, private holdings, account screenshots,
raw local logs, runtime SQLite databases, or private absolute paths. Public Git
may contain sanitized summaries, fixtures, contracts, and deterministic test
evidence.
