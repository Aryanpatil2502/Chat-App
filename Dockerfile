FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim

WORKDIR /app

COPY . /app

RUN uv sync

EXPOSE 5000

CMD ["uv", "run", "app.py"]