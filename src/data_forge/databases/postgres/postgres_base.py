from contextlib import contextmanager
from dataclasses import dataclass
from typing import Generator

from psycopg import Connection
from psycopg_pool import ConnectionPool

from data_forge.databases.engine import DBEngine

@dataclass
class PostgresDB:
    db_engine: DBEngine

    def __post_init__(self) -> None:
        self._pool = ConnectionPool(
            conninfo=self.db_engine.build_uri(),
            min_size=1,
            max_size=5,
            open=False
        )

    def transaction(self):
        with self._pool.connection() as conn:
            with conn.transaction():
                yield conn

    def open(self) -> None:
        self._pool.open()
        self._pool.wait(timeout=10)

    def close(self) -> None:
        self._pool.close()
