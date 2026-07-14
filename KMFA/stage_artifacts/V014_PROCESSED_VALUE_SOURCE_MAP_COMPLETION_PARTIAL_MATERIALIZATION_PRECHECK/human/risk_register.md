# Risk Register

- Risk: treating old private value-source fingerprints as matching the current partial application.
  Mitigation: the precheck requires target-slot intersection before replay readiness can become true.
- Risk: leaking private fingerprints publicly.
  Mitigation: public artifacts contain only aggregate counts; fingerprints stay in ignored runtime.
