"""MLNK price tracker.

Polls the swap.pcash DEX pools on EOS, finds the MLNK/USDCASH pair
and sends every price change to a Telegram chat.
"""
import os
import time
import traceback

import requests
from dotenv import load_dotenv

load_dotenv()

# EOS RPC
NODE_URL = os.getenv("EOS_NODE_URL", "https://eos.greymass.com/v1/chain/get_table_rows")
DEX_CONTRACT = "swap.pcash"
TARGET_SYMBOL = os.getenv("TARGET_SYMBOL", "MLNK")
QUOTE_SYMBOL = os.getenv("QUOTE_SYMBOL", "USDCASH")
POLL_SECONDS = int(os.getenv("POLL_SECONDS", "5"))

# Telegram (set these in .env, never commit them)
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def send_to_telegram(message: str) -> None:
    if not BOT_TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": message}, timeout=10)
    except requests.RequestException as e:
        print("Telegram send failed:", e)


def get_all_pairs() -> list[dict]:
    lower_bound = 30
    upper_bound = 30
    all_pairs = []
    while True:
        payload = {
            "json": True,
            "code": DEX_CONTRACT,
            "scope": DEX_CONTRACT,
            "table": "pools",
            "lower_bound": lower_bound,
            "upper_bound": upper_bound,
            "limit": 100,
        }
        r = requests.post(NODE_URL, json=payload, timeout=10).json()
        rows = r.get("rows", [])
        if not rows:
            break
        all_pairs.extend(rows)
        if not r.get("more"):
            break
        lower_bound = r.get("next_key", "")
    return all_pairs


def find_price() -> tuple[float | None, str | None]:
    for pair in get_all_pairs():
        amount0, sym0 = pair["token1"]["quantity"].split(" ")
        amount1, sym1 = pair["token2"]["quantity"].split(" ")
        if {sym0, sym1} == {TARGET_SYMBOL, QUOTE_SYMBOL}:
            amount0, amount1 = float(amount0), float(amount1)
            if sym1 == TARGET_SYMBOL:
                return amount0 / amount1, sym0
            return amount1 / amount0, sym1
    return None, None


def main() -> None:
    last_price = None
    while True:
        try:
            price, quote = find_price()
            if price is None:
                print(f"{TARGET_SYMBOL} pair not found on {DEX_CONTRACT}")
            else:
                price = round(price, 8)
                if price != last_price:
                    if last_price is None:
                        msg = f"1 {TARGET_SYMBOL} = {price:.8f} {quote} (initial)"
                    else:
                        change = (price - last_price) / last_price * 100
                        arrow = "📈" if price > last_price else "📉"
                        msg = f"{arrow} 1 {TARGET_SYMBOL} = {price:.8f} {quote} ({change:+.4f}%)"
                    last_price = price
                    print(msg)
                    send_to_telegram(msg)
        except Exception as e:
            print(f"Error: {e}\n{traceback.format_exc()}")
            send_to_telegram(f"⚠️ Tracker error:\n{e}")
            time.sleep(10)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
