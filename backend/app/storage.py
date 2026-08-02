import os
import uuid
import pandas as pd

UPLOAD_DIR = os.getenv("CLARIFAI_UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def save_upload(file_bytes: bytes, original_filename: str) -> str:
    token = uuid.uuid4().hex
    ext = ".xlsx" if original_filename.lower().endswith(".xlsx") else ".xls"
    path = os.path.join(UPLOAD_DIR, f"{token}{ext}")
    with open(path, "wb") as f:
        f.write(file_bytes)
    return token


def _resolve_path(file_token: str) -> str:
    for ext in (".xlsx", ".xls"):
        path = os.path.join(UPLOAD_DIR, f"{file_token}{ext}")
        if os.path.exists(path):
            return path
    raise FileNotFoundError(f"No uploaded file found for token {file_token}")


def load_dataframe(file_token: str) -> pd.DataFrame:
    path = _resolve_path(file_token)
    return pd.read_excel(path)


def cleaned_output_path(file_token: str) -> str:
    return os.path.join(UPLOAD_DIR, f"{file_token}_cleaned.xlsx")
