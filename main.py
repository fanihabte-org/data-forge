# from pathlib import Path
# from src.data_forge.builder.builder import Builder
#
# root_path = Path(__file__).resolve().parent
# config_path = root_path / "src/resources/manifest.json"
# download_folder = Path("/Users/fanielhabte/PycharmProjects/DataForgeProject")
# # if table_name == "Account":
# #
# # elif table_name == "Opportunity":
# #     download_dir = Path(
# #         "/Users/fanielhabte/PycharmProjects/DataForgeProject/DataExtracts/2026/08/09/Opportunity/750ebc3b6c444515915")
#
# if __name__ == "__main__":
#     builder = Builder(config_path=config_path)
#
#     context = builder.context()
#     pipeline = builder.pipeline()
#     pipeline.run_incremental_salesforce_pipeline()
#     pipeline.run_incremental_daily_pipeline()

from pathlib import Path
from data_forge.context.context import Context


def main():
    config_folder = Path("/Users/fanielhabte/Projects/apps/data-forge/src/resources/pipeline_config")
    context = Context.load_context(folder_path=config_folder)


if __name__ == '__main__':
    main()
