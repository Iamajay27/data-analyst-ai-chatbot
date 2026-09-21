from __future__ import annotations
import pandas as pd

def clean_dataframe(df: pd.DataFrame):
    cleaned = df.copy(deep=True)
    actions = []

    # Clean column names.
    new_cols = []
    for col in cleaned.columns:
        c = str(col).strip()
        c = " ".join(c.split())
        new_cols.append(c)
    if list(cleaned.columns) != new_cols:
        cleaned.columns = new_cols
        actions.append("Trimmed and normalized column names.")

    # Trim strings.
    obj_cols = cleaned.select_dtypes(include=["object", "string"]).columns
    for col in obj_cols:
        before = cleaned[col].copy()
        cleaned[col] = cleaned[col].map(lambda x: x.strip() if isinstance(x, str) else x)
        if not before.equals(cleaned[col]):
            actions.append(f"Trimmed extra whitespace in '{col}'.")

    # Remove exact duplicates.
    dup_count = int(cleaned.duplicated().sum())
    if dup_count:
        cleaned = cleaned.drop_duplicates().reset_index(drop=True)
        actions.append(f"Removed {dup_count} duplicate row(s).")

    # Conservative date inference.
    for col in cleaned.select_dtypes(include=["object", "string"]).columns:
        name = str(col).lower()
        if any(token in name for token in ("date", "time", "day")):
            parsed = pd.to_datetime(cleaned[col], errors="coerce")
            non_null_original = cleaned[col].notna().sum()
            valid_ratio = (parsed.notna().sum() / non_null_original) if non_null_original else 0
            if valid_ratio >= 0.8:
                cleaned[col] = parsed
                actions.append(f"Converted '{col}' to datetime.")

    if not actions:
        actions.append("No automatic cleaning changes were required.")

    return cleaned, actions
