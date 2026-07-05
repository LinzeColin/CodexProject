# Risk Register

- risk: Draft evidence could be mistaken for active owner authorization.
  mitigation: Public Go/No-Go and validator require `draft_is_active_record=false`, `active_authorized_fill_record_created=false` and downstream gates blocked.
- risk: Downstream phases could be run before owner activation.
  mitigation: Next required input remains owner or authorized delegate activation of the draft fill record.
