from abc import ABC
from enum import Enum

from pydantic import BaseModel
from typing import TYPE_CHECKING
from data_forge.context.models import Table
from data_forge.logging.watermark import Watermark

if TYPE_CHECKING:
    from data_forge.validator.models import TableValidationResult


class ResolutionType(Enum):
    WATERMARK_SYNC = 1
    TABLE_CREATION = 2


class Resolution(BaseModel, ABC):
    table: Table
    resolution_type: ResolutionType


class WatermarkSyncResolution(Resolution):
    synced_watermark: Watermark


class TableCreationResolution(Resolution):
    table_validation: "TableValidationResult"
