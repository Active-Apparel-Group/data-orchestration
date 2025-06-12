# Data Orchestration Makefile
.PHONY: help setup venv install install-dev test lint format clean up down logs

# Default target
help:
	@echo "Available targets:"
	@echo "  setup       - Full setup: create venv and install dependencies"
	@echo "  venv        - Create virtual environment"
	@echo "  install     - Install production dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  test        - Run tests"
	@echo "  lint        - Run linting"
	@echo "  format      - Format code with black"
	@echo "  clean       - Clean up temporary files"
	@echo "  up          - Start Kestra with docker-compose"
	@echo "  down        - Stop Kestra"
	@echo "  logs        - Show Kestra logs"

# Virtual environment setup
venv:
	python -m venv venv
	@echo "Virtual environment created. Activate with: venv\Scripts\activate"

# Install production dependencies
install: venv
	venv\Scripts\activate && pip install --upgrade pip
	venv\Scripts\activate && pip install -r requirements.txt

# Install development dependencies
install-dev: install
	venv\Scripts\activate && pip install pytest pytest-cov black flake8 mypy

# Full setup
setup: install-dev
	@echo "Setup complete! Activate the environment with: venv\Scripts\activate"

# Testing
test:
	venv\Scripts\activate && python -m pytest src/tests/ -v

validate:
	python validate_env.py

# Code quality
lint:
	venv\Scripts\activate && flake8 src/
	venv\Scripts\activate && mypy src/

format:
	venv\Scripts\activate && black src/

# Clean up
clean:
	if exist venv rmdir /s /q venv
	if exist __pycache__ rmdir /s /q __pycache__
	if exist .pytest_cache rmdir /s /q .pytest_cache
	if exist .mypy_cache rmdir /s /q .mypy_cache

# Docker operations
up:
	docker compose -f infra/docker-compose.kestra.yml up -d

down:
	docker compose -f infra/docker-compose.kestra.yml down

logs:
	docker compose -f infra/docker-compose.kestra.yml logs -f
