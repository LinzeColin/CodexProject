# Risk Register

- Risk: treating a blank response template as owner authorization.
  Mitigation: the template is explicitly non-active and the validator requires owner_group_decisions_supplied=false.
- Risk: leaking private row/group context publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; the response template and codebook remain private runtime only.
