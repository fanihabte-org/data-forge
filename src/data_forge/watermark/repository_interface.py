from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from psycopg import Connection

from data_forge.context.models import Table
from data_forge.watermark.models import Watermark

@dataclass
class WatermarkRepositoryInterface(ABC):

    @abstractmethod
    def fetch_by_table(self, conn: Connection, table: Table) -> Watermark | None:
        pass

    @abstractmethod
    def fetch_all(self, conn: Connection) -> dict[str, Watermark]:
        pass

    @abstractmethod
    def set_default(self, conn: Connection, table: Table, schema_name: str) -> Watermark:
        pass

    @abstractmethod
    def sync(self, conn: Connection, table: Table, schema_name: str) -> Watermark:
        pass

    @abstractmethod
    def upsert(self, watermark: Watermark, conn: Connection, new_highest_wm: datetime | str) -> Watermark:
        pass