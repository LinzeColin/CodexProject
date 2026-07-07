# Risk Register

- Risk: refreshed raw numeric evidence is mistaken for an authoritative source binding.
- Control: comparison retry remains false unless a deterministic processed/raw fingerprint pair exists.
- Risk: raw details leak into public artifacts.
- Control: raw index, raw file names, fields, values, context and fingerprints stay in ignored private runtime.
- Risk: raw data is modified during refresh.
- Control: the phase performs read/list/stat/parse/fingerprint only and checks root stat is unchanged.
