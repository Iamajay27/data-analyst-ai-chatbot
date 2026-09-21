from __future__ import annotations
import re
import sqlite3
from pathlib import Path
import pandas as pd

def safe_table_name(filename: str) -> str:
    stem = Path(filename).stem.lower()
    stem = re.sub(r"[^a-z0-9_]+", "_", stem).strip("_")
    if not stem:
        stem = "dataset"
    if stem[0].isdigit():
        stem = f"dataset_{stem}"
    return stem

def load_dataframe_to_sqlite(df: pd.DataFrame, db_path: str, table_name: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)

def get_schema(db_path: str, table_name: str) -> list[dict]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(f'PRAGMA table_info("{table_name}")')
        return [
            {"name": row[1], "type": row[2] or "TEXT"}
            for row in cur.fetchall()
        ]
