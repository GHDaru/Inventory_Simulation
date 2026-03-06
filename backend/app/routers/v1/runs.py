"""
v1 Runs router  –  /api/v1/runs

Endpoints
---------
POST   /api/v1/runs                Create a run (status=created)
GET    /api/v1/runs                List runs (id, name, status, createdAt, datasetName)
GET    /api/v1/runs/{id}           Run detail + status
POST   /api/v1/runs/{id}/execute   Queue and start execution (status=queued → running → done/failed)
GET    /api/v1/runs/{id}/results   Charts data + metrics
GET    /api/v1/runs/{id}/export.json  Full consolidated export
"""

import uuid
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.database import get_db
from app.db.models import Dataset, Run, RunResult
from app.models.runs_models import (
    V1CreateRunRequest,
    V1RunDetail,
    V1RunResults,
    V1RunSummary,
)
from app.models.simulation_models import ProductConfig, SimulationRequest
from app.services.simulator_service import run_simulation

router = APIRouter(prefix="/v1/runs", tags=["v1-runs"])

# ---- background worker ------------------------------------------------------


def _build_metrics(daily_records: list) -> list:
    """Derive per-product summary metrics from daily simulation records."""
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


async def _execute_run(run_id: uuid.UUID, db_factory) -> None:
    """Background task: run the simulation and persist results."""
    async with db_factory() as db:
        run: Run | None = await db.get(
            Run, run_id, options=[selectinload(Run.dataset)]
        )
        if run is None:
            return

        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            config = run.config_json
            products_raw = config.get("products", [])

            # Inject historical_data from associated dataset if present
            historical_data = None
            if run.dataset and run.dataset.data_json:
                # Expect data_json to be a list of records; extract the first
                # numeric column as historical demand if no explicit column given.
                records = run.dataset.data_json
                if records:
                    numeric_cols = [
                        k for k, v in records[0].items() if isinstance(v, (int, float))
                    ]
                    if numeric_cols:
                        historical_data = [r.get(numeric_cols[0]) for r in records]

            product_configs = []
            for p in products_raw:
                pc = dict(p)
                if historical_data is not None:
                    pc["historical_data"] = historical_data
                    pc["demand_params"] = None
                product_configs.append(ProductConfig(**pc))

            request = SimulationRequest(
                products=product_configs, days=config["days"]
            )
            result = run_simulation(request)

            metrics = _build_metrics(result.get("daily_records", []))

            run_result = RunResult(
                run_id=run_id,
                results_json={
                    "stock_history": result.get("stock_history"),
                    "daily_records": result.get("daily_records"),
                },
                metrics_json={"metrics": metrics},
            )
            db.add(run_result)

            run.status = "done"
            run.finished_at = datetime.now(timezone.utc)
            run.progress = 100
            await db.commit()

        except Exception as exc:  # noqa: BLE001
            run.status = "failed"
            run.error_message = f"{type(exc).__name__}: {exc}"
            run.finished_at = datetime.now(timezone.utc)
            await db.commit()


# ---- endpoints --------------------------------------------------------------


@router.post("", response_model=V1RunSummary, status_code=201)
async def create_run(
    request: V1CreateRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new simulation run with **status=created**.

    The run is NOT executed immediately.  Call
    ``POST /api/v1/runs/{id}/execute`` to start it.
    """
    name = request.name or f"Run {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}"

    # Validate dataset exists if provided
    if request.dataset_id is not None:
        dataset = await db.get(Dataset, request.dataset_id)
        if dataset is None:
            raise HTTPException(
                status_code=404,
                detail=f"Dataset '{request.dataset_id}' not found.",
            )

    run = Run(
        id=uuid.uuid4(),
        dataset_id=request.dataset_id,
        name=name,
        config_json={
            "days": request.days,
            "products": request.products,
        },
        status="created",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    dataset_name: str | None = None
    if run.dataset_id:
        ds = await db.get(Dataset, run.dataset_id)
        dataset_name = ds.name if ds else None

    summary = V1RunSummary.model_validate(run)
    summary.dataset_name = dataset_name
    return summary


@router.get("", response_model=list[V1RunSummary])
async def list_runs(db: AsyncSession = Depends(get_db)):
    """
    Return summary list of all runs.

    Each item includes *id*, *name*, *status*, *createdAt*, and
    optionally *datasetName* – all the fields the frontend menu needs.
    """
    result = await db.execute(
        select(Run)
        .options(selectinload(Run.dataset))
        .order_by(Run.created_at.desc())
    )
    runs = result.scalars().all()

    summaries = []
    for run in runs:
        s = V1RunSummary.model_validate(run)
        s.dataset_name = run.dataset.name if run.dataset else None
        summaries.append(s)
    return summaries


@router.get("/{run_id}", response_model=V1RunDetail)
async def get_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Return full metadata and configuration for a single run."""
    run = await db.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")
    return V1RunDetail.model_validate(run)


@router.post("/{run_id}/execute", response_model=V1RunDetail)
async def execute_run(
    run_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Queue a run for execution.

    Transitions the run from **created** → **queued** and schedules the
    simulation as a FastAPI ``BackgroundTask``.  Poll
    ``GET /api/v1/runs/{id}`` for status updates.
    """
    run = await db.get(Run, run_id, options=[selectinload(Run.dataset)])
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    if run.status not in ("created", "failed"):
        raise HTTPException(
            status_code=409,
            detail=f"Run is already in status '{run.status}' and cannot be re-queued.",
        )

    run.status = "queued"
    run.error_message = None
    await db.commit()
    await db.refresh(run)

    from app.db.database import AsyncSessionLocal

    if AsyncSessionLocal is None:
        raise HTTPException(status_code=503, detail="Database not configured.")

    background_tasks.add_task(_execute_run, run_id, AsyncSessionLocal)

    return V1RunDetail.model_validate(run)


@router.get("/{run_id}/results", response_model=V1RunResults)
async def get_run_results(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Get charts data and metrics for a completed run.

    * Returns **202** payload (status field) while the run is still in
      progress.
    * Returns **500** if the run failed.
    * Returns full results when ``status == done``.
    """
    run = await db.get(Run, run_id, options=[selectinload(Run.result)])
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    if run.status in ("created", "queued", "running"):
        return V1RunResults(run_id=run_id, status=run.status)

    if run.status == "failed":
        raise HTTPException(
            status_code=500,
            detail=run.error_message or "Simulation failed.",
        )

    rr: RunResult | None = run.result
    if rr is None:
        raise HTTPException(status_code=404, detail="Results not found for this run.")

    return V1RunResults(
        run_id=run_id,
        status=run.status,
        charts_data=rr.results_json,
        metrics=rr.metrics_json.get("metrics"),
    )


@router.get("/{run_id}/export.json")
async def export_run(run_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """
    Return a consolidated JSON export containing run config + results.

    Suitable for direct file download by the frontend.
    """
    run = await db.get(
        Run,
        run_id,
        options=[selectinload(Run.result), selectinload(Run.dataset)],
    )
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found.")

    export: dict = {
        "run": {
            "id": str(run.id),
            "name": run.name,
            "status": run.status,
            "created_at": run.created_at.isoformat() if run.created_at else None,
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "config": run.config_json,
            "dataset_id": str(run.dataset_id) if run.dataset_id else None,
            "dataset_name": run.dataset.name if run.dataset else None,
        },
        "results": None,
        "metrics": None,
    }

    if run.result:
        export["results"] = run.result.results_json
        export["metrics"] = run.result.metrics_json.get("metrics")

    return export
