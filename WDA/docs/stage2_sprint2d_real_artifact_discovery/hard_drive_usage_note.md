# Hard Drive Usage Note

Generated: 2026-07-03T09:34:23+10:00

Hard drive usage in Sprint 2D: required and used for APFS discovery if the source was available.

Observed mount state during discovery:

```text
/dev/disk4s1 on /Volumes/My Passport (exfat, local, nodev, nosuid, noowners, noatime, fskit)
/dev/disk6s1 on /Volumes/WDA_WECHAT_APFS (apfs, local, nodev, nosuid, read-only, journaled, noowners, nobrowse, mounted by linzezhang)
```

APFS raw source scanned: yes.

If APFS was scanned, it was mounted read-only at `/Volumes/WDA_WECHAT_APFS`; Sprint 2D used only path, size, mtime, extension, and path-derived signal metadata. No source writes were attempted.

The local metadata root was also scanned: `/Users/linzezhang/Downloads/WDA_MetaData`.

No raw private artifact was committed. No content snippets were written to reports.

Post-search state:
- APFS mount `/Volumes/WDA_WECHAT_APFS` was detached after discovery.
- External drive `/Volumes/My Passport` remained mounted as the host volume at final local cleanup time.
