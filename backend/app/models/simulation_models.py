from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class DemandParams(BaseModel):
    distribution_type: str = Field(..., description="'normal' or 'poisson'")
    params: Dict[str, float] = Field(
        ...,
        description="For 'normal': {'mean': float, 'std_dev': float}. For 'poisson': {'lambda': float}",
    )


class StockPolicyParams(BaseModel):
    product: str = Field(..., description="Product name (must match the product's name field)")
    type: str = Field(..., description="'minmax' or 'lot_size'")
    min_level: Optional[int] = Field(None, description="Reorder point")
    max_level: Optional[int] = Field(None, description="Target stock level (used in minmax)")
    lead_time: int = Field(..., description="Replenishment lead time in days")
    lot_size: Optional[int] = Field(None, description="Fixed order quantity (used in lot_size)")


class ProductConfig(BaseModel):
    name: str
    initial_stock: int = Field(0, ge=0)
    stock_policy_params: StockPolicyParams
    demand_params: Optional[DemandParams] = None
    historical_data: Optional[List[float]] = None


class SimulationRequest(BaseModel):
    products: List[ProductConfig]
    days: int = Field(..., gt=0, description="Number of days to simulate")


class DailyRecord(BaseModel):
    name: str
    day: int
    demand: float
    sales: float
    unmet_demand: float


class SimulationResponse(BaseModel):
    status: str
    days: int
    products: List[str]
    daily_records: List[Dict[str, Any]]
    stock_history: Dict[str, List[int]]
