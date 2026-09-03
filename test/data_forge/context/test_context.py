from pathlib import Path

from data_forge.builder.builder import Builder
from data_forge.context.context import Context
from data_forge.context.models import Catalog
from data_forge.db_engine.engine import DBEngine

config_path = Path(__file__).resolve().parent.parent.parent / "resources/pipeline_config_test"
builder = Builder(config_folder_path=config_path)
context = builder.context()

def test_context_object():
    assert isinstance(context, Context)

def test_get_catalog():
    assert isinstance(context.get_catalog(source="crm_test"), Catalog)
    assert context.get_catalog(source="crm_test").source_name == "crm_test"

def test_get_engine():
    assert isinstance(context.get_engine("erp"), DBEngine)

def test_get_salesforce_config():
    assert context.get_salesforce_config().client_id == "demo"

def test_get_pipeline_config():
    assert context.get_pipeline_config().watermark_table_name == "watermark_logs"
