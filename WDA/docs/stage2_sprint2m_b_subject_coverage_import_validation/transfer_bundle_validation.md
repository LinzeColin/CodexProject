# Transfer Bundle Validation

## Bundle

- Path checked: `/Users/linzezhang/Downloads/WDA_MetaData/stage2_inputs/sprint2m_a_subject_coverage_export/sprint2m_transfer_bundle.zip`
- Located inside the allowed input directory: yes
- Bundle SHA-256: `ba8ff637714711e444d6072f4e50a59452e1a286a51b7b49038cc11bfd285d0b`
- External bundle checksum status: `pass`
- Internal payload checksum status: `pass`
- Internal payload checksum files checked: `18`
- Internal missing checksum targets: `0`
- Internal checksum mismatches: `0`

## Safety Screen

| Check | Result |
|---|---|
| key material included | no |
| DB / SQLite files included | no |
| `sensitive_local_state/` included | no |
| logs included | no |
| `tool_work/` included | no |
| full export included | no |
| media paths requested or handled | no |
| external hard drive accessed | no |
| WeChat exporter tools run on new computer | no |

Notes: only the transfer bundle payload was validated. Adjacent old-computer
output checksum files were not treated as repo-safe payloads and were not copied
into Git.
