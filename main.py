from binance_downloader import BinanceDownloader
from pair_search import CryptoPairSelector
from config import CONFIG

ENABLE_DOWNLOAD = 0

def find_cointegrated_pairs(): 
    selector = CryptoPairSelector(CONFIG)
    coint_pairs, data = selector.select_trading_pairs()
    selector.plot_cointegrated_pairs(data, coint_pairs)

if __name__ == "__main__":

    if ENABLE_DOWNLOAD:
        print("Downloading data...")
        downloader = BinanceDownloader(CONFIG)
        downloader.download_data()

    find_cointegrated_pairs()