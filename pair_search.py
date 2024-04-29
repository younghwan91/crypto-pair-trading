import os
import csv
import itertools
import numpy as np
import pandas as pd
from binance.client import Client
from statsmodels.tsa.stattools import coint
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import tqdm
import scipy.stats as stats
from scipy.optimize import minimize

plt.style.use('dark_background')

class CryptoPairSelector:
    def __init__(self, config):
        self.client = Client(config['API_KEY'], config['API_SECRET'])
        self.directory = config['SAVING_DIR']
        self.interval = config['INTERVAL']  # Assuming you want to use the interval from the config
        self.n_coins = config['N_COINS']
        self.max_n_npd = config['MAX_N_NPD']
        self.train_ratio = config['TRAIN_RATIO']
        self.csv_filename = config['CSV_FILENAME']
        self.coint_threshold = config['COINT_THRESHOLD']
        self.trading_charge = config['TRADING_CHARGE']
        self.shapiro_threshold = config['SHAPIRO_THRESHOLD']

    def load_selected_trading_coins(self):
        print(f"Loading trading coins from {self.csv_filename}...")
        with open(os.path.join(self.directory, self.csv_filename), 'r') as file:
            reader = csv.reader(file)
            coins = [coin for row in reader for coin in row[:self.n_coins]]
            assert len(coins) >= self.n_coins, "N_COINS is greater than the number of trading coins"
            return coins

    def find_valid_coins(self, data):
        valid_coins = []
        for coin, df in data.items():
            coin_diff = np.log(df['Close']).diff().dropna()
            coin_diff = coin_diff[coin_diff != 0]
            if len(coin_diff) == 0:
                print(f'No price difference for {coin}')
                continue
            else:
                adf_test = adfuller(coin_diff)
                if adf_test[1] < 0.01:
                    valid_coins.append(coin)
                else:
                    print(f'{coin} is not integrated of order 1')

        print(f'Number of coins integrated of order 1: {len(valid_coins)}')

        return valid_coins

    def calculate_normalized_close_prices(self, data):

        normalized_prices = {}
        for coin, df in data.items():
            prices = df['Close']
            normalized_prices[coin] = prices / prices.iloc[0]
        return normalized_prices

    def calculate_npd(self, normalized_prices, pairs):

        pairs_npd = []
        for coin1, coin2 in pairs:
            common_indices = normalized_prices[coin1].index.intersection(normalized_prices[coin2].index)
            prices1 = normalized_prices[coin1].loc[common_indices]
            prices2 = normalized_prices[coin2].loc[common_indices]
            split_index = int(len(prices1) * self.train_ratio)
            npd = np.sum((prices1[:split_index] - prices2[:split_index]) ** 2)
            pairs_npd.append((coin1, coin2, npd))
        return pairs_npd

    def find_cointegrated_pairs(self, selected_pairs, data):

        coint_pairs = []
        for coin1, coin2 in tqdm.tqdm(selected_pairs):
            common_indices = data[coin1].index.intersection(data[coin2].index)
            prices1 = np.log(data[coin1].loc[common_indices]['Close'])
            prices2 = np.log(data[coin2].loc[common_indices]['Close'])
            split_index = int(len(prices1) * self.train_ratio)
            try:
                result_train = coint(prices1[:split_index], prices2[:split_index])
            except:
                print(f"Error in cointegration test for pair: {(coin1, coin2)}")
                print(split_index, len(prices1), len(prices2))            
            try:
                result_all = coint(prices1, prices2)
            except:
                print(f"Error in cointegration test for pair: {(coin1, coin2)}")
                print(split_index, len(prices1), len(prices2))

            if result_train[1] < self.coint_threshold and result_all[1] < self.coint_threshold :  # Using a common p-value threshold
                coint_pairs.append((coin1, coin2))
            
        return coint_pairs

    def select_trading_pairs(self):

        print(">>> Loading trading coins...")
        trading_pairs_usdt = self.load_selected_trading_coins()
        data = {pair: pd.read_pickle(os.path.join(self.directory, f'{pair}.pkl')) for pair in trading_pairs_usdt}

        print(">>> Finding valid coins...")
        valid_coins = self.find_valid_coins(data)
        trading_pairs_usdt = [coin for coin in trading_pairs_usdt if coin in valid_coins]
        data = {coin: df for coin, df in data.items() if coin in valid_coins}
        
        print(">>> Calculating normalized prices...")
        all_pairs = list(itertools.combinations(trading_pairs_usdt, 2))
        normalized_prices = self.calculate_normalized_close_prices(data)

        print(">>> Calculating NPD with train ratio...")
        npd_pairs = self.calculate_npd(normalized_prices, all_pairs)
        npd_pairs.sort(key=lambda x: x[2])

        if self.max_n_npd is None:
            selected_npd = [pair[:2] for pair in npd_pairs]
        else:
            selected_npd = [pair[:2] for pair in npd_pairs[:self.max_n_npd]]

        print(">>> Finding cointegrated pairs...")
        coint_pairs = self.find_cointegrated_pairs(selected_npd, data)

        print(f"Length of selected NPD pairs for cointegration testing: {len(selected_npd)} / {len(all_pairs)}")
        print(f"Length of cointegrated pairs: {len(coint_pairs)} / {len(selected_npd)}")
        print(f"Cointegrated pairs: {coint_pairs}")

        return coint_pairs, data
    
    def generate_signal(self, z_spread, threshold_long, threshold_short):
        # Initialize signal with 0
        signal = pd.Series(0, index=z_spread.index)

        # initial signal
        if z_spread[0] > threshold_long:
            signal[0] = -1
        elif z_spread[0] < threshold_short:
            signal[0] = 1


        return signal
    
    def plot_cointegrated_pairs(self, data, cointegrated_pairs):
        print("Plotting cointegrated pairs...")

        # sort the cointegrated pairs by the product of shapiro test and spread std
        # cointegrated_pairs = sorted(cointegrated_pairs, key=lambda x: stats.shapiro(data[x[0]]['Close'] - data[x[1]]['Close'])[0]*np.std(data[x[0]]['Close'] - data[x[1]]['Close']), reverse=True)

        for coin1, coin2 in cointegrated_pairs:
            common_indices = data[coin1].index.intersection(data[coin2].index)
            prices1 = np.log(data[coin1].loc[common_indices]['Close'])
            prices2 = np.log(data[coin2].loc[common_indices]['Close'])
            result_all = coint(prices1, prices2)
            split_index = int(len(prices1) * self.train_ratio)
            result_train = coint(prices1[:split_index], prices2[:split_index])

            # Perform linear regression to find the hedge ratio
            hedge_ratio, intercept = np.polyfit(prices1[:split_index], prices2[:split_index], 1)
            spread = prices2 - (hedge_ratio * prices1 + intercept)
            shapiro_test = stats.shapiro(spread)
            print(f'Shapiro test: {shapiro_test}')
            if shapiro_test[0] < self.shapiro_threshold:
                print(f'Spread is not normally distributed for pair: {coin1} and {coin2}')
                continue
            '''
            mean_train != mean_all
            std_train != std_all
            '''

            # Z-score the spread
            z_spread = (spread - spread.mean()) / spread.std()
            T = len(spread)
            f = lambda s0: -(s0-(self.trading_charge*2))*T*(1-stats.norm.cdf(s0, spread.mean(), spread.std()))
            x = np.linspace(0, 0.05, 100)
            f_values = [f(s0) for s0 in x]
            s0 = x[np.argmin(f_values)]

            print(spread.mean(), spread.std())
            lower_bound = -(s0-spread.mean())/spread.std()
            upper_bound = (s0-spread.mean())/spread.std()
            print(lower_bound, upper_bound)
            print(z_spread.head())
            signal = self.generate_signal(z_spread, lower_bound, upper_bound)

            plt.figure(figsize=(20, 10))
            row_size = 4
            plt.subplot(row_size, 1, 1)
            plt.plot(z_spread)
            plt.plot(z_spread.index, signal)
            plt.axvline(z_spread.index[split_index], color='r')
            plt.axhline(upper_bound, color = 'r', linestyle='--')
            plt.axhline(lower_bound, color = 'r', linestyle='--')
            plt.axhline(0.0)
            plt.ylabel('Z-score')
            plt.title(f'{coin1} and {coin2} Z-score')
            plt.text(0.02, 0.95, f'p-value (total): {result_all[1]:.4f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')
            plt.text(0.02, 0.85, f'p-value (train): {result_train[1]:.4f}', transform=plt.gca().transAxes, fontsize=12, verticalalignment='top')
            plt.grid(True)

            plt.subplot(row_size, 1, 2)
            plt.plot(spread)
            plt.axvline(spread.index[split_index], color='r') 
            plt.axhline(upper_bound*spread.std()+spread.mean(), color = 'r', linestyle='--')
            plt.axhline(lower_bound*spread.std()+spread.mean(), color = 'r', linestyle='--')
            plt.axhline(0.0)
            plt.ylabel('Spread')
            plt.title(f'{coin1} and {coin2} and stdev: {np.std(spread):.4f}')
            plt.grid(True)

            plt.subplot(row_size, 1, 3)
            # signal at t . diff t - (t-1). 
            # signal at t impact the diff at t+1
            # Hence, signal at t times the diff.shift(-1)
            # empty return filled with zeros
            spread_return = spread.diff()
            traded_return = signal * spread_return.shift(-1) # should not the signal shift forward instead 
            traded_return.fillna(0, inplace=True)
            # cumulated_return = (1+traded_return).cumprod()*100 # compound return
            cumulated_return = (traded_return.cumsum()+1)*100 # simple return
            plt.plot(cumulated_return)
            plt.axvline(z_spread.index[split_index], color='r')
            plt.ylabel('Cumulated Return (%)')
            plt.title(f'{coin1} and {coin2} Cumulated Return')
            plt.grid(True)

            plt.subplot(row_size, 1, 4)
            plt.hist(spread, bins=100, density=True, alpha=0.6, color='g')

            # Fit a normal distribution to the data
            mu, std = stats.norm.fit(spread)

            # Plot the PDF
            xmin, xmax = plt.xlim()
            x = np.linspace(xmin, xmax, 100)
            p = stats.norm.pdf(x, mu, std)
            plt.plot(x, p, 'r', linewidth=2)

            plt.ylabel('Frequency')
            plt.title(f'{coin1} and {coin2} Spread Distribution')
            plt.grid(True)


            plt.tight_layout()
            plt.show()
