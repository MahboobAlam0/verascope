.PHONY: setup test test-cov clean

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt
	cp -n .env.example .env || true
	@echo "Setup complete."
	@echo "Activate the environment with: source $(VENV)/bin/activate"
	@echo "Edit .env to add your LLM_PROVIDER and API key before running run_pipeline.py."

test:
	$(PYTHON) -m pytest tests/

test-cov:
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache $(VENV)
