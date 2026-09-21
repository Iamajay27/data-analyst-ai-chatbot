from src.sql_validator import validate_readonly_sql

def test_select_allowed():
    ok, _ = validate_readonly_sql("SELECT * FROM sales LIMIT 10")
    assert ok

def test_drop_rejected():
    ok, _ = validate_readonly_sql("DROP TABLE sales")
    assert not ok

def test_multi_statement_rejected():
    ok, _ = validate_readonly_sql("SELECT 1; SELECT 2")
    assert not ok
