import requests
import time
import traceback

# EOS RPC
NODE_URL = "https://eos.greymass.com/v1/chain/get_table_rows"
DEX_CONTRACT = "swap.pcash"
TARGET_SYMBOL = "MLNK"
TARGET_CONTRACT = "swap.pcash"

# Telegram
BOT_TOKEN = "8283871068:AAEnWDO4EbB6Y4ho7gKlfyvY_IYLBUTUjiM"
CHAT_ID = "-4814710741"

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)

def get_all_pairs():
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
            "limit": 100
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

def find_mlnk_price():
    pairs = get_all_pairs()
    for pair in pairs:
        sym0 = pair["token1"]["quantity"].split(" ")[1]
        sym1 = pair["token2"]["quantity"].split(" ")[1]

        if (sym0 == TARGET_SYMBOL or sym1 == TARGET_SYMBOL) and (sym0 == "USDCASH" or sym1 == "USDCASH"):
            amount1 = float(pair["token1"]["quantity"].split(" ")[0])
            amount2 = float(pair["token2"]["quantity"].split(" ")[0])

            if sym1 == TARGET_SYMBOL:
                return amount1 / amount2, sym0
            elif sym0 == TARGET_SYMBOL:
                return amount2 / amount1, sym1
    return None, None

if __name__ == "__main__":
    last_price = None

    while True:
        try:
            price, quote_sym = find_mlnk_price()
            if price:
                rounded_price = round(price, 8)
                if last_price is None or rounded_price != last_price:
                    if last_price is not None:
                        change_percent = ((rounded_price - last_price) / last_price) * 100
                        direction = "📈" if rounded_price > last_price else "📉"
                        msg = f"{direction} 1 {TARGET_SYMBOL} = {rounded_price:.8f} {quote_sym} ({change_percent:+.4f}%)"
                    else:
                        msg = f"1 {TARGET_SYMBOL} = {rounded_price:.8f} {quote_sym} (начальное значение)"

                    last_price = rounded_price
                    print(msg)
                    send_to_telegram(msg)
                else:
                    print(f"Цена не изменилась: {rounded_price:.8f} {quote_sym}")
            else:
                print("MLNK pair not found on", DEX_CONTRACT)
        except Exception as e:
            error_text = f"Ошибка: {e}\n{traceback.format_exc()}"
            print(error_text)
            send_to_telegram(f"⚠️ Ошибка в скрипте:\n{e}")
            time.sleep(10)  # Ждём перед перезапуском

        time.sleep(5)
