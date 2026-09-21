from __future__ import annotations
import pandas as pd
from .database import get_schema
from .llm_client import generate_sql, explain_result
from .query_executor import execute_query
from .sql_validator import validate_readonly_sql

def ask_data(question: str, db_path: str, table_name: str, sample_df: pd.DataFrame):
    schema = get_schema(db_path, table_name)
    sample = sample_df.head(5).to_csv(index=False)
    sql = generate_sql(question, table_name, schema, sample)

    ok, reason = validate_readonly_sql(sql)
    if not ok:
        raise ValueError(f"Generated SQL was rejected: {reason}")

    result = execute_query(db_path, sql)
    explanation = explain_result(question, sql, result.head(100).to_csv(index=False))
    return sql, result, explanation
