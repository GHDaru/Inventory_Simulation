import random
import numpy as np
from scipy.stats import norm, poisson

class DemandGenerator:
    def __init__(self, distribution_type, params):
        """
        Inicializa a classe DemandGenerator.

        Args:
            distribution_type (str): Tipo de distribuição ('normal' ou 'poisson').
            params (dict): Parâmetros para a distribuição.
        """
        self.distribution_type = distribution_type
        self.params = params

    def generate(self):
        """
        Gera a demanda com base na distribuição especificada.

        Returns:
            int: Quantidade demandada.
        """
        if self.distribution_type == 'normal':
            return self.normal_distribution(self.params['mean'], self.params['std_dev'])
        elif self.distribution_type == 'poisson':
            return self.poisson_distribution(self.params['lambda'])

    def normal_distribution(self, mean, std_dev):
        """
        Gera demanda baseada em uma distribuição normal.

        Args:
            mean (float): Média da distribuição.
            std_dev (float): Desvio padrão da distribuição.

        Returns:
            int: Quantidade demandada.
        """
        return max(0, int(random.gauss(mean, std_dev)))

    def poisson_distribution(self, lambda_):
        """
        Gera demanda baseada em uma distribuição Poisson.

        Args:
            lambda_ (float): Lambda da distribuição Poisson.

        Returns:
            int: Quantidade demandada.
        """
        return max(0, np.random.poisson(lambda_))

    @staticmethod
    def generate_historical_data(distribution_type, params, days):
        """
        Gera dados históricos de demanda.

        Args:
            distribution_type (str): Tipo de distribuição ('normal' ou 'poisson').
            params (dict): Parâmetros para a distribuição.
            days (int): Número de dias de dados históricos a serem gerados.

        Returns:
            list: Lista de demandas geradas para cada dia.
        """
        generator = DemandGenerator(distribution_type, params)
        return [generator.generate() for _ in range(days)]

    @staticmethod
    def calculate_distribution_parameters(historical_data, distribution_type):
        """
        Calcula os parâmetros da distribuição com base nos dados históricos.

        Args:
            historical_data (list): Lista de demandas históricas.
            distribution_type (str): Tipo de distribuição ('normal' ou 'poisson').

        Returns:
            dict: Parâmetros calculados para a distribuição.
        """
        if distribution_type == 'normal':
            mean = np.mean(historical_data)
            std_dev = np.std(historical_data)
            return {'mean': mean, 'std_dev': std_dev}
        elif distribution_type == 'poisson':
            lambda_ = np.mean(historical_data)
            return {'lambda': lambda_}

    @staticmethod
    def best_fit_distribution(historical_data):
        """
        Encontra o melhor ajuste da distribuição (entre normal e Poisson) com base nos dados históricos.

        Args:
            historical_data (list): Lista de demandas históricas.

        Returns:
            str: Tipo de distribuição que melhor se ajusta aos dados ('normal' ou 'poisson').
            dict: Parâmetros calculados para a distribuição.
        """
        # Calcular parâmetros para distribuição normal
        normal_params = DemandGenerator.calculate_distribution_parameters(historical_data, 'normal')
        normal_fit = norm(loc=normal_params['mean'], scale=normal_params['std_dev']).pdf(historical_data)
        normal_likelihood = np.sum(np.log(normal_fit))

        # Calcular parâmetros para distribuição Poisson
        poisson_params = DemandGenerator.calculate_distribution_parameters(historical_data, 'poisson')
        poisson_fit = poisson(mu=poisson_params['lambda']).pmf(historical_data)
        poisson_likelihood = np.sum(np.log(poisson_fit))

        # Comparar a verossimilhança e escolher a melhor distribuição
        if normal_likelihood > poisson_likelihood:
            return 'normal', normal_params
        else:
            return 'poisson', poisson_params