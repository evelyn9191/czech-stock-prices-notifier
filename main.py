import datetime
import random
import sys
import time
from typing import List

import requests
from bs4 import BeautifulSoup, ResultSet, Tag
from prettytable import PrettyTable

try:
    from win10toast import ToastNotifier
except ImportError:
    pass

from user_agents import CHROME_USER_AGENTS

STOCK_TARGETS = {
    "ČEZ, A.S.": {"purchase_price": 399, "target_price": 540, "purchased": 2020},
    "ERSTE GROUP BANK AG": {"purchase_price": 554, "target_price": 800, "sell_price": 950, "purchased": 2020, "sold": 2024},
    "KOMERČNÍ BANKA": {"purchase_price": 507, "target_price": 800, "sell_price": 812, "purchased": 2020, "sold": 2024},
    "MONETA MONEY BANK": {"purchase_price": 55.25, "target_price": 80, "sell_price": 100, "purchased": 2020, "sold": 2024},
    "PHILIP MORRIS ČR": {"purchase_price": 13400, "target_price": 15000, "purchased": 2020},
    "VIG": {"purchase_price": 445, "target_price": 600, "sell_price": 680, "purchased": 2020, "sold": 2024},
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
            stock_data = STOCK_TARGETS[stock_name]
            target_price = stock_data["target_price"]
            buying_price = stock_data["purchase_price"]
            sell_price = stock_data.get("sell_price", "")
            cleaned_current_price = get_cleaned_current_price(stock_item)
            gain = get_avg_yearly_gain(stock_data, cleaned_current_price, sell_price, buying_price, stock_name)
            stock_pairs.append((stock_name, buying_price, cleaned_current_price, target_price, sell_price, gain))
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
        name, _, current_price, target, _, difference = stock_item
        purchase_price = STOCK_TARGETS[name]["purchase_price"]
        if CHECK_IF_TARGET_HIT is True:
            if current_price / target >= 1:
                stocks_data.append(f"{name}: {purchase_price}/Now: {current_price}/Target: {target}/Gain: {difference}")
        else:
            stocks_data.append(f"{name}: {purchase_price}/Now: {current_price}/Target: {target}/Gain: {difference}")
    return stocks_data


def print_pretty_table(watched_stocks: list[tuple]) -> None:
    table = PrettyTable(["Stock", "Buying Price", "Current Price", "Target Price", "Sell Price", "Avg yearly gain in %", "Target hit"])

    watched_stocks.sort(key=lambda x: x[5], reverse=True)

    for stock_items in watched_stocks:
        full_info = [stock_info for stock_info in stock_items]
        hit_target_price = hit_target(full_info)
        full_info.append(hit_target_price)
        table.add_row(full_info)

    print(table)


def get_cleaned_current_price(stock_item: Tag) -> int:
    current_stock_price = stock_item.td.next_sibling.text.replace(",", ".").replace(" ", "")
    return int(float(current_stock_price))


def get_avg_yearly_gain(stock_data: dict, cleaned_current_price: int, sell_price: int | None, buying_price: int, stock_name: str) -> float:
    if sell_price:
        years_held = stock_data["sold"] - stock_data["purchased"]
        final_price = sell_price
    else:
        years_held = datetime.datetime.today().year - stock_data["purchased"]
        final_price = cleaned_current_price

    total_gain = (final_price - buying_price) / stock_data["purchase_price"] * 100
    avg_yearly_gain = total_gain / years_held
    return round(avg_yearly_gain, 1)


def hit_target(full_info: list) -> str:
    if full_info[4]:
        return "Y" if full_info[4] >= full_info[3] else "N"
    return "Y" if full_info[2] > full_info[3] else "N"


if __name__ == "__main__":
    stocks_items = get_rm_system_stocks_items()
    watched_stocks = get_stocks_prices(stocks_items)

    if sys.platform == 'win32':
        show_notification(watched_stocks)

    print_pretty_table(watched_stocks)
