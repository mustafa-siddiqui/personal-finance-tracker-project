.PHONY: test test-verbose install clean

# Run all unit tests
test:
	pytest

# Run all unit tests with verbose output
test-verbose:
	pytest -v

# Install dependencies into the active virtual environment
install:
	pip install -r requirements.txt

# Remove caches and bytecode
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	rm -rf .pytest_cache
