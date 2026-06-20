# 商域图谱 / Enterprise Ecosystem Intelligence

Enterprise Ecosystem Intelligence is a research-oriented enterprise ecosystem
and supply-chain exploration project.

## Governance Entry

The canonical CodexProject governance baseline is maintained in
`docs/governance/`:

- `MODEL_SPEC.md` for model, assumption, formula, methodology, strategy, and validation narrative.
- `model_registry.yaml`, `formula_registry.yaml`, and `parameter_registry.csv` for machine-readable model facts.
- `DEVELOPMENT_LEDGER.md` and `development_events.jsonl` for iteration and event evidence.
- `DELIVERY_PLAN.md` and `delivery_tasks.yaml` for task and acceptance evidence.
- `VERSION_MATRIX.yaml` for product, model, parameter, data, schema, and governance version separation.
- `TRACEABILITY_MATRIX.csv` for requirement-to-evidence closure.

Legacy Task Pack files and `data/*.csv` catalogs remain available as evidence
and compatibility inputs. They are not independent editable governance sources.

## Version Boundary

- Product version: `0.1.0` (`VERSION`, `package.json`, `pyproject.toml`).
- Legacy Task Pack label: `v4.2.0` preserved in `docs/governance/VERSION_MATRIX.yaml`.
- Governance spec version: `1.0.0`.

## Validation

```bash
python scripts/validate_governance.py
python scripts/validate_model_config.py config/model_profiles/balanced-v2.json config/thresholds/default-v2.json
python ../scripts/validate_project_governance.py --project EEI
```

Prototype, fixture, production implementation, live data, and real calibration
claims remain separate. Scores support research ordering and explanation; they
are not investment or trading signals.
