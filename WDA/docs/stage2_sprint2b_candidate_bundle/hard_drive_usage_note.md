# Hard Drive Usage Note

Generated: 2026-07-03T08:13:49+10:00

Sprint 2B-A used the external hard drive only to access the authoritative APFS sparseimage and create the local APFS-derived bundle. During the initial copy pass in this run, the APFS export was confirmed mounted read-only at `WDA_WECHAT_APFS`; no source write was attempted.

After the initial copy pass, validation found key-value store files that were too broad for the approved Sprint 2B-A scope. The external drive had already been unmounted and ejected, and macOS no longer enumerated it for command-line remount. The corrected bundle was therefore produced by pruning the existing local APFS-derived staging copy and rebuilding the manifest/checksums with stricter deny rules. No ExFAT partial copy and no WeChat source directory was used.

Current required handoff state for Sprint 2B-B:
- APFS source is not required.
- External hard drive is not required.
- Sprint 2B-B must use only the local bundle at `/Users/linzezhang/Downloads/WDA_MetaData/raw_ferry/sprint2b_candidate_db_bundle_20260703`.
- Raw Gate remains Conditional Investigation.
