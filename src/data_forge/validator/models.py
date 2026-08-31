from typing import Optional
from pydantic import BaseModel

from data_forge.context.models import Table
from data_forge.logging.watermark import Watermark
from data_forge.resolver.models import ResolutionType


class TableInfo(BaseModel):
    schema_name: str
    table_name: str
    estimated_rows: int


class ColumnValidation(BaseModel):
    all_exist: bool
    missing_columns: list


class WatermarkValidationResult(BaseModel):
    exist: bool
    resolved: bool
    watermark: Optional[Watermark]


class WatermarkValidationResultResolved(WatermarkValidationResult):
    table: Table
    resolution_type: ResolutionType
    synced_watermark: Watermark


class TableValidationResult(BaseModel):
    table_name: str
    exists: bool
    column_validation: ColumnValidation


class ValidationResult(BaseModel):
    source: TableValidationResult
    target: TableValidationResult
    watermark: WatermarkValidationResult
