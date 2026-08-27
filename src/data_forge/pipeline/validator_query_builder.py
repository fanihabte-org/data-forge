from psycopg.sql import SQL, Literal


def table_information_query(schema: str):
    return SQL(
        "select "
        "schemaname as schema_name "
        ", relname as table_name "
        ", n_live_tup as estimated_rows "
        "from pg_stat_user_tables "
        "where schemaname = {} "
        "order by n_live_tup desc;"
    ).format(
        Literal(schema)
    ).as_bytes()


def table_columns_query(schema: str, table: str):
    return SQL(
        "SELECT "
        "column_name as name "
        ", UPPER( "
        "CASE "
        "WHEN LOWER(data_type) IN ('character varying', 'varchar') "
        "THEN 'VARCHAR(' || character_maximum_length || ')' "
        "WHEN LOWER(data_type) IN ('character', 'char', 'bpchar') "
        "THEN 'CHAR(' || character_maximum_length || ')' "
        "WHEN numeric_precision IS NOT NULL AND numeric_scale IS NOT NULL AND LOWER(data_type) IN ('numeric', 'decimal') "
        "THEN 'NUMERIC(' || numeric_precision || ',' || numeric_scale || ')' "
        "WHEN LOWER(data_type) LIKE 'timestamp%' THEN 'TIMESTAMP' "
        "WHEN LOWER(data_type) IN ('integer', 'int', 'int4') THEN 'INTEGER' "
        "WHEN LOWER(data_type) IN ('bigint', 'int8') THEN 'BIGINT' "
        "ELSE data_type "
        "END "
        ") AS type "
        ", LOWER(is_nullable) AS nullability "
        "FROM information_schema.columns "
        "WHERE table_schema = {} AND table_name = {} "
        "ORDER BY ordinal_position;"
    ).format(
        Literal(schema),
        Literal(table)
    ).as_bytes()
