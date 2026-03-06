# Inventory Simulation — Frontend

React application (Vite) for configuring, running, and visualising inventory simulations.

## Features

* **SimulationForm** — configure simulation days, products, demand distributions, and stock replenishment policies.
* **FileUpload** — upload a CSV or Excel file with historical demand data; the simulator will automatically fit the best statistical distribution.
* **ResultsView** — interactive charts (stock levels, demand vs. unmet demand) and a summary table (service level, stockout days).

## Quick start

```bash
# From the frontend/ directory:
npm install
npm run dev
```

The app will be available at <http://localhost:5173>.  
Make sure the backend is running at <http://localhost:8000> (or set `VITE_API_URL` env var).

## Project layout

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # Axios API client
│   ├── components/
│   │   ├── FileUpload.jsx      # Historical data upload
│   │   ├── SimulationForm.jsx  # Simulation configuration form
│   │   └── ResultsView.jsx     # Charts and summary table
│   ├── App.jsx
│   └── main.jsx
├── vite.config.js
└── package.json
```

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend base URL |
