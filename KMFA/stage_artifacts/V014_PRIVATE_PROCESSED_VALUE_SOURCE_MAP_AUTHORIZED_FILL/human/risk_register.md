# Risk Register

- R1: Partial source-map fill cannot prove processed business value consistency; mitigation is `NO_GO` until all slots are filled and replayed.
- R2: Private source-map files could disclose internal refs if committed; mitigation is ignored runtime and validator Git-boundary checks.
- R3: Staged source map could be mistaken for completed materialization; mitigation is explicit materialization=false gates.
