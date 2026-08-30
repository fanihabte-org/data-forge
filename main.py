from pathlib import Path
from src.data_forge.builder.builder import Builder

root_path = Path(__file__).resolve().parent
config_path = root_path / "src/resources/pipeline_config"

if __name__ == "__main__":
    builder = Builder(config_folder_path=config_path)
    context = builder.context()
    erp_dbs_init = {"source_db_name": "erp", "source_name": "erp", "target_dw_name": "erae"}
    ops_dbs_init = {"source_db_name": "ops", "source_name": "ops", "target_dw_name": "erae"}

    builder.planner(**ops_dbs_init).build_plan()


