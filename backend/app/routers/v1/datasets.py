"""
v1 Datasets router  –  /api/v1/datasets

Endpoints
---------
POST   /api/v1/datasets            Upload and persist a dataset
GET    /api/v1/datasets            List all datasets (metadata only)
GET    /api/v1/datasets/{id}       Dataset detail (metadata + optional sample)
GET    /api/v1/datasets/{id}/data  Paginated data rows
"""

import io
import uuid
from typing import Any

import numpy as np
import pandas as pd
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.models import Dataset
from app.models.runs_models import DatasetDetailResponse, DatasetResponse

router = APIRouter(prefix="/v1/datasets", tags=["v1-datasets"])

# ---- configuration ----------------------------------------------------------

MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB
_MB = 1024 * 1024

# ---- helpers ----------------------------------------------------------------


def _infer_schema(df: pd.DataFrame) -> dict:
    """Return a schema dict describing each column's inferred type."""
    columns = []
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype):
            col_type = "int"
        elif pd.api.types.is_float_dtype(dtype):
            col_type = "float"
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            col_type = "date"
        else:
            # Try date parse for object columns
            try:
                pd.to_datetime(df[col].dropna().head(5))
                col_type = "date"
            except Exception:
                col_type = "string"
        columns.append({"name": col, "type": col_type})
    return {"columns": columns}


def _normalise_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column headers: lowercase, spaces → underscores."""
    df.columns = [
        str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns
    ]
    return df


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert DataFrame to JSON-serialisable list of dicts."""
    return df.where(pd.notna(df), None).to_dict(orient="records")


# ---- endpoints --------------------------------------------------------------


@router.post("", response_model=DatasetResponse, status_code=201)
async def create_dataset(
    file: UploadFile = File(...),
    name: str = Form(default="", description="Human-readable dataset name (defaults to filename)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a CSV, Excel, or JSON file and persist it as a dataset.

    * File size limit: **10 MB** (configurable via MAX_UPLOAD_MB env var).
    * Column headers are normalised (lowercase, underscores).
    * Schema (column names + types) and data are stored in Postgres (Neon).
    """
    filename: str = file.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in {"csv", "xlsx", "xls", "json"}:
        raise HTTPException(
            status_code=400,
            detail="Only CSV, Excel (.xlsx / .xls), and JSON files are supported.",
        )

    contents = await file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the maximum allowed size of {MAX_UPLOAD_BYTES // _MB} MB.",
        )

    try:
        if ext == "csv":
            df = pd.read_csv(io.BytesIO(contents))
        elif ext == "json":
            df = pd.read_json(io.BytesIO(contents))
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not parse file: {exc}") from exc

    df = _normalise_df(df)
    schema = _infer_schema(df)
    records = _df_to_records(df)

    dataset = Dataset(
        id=uuid.uuid4(),
        name=name or filename,
        source_type=ext if ext in {"csv", "xlsx", "json"} else "xlsx",
        schema_json=schema,
        data_json=records,
        row_count=len(records),
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    return DatasetResponse.model_validate(dataset)


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    """Return metadata for all datasets (data_json excluded)."""
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    datasets = result.scalars().all()
    return [DatasetResponse.model_validate(d) for d in datasets]


@router.get("/{dataset_id}", response_model=DatasetDetailResponse)
async def get_dataset(
    dataset_id: uuid.UUID,
    include_data: bool = Query(False, description="Include a sample of 20 rows"),
    db: AsyncSession = Depends(get_db),
):
    """Return dataset metadata and optionally a small data sample."""
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    sample: list | None = None
    if include_data and dataset.data_json:
        sample = dataset.data_json[:20]

    response = DatasetDetailResponse.model_validate(dataset)
    response.data_sample = sample
    return response


@router.get("/{dataset_id}/data")
async def get_dataset_data(
    dataset_id: uuid.UUID,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(100, ge=1, le=1000, description="Rows per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    Return paginated rows from the stored data_json.

    *page* and *page_size* control pagination.  Returns an empty list when
    data was not stored (e.g. large-file datasets using storage_uri).
    """
    dataset = await db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    data = dataset.data_json or []
    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size

    return {
        "dataset_id": dataset_id,
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": data[start:end],
    }
