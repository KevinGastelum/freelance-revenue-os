default:
    just --list

# Sync virtual environment dependencies using uv
install:
    uv sync

# Run the freelance-os CLI tool
run:
    uv run freelance-os

# Run pytest unit tests
test:
    uv run pytest
