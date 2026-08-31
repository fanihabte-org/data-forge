from __future__ import annotations

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Iterator

from psycopg import Connection

from data_forge.context.models import PipelineConfig

if TYPE_CHECKING:
    from data_forge.db_engine.engine import DBEngine


@dataclass
class SourceInterface(ABC):

    @abstractmethod
    def extract_after_watermark(self, sql_query: bytes, pipeline_config: PipelineConfig):
        pass

    @abstractmethod
    def bulk_extract_after_watermark(self, conn: Connection, sql_query: bytes, pipeline_config: PipelineConfig):
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
    def bulk_insert_batches(self, conn:Connection, sql_query: bytes, chunks: Iterator[bytes]):
        pass

    @abstractmethod
    def insert_batches(self, batches: list[tuple], sql_query: bytes):
        pass
