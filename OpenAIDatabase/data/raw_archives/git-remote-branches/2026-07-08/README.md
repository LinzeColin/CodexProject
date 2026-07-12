# CodexProject Remote Branch Archive - 2026-07-08

This archive preserves all non-main remote branch tips before cleanup removes remote branches from `LinzeColin/CodexProject`.

- Original bundle: `codexproject_remote_non_main_branches_20260708.bundle`
- Bundle size: `1161813692` bytes
- Bundle SHA256: `ec03e395898169ff1a625732bb1cb1582c5576e0f611c1be91d7ffad78f928e6`
- Branch refs recorded: `23`
- Split parts: `13`
- Manifest: `manifest.json`

## Restore

From this directory:

```bash
./restore.sh
```

Manual equivalent:

```bash
cat parts/codexproject_remote_non_main_branches_20260708.bundle.part-* > codexproject_remote_non_main_branches_20260708.bundle
shasum -a 256 codexproject_remote_non_main_branches_20260708.bundle
git bundle verify codexproject_remote_non_main_branches_20260708.bundle
```

The resulting SHA256 must equal:

```text
ec03e395898169ff1a625732bb1cb1582c5576e0f611c1be91d7ffad78f928e6
```

To restore branch refs from a clone of `main`, inspect the bundle with `git bundle list-heads` and fetch the desired refs explicitly.
