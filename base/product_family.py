class ProductFamily:
    def __init__(self, name):
        """
        Inicializa a classe ProductFamily.

        Args:
            name (str): Nome da família de produtos.
        """
        self.name = name
        self.products = []
        self.stock_history = []
        self.min_stock_history = []
        self.max_stock_history = []

    def add_product(self, product):
        """
        Adiciona um produto à família.

        Args:
            product (Product): Produto a ser adicionado.
        """
        self.products.append(product)

    def calculate_aggregated_stock(self):
        """
        Calcula o estoque agregado de todos os produtos na família.
        """
        num_days = len(self.products[0].current_stock_history)
        self.stock_history = [sum(product.current_stock_history[day] for product in self.products) for day in range(num_days)]

    def calculate_min_max_aggregated_stock(self):
        """
        Calcula os estoques mínimo e máximo agregados de todos os produtos na família.
        """
        num_days = len(self.products[0].current_stock_history)
        self.min_stock_history = [min(product.current_stock_history[day] for product in self.products) for day in range(num_days)]
        self.max_stock_history = [max(product.current_stock_history[day] for product in self.products) for day in range(num_days)]