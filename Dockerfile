FROM python:3.12
LABEL authors="fanielhabte"

# Copy uv binaries
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy official pre-compiled just binary
COPY --from=ghcr.io/casey/just:latest /just /usr/local/bin/just

WORKDIR /data-forge

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/data-forge/src"

COPY pyproject.toml uv.lock* ./
RUN uv sync --locked

# Point PATH directly to the .venv created by uv
ENV PATH="/data-forge/.venv/bin:$PATH"

COPY . .

CMD ["just", "run"]