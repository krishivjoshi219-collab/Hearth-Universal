FROM python:3.12-slim-bookworm

# Security: Create unprivileged system user
RUN groupadd -g 1000 hearth && useradd -u 1000 -g hearth -m -s /bin/bash hearth

WORKDIR /app

# Install dependencies first for efficient layer caching
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[aws]"

# Copy application source code
COPY src ./src
COPY mcp-server ./mcp-server
COPY web ./web
COPY skill ./skill
COPY config.example.yaml ./

# Configure persistent state storage and non-root permissions
ENV PORT=8787 \
    HEARTH_STATE_DIR=/data/state \
    PYTHONUNBUFFERED=1

RUN mkdir -p /data/state && chown -R hearth:hearth /app /data
VOLUME ["/data"]

USER hearth
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",\"8787\")}/health')"

CMD ["python", "mcp-server/server.py"]

