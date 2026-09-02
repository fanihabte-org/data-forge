FROM python:3.12
LABEL authors="fanielhabte"

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /data-forge

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/data-forge/src"

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen

COPY . .

ENTRYPOINT ["python3", "main.py"]