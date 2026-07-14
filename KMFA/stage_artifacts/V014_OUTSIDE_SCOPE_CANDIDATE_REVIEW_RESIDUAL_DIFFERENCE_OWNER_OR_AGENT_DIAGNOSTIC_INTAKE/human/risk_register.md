# Risk Register

- Risk: Treating an empty diagnostic-intake template as owner confirmation would overstate evidence.
- Control: validator requires pending_diagnostic_response_count=72, valid_diagnostic_response_count=0, actionable_resolution_count=0 and all downstream gates closed.
