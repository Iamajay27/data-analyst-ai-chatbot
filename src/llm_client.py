from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

class LLMUnavailable(RuntimeError):
    pass

def _client():
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise LLMUnavailable(
            "No OPENAI_API_KEY found. Add it to .env to enable AI-generated SQL."
        )
    from openai import OpenAI
    return OpenAI(api_key=key)

def generate_sql(question: str, table_name: str, schema: list[dict], sample_rows: str = "") -> str:
    client = _client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    schema_text = "\n".join(f"- {x['name']}: {x['type']}" for x in schema)

    system = f"""You convert natural-language analytics questions into safe SQLite SELECT queries.
Rules:
- Return SQL only, no markdown fences and no explanation.
- Use only table "{table_name}" and only listed columns.
- Generate exactly one read-only SELECT statement (WITH CTE is allowed).
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, PRAGMA, ATTACH, DETACH, or multiple statements.
- Use SQLite syntax.
- If a column name contains spaces or special characters, quote it with double quotes.
- Prefer LIMIT 100 for detailed row listings unless an aggregate is requested.

Schema:
{schema_text}

Small sample (for understanding values only; never assume values outside it):
{sample_rows[:4000]}
"""
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ],
    )
    sql = resp.choices[0].message.content.strip()
    if sql.startswith("```"):
        sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def explain_result(question: str, sql: str, result_csv: str) -> str:
    client = _client()
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    system = """You are a careful data analyst.
Explain only what the supplied query result supports.
Do not invent numbers, causes, trends, or business facts.
Keep the answer concise and useful."""
    prompt = f"""Question:
{question}

SQL:
{sql}

Query result:
{result_csv[:8000]}

Explain the answer in plain English."""
    resp = client.chat.completions.create(
        model=model,
        temperature=0.1,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    )
    return resp.choices[0].message.content.strip()
