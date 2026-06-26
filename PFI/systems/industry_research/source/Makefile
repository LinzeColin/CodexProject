DATE ?= 2026-06-06
PYTHON ?= python3
CODEX_PYTHON ?= python3
SYSTEM_SITE_PACKAGES ?=

.PHONY: doctor setup audit-stack evidence-decision test test-monitoring py-compile clean-cache

doctor:
	PYTHONPATH=. $(PYTHON) doctor.py --date $(DATE) --write-report --json

setup:
	./setup.sh $(DATE)

audit-stack:
	PYTHONPATH=. $(PYTHON) -m src.cli data-trust-audit --date $(DATE)
	PYTHONPATH=. $(PYTHON) -m src.cli reconciliation-audit --date $(DATE)
	PYTHONPATH=. $(PYTHON) -m src.cli manual-review-audit --date $(DATE)
	PYTHONPATH=. $(PYTHON) -m src.cli entity-registry-audit --date $(DATE)
	PYTHONPATH=. $(PYTHON) -m src.cli evidence-decision-audit --date $(DATE)
	PYTHONPATH=. $(PYTHON) -m src.cli report-layer-audit --date $(DATE)
	PYTHONPATH=. $(PYTHON) doctor.py --date $(DATE) --write-report

evidence-decision:
	PYTHONPATH=. $(PYTHON) -m src.cli evidence-decision-audit --date $(DATE)

test:
	$(CODEX_PYTHON) -c 'import sys; sys.path.insert(0, "."); sys.path.append("$(SYSTEM_SITE_PACKAGES)"); import pytest; raise SystemExit(pytest.main(["tests", "-q", "-p", "no:cacheprovider"]))'

test-monitoring:
	$(CODEX_PYTHON) -c 'import sys; sys.path.insert(0, "."); sys.path.append("$(SYSTEM_SITE_PACKAGES)"); import pytest; raise SystemExit(pytest.main(["tests/test_data_trust.py", "tests/test_reconciliation.py", "tests/test_manual_review.py", "tests/test_entity_registry.py", "tests/test_evidence_decision.py", "tests/test_report_layer.py", "tests/test_workflow_layer.py", "-q", "-p", "no:cacheprovider"]))'

py-compile:
	$(PYTHON) -m py_compile doctor.py src/cli.py src/monitoring/data_trust.py src/monitoring/reconciliation.py src/monitoring/manual_review.py src/monitoring/entity_registry.py src/monitoring/evidence_decision.py src/monitoring/report_layer.py

clean-cache:
	find . -type d \( -name __pycache__ -o -name .pytest_cache \) -prune -exec rm -rf {} +
