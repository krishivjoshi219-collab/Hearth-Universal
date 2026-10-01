.PHONY: install test run verify clean

install:
	pip install -e ".[dev,aws]"

test:
	pytest -v

run:
	python mcp-server/server.py

verify:
	pytest tests/test_mcp_http.py

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info build dist
