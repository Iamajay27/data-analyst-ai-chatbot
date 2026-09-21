from __future__ import annotations
import pandas as pd

def deterministic_result_summary(result: pd.DataFrame) -> str:
    if result is None or result.empty:
        return "The query returned no rows."

    if result.shape == (1, 1):
        return f"Result: **{result.iloc[0, 0]}**"

    if len(result) == 1:
        pairs = [f"**{c}**: {result.iloc[0][c]}" for c in result.columns]
        return " | ".join(pairs)

    return f"The query returned **{len(result)} row(s)** and **{len(result.columns)} column(s)**."
