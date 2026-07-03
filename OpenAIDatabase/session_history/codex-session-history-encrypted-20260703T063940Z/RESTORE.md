# Encrypted Codex Session History Backup 20260703T063940Z

This directory contains an encrypted, lossless backup of local Codex session history from the old Mac.

## Source Included

- /Users/linzezhang/.codex/sessions
- /Users/linzezhang/.codex/archived_sessions

## Encryption

- Algorithm: openssl enc -aes-256-cbc -pbkdf2 -salt
- Key file on old Mac: /Users/linzezhang/.codex/private_keys/codex-session-history-encrypted-20260703T063940Z.key
- Key SHA-256 fingerprint: 572681cd6fa5a452902912ade07b014b67c9c3110724c29899e2711cd55064b3
- The key file is not committed to GitHub. Transfer it separately and keep it private.

## Restore On New Mac

From this directory after cloning the repo:

```bash
shasum -a 256 -c PARTS_SHA256SUMS.txt
cat parts/codex-sessions-archived_sessions-20260703T063940Z.tar.enc.part-* > /tmp/codex-session-history-20260703T063940Z.tar.enc
openssl enc -d -aes-256-cbc -pbkdf2 -pass file:/path/to/codex-session-history-encrypted-20260703T063940Z.key \
  -in /tmp/codex-session-history-20260703T063940Z.tar.enc | tar -xvf - -C "$HOME"
rm -f /tmp/codex-session-history-20260703T063940Z.tar.enc
```

Do not overwrite a live new-Mac Codex profile until you decide whether to merge, replace, or restore into a temporary inspection folder.
