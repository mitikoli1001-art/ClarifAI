import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from ..storage import save_upload, load_dataframe

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Only .xlsx/.xls files are supported")

    contents = await file.read()
    token = save_upload(contents, file.filename)

    try:
        df = load_dataframe(token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read Excel file: {e}")

    # Convert sample rows to JSON-safe values: NaN/NaT -> None, everything else -> str.
    sample_df = df.head(5)
    sample_records = []
    for _, row in sample_df.iterrows():
        record = {}
        for col, val in row.items():
            record[str(col)] = None if pd.isna(val) else str(val)
        sample_records.append(record)

    preview = {
        "file_token": token,
        "original_filename": file.filename,
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns.astype(str)),
        "sample": sample_records,
        "null_counts": {str(k): int(v) for k, v in df.isna().sum().to_dict().items()},
    }
    return preview
