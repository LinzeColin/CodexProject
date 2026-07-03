# Old-Computer Export Runner Spec

The old computer should run the pinned `wechat-cli` / `wxkey` route because the
live-read path has already produced bounded message-level exports.

The full runner must:

- export all conversations without manual per-contact selection
- write only under WDA_MetaData
- use chunking, checkpointing, resume, checksums, and failure logs
- exclude key material, configs, DB files, raw logs, tool_work, and
  sensitive_local_state from transfer
- keep include_media_paths=false until media readiness is separately approved

This sprint does not execute the exporter.
