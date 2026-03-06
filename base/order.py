import uuid
import json

class Order:
    def __init__(self, product, quantity, arrival_day):
        """
        Inicializa a classe Order.

        Args:
            product (Product): O produto que está sendo pedido.
            quantity (int): Quantidade do produto no pedido.
            arrival_day (int): Dia de chegada do pedido.
        """
        self.id = str(uuid.uuid4())  # Atribui um ID único à ordem
        self.product = product
        self.quantity = quantity
        self.arrival_day = arrival_day

    def is_arrived(self, current_day):
        """
        Verifica se o pedido chegou no dia atual.

        Args:
            current_day (int): O dia atual da simulação.

        Returns:
            bool: True se o pedido chegou, False caso contrário.
        """
        return current_day >= self.arrival_day

    def to_dict(self):
        """
        Retorna os detalhes da ordem como um dicionário.

        Returns:
            dict: Detalhes da ordem.
        """
        return {
            'id': self.id,
            'product': self.product.name,
            'quantity': self.quantity,
            'arrival_day': self.arrival_day
        }
