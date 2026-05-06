.DEFAULT_GOAL := help
SHELL         := /bin/bash
ROOT          := $(shell pwd)
VENV          := $(ROOT)/.venv
PYTHON        := $(VENV)/bin/python3
PIP           := $(VENV)/bin/pip

# ── Colour helpers ─────────────────────────────────────────────────────────
BOLD  := \033[1m
CYAN  := \033[0;36m
GREEN := \033[0;32m
RESET := \033[0m

.PHONY: help setup run run-voice run-video models update clean lint

## help       Show this help message
help:
	@echo ""
	@echo "$(BOLD)AI Studio$(RESET) — available commands"
	@echo ""
	@grep -E '^## ' Makefile | sed 's/## /  $(CYAN)make $(RESET)/'
	@echo ""

## setup      Install all dependencies (run once)
setup:
	@echo -e "$(CYAN)[make setup]$(RESET) Running full setup ..."
	@bash scripts/setup.sh

## run        Launch the full AI Studio (voice + video + audio)
run:
	@echo -e "$(CYAN)[make run]$(RESET) Starting AI Studio (full) ..."
	@bash scripts/start.sh studio

## run-voice  Launch Voice-Pro features only (faster startup)
run-voice:
	@echo -e "$(CYAN)[make run-voice]$(RESET) Starting Voice-Pro mode ..."
	@bash scripts/start.sh voice

## run-video  Launch video / audio generation only
run-video:
	@echo -e "$(CYAN)[make run-video]$(RESET) Starting Video Generation mode ..."
	@bash scripts/start.sh video

## models     Download optional AI models interactively
models:
	@bash scripts/download_models.sh

## update     Pull latest Voice Pro code and update deps
update:
	@echo -e "$(CYAN)[make update]$(RESET) Updating voice-pro submodule ..."
	git submodule update --remote --merge voice-pro
	@echo -e "$(CYAN)[make update]$(RESET) Upgrading Python packages ..."
	source $(VENV)/bin/activate && pip install --upgrade -r requirements.txt -q
	source $(VENV)/bin/activate && pip install --upgrade -r voice-pro/requirements-voice-gpu.txt \
	    --extra-index-url https://download.pytorch.org/whl/cu124 -q || \
	source $(VENV)/bin/activate && pip install --upgrade -r voice-pro/requirements-voice-cpu.txt -q
	@echo -e "$(GREEN)[make update]$(RESET) Done."

## clean      Remove generated outputs and temp files
clean:
	@echo "Cleaning outputs ..."
	rm -rf voice-pro/outputs voice-pro/workspace
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "Done."

## lint       Run basic code checks (flake8 + mypy on src/)
lint:
	@source $(VENV)/bin/activate && \
	    pip install flake8 mypy -q && \
	    flake8 src/ --max-line-length=100 --ignore=E501,W503 && \
	    echo "Lint OK"

# ── internal ───────────────────────────────────────────────────────────────
$(VENV)/bin/activate:
	python3 -m venv $(VENV)
