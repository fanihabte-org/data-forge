export PATH := join(justfile_directory(), ".venv", "bin") + ":" + env_var('PATH')
export PYTHONPATH := join(justfile_directory(), "src")

run:
    python3 main.py

ci:
    docker compose --env-file .env.ci -f docker-compose.ci.yml up

pipeline:
    docker compose run --rm data-forge