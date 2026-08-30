from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from datetime import datetime

from typing import TYPE_CHECKING

from data_forge.context.models import Table, PipelineConfig

if TYPE_CHECKING:
    from data_forge.db_engine.engine import DBEngine
    from data_forge.logging.watermark import Watermark


@dataclass
class SourceInterface(ABC):

    @abstractmethod
    def extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    @abstractmethod
    def bulk_extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    @abstractmethod
    def bulk_extract_to_csv_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass


@dataclass
class TargetInterface(SourceInterface):
    db_engine: DBEngine

    @abstractmethod
    def bulk_insert_csv(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    @abstractmethod
    def bulk_insert_from_csv(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    @abstractmethod
    def bulk_insert_batches(self, sql_query: bytes, batches: list[tuple]):
        pass

    @abstractmethod
    def insert_batches(self,
                       batches: list[tuple],
                       insert_into_query: bytes,
                       table: Table,
                       watermark: Watermark,
                       run_datetime: datetime):
        pass
