import os
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import pandas as pd
import matplotlib.pyplot as plt
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import matplotlib.pyplot as plt
from config import CONFIG
from pairs_trading import PairsTrading

plt.style.use('dark_background')
os.environ['KMP_DUPLICATE_LIB_OK']='True'

TRADING_CHARGE = CONFIG["TRADING_CHARGE"]
MAX_TRADE_PORTION = CONFIG["MAX_TRADE_PORTION"]

TRAIN_RATIO = CONFIG["TRAIN_RATIO"]

class TradingEnv(gym.Env):
    """Custom Environment that follows gym interface."""

    def __init__(self, asset_pair, formation_window_size, 
                 trading_window_size, initial_balance, hedge_ratio_option):
        super().__init__()

        self.asset_pair = asset_pair 
        self.initial_balance = initial_balance
        self.formation_window_size = formation_window_size
        self.trading_window_size = trading_window_size

        # self.action_space = spaces.Box(low=0.1, high=4, shape=(1,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.observation_space = spaces.Box(low=-5, high=5, shape=(trading_window_size+1,), dtype=np.float32)                           

        pt = PairsTrading(asset_pair=asset_pair)

        data = pt.load_data(option= hedge_ratio_option)
        self.spread = data['spread'].values
        self.price1 = data[f'Close_{asset_pair[0]}'].values
        self.price2 = data[f'Close_{asset_pair[1]}'].values
        self.hedge_ratio = pt.hedge_ratio
        self.intercept = pt.intercept
        self.reset()

    def reset(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
        self.balance = self.initial_balance
        self.t = self.trading_window_size-1
        self.done = False
        self.reward = 0
        self.position = 0
        self.prev_position = 0

        self.num_open_pos = 0
        self.num_close_pos = 0
        self.num_hold_pos = 0
        self.num_assets = [0, 0]        
        self.open_pos_prices = [0, 0]  
        self.close_pos_prices = [0, 0] 
        return self._get_observation(), None

    def step(self, action):

        current_spread = self.spread[self.t]
        trading_spread = self.spread[self.t - self.trading_window_size + 1:self.t + 1]
        
        std_trading_window = np.std(trading_spread)
        mean_trading_window = np.mean(trading_spread)
        z_window = (trading_spread - mean_trading_window)/std_trading_window
        z_val = (current_spread - mean_trading_window)/std_trading_window

        self.bet_size = self.balance * MAX_TRADE_PORTION
        self.prev_t = self.t-1
        self.prev_position = self.position       
        self.reward = 0

        if self.position == 0:
            if action == 1:
                direction = -1 if z_val > 0 else 1
                self._open_position(direction)
            elif action == 0:
                self.num_hold_pos += 1
        elif (self.position == 1 and z_val > 0) or (self.position == -1 and z_val < 0):
            self._close_position()
        else:
            if action == 1:
                self._close_position()
            elif action == 0:
                self.num_hold_pos += 1

        reward = self._get_reward()
        self.t += 1
        observation = self._get_observation()
        terminated = self._is_done()

        return observation, reward, terminated, {}, {}

    def _open_position(self, direction):
        self.position = direction
        self.num_open_pos += 1
        self.open_pos_prices = [self.price1[self.t], self.price2[self.t]]  # Save the open prices

        self.bet_amount_1 = self.bet_size/(1+self.hedge_ratio[self.t])
        self.bet_amount_2 = self.bet_size - self.bet_amount_1
        self.num_assets[0] = direction*self.bet_amount_1/self.price1[self.t]
        self.num_assets[1] = -1*direction*self.bet_amount_2/self.price2[self.t]

        self.reward -= TRADING_CHARGE

    def _close_position(self):
        self.num_close_pos += 1
        self.close_pos_prices = [self.price1[self.t], self.price2[self.t]]  # Save the close prices
        self.num_assets = [0, 0]
        self.position = 0

        self.reward -= TRADING_CHARGE

    def _get_observation(self):
        observation = np.concatenate([
                    self.spread[self.T - self.trading_window_size+1:self.t+1], 
                    [self.position]
                    ])
        return observation

    def _is_done(self):
        return self.t >= len(self.spread)

    def _get_reward(self):
            
        if self.prev_position == 0:
            reward = self.reward

        else:
            # the difference between the current spread and the spread when the position was opened
            prev_y2 = self.hedge_ratio[self.prev_t]*np.log(self.price2[self.prev_t]) + self.intercept[self.prev_t]
            prev_y1 = np.log(self.price1[self.prev_t])
            prev_spread = prev_y1 - prev_y2

            current_y2 = self.hedge_ratio[self.t]*np.log(self.price2[self.t]) + self.intercept[self.t]
            current_y1 = np.log(self.price1[self.t])
            current_spread = current_y1 - current_y2

            reward = self.reward + (current_spread - prev_spread)*self.prev_position

        return reward

    def render(self):
        pass

if __name__ == "__main__":

    mode = 1
    formation_window_size = 50
    trading_window_size = 50
    initial_balance = 10000
    hedge_ratio_option = 'kalman'
    total_timesteps = 100000
    
    # Initialize the environment
    env = TradingEnv(asset_pair=['XLM', 'IOTA'], 
                    formation_window_size= formation_window_size,
                    trading_window_size= trading_window_size, 
                    initial_balance= initial_balance, 
                    hedge_ratio_option= hedge_ratio_option)

    env = DummyVecEnv([lambda: env])
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps= total_timesteps)
    model.save("ppo_trading")

    model = PPO.load("ppo_trading")
    obs = env.reset()
    # Lists to store rewards
    rewards = []
    positions = []
    actions = []

    done = False
    total_reward = 0
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, done, _ = env.step(action)
        positions.append(obs[0][-1])
        actions.append(action[0])
        rewards.append(reward+1)
        total_reward += reward

    # Plot the cumulative rewards
    plt.subplot(3, 1, 1)
    plt.plot(range(len(rewards)), np.cumprod(rewards), label='Cumulative Reward', color='lime')
    plt.xlabel('Time Step')
    plt.ylabel('Cumulative Reward')
    plt.legend()

    plt.subplot(3, 1, 2)
    plt.plot(range(len(positions)), positions, label='Position', color = 'lime')
    plt.xlabel('Time Step')
    plt.ylabel('Position')
    plt.legend()

    plt.subplot(3, 1, 3)
    plt.plot(range(len(actions)), actions, label='Threshold', color = 'lime')
    plt.xlabel('Time Step')
    plt.ylabel('Threshold')
    plt.legend()

    plt.show()