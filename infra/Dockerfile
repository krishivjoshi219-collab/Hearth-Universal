FROM python:3.12-slim-bookworm AS builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[aws]" --prefix /install

FROM python:3.12-slim-bookworm
# Security: unprivileged user + tini init for signal handling
RUN groupadd -g 1000 hearth && useradd -u 1000 -g hearth -m -s /bin/false hearth \
    && apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /install /usr/local
COPY --chown=hearth:hearth src ./src
COPY --chown=hearth:hearth mcp-server ./mcp-server
COPY --chown=hearth:hearth web2 ./web2
COPY --chown=hearth:hearth skill ./skill
COPY --chown=hearth:hearth config.example.yaml ./

ENV PORT=8787 \
    HEARTH_STATE_DIR=/data/state \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN mkdir -p /data/state && chown -R hearth:hearth /app /data
VOLUME ["/data"]

USER hearth
EXPOSE 8787

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\",\"8787\")}/health')"

ENTRYPOINT ["tini", "--"]
CMD ["python", "mcp-server/server.py"]
