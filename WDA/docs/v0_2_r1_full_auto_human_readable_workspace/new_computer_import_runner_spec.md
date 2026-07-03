# New-Computer Import Runner Spec

The new computer is the WDA Control Plane. v0.2-R1 currently runs the local
report generator over the existing seed and analysis layer.

For full coverage, the next runner must perform:

1. transfer bundle checksum validation
2. forbidden-file exclusion validation
3. Raw Import Pack conversion
4. local Data Core import
5. deterministic analysis
6. Chinese report generation

All databases and full-sensitive outputs must stay under WDA_MetaData.
