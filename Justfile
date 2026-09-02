export PATH := join(justfile_directory(), ".venv", "bin") + ":" + env_var('PATH')
export PYTHONPATH := join(justfile_directory(), "src")

ci_compose := "docker compose --env-file .env.ci -f docker-compose.yml -f docker-compose.ci.yml up"
dev_compose := "docker compose up"

# Main run recipe
run *args:
    python3 main.py {{ args }}

# Dedicated pipeline recipe (if you prefer calling `just pipeline`)
pipeline:
    python3 main.py

ci:
    {{ ci_compose }}

dev:
    {{ dev_compose }}