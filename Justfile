export PATH := join(justfile_directory(), ".venv", "bin") + ":" + env_var('PATH')
export PYTHONPATH := join(justfile_directory(), "src")

compose := "docker compose --env-file .env.ci -f docker-compose.ci.yml"

run:
    python3 main.py

ci-up:
    {{ compose }} up -d

ci-test:
    {{ compose }} run --build --remove-orphans --rm data-forge-ci uv run pytest

ci-down:
    {{ compose }} down

ci-run: ci-up ci-test ci-down

pipeline:
    docker compose run --build --remove-orphans -T --rm data-forge

deploy-test:
    docker compose run --build --remove-orphans data-forge uv run pytest