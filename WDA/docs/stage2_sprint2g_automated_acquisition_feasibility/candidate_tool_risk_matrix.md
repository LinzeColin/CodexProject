# Candidate Tool Risk Matrix

| Route | Legal/privacy risk | Security risk | Technical risk | Main unacceptable condition | Rollback |
|---|---:|---:|---:|---|---|
| `wechat-cli` / `wx-cli` style local CLI exporter | High | High | Medium-high | Requires unapproved key extraction, upload, broad export, or writes outside WDA_MetaData | Stop process, delete trial output, preserve command log only |
| `wechat-local-mcp` style exporter | High | High | Medium-high | Plaintext cache or local API cannot be constrained to WDA_MetaData and localhost-only use | Stop server, remove cache, delete trial output |
| PyWxDump-style exporter | High | High | High on macOS | macOS 4.1.11 unsupported or tool requires Windows-only workflow | Do not execute; retain research note |
| chatlog/EchoTrace-style exporter | High | Medium-high | High | Tool is unmaintained or cannot produce auditable local exports | Do not execute; retain research note |
| WeChatTweak/exporter-style macOS route | High | Very high | High | Requires invasive client modification without explicit approval | Uninstall tweak if installed, restore original client state |
| Official/user-visible backup or migration | Low-medium | Low | High for WDA import | Backup cannot be opened or converted to message-level records | Stop; no data imported |
| Fully self-developed raw adapter | Very high | Very high | Very high | Requires protected-store bypass, key extraction, or reverse engineering without explicit approval | Do not start implementation |

## Non-Negotiable Controls

- No tool execution in Sprint 2G.
- No raw data upload.
- No broad export until a minimal trial proves local output shape.
- No RAG/Web/Matrix work before a valid `messages.jsonl` exists.
- Raw Gate stays `Conditional Investigation`.

