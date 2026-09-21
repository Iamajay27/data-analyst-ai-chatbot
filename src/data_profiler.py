from __future__ import annotations
import pandas as pd

def profile_dataframe(df: pd.DataFrame) -> dict:
    rows, cols = df.shape
    total_cells = rows * cols
    missing = int(df.isna().sum().sum())
    missing_pct = (missing / total_cells * 100) if total_cells else 0

    numeric = list(df.select_dtypes(include="number").columns)
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    categorical = [c for c in df.columns if c not in numeric and c not in date_cols]

    return {
        "rows": rows,
        "columns": cols,
        "missing_values": missing,
        "missing_pct": round(missing_pct, 2),
        "duplicates": int(df.duplicated().sum()),
        "numeric_columns": numeric,
        "categorical_columns": categorical,
        "date_columns": date_cols,
        "memory_mb": round(df.memory_usage(deep=True).sum() / 1024 / 1024, 2),
        "schema": pd.DataFrame({
            "column": [str(c) for c in df.columns],
            "dtype": [str(df[c].dtype) for c in df.columns],
            "missing": [int(df[c].isna().sum()) for c in df.columns],
            "unique": [int(df[c].nunique(dropna=True)) for c in df.columns],
        }),
    }
