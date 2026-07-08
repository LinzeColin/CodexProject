# ChatGPT Raw Export Archive - 2026-07-07

This directory stores the complete original July 2026 ChatGPT export as GitHub-compatible split parts.

Public visibility warning: this repository is public. The user explicitly selected option 2 and confirmed that the complete original raw ChatGPT export may be committed to GitHub despite public repository visibility.

## Original File

- Filename: `6c7acaff424d50d929d3779259c2c0eccd140d4afdf99ae1816dc673988dcd83-2026-07-07-04-49-46-53d01542c71941e199f8cdac3bbda0ce.zip`
- Size: `1473421021` bytes
- SHA256: `52f204dd8d78b76a79c6fc37e3e09987d3ab682c87098da017b894dd88c3a868`
- Parts: `16`
- Manifest: `manifest.json`

## Restore

From this directory:

```bash
./restore.sh
```

Manual equivalent:

```bash
cat parts/chatgpt_raw_export_2026-07-07.zip.part-* > 6c7acaff424d50d929d3779259c2c0eccd140d4afdf99ae1816dc673988dcd83-2026-07-07-04-49-46-53d01542c71941e199f8cdac3bbda0ce.zip
shasum -a 256 6c7acaff424d50d929d3779259c2c0eccd140d4afdf99ae1816dc673988dcd83-2026-07-07-04-49-46-53d01542c71941e199f8cdac3bbda0ce.zip
```

The resulting SHA256 must equal:

```text
52f204dd8d78b76a79c6fc37e3e09987d3ab682c87098da017b894dd88c3a868
```
