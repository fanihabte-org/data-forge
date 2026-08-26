from pathlib import Path
from src.data_forge.builder.builder import Builder

root_path = Path(__file__).resolve().parent
config_path = root_path / "src/resources/pipeline_config"

# if table_name == "Account":
#
# elif table_name == "Opportunity":
#     download_dir = Path(
#         "/Users/fanielhabte/PycharmProjects/DataForgeProject/DataExtracts/2026/08/09/Opportunity/750ebc3b6c444515915")

if __name__ == "__main__":
    builder = Builder(config_folder_path=config_path)
    context = builder.context()
    pipeline = builder.pipeline()

    # pipeline.run_incremental_salesforce_pipeline()
    pipeline.run_incremental_daily_pipeline()