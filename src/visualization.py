from __future__ import annotations
import pandas as pd
import plotly.express as px

def auto_chart(df: pd.DataFrame, question: str = ""):
    if df is None or df.empty or len(df.columns) < 2:
        return None

    cols = list(df.columns)
    num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    non_num = [c for c in cols if c not in num_cols]

    if len(df) > 50:
        return None

    # Time-like first column + numeric -> line
    first = cols[0]
    if num_cols and (
        pd.api.types.is_datetime64_any_dtype(df[first])
        or any(t in str(first).lower() for t in ("date", "month", "year", "time"))
    ):
        y = num_cols[0]
        return px.line(df, x=first, y=y, markers=True, title=f"{y} by {first}")

    # Category + number -> bar
    if non_num and num_cols:
        x, y = non_num[0], num_cols[0]
        if df[x].nunique(dropna=True) <= 30:
            return px.bar(df, x=x, y=y, title=f"{y} by {x}")

    # Two numeric columns -> scatter
    if len(num_cols) >= 2:
        return px.scatter(df, x=num_cols[0], y=num_cols[1],
                          title=f"{num_cols[1]} vs {num_cols[0]}")

    return None
