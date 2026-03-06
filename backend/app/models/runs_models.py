from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime


# ---------------------------------------------------------------------------
# Legacy (v0) models – kept for backward-compatibility with existing routes
# ---------------------------------------------------------------------------

class DatasetMeta(BaseModel):
    id: str
    filename: str
    column: str
    rows: int
    mean: float
    std_dev: float
    min_val: float
    max_val: float
    created_at: str


class CreateRunRequest(BaseModel):
    name: Optional[str] = None
    days: int = Field(..., gt=0, description="Number of days to simulate")
    products: List[Dict[str, Any]]
    dataset_id: Optional[str] = Field(None, description="Dataset to use for historical demand")


class RunSummary(BaseModel):
    id: str
    name: str
    status: str  # created | running | done | failed
    created_at: str
    dataset_id: Optional[str] = None


class RunDetail(BaseModel):
    id: str
    name: str
    status: str
    created_at: str
    dataset_id: Optional[str] = None
    config: Dict[str, Any]
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# v1 Pydantic models – used by the /api/v1/ routers (Neon-backed)
# ---------------------------------------------------------------------------

class SchemaColumn(BaseModel):
    name: str
    type: str  # int | float | string | date


class DatasetSchema(BaseModel):
    columns: List[SchemaColumn]


class DatasetResponse(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    dataset_schema: Dict[str, Any] = Field(alias="schema_json")
    row_count: int
    created_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class DatasetDetailResponse(DatasetResponse):
    """Includes optional data sample (first N records)."""
    data_sample: Optional[List[Dict[str, Any]]] = None


class V1CreateRunRequest(BaseModel):
    name: Optional[str] = None
    days: int = Field(..., gt=0, description="Number of days to simulate")
    products: List[Dict[str, Any]]
    dataset_id: Optional[uuid.UUID] = Field(
        None, description="UUID of the dataset to use for historical demand"
    )


class V1RunSummary(BaseModel):
    id: uuid.UUID
    name: str
    status: str  # created | queued | running | done | failed
    created_at: datetime
    dataset_id: Optional[uuid.UUID] = None
    dataset_name: Optional[str] = None

    model_config = {"from_attributes": True}


class V1RunDetail(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    dataset_id: Optional[uuid.UUID] = None
    config_json: Dict[str, Any]
    progress: Optional[int] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class RunMetric(BaseModel):
    product: str
    total_demand: float
    total_unmet_demand: float
    stockout_days: int
    service_level_pct: float


class V1RunResults(BaseModel):
    run_id: uuid.UUID
    status: str
    charts_data: Optional[Dict[str, Any]] = None
    metrics: Optional[List[RunMetric]] = None
