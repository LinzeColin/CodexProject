# KMFA v0.1.4 S17-P2 Notification Policy Risk Register

- risk: Reminder metadata could be mistaken for real message delivery.
  mitigation: Delivery mode is metadata outbox only; delivery count stays zero.
- risk: Reminder content could be mistaken for a formal report.
  mitigation: The phase logs only short public-safe reminders and blocks report body, attachments, and decision basis.
