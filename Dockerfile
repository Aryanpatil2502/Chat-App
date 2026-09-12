FROM ghcr.io/astral-sh/uv:python3.14-trixie-slim



WORKDIR /app

COPY . /app

RUN uv venv
RUN uv sync

EXPOSE 80
CMD [".venv/bin/python", "app.py"]