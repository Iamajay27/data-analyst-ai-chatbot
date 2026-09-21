import pandas as pd
from src.database import load_dataframe_to_sqlite
from src.query_executor import execute_query

def test_query_executor(tmp_path):
    db = tmp_path / "test.db"
    df = pd.DataFrame({"city": ["A", "B"], "sales": [10, 20]})
    load_dataframe_to_sqlite(df, str(db), "sales")
    out = execute_query(str(db), "SELECT SUM(sales) AS total FROM sales")
    assert out.iloc[0]["total"] == 30
