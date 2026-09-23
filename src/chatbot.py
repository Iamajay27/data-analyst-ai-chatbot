from __future__ import annotations

import pandas as pd

from .database import get_schema
from .llm_client import LLMUnavailable, explain_result, generate_sql
from .local_fallback import answer_local
from .query_executor import execute_query
from .sql_validator import validate_readonly_sql


def ask_data(question: str, db_path: str, table_name: str, sample_df: pd.DataFrame):
    """Answer with AI when available; automatically fall back to local Pandas.

    Local fallback is used for supported basic analytics when the API key is
    missing, exhausted, rate-limited, or otherwise unavailable.
    """
    try:
        schema = get_schema(db_path, table_name)
        sample = sample_df.head(5).to_csv(index=False)
        sql = generate_sql(question, table_name, schema, sample)

        ok, reason = validate_readonly_sql(sql)
        if not ok:
            raise ValueError(f"Generated SQL was rejected: {reason}")

        result = execute_query(db_path, sql)
        explanation = explain_result(question, sql, result.head(100).to_csv(index=False))
        return sql, result, explanation, "ai_sql"
    except Exception as ai_error:
        # Do not let API failures prevent basic analytics.
        try:
            answer, result, operation = answer_local(question, sample_df)
            fallback_note = (
                "\n\n> ℹ️ **Local fallback mode:** The AI API was unavailable, "
                "so this supported calculation was completed with Pandas locally."
            )
            return f"{answer}{fallback_note}", result, answer, operation
        except Exception:
            # Preserve the original AI error when the question is outside the
            # local fallback's supported operations.
            if isinstance(ai_error, LLMUnavailable):
                raise ai_error
            raise ai_error
