FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY src ./src
COPY mcp-server ./mcp-server
COPY web ./web
COPY skill ./skill
COPY config.example.yaml ./
ENV PORT=8000 HEARTH_STATE_DIR=/tmp/hearth-state
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request,os;print(urllib.request.urlopen(f\"http://localhost:{os.environ.get('PORT','8000')}/health\").read())"
CMD ["python", "mcp-server/server.py"]
