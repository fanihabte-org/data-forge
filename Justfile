export PATH := join(justfile_directory(), ".venv", "bin") + ":" + env_var('PATH')
export PYTHONPATH := join(justfile_directory(), "src")

ci_compose := "docker compose --env-file .env.ci -f docker-compose.ci.yml"
prod_compose := "docker compose run --build --remove-orphans"

run:
    python3 main.py

ci-up:
    {{ ci_compose }} up -d

ci-test:
    {{ ci_compose }} run --build --remove-orphans --rm data-forge-ci uv run pytest

ci-down:
    {{ ci_compose }} down

pipeline-run:
    {{ prod_compose }} -T --rm data-forge

prod-test:
    {{ prod_compose }} data-forge uv run pytest

git-merge:
    git fetch origin main && git reset --hard origin/main

git-clean:
    git clean -fd

ci-run: ci-up ci-test ci-down

deploy: git-merge git-clean prod-test

