from typing import Optional
from pydantic import BaseModel

from data_forge.context.models import Table, Column
from data_forge.watermark.models import Watermark


class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    estimated_rows: int


class TableDetail(BaseModel):
    table: Table
    info: TableInfo
    columns: list[Column]


class ColumnValidation(BaseModel):
    all_exist: bool
    missing_columns: list


class WatermarkValidationResult(BaseModel):
    exist: bool
    resolved: bool
    watermark: Optional[Watermark]


class TableValidationResult(BaseModel):
    table_name: str
    exists: bool
    column_validation: ColumnValidation


class ValidationResult(BaseModel):
    source: TableValidationResult
    target: TableValidationResult
    watermark: WatermarkValidationResult
