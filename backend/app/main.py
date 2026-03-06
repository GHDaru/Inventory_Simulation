from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import simulation, upload, datasets, runs
from app.routers.v1 import datasets as v1_datasets, runs as v1_runs


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Initialise the database tables on startup (idempotent)."""
    from app.db.database import init_db

    await init_db()
    yield


app = FastAPI(
    title="Inventory Simulation API",
    description=(
        "REST API for running inventory policy simulations. "
        "Configure products, demand distributions, and replenishment policies "
        "to simulate stock levels over time."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the React dev-server (port 5173) and any other local origins to
# communicate with the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Legacy (v0) routes – kept for backward-compatibility
app.include_router(simulation.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(runs.router, prefix="/api")

# v1 routes – Neon/Postgres-backed
app.include_router(v1_datasets.router, prefix="/api")
app.include_router(v1_runs.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    """Health-check endpoint."""
    return {"status": "ok"}
