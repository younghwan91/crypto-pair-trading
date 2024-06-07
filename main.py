from config import CONFIG
from trader import CryptoTrader
from binance.client import Client
import json

ENABLE_PLOT = 0
TESTNET = 0
TRADE = 1

if TESTNET:
    api_key = 'REDACTED_BINANCE_API_KEY_0'
    api_secret = 'REDACTED_BINANCE_API_SECRET_1'
else:
    with open('binance_id.json', 'r') as file:
        config = json.load(file)
        api_key = config['api_key']
        api_secret = config['api_secret']

client = Client(api_key=api_key, api_secret=api_secret, testnet=TESTNET)
trader = CryptoTrader(client, CONFIG, ENABLE_PLOT)
trader.print_futures_balance()

if TRADE:
    trader.run_trading_cycle()
 