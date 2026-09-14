NAME := git-manager
DIR  ?= .

.PHONY: help sync run lint fmt test cov build install uninstall upgrade clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*##' '{printf "  %-10s %s\n", $$1, $$2}'

sync: ## Create .venv and install dependencies from uv.lock
	uv sync

run: ## Run the TUI (DIR=<path> to scan another folder)
	uv run $(NAME) $(DIR)

lint: ## Check lint rules and formatting, changing nothing
	uv run ruff check .
	uv run ruff format --check .

fmt: ## Apply lint fixes and format the code
	uv run ruff check --fix .
	uv run ruff format .

test: ## Run the test suite with coverage
	uv run pytest

cov: ## Write an HTML coverage report to htmlcov/
	uv run pytest --cov-report=html

build: ## Build a standalone binary into dist/
	uv run pyinstaller --onefile --name $(NAME) --collect-all textual \
		--paths src src/git_manager/__main__.py

install: ## Install `git-manager` on your PATH
	uv tool install --force .

uninstall: ## Remove `git-manager` from your PATH
	uv tool uninstall git-manager

upgrade: ## Upgrade locked dependencies to their latest allowed versions
	uv lock --upgrade

clean: ## Remove build artifacts
	rm -rf build dist *.spec htmlcov .coverage .pytest_cache \
		src/git_manager/__pycache__ tests/__pycache__
