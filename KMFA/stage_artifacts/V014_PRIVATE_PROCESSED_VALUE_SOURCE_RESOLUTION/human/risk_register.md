# Risk Register

- R1: Processed value source map is unavailable; mitigation is to keep NO_GO and capture the private map in a later phase.
- R2: Public artifacts could leak private value strings; mitigation is aggregate-only evidence and validator scans.
- R3: Source resolution could be confused with value comparison; mitigation is explicit comparison=false gates.
