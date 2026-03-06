import uuid
import threading
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.runs_models import CreateRunRequest, RunSummary, RunDetail
from app.models.simulation_models import SimulationRequest, ProductConfig
from app.services.simulator_service import run_simulation
from app import store

router = APIRouter(prefix="/runs", tags=["runs"])


def _execute_run(run_id: str) -> None:
    """Run the simulation in a background thread and update the run record."""
    with store._lock:
        run = store.runs.get(run_id)
        if run is None:
            return
        run["status"] = "running"

    try:
        config = run["config"]
        products_raw = config["products"]

        # If a dataset_id is provided, inject historical_data into every product
        dataset_id = run.get("dataset_id")
        historical_data = None
        if dataset_id:
            with store._lock:
                dataset = store.datasets.get(dataset_id)
            if dataset:
                historical_data = dataset.get("historical_data")

        # Build ProductConfig list
        product_configs = []
        for p in products_raw:
            pc = dict(p)
            if historical_data is not None:
                pc["historical_data"] = historical_data
                pc["demand_params"] = None
            product_configs.append(ProductConfig(**pc))

        request = SimulationRequest(products=product_configs, days=config["days"])
        result = run_simulation(request)

        with store._lock:
            store.runs[run_id]["status"] = "done"
            store.runs[run_id]["results"] = result

    except Exception as exc:  # noqa: BLE001
        with store._lock:
            store.runs[run_id]["status"] = "failed"
            store.runs[run_id]["error"] = str(exc)


@router.get("", response_model=list[RunSummary])
def list_runs():
    """Return a summary list of all simulation runs."""
    with store._lock:
        items = list(store.runs.values())
    return [
        RunSummary(
            id=r["id"],
            name=r["name"],
            status=r["status"],
            created_at=r["created_at"],
            dataset_id=r.get("dataset_id"),
        )
        for r in items
    ]


@router.post("", response_model=RunSummary, status_code=201)
def create_run(request: CreateRunRequest, background_tasks: BackgroundTasks):
    """
    Create a new simulation run and immediately start executing it in the background.

    Returns the run summary with status **created**. Poll
    ``GET /api/runs/{runId}`` or ``GET /api/runs/{runId}/results`` to check
    progress.
    """
    run_id = str(uuid.uuid4())
    name = request.name or f"Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"

    run = {
        "id": run_id,
        "name": name,
        "status": "created",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_id": request.dataset_id,
        "config": {
            "days": request.days,
            "products": [p for p in request.products],
        },
        "results": None,
        "error": None,
    }

    with store._lock:
        store.runs[run_id] = run

    background_tasks.add_task(_execute_run, run_id)

    return RunSummary(
        id=run["id"],
        name=run["name"],
        status=run["status"],
        created_at=run["created_at"],
        dataset_id=run.get("dataset_id"),
    )


@router.get("/{run_id}", response_model=RunDetail)
def get_run(run_id: str):
    """Get full metadata and config for a specific run."""
    with store._lock:
        run = store.runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return RunDetail(
        id=run["id"],
        name=run["name"],
        status=run["status"],
        created_at=run["created_at"],
        dataset_id=run.get("dataset_id"),
        config=run["config"],
        error=run.get("error"),
    )


@router.get("/{run_id}/results")
def get_run_results(run_id: str):
    """
    Get the results of a completed run.

    Returns 404 if the run does not exist, 202 (Accepted) if it is still
    running, and 200 with the full results payload when done.
    """
    with store._lock:
        run = store.runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    status = run["status"]

    if status in ("created", "running"):
        return {"run_id": run_id, "status": status, "results": None}

    if status == "failed":
        raise HTTPException(status_code=500, detail=run.get("error", "Simulation failed."))

    results = run.get("results", {})
    # Build metrics from results
    metrics = _build_metrics(results)

    return {
        "run_id": run_id,
        "status": status,
        "charts_data": {
            "stock_history": results.get("stock_history"),
            "daily_records": results.get("daily_records"),
        },
        "metrics": metrics,
        "daily_records": results.get("daily_records"),
        "stock_history": results.get("stock_history"),
    }


def _build_metrics(results: dict) -> list:
    """Derive summary metrics from simulation results."""
    daily_records = results.get("daily_records", [])
    if not daily_records:
        return []

    from collections import defaultdict

    product_rows: dict = defaultdict(list)
    for rec in daily_records:
        product_rows[rec["name"]].append(rec)

    metrics = []
    for name, rows in product_rows.items():
        total_demand = sum(r["demand"] for r in rows)
        total_unmet = sum(r["unmet_demand"] for r in rows)
        stockout_days = sum(1 for r in rows if r["unmet_demand"] > 0)
        service_level = (
            ((total_demand - total_unmet) / total_demand * 100) if total_demand > 0 else 100.0
        )
        metrics.append(
            {
                "product": name,
                "total_demand": round(total_demand, 2),
                "total_unmet_demand": round(total_unmet, 2),
                "stockout_days": stockout_days,
                "service_level_pct": round(service_level, 1),
            }
        )
    return metrics
