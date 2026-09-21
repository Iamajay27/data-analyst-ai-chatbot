from __future__ import annotations
import io
import pandas as pd

MAX_FILE_MB = 25
SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}

class DataLoadError(Exception):
    pass

def _extension(filename: str) -> str:
    filename = filename.lower().strip()
    for ext in SUPPORTED_EXTENSIONS:
        if filename.endswith(ext):
            return ext
    return ""

def load_uploaded_file(uploaded_file) -> pd.DataFrame:
    """Load Streamlit UploadedFile or file-like object into a DataFrame."""
    name = getattr(uploaded_file, "name", "uploaded.csv")
    ext = _extension(name)
    if not ext:
        raise DataLoadError("Unsupported file type. Please upload CSV, XLSX, or XLS.")

    raw = uploaded_file.getvalue() if hasattr(uploaded_file, "getvalue") else uploaded_file.read()
    if not raw:
        raise DataLoadError("The uploaded file is empty.")
    if len(raw) > MAX_FILE_MB * 1024 * 1024:
        raise DataLoadError(f"File is too large. Maximum supported size is {MAX_FILE_MB} MB.")

    try:
        bio = io.BytesIO(raw)
        if ext == ".csv":
            try:
                df = pd.read_csv(bio)
            except UnicodeDecodeError:
                bio.seek(0)
                df = pd.read_csv(bio, encoding="latin-1")
        else:
            df = pd.read_excel(bio)
    except Exception as exc:
        raise DataLoadError(f"Could not read the file: {exc}") from exc

    if df.empty and len(df.columns) == 0:
        raise DataLoadError("No usable tabular data was found.")
    return df
