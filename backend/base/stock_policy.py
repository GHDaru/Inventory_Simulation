from .order import Order
class StockPolicy:
    def __init__(self, product, type, min_level=None, max_level=None, lead_time=None, lot_size=None):
        """
        Inicializa a classe StockPolicy.

        Args:
            product (Product): O produto ao qual esta política se aplica.
            type (str): Tipo de política de estoque ('minmax' ou 'lot_size').
            min_level (int, optional): Nível mínimo de estoque (ponto de pedido).
            max_level (int, optional): Nível máximo de estoque.
            lead_time (int, optional): Tempo de reposição (dias).
            lot_size (int, optional): Tamanho do lote para reposição.
        """
        self.product = product
        self.type = type
        self.min_level = min_level
        self.max_level = max_level
        self.lead_time = lead_time
        self.lot_size = lot_size
        self.total_orders = 0

    def check_reorder(self):
        """
        Verifica se um novo pedido de reposição deve ser feito.
        """
        total_stock = self.product.inventory.current_stock + self.product.inventory.pending_order_quantity()
        orders_quantity = 0

        if self.type == 'minmax':
            if total_stock <= self.min_level:
                order_quantity = self.max_level - total_stock
                order = Order(self.product, order_quantity, self.product.inventory.current_day + self.lead_time)
                self.product.inventory.place_order(order)
                self.total_orders += 1
                orders_quantity += 1
                print(f"Order placed for {self.product.name}: {order_quantity} units, arriving in {self.lead_time} days")
        if self.type == 'lot_size':
            if total_stock <= self.min_level:
                order_quantity = self.lot_size
                order = Order(self.product, order_quantity, self.product.inventory.current_day + self.lead_time)
                self.product.inventory.place_order(order)
                self.total_orders += 1
                orders_quantity += 1
                print(f"Order placed for {self.product.name}: {order_quantity} units, arriving in {self.lead_time} days")

        return orders_quantity
