# MLNK Price Tracker

Real-time price monitor for the **MLNK** token on the `swap.pcash` DEX (EOS).
It reads the liquidity pools straight from the chain via RPC, calculates the MLNK/USDCASH price
and sends every change to a Telegram chat.

```
📈 1 MLNK = 0.12345678 USDCASH (+0.4210%)
📉 1 MLNK = 0.12290011 USDCASH (-0.4509%)
```

## Features
- Reads pool reserves directly from the chain (`get_table_rows`), no third-party price API
- Paginates through all pools and finds the target pair automatically
- Alerts only when the price actually changes, with % change and direction
- Survives RPC/network errors: logs, notifies Telegram, retries
- Configurable via environment variables (token, pair, poll interval, RPC node)

## Setup
```bash
pip install -r requirements.txt
cp .env.example .env   # fill in BOT_TOKEN and CHAT_ID
python tracker.py
```

| Variable | Default | Description |
|---|---|---|
| `BOT_TOKEN` | — | Telegram bot token from @BotFather |
| `CHAT_ID` | — | Chat / group id to post alerts to |
| `TARGET_SYMBOL` | `MLNK` | Token to track |
| `QUOTE_SYMBOL` | `USDCASH` | Quote token of the pair |
| `POLL_SECONDS` | `5` | Polling interval |
| `EOS_NODE_URL` | greymass | EOS RPC endpoint |

## Stack
Python · requests · EOS RPC · Telegram Bot API
