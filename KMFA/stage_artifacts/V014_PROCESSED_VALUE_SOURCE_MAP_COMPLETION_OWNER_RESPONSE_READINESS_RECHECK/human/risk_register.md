# Risk Register

- Risk: proceeding without owner response would fabricate authorization.
  Mitigation: this gate keeps active authorization, source-map application and reconciliation closed.
- Risk: private response details leaking publicly.
  Mitigation: public artifacts contain only aggregate counts and gate flags; private item statuses stay ignored.
