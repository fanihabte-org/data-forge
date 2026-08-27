from abc import ABC
from enum import Enum
from typing import Optional


class ExecutionCategory(Enum):
    EXPORT = 1
    IMPORT = 2
    CREATE_TABLE = 3


class ExecutionType(Enum):
    BULK = 1
    INCREMENTAL = 2


class Plan(ABC):
    category: str
    type: Optional[str] = None

    def execute(self):
        ...

    def report(self):
        ...

