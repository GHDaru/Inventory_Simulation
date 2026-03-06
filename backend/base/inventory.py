class Inventory:
    def __init__(self, initial_stock):
        self.initial_stock = initial_stock
        self.current_stock = initial_stock
        self.pending_orders = []
        self.current_day = 0
        self.order_history = []  # Adicionando histórico de ordens

    def receive_orders(self, current_day):
        orders_to_remove = []
        for order in self.pending_orders:
            if order.is_arrived(current_day):
                self.current_stock += order.quantity
                orders_to_remove.append(order)
                print(f"Order received: {order.quantity} units")
        for order in orders_to_remove:
            self.pending_orders.remove(order)

    def update_stock(self, demand):
        if demand > self.current_stock:
            unmet_demand = demand - self.current_stock
            self.current_stock = 0
            return unmet_demand
        else:
            self.current_stock -= demand
            return 0

    def pending_order_quantity(self):
        return sum(order.quantity for order in self.pending_orders)

    def place_order(self, order):
        self.pending_orders.append(order)
        # Adiciona a ordem ao histórico como JSON no momento da inserção
        self.order_history.append({
            'id': order.id,
            'product': order.product.name,
            'quantity': order.quantity,
            'arrival_day': order.arrival_day,
            'status': 'placed'
        })
