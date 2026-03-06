import io
import pandas as pd
from fastapi import APIRouter, HTTPException
from app.models.simulation_models import SimulationRequest, SimulationResponse
from app.services.simulator_service import run_simulation

router = APIRouter(prefix="/simulate", tags=["simulation"])


@router.post("", response_model=SimulationResponse)
def simulate(request: SimulationRequest):
    """
    Run an inventory simulation.

    Send a JSON body describing each product (name, initial stock, demand
    distribution, and stock replenishment policy) together with the number of
    days to simulate.  The endpoint returns per-day demand / unmet-demand
    records and a complete stock-level history for every product.
    """
    try:
        result = run_simulation(request)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
