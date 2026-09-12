from dataclasses import dataclass
from psycopg import Connection, connect


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
        return f"user={self.user} password={self.password} host={self.host} port={self.port} dbname={self.dbname}"
