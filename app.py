from __future__ import annotations
from pathlib import Path
import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.data_loader import load_uploaded_file, DataLoadError
from src.data_cleaner import clean_dataframe
from src.data_profiler import profile_dataframe
from src.database import safe_table_name, load_dataframe_to_sqlite, get_schema
from src.sql_validator import validate_readonly_sql
from src.query_executor import execute_query, QueryExecutionError
from src.visualization import auto_chart
from src.insights import deterministic_result_summary
from src.chatbot import ask_data
from src.llm_client import LLMUnavailable

load_dotenv()

st.set_page_config(
    page_title="Data Analyst AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
[data-testid="stMetric"] {
    border: 1px solid rgba(128,128,128,.25);
    padding: 14px;
    border-radius: 14px;
}
div[data-testid="stChatMessage"] {
    border: 1px solid rgba(128,128,128,.18);
    border-radius: 14px;
}
.small-muted {opacity:.72; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

APP_DIR = Path(__file__).parent
DB_PATH = str(APP_DIR / "database" / "analytics.db")

def init_state():
    defaults = {
        "original_df": None,
        "df": None,
        "filename": None,
        "table_name": None,
        "cleaning_actions": [],
        "messages": [],
        "last_sql": "",
        "last_result": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_dataset_state():
    st.session_state.original_df = None
    st.session_state.df = None
    st.session_state.filename = None
    st.session_state.table_name = None
    st.session_state.cleaning_actions = []
    st.session_state.messages = []
    st.session_state.last_sql = ""
    st.session_state.last_result = None

def numeric_kpis(df: pd.DataFrame):
    cols = list(df.columns)
    lower = {str(c).lower(): c for c in cols}
    candidates = []
    for words, label, agg in [
        (["revenue", "sales", "amount"], "Total", "sum"),
        (["profit"], "Total Profit", "sum"),
        (["quantity", "qty"], "Total Quantity", "sum"),
    ]:
        found = next((orig for low, orig in lower.items() if any(w in low for w in words)), None)
        if found is not None and pd.api.types.is_numeric_dtype(df[found]):
            val = df[found].sum() if agg == "sum" else df[found].mean()
            candidates.append((f"{label} {found}" if label == "Total" else label, val))
    return candidates[:4]

init_state()

st.sidebar.title("📊 Data Analyst AI")
page = st.sidebar.radio(
    "Navigate",
    ["Upload Dataset", "Dashboard", "Data Explorer", "AI Chatbot", "SQL Explorer", "Insights"],
)

uploaded = st.sidebar.file_uploader("Upload CSV / Excel", type=["csv", "xlsx", "xls"])

if uploaded is not None:
    changed = uploaded.name != st.session_state.filename
    if changed:
        try:
            raw_df = load_uploaded_file(uploaded)
            cleaned_df, actions = clean_dataframe(raw_df)
            table_name = safe_table_name(uploaded.name)
            load_dataframe_to_sqlite(cleaned_df, DB_PATH, table_name)
            st.session_state.original_df = raw_df
            st.session_state.df = cleaned_df
            st.session_state.filename = uploaded.name
            st.session_state.table_name = table_name
            st.session_state.cleaning_actions = actions
            st.session_state.messages = []
            st.session_state.last_sql = ""
            st.session_state.last_result = None
            st.sidebar.success("Dataset ready")
        except DataLoadError as exc:
            st.sidebar.error(str(exc))
        except Exception as exc:
            st.sidebar.error(f"Could not prepare dataset: {exc}")

if st.sidebar.button("Reset dataset"):
    reset_dataset_state()
    st.rerun()

st.sidebar.markdown("---")
ai_enabled = bool(os.getenv("OPENAI_API_KEY", "").strip())
st.sidebar.caption("AI mode: " + ("✅ API key detected" if ai_enabled else "⚪ Add OPENAI_API_KEY to .env"))

df = st.session_state.df

if page == "Upload Dataset":
    st.title("Data Analyst AI Chatbot")
    st.write("Upload a CSV or Excel file, then explore it with dashboards, SQL, and natural-language questions.")
    if df is None:
        st.info("Use the uploader in the sidebar to begin.")
    else:
        p = profile_dataframe(df)
        st.success(f"Loaded **{st.session_state.filename}** into SQLite table `{st.session_state.table_name}`.")
        a, b, c, d = st.columns(4)
        a.metric("Rows", f"{p['rows']:,}")
        b.metric("Columns", p["columns"])
        c.metric("Missing", f"{p['missing_pct']}%")
        d.metric("Memory", f"{p['memory_mb']} MB")
        st.subheader("Cleaning log")
        for item in st.session_state.cleaning_actions:
            st.write("•", item)
        st.subheader("Preview")
        st.dataframe(df.head(20), use_container_width=True)

elif df is None:
    st.title(page)
    st.warning("Upload a CSV or Excel dataset first.")

elif page == "Dashboard":
    st.title("Dashboard")
    p = profile_dataframe(df)

    kpis = numeric_kpis(df)
    cols = st.columns(max(4, len(kpis)))
    base_metrics = [
        ("Rows", f"{p['rows']:,}"),
        ("Columns", p["columns"]),
        ("Missing", f"{p['missing_pct']}%"),
        ("Duplicates", p["duplicates"]),
    ]
    for i, (label, value) in enumerate(base_metrics):
        cols[i].metric(label, value)

    if kpis:
        st.subheader("Detected KPIs")
        kcols = st.columns(len(kpis))
        for i, (label, value) in enumerate(kpis):
            if isinstance(value, (int, float)):
                kcols[i].metric(label, f"{value:,.2f}")
            else:
                kcols[i].metric(label, value)

    st.subheader("Data Quality")
    q1, q2, q3 = st.columns(3)
    q1.metric("Numeric columns", len(p["numeric_columns"]))
    q2.metric("Categorical columns", len(p["categorical_columns"]))
    q3.metric("Date columns", len(p["date_columns"]))

    st.subheader("Quick numeric overview")
    if p["numeric_columns"]:
        st.dataframe(df[p["numeric_columns"]].describe().T, use_container_width=True)
    else:
        st.info("No numeric columns detected.")

elif page == "Data Explorer":
    st.title("Data Explorer")
    tab1, tab2, tab3 = st.tabs(["Preview", "Schema", "Statistics"])

    with tab1:
        n = st.slider("Rows to display", 5, min(100, max(5, len(df))), min(20, max(5, len(df))))
        st.dataframe(df.head(n), use_container_width=True)

    with tab2:
        p = profile_dataframe(df)
        st.dataframe(p["schema"], use_container_width=True)
        st.subheader("Missing values")
        miss = pd.DataFrame({
            "column": df.columns,
            "missing": df.isna().sum().values,
            "missing_pct": (df.isna().mean().values * 100).round(2),
        }).sort_values("missing_pct", ascending=False)
        st.dataframe(miss, use_container_width=True)

    with tab3:
        st.dataframe(df.describe(include="all").T, use_container_width=True)

elif page == "AI Chatbot":
    st.title("AI Chatbot")
    st.caption("Ask questions about the uploaded data. AI-generated SQL is validated before execution.")

    if not ai_enabled:
        st.info("AI API is not enabled. Basic analytics such as average, sum, count, max, min, and group-by still work locally with Pandas.")
    else:
        st.success("AI mode is enabled. If the API is unavailable or out of credits, supported basic questions automatically use the local Pandas fallback.")

    suggestions = []
    numeric = list(df.select_dtypes(include="number").columns)
    categorical = [c for c in df.columns if c not in numeric]
    if numeric:
        suggestions.append(f"What is the average {numeric[0]}?")
        suggestions.append(f"What is the total {numeric[0]}?")
    if categorical and numeric:
        suggestions.append(f"Show {numeric[0]} by {categorical[0]}.")
        suggestions.append(f"Which {categorical[0]} has the highest {numeric[0]}?")

    if suggestions:
        st.write("**Suggested questions**")
        st.write(" · ".join(suggestions[:4]))

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sql"):
                with st.expander("SQL used"):
                    st.code(msg["sql"], language="sql")

    question = st.chat_input("Ask a question about your data")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            try:
                sql, result, explanation, mode = ask_data(
                    question,
                    DB_PATH,
                    st.session_state.table_name,
                    df
                )
                if mode.startswith("local_pandas"):
                    st.info("🟢 Local Pandas fallback used — no API credits were required for this question.")
                else:
                    st.info("🔵 AI + SQLite mode used.")
                st.markdown(explanation)
                st.dataframe(result, use_container_width=True)
                fig = auto_chart(result, question)
                if fig is not None:
                    st.plotly_chart(fig, use_container_width=True)
                with st.expander("SQL used"):
                    st.code(sql, language="sql")

                st.session_state.last_sql = sql
                st.session_state.last_result = result
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": explanation,
                    "sql": sql,
                })
            except LLMUnavailable as exc:
                st.error(str(exc))
            except Exception as exc:
                st.error(f"Could not answer that question: {exc}")

elif page == "SQL Explorer":
    st.title("SQL Explorer")
    st.caption("Read-only SELECT queries only.")

    schema = get_schema(DB_PATH, st.session_state.table_name)
    st.write("**Table:**", f"`{st.session_state.table_name}`")
    st.dataframe(pd.DataFrame(schema), use_container_width=True)

    default_sql = st.session_state.last_sql or f'SELECT * FROM "{st.session_state.table_name}" LIMIT 20'
    sql = st.text_area("SQL query", value=default_sql, height=180)

    ok, reason = validate_readonly_sql(sql)
    if ok:
        st.success("Query passes read-only validation.")
    else:
        st.warning(reason)

    if st.button("Run Query", type="primary"):
        try:
            result = execute_query(DB_PATH, sql)
            st.session_state.last_result = result
            st.session_state.last_sql = sql
            st.dataframe(result, use_container_width=True)
            st.markdown(deterministic_result_summary(result))
            fig = auto_chart(result)
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
        except QueryExecutionError as exc:
            st.error(str(exc))

elif page == "Insights":
    st.title("Insights")
    st.write("This page summarizes useful facts directly from the dataset without inventing claims.")

    p = profile_dataframe(df)
    st.markdown(f"""
- **{p['rows']:,} rows** and **{p['columns']} columns**
- **{p['missing_pct']}%** of all cells are missing
- **{len(p['numeric_columns'])} numeric**, **{len(p['categorical_columns'])} categorical**, and **{len(p['date_columns'])} date** column(s)
""")

    if p["numeric_columns"]:
        stats = df[p["numeric_columns"]].describe().T
        st.subheader("Numeric summary")
        st.dataframe(stats, use_container_width=True)

    cat_cols = p["categorical_columns"][:3]
    for c in cat_cols:
        st.subheader(f"Top values — {c}")
        vc = df[c].astype("string").value_counts(dropna=False).head(10).rename_axis(c).reset_index(name="count")
        st.dataframe(vc, use_container_width=True)
        fig = auto_chart(vc)
        if fig is not None:
            st.plotly_chart(fig, use_container_width=True)
