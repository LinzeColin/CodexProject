# KMFA v0.1.4 Stage 10 Review Risk Register

| Risk | Control | Status |
|---|---|---|
| D-grade reports are mistaken for formal management reports | release_state keeps formal report and business basis false | controlled |
| Historical upload evidence is treated as current gate | review finding F01 fixes current v1.4 upload boundary to deferred | controlled |
| Report export evidence leaks raw/private values | validator scans review evidence and requires public-safe aggregate-only evidence | controlled |
| Review drifts into S11 or GitHub upload | manifest and validator require s11_p1_performed=false and github_upload_performed=false | controlled |
