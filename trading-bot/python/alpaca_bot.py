"""
Alpaca bot — runs the SMC + RSI strategy and places orders on Alpaca.
PAPER trading by default (fake money). US stocks + crypto.

Setup:
  1. Make a free account at alpaca.markets -> switch to "Paper Trading" -> API Keys -> Generate.
  2. Copy alpaca_config.example.json to alpaca_config.json and paste your keys in it.
  3. python alpaca_bot.py            (keeps running, checks every candle)
     python alpaca_bot.py --once     (one check, then exit — good for testing)

Rules:
  - Stocks: bracket order (entry + stop loss + take profit sent together). Buys and short sells.
  - Crypto: buy only (Alpaca can't short crypto). Stop loss / take profit watched by the bot.
  - One position per symbol, risk % of equity per trade, emergency stop on max drawdown.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

from strategy import Params, generate_signals

HERE = Path(__file__).parent
CONFIG_FILE = HERE / "alpaca_config.json"
STATE_FILE = HERE / "alpaca_state.json"

PAPER_URL = "https://paper-api.alpaca.markets"
LIVE_URL = "https://api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"

TF = {"15m": ("15Min", 15), "1h": ("1Hour", 60), "4h": ("4Hour", 240), "1d": ("1Day", 1440)}

DEFAULT_CONFIG = {
    "key": "PASTE_YOUR_PAPER_KEY_HERE",
    "secret": "PASTE_YOUR_PAPER_SECRET_HERE",
    "live": False,
    "timeframe": "1h",
    "stocks": ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "META", "SHOP", "RY"],
    "crypto": ["BTC/USD", "ETH/USD", "SOL/USD"],
    "risk_percent": 1.0,
    "max_position_percent": 20.0,
    "max_open_positions": 5,
    "max_drawdown_percent": 10.0,
    "require_rsi_divergence": True,
    "rr": 2.0,
}


def log(msg: str):
    print(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}", flush=True)


class Alpaca:
    def __init__(self, key: str, secret: str, live: bool):
        self.base = LIVE_URL if live else PAPER_URL
        self.s = requests.Session()
        self.s.headers.update({"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret})

    def _req(self, method, url, **kw):
        r = self.s.request(method, url, timeout=30, **kw)
        if r.status_code >= 400:
            raise RuntimeError(f"{method} {url} -> {r.status_code}: {r.text[:300]}")
        return r.json() if r.text else {}

    # --- trading ---
    def account(self):
        return self._req("GET", f"{self.base}/v2/account")

    def clock(self):
        return self._req("GET", f"{self.base}/v2/clock")

    def positions(self):
        return {p["symbol"]: p for p in self._req("GET", f"{self.base}/v2/positions")}

    def open_orders(self):
        return self._req("GET", f"{self.base}/v2/orders", params={"status": "open", "limit": 500})

    def order(self, payload):
        return self._req("POST", f"{self.base}/v2/orders", json=payload)

    def close_position(self, symbol):
        return self._req("DELETE", f"{self.base}/v2/positions/{symbol.replace('/', '')}")

    def close_all(self):
        return self._req("DELETE", f"{self.base}/v2/positions", params={"cancel_orders": "true"})

    # --- market data ---
    def bars(self, symbol: str, tf: str, n: int = 500) -> pd.DataFrame:
        tf_name, minutes = TF[tf]
        crypto = "/" in symbol
        # stocks only trade ~7h/day, so look further back to get enough candles
        days = n * minutes / 1440 * (1.2 if crypto else (4.5 if minutes < 1440 else 1.6)) + 5
        start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows, token = [], None
        while True:
            params = {"timeframe": tf_name, "start": start, "limit": 10000}
            if token:
                params["page_token"] = token
            if crypto:
                params["symbols"] = symbol
                js = self._req("GET", f"{DATA_URL}/v1beta3/crypto/us/bars", params=params)
                rows += js.get("bars", {}).get(symbol, [])
            else:
                params.update(feed="iex", adjustment="split")
                js = self._req("GET", f"{DATA_URL}/v2/stocks/{symbol}/bars", params=params)
                rows += js.get("bars") or []
            token = js.get("next_page_token")
            if not token:
                break
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows).rename(columns={"t": "time", "o": "open", "h": "high", "l": "low", "c": "close", "v": "volume"})
        df["time"] = pd.to_datetime(df["time"], utc=True)
        df = df.set_index("time")[["open", "high", "low", "close", "volume"]].astype(float)
        # drop the candle that is still forming
        if len(df) and df.index[-1] + timedelta(minutes=minutes) > datetime.now(timezone.utc):
            df = df.iloc[:-1]
        return df.tail(n)


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def run_cycle(api: Alpaca, cfg: dict, state: dict):
    acct = api.account()
    equity = float(acct["equity"])
    state.setdefault("start_equity", equity)
    dd = (state["start_equity"] - equity) / state["start_equity"] * 100
    log(f"Equity {equity:,.2f} {acct.get('currency', 'USD')}  drawdown {dd:.1f}%  ({'LIVE' if cfg['live'] else 'PAPER'})")
    if dd >= cfg["max_drawdown_percent"]:
        log("EMERGENCY STOP: max drawdown reached — closing everything and stopping.")
        api.close_all()
        state["halted"] = True
        return

    positions = api.positions()
    p = Params(require_rsi_div=cfg["require_rsi_divergence"], rr=cfg["rr"])
    market_open = api.clock().get("is_open", False)
    managed = state.setdefault("crypto_exits", {})

    # --- crypto exits are watched by the bot (Alpaca has no bracket orders for crypto) ---
    for sym, ex in list(managed.items()):
        if sym.replace("/", "") not in positions:
            managed.pop(sym)
            continue
        df = api.bars(sym, "15m", 3)
        if df.empty:
            continue
        price = df["close"].iloc[-1]
        if price <= ex["sl"] or price >= ex["tp"]:
            log(f"{sym}: {'STOP LOSS' if price <= ex['sl'] else 'TAKE PROFIT'} hit at {price:.2f} — closing")
            api.close_position(sym)
            managed.pop(sym)

    symbols = [(s, False) for s in cfg["stocks"]] + [(s, True) for s in cfg["crypto"]]
    for sym, crypto in symbols:
        try:
            df = api.bars(sym, cfg["timeframe"])
        except Exception as e:  # noqa: BLE001
            log(f"{sym}: data error {e}")
            continue
        if len(df) < 100:
            log(f"{sym}: not enough data ({len(df)} candles)")
            continue
        sigs = [s for s in generate_signals(df, p) if s.bar == len(df) - 1]
        if not sigs:
            continue
        s = sigs[-1]
        bar_id = f"{sym}@{df.index[-1].isoformat()}"
        if bar_id in state.setdefault("done", []):
            continue
        state["done"] = (state["done"] + [bar_id])[-500:]
        log(f"{sym}: SIGNAL {s.side.upper()} entry {s.entry:.4f} SL {s.sl:.4f} TP {s.tp:.4f} "
            f"(RSI div: {'yes' if s.info['rsi_div'] else 'no'})")

        if sym.replace("/", "") in positions:
            log(f"{sym}: already have a position — skipped")
            continue
        if len(positions) >= cfg["max_open_positions"]:
            log(f"{sym}: max open positions reached — skipped")
            continue
        if crypto and s.side == "sell":
            log(f"{sym}: crypto can't be shorted on Alpaca — skipped")
            continue
        if not crypto and not market_open:
            log(f"{sym}: stock market closed — skipped")
            continue

        risk_per_unit = abs(s.entry - s.sl)
        qty = equity * cfg["risk_percent"] / 100 / risk_per_unit
        qty = min(qty, equity * cfg["max_position_percent"] / 100 / s.entry)
        if crypto:
            qty = math.floor(qty * 1e6) / 1e6
            notional_ok = qty * s.entry >= 1
        else:
            qty = math.floor(qty)               # bracket orders need whole shares
            notional_ok = qty >= 1
        if not notional_ok:
            log(f"{sym}: position size too small — skipped")
            continue

        side = "buy" if s.side == "buy" else "sell"
        try:
            if crypto:
                api.order({"symbol": sym, "qty": str(qty), "side": side, "type": "market", "time_in_force": "gtc"})
                managed[sym] = {"sl": s.sl, "tp": s.tp}
            else:
                api.order({
                    "symbol": sym, "qty": str(qty), "side": side, "type": "market", "time_in_force": "gtc",
                    "order_class": "bracket",
                    "take_profit": {"limit_price": f"{s.tp:.2f}"},
                    "stop_loss": {"stop_price": f"{s.sl:.2f}"},
                })
            positions[sym.replace("/", "")] = {"symbol": sym}
            log(f"{sym}: ORDER SENT {side.upper()} {qty}")
        except Exception as e:  # noqa: BLE001
            log(f"{sym}: order failed — {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="run one check and exit")
    a = ap.parse_args()

    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULT_CONFIG, indent=2))
        print(f"Created {CONFIG_FILE.name} — open it, paste your Alpaca PAPER keys, then run again.")
        return
    cfg = {**DEFAULT_CONFIG, **load_json(CONFIG_FILE, {})}
    if "PASTE" in cfg["key"]:
        print(f"Open {CONFIG_FILE.name} and paste your Alpaca keys first.")
        return
    if cfg["live"]:
        print("!!! LIVE TRADING with real money is ON (\"live\": true in the config). Starting in 10 s — Ctrl+C to cancel.")
        time.sleep(10)

    api = Alpaca(cfg["key"], cfg["secret"], cfg["live"])
    state = load_json(STATE_FILE, {})
    minutes = TF[cfg["timeframe"]][1]
    log(f"Bot started — {cfg['timeframe']} candles, {len(cfg['stocks'])} stocks, {len(cfg['crypto'])} crypto")

    while True:
        if state.get("halted"):
            log("Bot is halted (max drawdown). Delete alpaca_state.json to reset.")
            return
        try:
            run_cycle(api, cfg, state)
        except Exception as e:  # noqa: BLE001
            log(f"cycle error: {e}")
        STATE_FILE.write_text(json.dumps(state, indent=2))
        if a.once:
            return
        # wake up shortly after the next candle closes
        now = datetime.now(timezone.utc)
        step = 15 * 60   # every 15 min: new candles + crypto stop/target checks
        wait = step - (now.timestamp() % step) + 20
        log(f"next check in {wait / 60:.0f} min")
        time.sleep(wait)


if __name__ == "__main__":
    main()
