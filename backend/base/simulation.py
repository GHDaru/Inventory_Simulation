import pandas as pd

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
                # Only append the most recent day's record (daily_info grows
                # cumulatively across days, so we take just the last entry).
                all_daily_info.append(product.daily_info[-1])

        # Salva o histórico de estoque em um DataFrame (sem persistir em disco)
        df = pd.DataFrame(self.stock_history)

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
