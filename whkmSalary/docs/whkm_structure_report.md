# whkmSalary Structure Report

Task: S4PCT02  
Acceptance: ACC-S4PCT02  
Baseline: 9bfe50b2195e8cfc04eb493e028c0f72e1ae0a90

## Scope

S4PCT02 establishes a minimal `src` / `tests` / `config` / Chinese owner-entry structure for whkmSalary. It does not change salary formulas, province weights, Streamlit field defaults, Railway startup commands, or payroll readiness status.

## Active Structure

| Area | Path | Responsibility |
|---|---|---|
| Runtime code | `whkmSalary/src/whkm_salary/salary_logic.py` | Quarterly performance salary calculation implementation. |
| Runtime UI | `whkmSalary/src/whkm_salary/streamlit_app.py` | Streamlit form and display implementation. |
| Compatibility imports | `whkmSalary/salary_logic.py` | Preserves existing `from salary_logic import ...` callers and tests. |
| Compatibility startup | `whkmSalary/streamlit_app.py` | Preserves `Procfile` command and forwards to package UI. |
| Tests | `whkmSalary/tests/` | Boundary, weight, rounding, and structure compatibility coverage. |
| Structure config | `whkmSalary/config/structure_contract.yaml` | Records code/test/config/Chinese-entry ownership only. |
| Machine truth | `whkmSalary/docs/governance/` | Lean v2 source of facts, limitations, and evidence links. |
| Chinese owner entries | `whkmSalary/功能清单`, `whkmSalary/开发记录`, `whkmSalary/模型参数文件` | Human-readable current state, task, and model/parameter surfaces. |

## OLD_TO_NEW_MAP

| Old path | New path | Compatibility |
|---|---|---|
| `whkmSalary/salary_logic.py` | `whkmSalary/src/whkm_salary/salary_logic.py` | Root wrapper remains and re-exports the package module. |
| `whkmSalary/streamlit_app.py` | `whkmSalary/src/whkm_salary/streamlit_app.py` | Root wrapper remains and runs the package module. |

## Stop Conditions

| Stop condition | Result | Evidence |
|---|---:|---|
| whkmSalary large calculation rewrite for appearance | no | Only file location/import boundary changed; formula bodies stay in moved module. |
| Startup command changed without README sync | no | `Procfile` remains unchanged and README records the preserved command. |
| Business parameters moved into config without owner proof | no | `config/` records structure only; payroll parameters remain governed as before. |
| Tests bypass root compatibility imports | no | Existing tests still import `salary_logic`; added structure checks cover package paths. |

## Rollback

Rollback is a single git revert of the S4PCT02 commit. If manual recovery is needed, move `src/whkm_salary/salary_logic.py` back to `salary_logic.py`, move `src/whkm_salary/streamlit_app.py` back to `streamlit_app.py`, remove `src/whkm_salary/`, `config/structure_contract.yaml`, this report, and revert governance evidence links.
