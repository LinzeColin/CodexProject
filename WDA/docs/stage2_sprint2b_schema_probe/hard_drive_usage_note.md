# Sprint 2B-B Hard Drive Usage Note

Generated: 2026-07-03T08:15:45+10:00

Sprint 2B-B used only the local copied candidate bundle. Before the probe, the external hard drive and APFS export mount were absent from the system mount table and no external physical disk was enumerated by `diskutil list external physical`.

The schema probe did not access source APFS paths, the external drive, the abandoned ExFAT partial copy, or any WeChat source directory.

Sprint 2B-B can be repeated without the external hard drive as long as the local bundle remains available.
