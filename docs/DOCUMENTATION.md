# Inventory Simulation — Technical Documentation

## Table of contents

1. [Overview](#overview)
2. [Project structure](#project-structure)
3. [Core simulation engine](#core-simulation-engine)
   - [DemandGenerator](#demandgenerator)
   - [Inventory](#inventory)
   - [Order](#order)
   - [StockPolicy](#stockpolicy)
   - [Product](#product)
   - [ProductFamily](#productfamily)
   - [Simulator](#simulator)
4. [Simulation flow](#simulation-flow)
5. [Supported stock policies](#supported-stock-policies)
6. [Demand distributions](#demand-distributions)
7. [API endpoints](#api-endpoints)
8. [Frontend overview](#frontend-overview)
9. [Running the project](#running-the-project)

---

## Overview

**Inventory Simulation** is a discrete-time, day-by-day inventory management simulator.  
It models demand uncertainty, order lead times, and stock replenishment policies for one or more
products (optionally grouped in families).

The project is split into two parts:

| Folder | Purpose |
|--------|---------|
| `backend/` | Python simulation engine + FastAPI REST API |
| `frontend/` | React (Vite) web application for configuration and visualization |

---

## Project structure

```
Inventory_Simulation/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry-point
│   │   ├── routers/
│   │   │   ├── simulation.py         # POST /api/simulate
│   │   │   └── upload.py             # POST /api/upload
│   │   ├── models/
│   │   │   └── simulation_models.py  # Pydantic request / response schemas
│   │   └── services/
│   │       └── simulator_service.py  # Bridges API with simulation core
│   ├── base/                         # Core simulation engine
│   │   ├── demand.py
│   │   ├── inventory.py
│   │   ├── order.py
│   │   ├── product.py
│   │   ├── product_family.py
│   │   ├── simulation.py
│   │   ├── stock_policy.py
│   │   └── visualization.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.js
│   │   ├── components/
│   │   │   ├── SimulationForm.jsx
│   │   │   ├── FileUpload.jsx
│   │   │   └── ResultsView.jsx
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── package.json
└── docs/
    └── DOCUMENTATION.md              # This file
```

---

## Core simulation engine

All engine classes live in `backend/base/`.

### DemandGenerator

**File:** `base/demand.py`

Generates stochastic daily demand.  Supports two statistical distributions.

| Method | Description |
|--------|-------------|
| `__init__(distribution_type, params)` | Store the chosen distribution and its parameters |
| `generate() → int` | Sample one demand value (≥ 0) |
| `normal_distribution(mean, std_dev) → int` | Draw from `N(mean, std_dev²)`, clipped at 0 |
| `poisson_distribution(lambda_) → int` | Draw from `Poisson(λ)` |
| `generate_historical_data(dist, params, days) → list` | *static* — generate a synthetic demand history |
| `calculate_distribution_parameters(data, dist) → dict` | *static* — MLE parameter estimation |
| `best_fit_distribution(historical_data) → (str, dict)` | *static* — compare Normal vs Poisson by log-likelihood and return the best fit |

---

### Inventory

**File:** `base/inventory.py`

Tracks the physical stock position for one product.

| Attribute | Type | Description |
|-----------|------|-------------|
| `initial_stock` | int | Starting stock level |
| `current_stock` | int | Current on-hand stock |
| `pending_orders` | list[Order] | Orders placed but not yet arrived |
| `current_day` | int | Day index set by the simulator loop |
| `order_history` | list[dict] | Audit log of all placed orders |

| Method | Description |
|--------|-------------|
| `receive_orders(current_day)` | Move arrived orders into `current_stock` |
| `update_stock(demand) → int` | Deduct demand; return unmet demand (0 if fully met) |
| `pending_order_quantity() → int` | Sum of all in-transit order quantities |
| `place_order(order)` | Append an Order to pending list and order history |

---

### Order

**File:** `base/order.py`

Represents a replenishment order.

| Attribute | Description |
|-----------|-------------|
| `id` | UUID (unique per order) |
| `product` | Reference to the owning `Product` |
| `quantity` | Units ordered |
| `arrival_day` | Day on which the order will be received |

| Method | Description |
|--------|-------------|
| `is_arrived(current_day) → bool` | `True` when `current_day >= arrival_day` |
| `to_dict() → dict` | Serialize to JSON-friendly dict |

---

### StockPolicy

**File:** `base/stock_policy.py`

Implements the replenishment decision logic.

| Attribute | Description |
|-----------|-------------|
| `product` | Reference to the owning `Product` |
| `type` | `'minmax'` or `'lot_size'` |
| `min_level` | Reorder point (trigger threshold) |
| `max_level` | Target stock level (used in *minmax* only) |
| `lead_time` | Days until an order arrives |
| `lot_size` | Fixed order quantity (used in *lot_size* only) |
| `total_orders` | Counter of orders placed during the simulation |

| Method | Description |
|--------|-------------|
| `check_reorder() → int` | Evaluate policy; place an Order if needed; return 1 or 0 |

---

### Product

**File:** `base/product.py`

Aggregates all elements of a single SKU.

| Attribute | Description |
|-----------|-------------|
| `name` | Product identifier |
| `initial_stock` | Starting stock (copied to `Inventory`) |
| `inventory` | `Inventory` instance |
| `stock_policy` | `StockPolicy` instance |
| `demand_generator` | `DemandGenerator` instance |
| `current_stock_history` | List of end-of-day stock levels |
| `unmet_demand_history` | List of daily unmet demand values |
| `daily_info` | List of dicts with per-day metrics |

| Method | Description |
|--------|-------------|
| `update_stock(demand, current_day, orders_quantity)` | Apply demand, record metrics |

---

### ProductFamily

**File:** `base/product_family.py`

Groups multiple products for aggregated reporting.

| Method | Description |
|--------|-------------|
| `add_product(product)` | Add a product to this family |
| `calculate_aggregated_stock()` | Sum daily stock across all products |
| `calculate_min_max_aggregated_stock()` | Compute daily min/max across products |

---

### Simulator

**File:** `base/simulation.py`

Orchestrates the day-by-day simulation loop.

```
Simulator(products, days)
    └── run() → pd.DataFrame
```

The `run()` method iterates over `days` and for each day and each product:

1. Updates the inventory's `current_day`.
2. Generates demand via `demand_generator.generate()`.
3. Evaluates the stock policy via `stock_policy.check_reorder()`.
4. Applies demand to stock via `product.update_stock()`.
5. Receives any arriving orders via `inventory.receive_orders()`.
6. Records the end-of-day stock level.

Returns a `pd.DataFrame` with columns `name`, `day`, `demand`, `sales`, `unmet_demand`.

---

## Simulation flow

```
Day 0 … N-1
  ┌──────────────────────────────────────────────┐
  │  1. inventory.current_day = day              │
  │  2. demand = demand_generator.generate()     │
  │  3. orders = stock_policy.check_reorder()    │  ← may place a new Order
  │  4. product.update_stock(demand, day, orders)│  ← reduce stock, record unmet demand
  │  5. inventory.receive_orders(day)            │  ← add arrived orders to stock
  │  6. record stock level                       │
  └──────────────────────────────────────────────┘
```

> **Note:** Order arrival happens *after* demand is served on the same day, so same-day
> replenishment is not possible.

---

## Supported stock policies

### Min / Max (`type = "minmax"`)

* **Trigger:** `current_stock + pending_orders ≤ min_level`
* **Order quantity:** `max_level − (current_stock + pending_orders)`
* Replenishes to the maximum every time the position falls to or below the minimum.

### Lot size (`type = "lot_size"`)

* **Trigger:** `current_stock + pending_orders ≤ min_level`
* **Order quantity:** fixed `lot_size`
* Orders a constant quantity each time the trigger is reached.

---

## Demand distributions

| Distribution | Parameters | Best suited for |
|---|---|---|
| **Normal** | `mean`, `std_dev` | Continuous / high-volume demand with symmetric variability |
| **Poisson** | `lambda` | Low-volume, discrete, count-based demand |

When historical data is provided, `DemandGenerator.best_fit_distribution()` compares the
log-likelihood of both models and selects the better fit automatically.

---

## API endpoints

Base URL: `http://localhost:8000`

### `GET /api/health`

Health check.

**Response:**
```json
{ "status": "ok" }
```

---

### `POST /api/simulate`

Run an inventory simulation.

**Request body:**
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

**Response:**
```json
{
  "status": "success",
  "days": 90,
  "products": ["Product A"],
  "daily_records": [
    { "name": "Product A", "day": 0, "demand": 11, "sales": 11, "unmet_demand": 0 }
  ],
  "stock_history": {
    "Product A": [89, 78, ...]
  }
}
```

---

### `POST /api/upload`

Upload a CSV or Excel file with historical demand data.

**Form fields:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | `.csv`, `.xlsx`, or `.xls` |
| `column` | string | Column name containing demand values (default: `demand`) |

**Response:**
```json
{
  "filename": "history.csv",
  "column": "demand",
  "rows": 365,
  "mean": 9.87,
  "std_dev": 2.14,
  "min": 3.0,
  "max": 18.0,
  "historical_data": [10, 8, 12, ...]
}
```

The `historical_data` array can be passed directly to the `POST /api/simulate` endpoint as
the `historical_data` field of a product, instead of specifying `demand_params`.

---

## Frontend overview

| Component | Description |
|-----------|-------------|
| `FileUpload` | Drag-and-drop or click-to-select CSV/Excel upload. Shows upload statistics. |
| `SimulationForm` | Multi-product configuration form. Supports adding/removing products, choosing demand distribution and stock policy. |
| `ResultsView` | Displays: summary table (total demand, unmet demand, stockout days, service level) + line chart of stock levels + bar charts of demand vs. unmet demand per product. |

**Technology stack:** React 18, Vite 7, Recharts, Axios.

---

## Running the project

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```
