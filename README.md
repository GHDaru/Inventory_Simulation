# Inventory Simulation

Discrete-time inventory management simulator with a FastAPI backend and a React frontend.

## Repository layout

```
Inventory_Simulation/
├── backend/    # Python simulation engine + FastAPI REST API
├── frontend/   # React (Vite) web app
└── docs/       # Technical documentation
    └── DOCUMENTATION.md
```

## Quick start

**Backend** (Python 3.10+):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API available at <http://localhost:8000> · Swagger UI at <http://localhost:8000/docs>

**Frontend** (Node 18+):

```bash
cd frontend
npm install
npm run dev
```

App available at <http://localhost:5173>

## Documentation

See [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md) for a full description of the simulation
engine, API endpoints, supported policies, and demand distributions.
