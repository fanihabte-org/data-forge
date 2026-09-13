from contextlib import contextmanager
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Generator

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.validator.models import TableDetail
from data_forge.watermark.models import Watermark


@dataclass
class TargetInterface(ABC):

    @contextmanager
    def transaction(self):
        pass

    @abstractmethod
    def bulk_insert_from_csv(self, conn: Connection, table: Table):
        pass

    @abstractmethod
    def bulk_insert_batches(self, conn: Connection, table: Table, batches: list[bytes]):
        pass

    @abstractmethod
    def insert_batches(self, conn: Connection, table: Table, batches: list[tuple]):
        pass

    @abstractmethod
    def create_table(self, conn: Connection, table: Table):
        pass

    @abstractmethod
    def fetch_table_detail(self, table: Table) -> TableDetail:
        pass

    @abstractmethod
    def fetch_watermark(self, conn: Connection, table: Table) -> Watermark | None:
        pass

    @abstractmethod
    def fetch_watermarks(self, conn: Connection) -> dict[str, Watermark]:
        pass

    @abstractmethod
    def set_default_watermark(self, conn: Connection, table: Table) -> Watermark:
        pass

    @abstractmethod
    def sync_watermark(self, conn: Connection, table: Table) -> Watermark:
        pass
