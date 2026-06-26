PYTHON ?= python3
OUTPUT_DIR ?= outputs/finance_ledger_20220605_20260603
LEDGER_DB ?= data/finance_ledger/finance_ledger.sqlite
INPUT ?= data/finance_ledger/sources

.PHONY: doctor doctor-output test validate weekly finalize clean run-contract

doctor:
	$(PYTHON) scripts/doctor.py

doctor-output:
	$(PYTHON) scripts/doctor.py --require-output --write-audit $(OUTPUT_DIR)/audit/codex_workflow_doctor.json --write-report $(OUTPUT_DIR)/reports/codex_workflow_contract_report.pdf

test:
	PYTHONPATH=src $(PYTHON) -m pytest tests -q

validate:
	$(PYTHON) scripts/validate_outputs.py --output $(OUTPUT_DIR) --db $(LEDGER_DB) --require-ledger

weekly:
	$(PYTHON) scripts/weekly_update.py --input $(INPUT) --ledger-db $(LEDGER_DB) --output $(OUTPUT_DIR)

finalize:
	$(PYTHON) scripts/finalize_delivery.py --output-dir $(OUTPUT_DIR) --ledger-db $(LEDGER_DB) --ensure-server --json

clean:
	find src tests scripts -type d -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf .pytest_cache

run-contract:
	@sed -n '1,220p' docs/run_contract_template.md
