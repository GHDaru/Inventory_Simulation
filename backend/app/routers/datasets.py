import io
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from app.models.runs_models import DatasetMeta
from app import store

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("", response_model=DatasetMeta, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    column: str = Form(default="demand", description="Column name containing demand data"),
):
    """
    Upload a CSV or Excel file and store it as a dataset.

    Returns a *datasetId* and metadata that can be referenced when creating
    simulation runs.
    """
    filename = file.filename or ""
    if not (
        filename.endswith(".csv")
        or filename.endswith(".xlsx")
        or filename.endswith(".xls")
        or filename.endswith(".json")
    ):
        raise HTTPException(
            status_code=400,
            detail="Only CSV, Excel (.xlsx / .xls) and JSON files are supported.",
        )

    contents = await file.read()
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
        elif filename.endswith(".json"):
            df = pd.read_json(io.BytesIO(contents))
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
    dataset_id = str(uuid.uuid4())

    dataset = {
        "id": dataset_id,
        "filename": filename,
        "column": column,
        "rows": len(values),
        "mean": float(np.mean(values)),
        "std_dev": float(np.std(values)),
        "min_val": float(np.min(values)),
        "max_val": float(np.max(values)),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "historical_data": values,
    }

    with store._lock:
        store.datasets[dataset_id] = dataset

    return DatasetMeta(**{k: v for k, v in dataset.items() if k != "historical_data"})


@router.get("", response_model=list[DatasetMeta])
def list_datasets():
    """Return summary metadata for all uploaded datasets."""
    with store._lock:
        items = list(store.datasets.values())
    return [
        DatasetMeta(**{k: v for k, v in d.items() if k != "historical_data"})
        for d in items
    ]
