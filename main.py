import random
import sys
import time
from typing import List

import requests
from bs4 import BeautifulSoup, ResultSet
from prettytable import PrettyTable

try:
    from win10toast import ToastNotifier
except ImportError:
    pass

from user_agents import CHROME_USER_AGENTS

STOCK_TARGETS = {
    "ČEZ, A.S.": {"purchase_price": 399, "target_price": 540},
    "ERSTE GROUP BANK AG": {"purchase_price": 554, "target_price": 800},
    "KOMERČNÍ BANKA": {"purchase_price": 507, "target_price": 800},
    "MONETA MONEY BANK": {"purchase_price": 55.25, "target_price": 80},
    "PHILIP MORRIS ČR": {"purchase_price": 13400, "target_price": 15000},
    "VIG": {"purchase_price": 445, "target_price": 600},
  }
CHECK_IF_TARGET_HIT = False


def get_rm_system_stocks_items() -> ResultSet:
    response = requests.get("https://www.rmsystem.cz/kurzy-online/akcie/easyclick",
                            headers={"User-Agent": random.choice(CHROME_USER_AGENTS)})
    html = response.text
    soup = BeautifulSoup(html, "lxml")
    stocks = soup.select("table.tbl1 tr")
    return stocks


def get_stocks_prices(stocks_items: ResultSet) -> List[tuple]:
    stock_pairs = []
    for stock_item in stocks_items[1:]:
        stock_name = stock_item.td.text
        try:
            target_price = STOCK_TARGETS[stock_name]["target_price"]
            current_stock_price = stock_item.td.next_sibling.text.replace(",", ".").replace(" ", "")
            cleaned_current_price = int(float(current_stock_price))
            stock_pairs.append((stock_name, cleaned_current_price, target_price))
        except KeyError:
            continue
    return stock_pairs


def show_notification(watched_stocks: List[tuple]):
    toaster = ToastNotifier()
    stocks_data = filter_watched_stocks(watched_stocks)
    for stock_data in stocks_data:
        toaster.show_toast(
            "Stock Price Notifier",
            stock_data,
            # icon for personal use only, see
            # https://www.pngitem.com/middle/obimbx_stocks-market-icon-stock-exchanges-icon-hd-png/
            icon_path="stock_icon.ico",
            duration=5,
            threaded=True
        )
        while toaster.notification_active():
            time.sleep(0.1)


def filter_watched_stocks(stocks: List[tuple]) -> List[str]:
    stocks_data = []
    for stock_item in stocks:
        name, current_price, target = stock_item
        purchase_price = STOCK_TARGETS[name]["purchase_price"]
        if CHECK_IF_TARGET_HIT is True:
            if current_price / target >= 1:
                stocks_data.append(f"{name}: {purchase_price}/Now: {current_price}/Target: {target}")
        else:
            stocks_data.append(f"{name}: {purchase_price}/Now: {current_price}/Target: {target}")
    return stocks_data


def print_pretty_table(watched_stocks: list[tuple]) -> None:
    table = PrettyTable(['Stock', 'Current Price', 'Target Price'])

    for stock in watched_stocks:
        table.add_row(stock)

    print(table)


if __name__ == "__main__":
    stocks_items = get_rm_system_stocks_items()
    watched_stocks = get_stocks_prices(stocks_items)
    if sys.platform == 'win32':
        show_notification(watched_stocks)
    else:
        print_pretty_table(watched_stocks)
