from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data_forge.context.context import Catalog
    from data_forge.db_engine.engine import DBEngine
    from data_forge.logging.watermark import Watermark


@dataclass
class SourceInterface(ABC):

    @abstractmethod
    def extract_after_watermark(self, run_datetime: datetime, watermark):
        pass

    @abstractmethod
    def bulk_export_all(self, run_datetime: datetime, table_name: str):
        pass

    @abstractmethod
    def bulk_export_after_watermark(self, run_datetime: datetime, watermark: Watermark):
        pass


@dataclass
class TargetInterface(SourceInterface):
    db_engine: DBEngine

    @abstractmethod
    def bulk_insert_csv(self, table_name: str, source: str, download_dir: Path, run_datetime: datetime, columns: list):
        pass

    @abstractmethod
    def insert_batches(self, batches: list[tuple], table_name: str, source: str, run_datetime: datetime, watermark: Watermark, columns: list):
        pass
