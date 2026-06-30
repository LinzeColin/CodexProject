# Stage 4 Phase 4.3 Risk and Rollback

- Risk: Chrome headless evidence depends on local Chrome availability.
- Risk: current real data has no confirmed_zero production metric; this phase proves the gate and records real_confirmed_zero_metric_count=0.
- Rollback: revert the Phase 4.3 commit; no user financial data is modified.
- Stop condition: any blocked metric rendering `CNY 0.00`, missing screenshots, or zero display without source/as_of/record_count/formula evidence.
