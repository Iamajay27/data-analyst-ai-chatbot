import pandas as pd

from src.local_fallback import answer_local


def sample_df():
    return pd.DataFrame({
        "city": ["Mumbai", "Delhi", "Mumbai", "Delhi"],
        "category": ["A", "A", "B", "B"],
        "sales": [100, 200, 300, 400],
        "quantity": [1, 2, 3, 4],
    })


def test_average_local():
    answer, result, op = answer_local("What is the average sales?", sample_df())
    assert result.iloc[0]["sales"] == 250
    assert op == "local_pandas_mean"


def test_sum_local():
    answer, result, op = answer_local("What is the total sales?", sample_df())
    assert result.iloc[0]["sales"] == 1000


def test_count_local():
    answer, result, op = answer_local("How many rows are there?", sample_df())
    assert result.iloc[0]["count"] == 4


def test_groupby_local():
    answer, result, op = answer_local("What is the average sales by city?", sample_df())
    values = dict(zip(result["city"], result["mean_sales"]))
    assert values["Mumbai"] == 200
    assert values["Delhi"] == 300


def test_filter_local():
    answer, result, op = answer_local("What is the total sales from Mumbai?", sample_df())
    assert result.iloc[0]["sales"] == 400
