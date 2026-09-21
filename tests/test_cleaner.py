import pandas as pd
from src.data_cleaner import clean_dataframe

def test_cleaner_removes_duplicates_and_trims():
    df = pd.DataFrame({" name ": [" A ", " A "]})
    out, actions = clean_dataframe(df)
    assert list(out.columns) == ["name"]
    assert len(out) == 1
    assert out.iloc[0, 0] == "A"
