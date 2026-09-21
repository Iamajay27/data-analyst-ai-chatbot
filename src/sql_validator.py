from __future__ import annotations
import re

FORBIDDEN = {
    "insert", "update", "delete", "drop", "alter", "truncate",
    "replace", "create", "attach", "detach", "pragma", "vacuum",
    "reindex", "grant", "revoke"
}

def validate_readonly_sql(sql: str) -> tuple[bool, str]:
    if not sql or not sql.strip():
        return False, "SQL query is empty."

    stripped = sql.strip().rstrip(";").strip()
    lowered = re.sub(r"\s+", " ", stripped.lower())

    # One statement only.
    if ";" in stripped:
        return False, "Only one SQL statement is allowed."

    # Permit SELECT or WITH...SELECT CTEs.
    if not (lowered.startswith("select ") or lowered.startswith("with ")):
        return False, "Only read-only SELECT queries are allowed."

    tokens = set(re.findall(r"\b[a-z_]+\b", lowered))
    bad = sorted(tokens.intersection(FORBIDDEN))
    if bad:
        return False, f"Blocked SQL keyword(s): {', '.join(bad)}"

    # Reduce abuse in demos.
    if "sqlite_master" in lowered:
        return False, "Access to SQLite metadata tables is blocked."

    return True, "OK"
