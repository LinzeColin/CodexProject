# KMFA v0.1.4 S17-P1 Access Security Risk Register

- risk: Permission evidence could be mistaken as live authorization enforcement.
  mitigation: Current output is a public-safe policy lock only; live connector and business execution stay blocked.
- risk: Notification audit policy could be mistaken as notification delivery.
  mitigation: S17-P1 records audit policy only; notification delivery is reserved for S17-P2 and remains blocked here.
