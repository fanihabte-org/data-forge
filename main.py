from pathlib import Path
from src.data_forge.builder.builder import Builder

root_path = Path(__file__).resolve().parent
config_path = root_path / "src/resources/pipeline_config"

if __name__ == "__main__":
    builder = Builder(config_folder_path=config_path)
    context = builder.context()
    pipeline = builder.pipeline()

    pipeline.analyze(source_db=pipeline.ops)
    pipeline.explain_plan(source_db=pipeline.ops)