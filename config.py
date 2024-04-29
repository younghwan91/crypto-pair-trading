import datetime as dt
import os

file_path = 'D:\\binance_key.txt'
with open(file_path, 'r') as file:
    lines = file.readlines()

API_key = lines[0].strip()  # API key is on the first line
secret_key = lines[1].strip()  # Secret key is on the second line

CONFIG = {
    'API_KEY': API_key, 
    'API_SECRET': secret_key,
    "FOLDER_NAME": 'futures',
    "SAVING_DIR": 'D:\crypto_historical',
    "CSV_FILENAME": "pairs_list.csv",
    "N_COINS": 50,
    "INTERVAL": '5m',
    "START_STR": '1 day ago',
    "END_STR": dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "MAX_N_NPD": 500,
    "TRAIN_RATIO": 0.5,
    "COINT_THRESHOLD": 0.05,
    "QUOTE_COIN": 'USDT',
    "TRADING_CHARGE": 0.0004,
    "TRADAING_TAX": 0,
    "MAX_TRADE_PORTION": 0.02,
    "SHAPIRO_THRESHOLD": 0.95,
}
saving_dir = os.path.join(CONFIG["SAVING_DIR"], CONFIG["FOLDER_NAME"], CONFIG["INTERVAL"])
# add saving_dir to CONFIG
CONFIG["SAVING_DIR"] = saving_dir