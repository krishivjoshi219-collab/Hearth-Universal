.PHONY: install test run verify clean backup docker-build deploy

install:
	pip install -e ".[dev,aws]"

test:
	pytest -v

run:
	python mcp-server/server.py

verify:
	pytest tests/test_mcp_http.py

clean:
	@if [ "$$HEARTH_ENV" = "production" ]; then echo "refusing to wipe state while HEARTH_ENV=production"; exit 1; fi
	rm -rf __pycache__ .pytest_cache *.egg-info build dist .coverage htmlcov
	rm -f state/proposals.json state/audit.jsonl state/heartbeat.json state/brain_config.json
	find state -name "memory.corrupt.*.db" -delete 2>/dev/null; true

backup:
	@mkdir -p backups
	@ts=$$(date -u +%Y%m%dT%H%M%SZ); tar -czf backups/state-$$ts.tgz state/; echo "wrote backups/state-$$ts.tgz"

docker-build:
	docker build -f infra/Dockerfile -t hearth-universal:latest .

deploy:
	@echo "Set PUBLIC_BASE_URL=https://<your-host> then: docker run -e PUBLIC_BASE_URL -p 8787:8787 hearth-universal:latest"
