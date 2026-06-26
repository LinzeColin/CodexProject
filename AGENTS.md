# CodexProject Agent Contract

## Repository Scope

This repository is the source-level project hub for active Codex projects.
PFI V0.2 Stage work in this checkout must use `PFI/` as the registered PFI
project path.

## PFI V0.2

- Current registered PFI path: `PFI/`.
- Current PFI governing contract: `PFI/AGENTS.md`.
- Current PFI Stage 2 handoff: `PFI/HANDOFF.md`.
- PFI V0.2 target IA has eight first-level entries.
- Existing PFI/大数据模拟器 capability maps to
  `投资管理 > 策略实验室 / 大数据模拟器`.
- Do not move `PFI/大数据模拟器/qbvs` during Stage 2.
- Stage 2 data-source work must keep non-CSV sources first-class and route
  low-confidence inputs into review before ledger acceptance.

## Changed-Scope Check

For PFI work, inspect changed scope before closeout with:

```bash
git diff --name-only origin/main...HEAD -- PFI AGENTS.md README.md governance/projects.yaml
git diff --check
```

If `origin/main` is unavailable in a local checkout, use the current tracking
branch merge base and record the fallback in the delivery note.

## Boundaries

- Do not move, rename, or broad-refactor active PFI runtime paths during Stage 2.
- Do not add rejected Alpha variants, Alpha product pages, or system/development
  product first-level navigation to PFI.
- Do not read, reuse, migrate, or depend on the excluded external payment
  project named in the PFI TaskPack.
- Do not request trading passwords, submit real orders, or add autonomous
  real-money trading flows.
