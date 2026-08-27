from dataclasses import dataclass
from psycopg.rows import class_row
from data_forge.pipeline.validator_query_builder import table_information_query, table_columns_query
from data_forge.db_engine.engine import DBEngine
from data_forge.db_services.source import SourceDB
from data_forge.db_services.target import TargetDW
from data_forge.sales_force.sales_force import SalesForce
from data_forge.context.context import Column


@dataclass
class TableInfo:
    schema_name: str
    table_name: str
    estimated_rows: int


@dataclass
class Validator:
    source_db: SourceDB
    target_dw: TargetDW
    salesforce: SalesForce

    def run_checks(self) -> dict:
        return {
            "tables_in_source_checks": self.check_tables_exist(self.source_db.db_engine),
            "tables_in_target_checks": self.check_tables_exist(self.target_dw.db_engine),
            "table_columns_checks_vs_source": self.check_table_columns(self.source_db.db_engine),
            "table_columns_checks_vs_target": self.check_table_columns(self.target_dw.db_engine),
        }

    def fetch_tables_info(self, db_engine: DBEngine) -> list[TableInfo]:
        schema = self.source_db.catalog.source_name
        with db_engine.build_connection() as conn:
            with conn.cursor(row_factory=class_row(TableInfo)) as cur:
                return cur.execute(table_information_query(schema=schema)).fetchall()

    def check_tables_exist(self, db_engine: DBEngine) -> dict:
        current_tables = self.fetch_tables_info(db_engine)
        db_table_names = {table.table_name for table in current_tables}
        needed_tables = set(self.source_db.catalog.tables.keys())

        missing_tables = list(needed_tables - db_table_names)

        if missing_tables:
            print(f"DataBase: {db_engine.dbname} | Missing: {missing_tables}")

        return {
            "all_tables_exist": not missing_tables,
            "missing_tables": missing_tables
        }

    def check_table_columns(self, db_engine: DBEngine) -> dict:
        response = {}
        schema = self.source_db.catalog.source_name

        # Open one connection for all tables to keep it fast
        with db_engine.build_connection() as conn:
            with conn.cursor(row_factory=class_row(Column)) as cur:
                for table_name, table_obj in self.source_db.catalog.tables.items():

                    query = table_columns_query(schema=schema, table=table_name)
                    db_columns = cur.execute(query).fetchall()

                    needed_columns = table_obj.columns
                    missing_columns = list(set(needed_columns) - set(db_columns))

                    if missing_columns:
                        print(f"Table: {table_name} | Missing: {missing_columns}")

                    response[table_name] = {
                        "all_columns_exists": not missing_columns,
                        "errored_columns": missing_columns
                    }
        return response
