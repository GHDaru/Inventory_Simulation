import matplotlib.pyplot as plt
import pandas as pd

def plot_stock_levels(stock_history):
    """
    Plota os níveis de estoque dos produtos ao longo do tempo.

    Args:
        stock_history (dict): Dicionário contendo o histórico de níveis de estoque para cada produto.
    """
    plt.figure(figsize=(12, 6))
    for product_name, levels in stock_history.items():
        plt.plot(levels, label=product_name)
    plt.xlabel('Day')
    plt.ylabel('Stock Level')
    plt.title('Stock Levels Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_family_stock_levels(family):
    """
    Plota os níveis de estoque agregados de uma família de produtos ao longo do tempo.

    Args:
        family (ProductFamily): Instância da classe ProductFamily cujos níveis de estoque agregados serão plotados.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(family.stock_history, label='Aggregated Stock')
    plt.plot(family.min_stock_history, label='Min Stock', linestyle='--')
    plt.plot(family.max_stock_history, label='Max Stock', linestyle='--')
    plt.xlabel('Day')
    plt.ylabel('Stock Level')
    plt.title(f'{family.name} Stock Levels Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

def save_stock_history(stock_history, file_format='csv', file_name='stock_history'):
    """
    Salva o histórico de níveis de estoque em um arquivo CSV ou Excel.

    Args:
        stock_history (dict): Dicionário contendo o histórico de níveis de estoque para cada produto.
        file_format (str): Formato do arquivo ('csv' ou 'excel').
        file_name (str): Nome do arquivo (sem extensão).

    Returns:
        pd.DataFrame: DataFrame contendo o histórico de níveis de estoque.
    """
    df = pd.DataFrame(stock_history)
    if file_format == 'csv':
        df.to_csv(f'{file_name}.csv', index=False)
    elif file_format == 'excel':
        df.to_excel(f'{file_name}.xlsx', index=False)
    return df

def plot_unmet_demand(product):
    """
    Plota a demanda não atendida ao longo do tempo para um produto específico.

    Args:
        product (Product): Instância da classe Product cujos dados de demanda não atendida serão plotados.
    """
    plt.figure(figsize=(12, 6))
    plt.plot(product.unmet_demand_history, label=f'Unmet Demand for {product.name}')
    plt.xlabel('Day')
    plt.ylabel('Unmet Demand')
    plt.title(f'Unmet Demand for {product.name} Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()

def plot_stockout_days(product):
    """
    Plota os dias de ruptura de estoque ao longo do tempo para um produto específico.

    Args:
        product (Product): Instância da classe Product cujos dados de dias de ruptura de estoque serão plotados.
    """
    stockout_days = [1 if demand > 0 else 0 for demand in product.unmet_demand_history]
    plt.figure(figsize=(12, 6))
    plt.plot(stockout_days, label=f'Stockout Days for {product.name}')
    plt.xlabel('Day')
    plt.ylabel('Stockout')
    plt.title(f'Stockout Days for {product.name} Over Time')
    plt.legend()
    plt.grid(True)
    plt.show()
