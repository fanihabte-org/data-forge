from typing import Optional
from pydantic import BaseModel

from data_forge.logging.watermark import Watermark


class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    estimated_rows: int


class ColumnValidation(BaseModel):
    all_exist: bool
    missing_columns: list


class WatermarkValidationResult(BaseModel):
    exist: bool
    watermark: Optional[Watermark]


class TableValidationResult(BaseModel):
    table_name: str
    exists: bool
    column_validation: ColumnValidation
