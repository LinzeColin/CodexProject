# Source Evidence Audit

- Generated: 2026-06-13T06:50:52+08:00
- Audit run ID: source_evidence_20260613_065052_0800
- Status: pass
- Row count: 17
- Valid reference count: 17
- Invalid reference count: 0
- Local hashed file count: 3
- URL count: 14
- SQLite rows written: 17
- Status counts: {'valid_url': 14, 'hashed_local_file': 3}
- Area counts: {'fund_rules': 8, 'candidate_universe': 7, 'benchmark_history': 2}

## Scope

This audit records source references from production intake files or a selected intake pack. It hashes local evidence files and validates URL shape, but it does not fetch remote URLs or treat public aggregation as official evidence. When `--pack-dir` is used, relative local evidence paths resolve from that pack directory.

## Failed Or Weak References

- None

## Local Evidence Hashes

| Area | Row | File | SHA256 | Bytes | MTime |
|---|---|---|---|---|---|
| candidate_universe | 270042 | `data/moomoo/moomoo_collect_20260612T222828Z_deebca84/US_QQQ_K_DAY_2026-03-02_2026-06-12.csv` | `53e70ec22bf7eb876ad6d4570139b5113def207e1e3c4942b8a8fd217c30d6f0` | 10640 | 2026-06-13T06:28:56+08:00 |
| candidate_universe | 018043 | `data/moomoo/moomoo_collect_20260612T222828Z_deebca84/US_QQQ_K_DAY_2026-03-02_2026-06-12.csv` | `53e70ec22bf7eb876ad6d4570139b5113def207e1e3c4942b8a8fd217c30d6f0` | 10640 | 2026-06-13T06:28:56+08:00 |
| candidate_universe | 013171 | `data/moomoo/moomoo_collect_20260612T222828Z_deebca84/HK_03033_K_DAY_2026-03-02_2026-06-12.csv` | `8c5214b65f4ae8a94efb4254f4326fda37548591333d12515d1f3bddddf3b758` | 10275 | 2026-06-13T06:28:57+08:00 |
