from contextlib import contextmanager
from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Generator

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.validator.models import TableDetail
from data_forge.watermark.models import Watermark


@dataclass
class SourceInterface(ABC):

    @contextmanager
    def transaction(self):
        pass

    @abstractmethod
    def extract_after_watermark(self, conn: Connection, table: Table, watermark: Watermark):
        pass

    @abstractmethod
    def bulk_extract_after_watermark(self, conn: Connection, table: Table, watermark: Watermark):
        pass

    @abstractmethod
    def bulk_extract_to_csv_after_watermark(self, conn: Connection, table: Table, watermark: Watermark):
        pass

    @abstractmethod
    def fetch_table_detail(self, conn: Connection, table: Table) -> TableDetail:
        pass

    @abstractmethod
    def analyze_table(self, conn: Connection, table: Table, watermark: Watermark):
        pass
