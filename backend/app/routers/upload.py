import io
import numpy as np
import pandas as pd
from fastapi import APIRouter, File, UploadFile, HTTPException, Form

router = APIRouter(prefix="/upload", tags=["upload"])


@router.post("")
async def upload_historical_data(
    file: UploadFile = File(...),
    column: str = Form(default="demand", description="Column name containing demand data"),
):
    """
    Upload a CSV or Excel file with historical demand data.

    The file must contain at least one numeric column.  Use the **column**
    form field to specify which column holds the demand values (default:
    ``demand``).

    Returns a summary of the uploaded data and the raw values that can be
    passed to the ``/simulate`` endpoint as ``historical_data``.
    """
    filename = file.filename or ""
    if not (filename.endswith(".csv") or filename.endswith(".xlsx") or filename.endswith(".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel (.xlsx / .xls) files are supported.",
        )

    contents = await file.read()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}") from exc

    if column not in df.columns:
        raise HTTPException(
            status_code=422,
            detail=f"Column '{column}' not found. Available columns: {list(df.columns)}",
        )

    values = df[column].dropna().tolist()

    return {
        "filename": filename,
        "column": column,
        "rows": len(values),
        "mean": float(np.mean(values)),
        "std_dev": float(np.std(values)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "historical_data": values,
    }
