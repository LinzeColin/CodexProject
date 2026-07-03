# Current Status Summary

## Sprint 2H Validated Facts

- Selected route: `r266-tech/wechat-cli` / `wxkey` family.
- Repo pin: `5c76757e849da3f595a0ef7402d23fe15fd78322`.
- Release used: `wechat-cli v1.6.19`, `darwin-arm64`.
- Execution environment reported by Sprint 2H: old computer, macOS `26.5.1`,
  arm64, WeChat `4.1.11` build `269077`.
- `wxkey bootstrap` succeeded under the approved high-permission trial.
- Key config shape was reported as schema version `2`.
- Key coverage reached `25/26`.
- Image key was not captured.
- `wechat-cli status`, strict `wechat-cli status`, and post-bootstrap
  `wxkey doctor` hung with no usable JSON result.

## Current Decision State

- Sprint 2H did not produce `messages.jsonl`.
- Sprint 2H did not produce a minimal message-level sample.
- Raw Gate remains `Conditional Investigation`, not Go.
- RAG/Web/Matrix remain blocked.
- Sprint 2I does not need the external hard drive.

## Next Decision

Run one bounded old-computer remediation sprint only if explicitly approved.

