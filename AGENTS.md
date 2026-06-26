# CodexProject Agent Contract

## Repository Scope

This repository is the source-level project hub for active Codex projects.
PFI Stage work in this checkout must use `PFI_OS/` as the registered PFI
project path unless a later governance change explicitly moves it.

## PFI V0.2 Stage 0

- Current registered PFI path: `PFI_OS/`.
- Current PFI governing contract: `PFI_OS/AGENTS.md`.
- Current PFI Stage 0 handoff: `PFI_OS/docs/pfi_v02/STAGE0_COMPATIBILITY_AUDIT.md`.
- PFI V0.2 target IA has eight first-level entries; current six Web Shell
  entries remain compatibility aliases until Stage 1 migration.
- Existing PFI/大数据模拟器 capability maps to
  `投资管理 > 策略实验室 / 大数据模拟器`.

## Changed-Scope Check

For PFI work, inspect changed scope before closeout with:

```bash
git diff --name-only origin/main...HEAD -- PFI_OS AGENTS.md README.md governance/projects.yaml
git diff --check
```

If `origin/main` is unavailable in a local checkout, use the current tracking
branch merge base and record the fallback in the delivery note.

## Boundaries

- Do not move, rename, or broad-refactor active PFI runtime paths during Stage 0.
- Do not add rejected Alpha variants, Alpha product pages, or system/development
  product first-level navigation to PFI.
- Do not read, reuse, migrate, or depend on the excluded external payment
  project named in the PFI TaskPack.
- Do not request trading passwords, submit real orders, or add autonomous
  real-money trading flows.
