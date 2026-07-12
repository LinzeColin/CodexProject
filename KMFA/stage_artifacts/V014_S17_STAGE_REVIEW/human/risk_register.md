# KMFA v0.1.4 Stage 17 Review Risk Register

- risk: Metadata-only notification evidence could be mistaken as real delivery.
  mitigation: Review locks real delivery, full email body, attachment and recipient plaintext counts at zero.
- risk: Operations SOP evidence could be mistaken as production restore or app reinstall.
  mitigation: Review locks production restore, external service, live connector and app reinstall counts at zero.
