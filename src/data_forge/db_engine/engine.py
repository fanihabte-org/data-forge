from dataclasses import dataclass
from psycopg import Connection, connect

from data_forge.context.context import Context


@dataclass
class DBEngine:
    host: str
    dbname: str
    password: str
    port: int
    user: str

    def build_connection(self) -> Connection:
        return connect(dbname=self.dbname, user=self.user, password=self.password, port=self.port, host=self.host)

    def build_uri(self) -> str:
        # database uri syntax
        # dialect://username:password@host:port/database
        return f"{self.user}:{self.password}@{self.host}:{self.port}/{self.dbname}"

    @classmethod
    def configure(cls, context: Context, db_name: str) -> "DBEngine":
        return cls(**context.databases[db_name])
