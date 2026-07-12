# KMFA v0.1.4 S15-P3 Risk Register

| Risk | Control |
|---|---|
| Boundary contract is mistaken for live salary integration | API, connector, file export and live read flags remain false |
| Future read draft is mistaken for payroll approval | salary, bonus, payroll, final payment and payment execution gates remain false |
| Phase drifts into Stage 15 review or upload | Stage review and upload flags remain false |
| Raw/private material leaks into public evidence | Evidence stores public-safe refs, hashes, counts and status only |
