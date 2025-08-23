FROM ghcr.io/civicactions/pyction:latest

COPY pyproject.toml uv.lock ./

RUN uv venv .dockerenv
RUN uv sync --no-dev

WORKDIR /app

COPY . .

EXPOSE 5000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5000", "--reload"]
