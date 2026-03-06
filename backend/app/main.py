from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import simulation, upload, datasets, runs

app = FastAPI(
    title="Inventory Simulation API",
    description=(
        "REST API for running inventory policy simulations. "
        "Configure products, demand distributions, and replenishment policies "
        "to simulate stock levels over time."
    ),
    version="1.0.0",
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

app.include_router(simulation.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(runs.router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    """Health-check endpoint."""
    return {"status": "ok"}
