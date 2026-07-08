# Restore 20260708T160935Z

本目录包含 archived_sessions 清理备份。

```bash
shasum -a 256 -c PARTS_SHA256SUMS.txt
cat parts/codex-sessions-archived_sessions-20260708T160935Z.tar.enc.part-* > /tmp/20260708T160935Z.tar.enc
openssl enc -d -aes-256-cbc -pbkdf2 -pass file:/path/to/keyfile \
  -in /tmp/20260708T160935Z.tar.enc | tar -xvf - -C "$HOME"
```
