.PHONY: install test run verify clean docker-build deploy

install:
	pip install -e ".[dev,aws]"

test:
	pytest -v

run:
	python mcp-server/server.py

verify:
	pytest tests/test_mcp_http.py

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info build dist .coverage htmlcov
	rm -f state/proposals.json state/audit.jsonl state/heartbeat.json
	find state -name "memory.corrupt.*.db" -delete 2>/dev/null; true

docker-build:
	docker build -f infra/Dockerfile -t hearth-universal:latest .

deploy:
	@echo "Set PUBLIC_BASE_URL=https://<your-host> then: docker run -e PUBLIC_BASE_URL -p 8787:8787 hearth-universal:latest"
