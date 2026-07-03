# Candidate Tool Matrix

Evidence is based on public documentation only. No candidate was executed.
macOS WeChat 4.1.11 support is unproven until a controlled trial verifies it.

| Route | Platform support | WeChat 4.1.11 support | Live WeChat | Admin/sudo | Key extraction | DB decryption | Output formats | Full/all contacts | Selected contacts | Incremental export | WDA_MetaData-only output | Old/new computer fit | Raw Import Pack potential | Decision |
|---|---|---:|---:|---:|---:|---:|---|---|---|---|---|---|---|---|
| `wechat-cli` / `wx-cli` style local CLI exporter | macOS-focused candidates exist | Not verified; related macOS exporters claim WeChat 4.x support | Likely yes for key discovery | Likely yes | Likely yes | Yes in documented implementations | JSON, CSV, text-like exports depending on tool | Likely if contacts command is supported; must verify | Likely if conversation/contact filters exist; must verify | Unknown; must test | Likely yes if CLI output path is configurable | Old computer for acquisition; new computer validates output | High after adapter conversion | Recommended controlled trial route |
| `wechat-local-mcp` style exporter | macOS local-first, agent-facing | Not verified | Yes in documented security model | Yes or Keychain-mediated sudo | Yes through companion key tool | Yes | API/structured local outputs, cache snapshots | Possible; must verify endpoint coverage | Possible; must verify query/filter support | Unknown | Must be forced to WDA path and local cache policy | Old computer for acquisition; new computer for validation | High, but with higher integration risk | Backup to CLI route |
| PyWxDump-style exporter | Mainly Windows-tested | Weak for macOS; PyPI says tested only under Windows | Depends on route | Often yes | Often yes | Yes | Commonly JSON/CSV/HTML-like in ecosystem | Possible on supported platforms; macOS unproven | Possible on supported platforms; macOS unproven | Unknown | Unknown | Poor fit for old macOS first trial | Medium if port works | Not recommended first |
| chatlog/EchoTrace-style exporter | Local desktop/export ecosystem | Unknown; EchoTrace is stopped-maintenance | Likely yes | Unknown/likely | Likely yes | Yes | HTML/report/export formats | Possible but not proven | Possible but not proven | Unknown | Unknown | Old computer only if compatible | Medium | Research backup only |
| WeChatTweak/exporter-style macOS route | macOS-specific | Unknown for current WeChat 4.1.11 | Yes | Yes for install | Avoids or hides key path through injected API, but still invasive | Uses modified client route | JSON per chat in documented exporter | Unclear | Selected chat route appears possible | Unknown | Output folder can likely be controlled | Old computer only | Medium to high after adapter | High-risk backup |
| Official/user-visible backup or migration | Official/user-visible | Supported by WeChat ecosystem, but not readable on computer | Usually live app/device | No special DB access | No | No | Backup files, not open readable message exports | Not sufficient | Not sufficient | No | N/A | Can assist transfer, not WDA import | Low without readable export | Not sufficient alone |
| Fully self-developed raw adapter | Custom | Unknown and version-fragile | Likely yes or copied DB/key sources | Likely yes | Yes | Yes | WDA-native possible | Possible | Possible | Possible | Yes | Old computer acquisition, new computer compute | High if built | Reject unless explicitly authorized later |

## Candidate Recommendation

Use a local CLI exporter route for the first controlled trial because it has the
best chance to produce deterministic files that can be converted into the WDA
Raw Import Pack, while avoiding the extra server surface of an MCP wrapper and
the invasive runtime modification surface of WeChatTweak-style routes.
