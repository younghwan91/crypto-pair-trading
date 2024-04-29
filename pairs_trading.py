import os
import numpy as np
import pickle
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.stattools import adfuller
from pykalman import KalmanFilter
from config import CONFIG
import matplotlib.pyplot as plt

TIME_INTERVAL = CONFIG["INTERVAL"]
FOLDER_NAME = CONFIG["FOLDER_NAME"]
QUOTE_COIN = CONFIG["QUOTE_COIN"]
TRAIN_RATIO = CONFIG["TRAIN_RATIO"]
DIRECTORY = f'D:\crypto_historical\{FOLDER_NAME}\{TIME_INTERVAL}'

class PairsTrading():
    def __init__(self, asset_pair):
        self.asset_pair = asset_pair 
        
    def calculate_initial_params(self, log_price_1, log_price_2):
        X = sm.add_constant(log_price_2) # y1t = gamma*y2t + c
        model = sm.OLS(log_price_1, X)
        results = model.fit()

        return results.params.iloc[1], results.params.iloc[0]

    def calculate_spread(self, log_price_1, log_price_2, option):
        train_length = int(len(log_price_1)*TRAIN_RATIO)
        log_price_1_train = log_price_1[:train_length]
        log_price_2_train = log_price_2[:train_length]

        init_hedge_ratio, init_intercept = self.calculate_initial_params(log_price_1_train, log_price_2_train)

        if option == 'kalman':
            X = log_price_2.values.reshape(-1, 1)
            y = log_price_1.values.reshape(-1, 1)
            delta = 1e-5
            trans_cov = delta / (1 - delta) * np.eye(2)
            obs_cov = 10
            obs_mat = sm.add_constant(X, prepend=False)[:, np.newaxis]

            kf = KalmanFilter(n_dim_obs=1, n_dim_state=2,
                            initial_state_mean=np.array([init_hedge_ratio, init_intercept]),
                            initial_state_covariance=np.array([[1, 0], 
                                                               [0, 1]]),
                            transition_matrices=np.eye(2),
                            observation_matrices=obs_mat,
                            observation_covariance=obs_cov,
                            transition_covariance=trans_cov)
            
            # kf = kf.em(y, n_iter=5)
            state_means, _ = kf.filter(y)
            # state_means, _ = kf.smooth(y)
            self.hedge_ratio = state_means[:, 0]
            self.intercept = state_means[:, 1]

        else:
            self.hedge_ratio = init_hedge_ratio
            self.intercept = init_intercept
        
        spread = log_price_1.squeeze() - (self.hedge_ratio*log_price_2.squeeze() + self.intercept)

        return spread

    def load_data(self, option = 'ols'):
        asset1, asset2 = self.asset_pair
        asset1_path = os.path.join(DIRECTORY, f"{asset1}{QUOTE_COIN}.pkl")
        asset2_path = os.path.join(DIRECTORY, f"{asset2}{QUOTE_COIN}.pkl")

        with open(asset1_path, "rb") as f:
            asset1_data = pickle.load(f)
        with open(asset2_path, "rb") as f:
            asset2_data = pickle.load(f)

        price_1 = asset1_data[['Close']]
        price_2 = asset2_data[['Close']]

        log_price_1 = np.log(price_1)
        log_price_2 = np.log(price_2)

        spread = self.calculate_spread(log_price_1, log_price_2, option)

        merged_data = pd.merge(price_1, price_2, left_index=True, right_index=True, suffixes=(f"_{asset1}", f"_{asset2}"))
        data = pd.concat([spread, merged_data], axis= 1)
        data.rename(columns={data.columns[0]: 'spread'}, inplace=True)

        return data

if __name__ == "__main__":
    pt = PairsTrading(asset_pair=('XLM', 'IOTA'))

    data = pt.load_data(option='kalman')
    plt.subplot(3, 1, 1)
    plt.plot(data['spread'])
    plt.subplot(3, 1, 2)
    plt.plot(pt.hedge_ratio)
    plt.subplot(3, 1, 3)
    plt.plot(pt.intercept)
    
    plt.tight_layout()
    plt.show()