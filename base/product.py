from .demand import DemandGenerator

from .inventory import Order
import numpy as np

class Product:
    def __init__(self, name, initial_stock = 0, stock_policy_params = None, family = None, demand_params=None, historical_data=None):
        self.name = name
        self.initial_stock = initial_stock
        self.current_stock = initial_stock
        self.family = family
        self.stock_policy = StockPolicy(**stock_policy_params)
        self.demand_generator = None
        self.current_stock_history = []
        self.stockout_days = 0
        self.unmet_demand_history = []
        self.unmet_demand = 0
        self.daily_info = []  # Adding the list of dictionaries to store daily information

        if historical_data:
            distribution_type, params = DemandGenerator.best_fit_distribution(historical_data)
            self.demand_generator = DemandGenerator(distribution_type, params)
        elif demand_params:
            self.demand_generator = DemandGenerator(demand_params['distribution_type'], demand_params['params'])

    def update_stock(self, demand, current_day, orders_quantity):
        # Entradas de estoque ocorrem no final do dia        
        #demanda não atendida
        self.unmet_demand = 0 if demand <= self.current_stock else demand - self.current_stock
        #Atualiza posição de estoque
        self.current_stock = 0 if demand >= self.current_stock else self.current_stock - demand
        self.daily_info.append({
                'name':self.name,
                'day': current_day,
                'demand': demand,                
                'sales': demand,
                'unmet_demand': self.unmet_demand
                
        })               
