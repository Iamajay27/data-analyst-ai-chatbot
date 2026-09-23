from __future__ import annotations

import re
from typing import Optional

import pandas as pd


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _find_column(question: str, columns) -> Optional[str]:
    q = _norm(question)
    cols = list(columns)
    # Exact/quoted column names first.
    for c in sorted(cols, key=lambda x: len(str(x)), reverse=True):
        cs = str(c).lower()
        if cs in q:
            return c
    # Common semantic aliases.
    aliases = {
        "sales": ["sales", "sale", "revenue", "amount", "price"],
        "profit": ["profit", "margin"],
        "quantity": ["quantity", "qty", "units"],
        "age": ["age"],
    }
    for canonical, words in aliases.items():
        if any(re.search(rf"\b{re.escape(w)}\b", q) for w in words):
            for c in cols:
                if canonical == str(c).lower() or any(w in str(c).lower() for w in words):
                    return c
    return None


def _find_group_column(question: str, columns, value_col: Optional[str]) -> Optional[str]:
    q = _norm(question)
    candidates = [c for c in columns if c != value_col]
    patterns = [
        r"\bby\s+([a-z0-9_ -]+?)(?:\?|\.|$)",
        r"\bper\s+([a-z0-9_ -]+?)(?:\?|\.|$)",
        r"\bfor each\s+([a-z0-9_ -]+?)(?:\?|\.|$)",
    ]
    for pat in patterns:
        m = re.search(pat, q)
        if m:
            phrase = m.group(1).strip()
            for c in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
                if str(c).lower() == phrase or str(c).lower() in phrase or phrase in str(c).lower():
                    return c
    # Natural questions: "which category/city/product ..."
    for c in sorted(candidates, key=lambda x: len(str(x)), reverse=True):
        cl = str(c).lower()
        if re.search(rf"\b(which|each|per)\s+{re.escape(cl)}\b", q):
            return c
    return None


def _find_filter(question: str, df: pd.DataFrame):
    q = _norm(question)
    for c in df.columns:
        cl = str(c).lower()
        # from Mumbai / in Mumbai / where city is Mumbai
        patterns = [rf"\bfrom\s+([^,.?]+)", rf"\bin\s+([^,.?]+)", rf"\b{re.escape(cl)}\s*(?:is|=|:)\s*['\"]?([^,'\"?.]+)"]
        for pat in patterns:
            m = re.search(pat, q)
            if m:
                raw = m.group(1).strip()
                # Avoid treating generic words as values.
                if raw and raw not in {"the", "data", "dataset", "this"}:
                    for val in df[c].dropna().astype(str).unique():
                        if str(val).lower() == raw.lower() or str(val).lower() in raw.lower() or raw.lower() in str(val).lower():
                            return c, val
    return None, None


def _fmt_num(x) -> str:
    if pd.isna(x):
        return "N/A"
    if isinstance(x, float) and x.is_integer():
        return f"{int(x):,}"
    return f"{x:,.2f}" if isinstance(x, (int, float)) else str(x)


def answer_local(question: str, df: pd.DataFrame):
    """Answer common analytical questions locally using Pandas.

    Returns (answer, result_df, operation) or raises ValueError when the
    question is outside the supported local patterns.
    """
    if df is None or df.empty:
        raise ValueError("The dataset is empty.")

    q = _norm(question)
    numeric_cols = list(df.select_dtypes(include="number").columns)
    if not numeric_cols:
        # Count can still work on categorical-only data.
        if "count" not in q and "how many" not in q:
            raise ValueError("No numeric column is available for this local calculation.")

    # Identify aggregation.
    if re.search(r"\b(average|avg|mean)\b", q):
        agg = "mean"
    elif re.search(r"\b(total|sum)\b", q):
        agg = "sum"
    elif re.search(r"\b(maximum|max|highest|largest)\b", q):
        agg = "max"
    elif re.search(r"\b(minimum|min|lowest|smallest)\b", q):
        agg = "min"
    elif re.search(r"\b(count|how many|number of)\b", q):
        agg = "count"
    else:
        raise ValueError("Local fallback supports average, sum, count, max, min, and group-by questions.")

    value_col = _find_column(q, df.columns)
    if value_col is None and numeric_cols:
        # For generic "total/average" choose the first numeric column.
        value_col = numeric_cols[0]

    group_col = _find_group_column(q, df.columns, value_col)
    filter_col, filter_value = _find_filter(q, df)
    work = df.copy()
    if filter_col is not None:
        work = work[work[filter_col].astype(str).str.lower() == str(filter_value).lower()]

    if agg == "count":
        if group_col:
            result = work.groupby(group_col, dropna=False).size().reset_index(name="count").sort_values("count", ascending=False)
            answer = f"Here is the count grouped by {group_col}."
            return answer, result.reset_index(drop=True), "local_pandas_groupby_count"
        result = pd.DataFrame({"count": [len(work)]})
        return f"The count is **{len(work):,}**.", result, "local_pandas_count"

    if value_col not in numeric_cols:
        raise ValueError(f"'{value_col}' is not numeric, so {agg} cannot be calculated locally.")

    if group_col:
        result = work.groupby(group_col, dropna=False)[value_col].agg(agg).reset_index(name=f"{agg}_{value_col}")
        result = result.sort_values(f"{agg}_{value_col}", ascending=agg in {"max", "sum", "mean"}).reset_index(drop=True)
        if agg == "max":
            # For "which ... highest" show the highest group first.
            result = result.sort_values(f"{agg}_{value_col}", ascending=False).reset_index(drop=True)
        if agg == "min":
            result = result.sort_values(f"{agg}_{value_col}", ascending=True).reset_index(drop=True)
        answer = f"Calculated **{agg} of {value_col} grouped by {group_col}** using local Pandas (no API call)."
        return answer, result, f"local_pandas_groupby_{agg}"

    value = getattr(work[value_col], agg)()
    result = pd.DataFrame({value_col: [value]})
    label = {"mean": "average", "sum": "total", "max": "maximum", "min": "minimum"}[agg]
    answer = f"The **{label} {value_col}** is **{_fmt_num(value)}**.\n\n*Calculated locally with Pandas — no OpenAI API call was required.*"
    return answer, result, f"local_pandas_{agg}"
