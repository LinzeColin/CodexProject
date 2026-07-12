# Risk Register

- risk: readiness may be mistaken for application.
  mitigation: source-map application flags remain false and Go/No-Go remains NO_GO.
- risk: private target/ref/fingerprint details may leak into public evidence.
  mitigation: public artifacts store aggregate counts only; validator scans forbidden public markers.
- risk: raw inbox may be accidentally touched.
  mitigation: phase reads only prior private runtime and public metadata; raw boundary flags remain false.
