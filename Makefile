# Makefile for CineFluent API development

.PHONY: help install install-dev test test-cov run run-dev format lint clean deploy

# Default target
help:
	@echo "CineFluent API Development Commands"
	@echo "=================================="
	@echo "install     - Install production dependencies"
	@echo "install-dev - Install development dependencies"
	@echo "test        - Run tests"
	@echo "test-cov    - Run tests with coverage"
	@echo "run         - Run the API server"
	@echo "run-dev     - Run the API server in development mode"
	@echo "format      - Format code with black"
	@echo "lint        - Lint code with flake8"
	@echo "clean       - Clean cache and temp files"
	@echo "deploy      - Deploy to Railway"

# Installation
install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install black flake8 isort

# Testing
test:
	pytest tests/ -v

test-cov:
	pytest tests/ -v --cov=. --cov-report=html --cov-report=term

# Running
run:
	python main.py

run-dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Code quality
format:
	black .
	isort .

lint:
	flake8 . --exclude=venv,__pycache__,.git
	
# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

# Railway deployment
deploy:
	railway up

# Database operations
db-schema:
	@echo "Run this in Supabase SQL Editor:"
	@echo "database/complete_schema.sql"

# Development setup
setup-dev: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make run-dev' to start the development server"

# Production setup
setup-prod: install
	@echo "Production environment setup complete!"
	@echo "Run 'make run' to start the server"
