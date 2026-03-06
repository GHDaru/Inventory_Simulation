# Inventory Simulation — Backend

FastAPI application that exposes the inventory simulation engine as a REST API.

## Project layout

```
backend/
├── app/
│   ├── main.py               # FastAPI application entry-point
│   ├── routers/
│   │   ├── simulation.py     # POST /api/simulate
│   │   └── upload.py         # POST /api/upload
│   ├── models/
│   │   └── simulation_models.py  # Pydantic request / response schemas
│   └── services/
│       └── simulator_service.py  # Bridges API layer with simulation core
└── base/                     # Core simulation engine (see docs/DOCUMENTATION.md)
    ├── demand.py
    ├── inventory.py
    ├── order.py
    ├── product.py
    ├── product_family.py
    ├── simulation.py
    ├── stock_policy.py
    └── visualization.py
```

## Quick start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start the development server (from the backend/ directory)
uvicorn app.main:app --reload
```

The API will be available at <http://localhost:8000>.  
Interactive docs: <http://localhost:8000/docs>

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/api/health` | Health check |
| `POST` | `/api/simulate` | Run simulation |
| `POST` | `/api/upload` | Upload historical demand data |

### POST `/api/simulate` — example body

```json
{
  "days": 90,
  "products": [
    {
      "name": "Product A",
      "initial_stock": 100,
      "stock_policy_params": {
        "product": "Product A",
        "type": "minmax",
        "min_level": 20,
        "max_level": 150,
        "lead_time": 5
      },
      "demand_params": {
        "distribution_type": "normal",
        "params": { "mean": 10, "std_dev": 2 }
      }
    }
  ]
}
```

### POST `/api/upload` — form fields

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | CSV or Excel file |
| `column` | string | Column name with demand data (default: `demand`) |
