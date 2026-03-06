from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


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
