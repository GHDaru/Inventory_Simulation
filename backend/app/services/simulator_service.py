import sys
import os

# Ensure the backend root is on the path so that `base` is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from base.product import Product
from base.simulation import Simulator
from app.models.simulation_models import SimulationRequest


def build_product(product_cfg) -> Product:
    """Instantiate a Product from a ProductConfig."""
    policy_data = product_cfg.stock_policy_params.model_dump()

    product = Product(
        name=product_cfg.name,
        initial_stock=product_cfg.initial_stock,
        stock_policy_params=policy_data,
        demand_params=(
            product_cfg.demand_params.model_dump() if product_cfg.demand_params else None
        ),
        historical_data=product_cfg.historical_data,
    )
    return product


def run_simulation(request: SimulationRequest) -> dict:
    """
    Execute the inventory simulation and return a structured result dict.
    """
    products = [build_product(p) for p in request.products]

    simulator = Simulator(products=products, days=request.days)
    df_daily = simulator.run()

    return {
        "status": "success",
        "days": request.days,
        "products": [p.name for p in products],
        "daily_records": df_daily.to_dict(orient="records"),
        "stock_history": simulator.stock_history,
    }
