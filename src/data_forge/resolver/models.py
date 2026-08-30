from abc import ABC
from enum import Enum

from pydantic import BaseModel

from data_forge.context.models import Table
from data_forge.validator.models import WatermarkValidationResult, TableValidationResult


class ResolutionType(Enum):
    WATERMARK_SYNC = 1
    TABLE_CREATION = 2


class Resolution(BaseModel, ABC):
    table: Table
    resolution_type: ResolutionType


class WatermarkSyncResolution(Resolution):
    watermark_validation_result: WatermarkValidationResult


class TableCreationResolution(Resolution):
    table_validation: TableValidationResult
