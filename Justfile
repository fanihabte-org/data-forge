export PATH := join(justfile_directory(), ".venv", "bin") + ":" + env_var('PATH')
export PYTHONPATH := join(justfile_directory(), "src")

run:
    python3 main.py

ci-up:
    docker compose --env-file .env.ci -f docker-compose.ci.yml up -d

ci-test:
    docker compose --env-file .env.ci -f docker-compose.ci.yml run --rm data-forge-ci uv run pytest

ci-down:
    docker compose --env-file .env.ci -f docker-compose.ci.yml down

ci-run: ci-up ci-test ci-down

pipeline:
    docker compose run --rm data-forge