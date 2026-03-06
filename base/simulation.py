import pandas as pd
from .visualization import plot_stock_levels, plot_family_stock_levels, save_stock_history, plot_unmet_demand, plot_stockout_days

class Simulator:
    def __init__(self, products, days):
        """
        Inicializa a classe Simulator.

        Args:
            products (list[Product]): Lista de produtos a serem gerenciados pelo inventário.
            days (int): Número de dias para a simulação.
        """
        self.products = products
        self.days = days
        self.stock_history = {product.name: [] for product in products}

    def run(self):
        """
        Executa a simulação por um número definido de dias.
        """
        all_daily_info = []

        for day in range(self.days):
            for product in self.products:
                product.inventory.current_day = day
                demand = product.demand_generator.generate()
                orders_quantity = product.stock_policy.check_reorder()
                product.update_stock(demand, day, orders_quantity)
                product.inventory.receive_orders(day)
                self.stock_history[product.name].append(product.inventory.current_stock)
                product.current_stock_history.append(product.inventory.current_stock)
                all_daily_info.extend(product.daily_info)

        # Plota os níveis de estoque dos produtos ao longo do tempo
        # plot_stock_levels(self.stock_history)
        # Salva o histórico de estoque em um DataFrame e arquivos
        df = save_stock_history(self.stock_history)

        # Calcula e plota os níveis de estoque agregados para cada família de produtos
        # for family in set(product.family for product in self.products):
        #     family.calculate_aggregated_stock()
        #     family.calculate_min_max_aggregated_stock()
        #     plot_family_stock_levels(family)

        # Plota a demanda não atendida e os dias de ruptura de estoque para cada produto
        # for product in self.products:
        #     plot_unmet_demand(product)
        #     plot_stockout_days(product)

        # Criar o DataFrame com as informações diárias
        df_daily_info = pd.DataFrame(all_daily_info)
        return df_daily_info
