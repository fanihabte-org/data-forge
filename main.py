from pathlib import Path
from src.data_forge.builder.builder import Builder

root_path = Path(__file__).resolve().parent
config_path = root_path / "src/resources/pipeline_config"

builder = Builder(config_folder_path=config_path)
context = builder.context()
erp_dbs_init = {"source_db_name": "erp", "source_name": "erp", "target_dw_name": "erae"}
ops_dbs_init = {"source_db_name": "ops", "source_name": "ops", "target_dw_name": "erae"}

for db_init in [erp_dbs_init, ops_dbs_init]:
    pipeline = builder.pipeline(**db_init)
    pipeline.run()
