from dataclasses import dataclass
from abc import ABC, abstractmethod

from data_forge.context.models import Table
from data_forge.validator.models import TableDetail
from data_forge.watermark.models import Watermark


@dataclass
class SourceInterface(ABC):

    @abstractmethod
    def extract_after_watermark(self, table: Table, watermark: Watermark):
        pass

    @abstractmethod
    def bulk_extract_after_watermark(self, table: Table, watermark: Watermark):
        pass

    @abstractmethod
    def bulk_extract_to_csv_after_watermark(self, table: Table, watermark: Watermark):
        pass

    @abstractmethod
    def fetch_table_detail(self, table: Table) -> TableDetail:
        pass

    @abstractmethod
    def analyze_table(self, table: Table, watermark: Watermark):
        pass
