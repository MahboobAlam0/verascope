.PHONY: setup test test-cov clean

VENV := .venv

# venv layout differs by platform (Scripts/ + .exe on Windows, bin/
# elsewhere), and so does the system interpreter name (python3 is a broken
# Windows Store alias stub on Windows, not a real interpreter) - detected
# via $(OS), which Windows sets and Git Bash/MSYS inherits.
ifeq ($(OS),Windows_NT)
	SYSTEM_PYTHON := python
	PYTHON := $(VENV)/Scripts/python.exe
	PIP := $(VENV)/Scripts/pip.exe
	ACTIVATE_HINT := $(VENV)/Scripts/activate
else
	SYSTEM_PYTHON := python3
	PYTHON := $(VENV)/bin/python
	PIP := $(VENV)/bin/pip
	ACTIVATE_HINT := $(VENV)/bin/activate
endif

setup:
	$(SYSTEM_PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip -q
	$(PIP) install -r requirements.txt
	cp -n .env.example .env || true
	@echo "Setup complete."
	@echo "Activate the environment with: source $(ACTIVATE_HINT)"
	@echo "Edit .env to add your LLM_PROVIDER and API key before running run_pipeline.py."

test:
	$(PYTHON) -m pytest tests/

test-cov:
	$(PYTHON) -m pytest tests/ --cov=src --cov-report=term-missing

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache $(VENV)
