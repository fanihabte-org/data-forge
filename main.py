from pathlib import Path
from src.data_forge.builder.builder import Builder

root_path = Path(__file__).resolve().parent
config_path = root_path / "src/resources/manifest.json"

if __name__ == "__main__":
    builder = Builder(config_path=config_path)

    context = builder.context()
    export_path = Path(context.export_path)

    pipeline = builder.pipeline()
    pipeline.run_daily_pipeline()
