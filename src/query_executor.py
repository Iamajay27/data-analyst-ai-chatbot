from __future__ import annotations
import sqlite3
import pandas as pd
from .sql_validator import validate_readonly_sql

class QueryExecutionError(Exception):
    pass

def execute_query(db_path: str, sql: str, max_rows: int = 1000) -> pd.DataFrame:
    ok, reason = validate_readonly_sql(sql)
    if not ok:
        raise QueryExecutionError(reason)

    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA query_only = ON")
            df = pd.read_sql_query(sql, conn)
    except Exception as exc:
        raise QueryExecutionError(f"SQL execution failed: {exc}") from exc

    if len(df) > max_rows:
        return df.head(max_rows)
    return df
