import io
from types import SimpleNamespace
from src.data_loader import load_uploaded_file

class FakeUpload:
    def __init__(self, name, raw):
        self.name = name
        self._raw = raw
    def getvalue(self):
        return self._raw

def test_csv_load():
    up = FakeUpload("a.csv", b"x,y\n1,2\n3,4\n")
    df = load_uploaded_file(up)
    assert df.shape == (2, 2)
