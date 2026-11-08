"""
Alpaca bot — runs the SMC + RSI strategy and places orders on Alpaca.
PAPER trading by default (fake money). US stocks + crypto.

Setup:
  1. Make a free account at alpaca.markets -> switch to "Paper Trading" -> API Keys -> Generate.
  2. Copy alpaca_config.example.json to alpaca_config.json and paste your keys in it.
  3. python alpaca_bot.py            (keeps running, checks every candle)
     python alpaca_bot.py --once     (one check, then exit — good for testing)

Rules:
  - Saudi stocks (Tadawul codes like "2222"): used only if your Alpaca account can trade them —
    the bot looks them up at start (python alpaca_bot.py --check-markets shows what you have).
    Buy only, SL/TP watched by the bot, Sunday-Thursday 10:00-15:00 Riyadh time.
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
    "saudi": ["2222", "1120", "1150", "1180", "2010", "7010", "1211", "2082", "1010", "2280"],
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


SAR_PER_USD = 3.75   # the riyal is pegged to the dollar


def saudi_market_open() -> bool:
    """Tadawul: Sunday-Thursday, 10:00-15:00 Riyadh time (UTC+3)."""
    now = datetime.now(timezone.utc) + timedelta(hours=3)
    return now.weekday() in (6, 0, 1, 2, 3) and 10 <= now.hour + now.minute / 60 < 15


def find_saudi_assets(api: Alpaca, codes: list[str]) -> dict[str, str]:
    """Map Tadawul codes (e.g. "2222") to the symbol Alpaca uses for them on this account."""
    try:
        assets = api._req("GET", f"{api.base}/v2/assets", params={"status": "active"})
    except Exception as e:  # noqa: BLE001
        log(f"could not list assets: {e}")
        return {}
    found = {}
    for code in codes:
        for x in assets:
            sym, ex = str(x.get("symbol", "")), str(x.get("exchange", "")).upper()
            if not x.get("tradable"):
                continue
            if sym == code or sym.split(".")[0] == code and ("TADAWUL" in ex or "SA" in ex or sym != code):
                found[code] = sym
                break
    return found


def get_bars(api: Alpaca, sym: str, kind: str, tf: str, n: int = 500) -> pd.DataFrame:
    if kind != "saudi":
        return api.bars(sym, tf, n)
    # Saudi candles from Yahoo (2222.SR); orders still go through Alpaca
    from data import yahoo
    yf_tf = {"15m": "15m", "1h": "1h", "4h": "1h", "1d": "1d"}[tf]
    df = yahoo(f"{sym}.SR", yf_tf, "730d" if yf_tf != "15m" else "60d")
    minutes = TF[tf][1]
    if len(df) and df.index[-1] + timedelta(minutes=minutes) > datetime.now(timezone.utc):
        df = df.iloc[:-1]
    return df.tail(n)


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
    us_open = api.clock().get("is_open", False)
    managed = state.setdefault("crypto_exits", {})   # positions whose SL/TP the bot watches

    # Saudi symbols: look up how Alpaca names them (once per run)
    if cfg.get("saudi") and "saudi_map" not in state:
        state["saudi_map"] = find_saudi_assets(api, cfg["saudi"])
        missing = [c for c in cfg["saudi"] if c not in state["saudi_map"]]
        if state["saudi_map"]:
            log(f"Saudi stocks tradable on this account: {state['saudi_map']}")
        if missing:
            log(f"Saudi codes NOT found on this account (skipped): {', '.join(missing)}")
    saudi_map = state.get("saudi_map", {})

    # --- exits watched by the bot (crypto + Saudi: no bracket orders) ---
    for key, ex in list(managed.items()):
        order_sym = ex.get("order_sym", key)
        if order_sym.replace("/", "") not in positions:
            managed.pop(key)
            continue
        kind = ex.get("kind", "crypto")
        try:
            df = get_bars(api, key, kind, "15m" if kind == "crypto" else "1h", 3)
        except Exception as e:  # noqa: BLE001
            log(f"{key}: price check failed {e}")
            continue
        if df.empty:
            continue
        price = df["close"].iloc[-1]
        if kind == "saudi" and not saudi_market_open():
            continue
        if price <= ex["sl"] or price >= ex["tp"]:
            log(f"{key}: {'STOP LOSS' if price <= ex['sl'] else 'TAKE PROFIT'} hit at {price:.2f} — closing")
            api.close_position(order_sym)
            managed.pop(key)

    symbols = ([(s, s, "stock") for s in cfg["stocks"]]
               + [(s, s, "crypto") for s in cfg["crypto"]]
               + [(code, saudi_map[code], "saudi") for code in cfg.get("saudi", []) if code in saudi_map])
    for sym, order_sym, kind in symbols:
        try:
            df = get_bars(api, sym, kind, cfg["timeframe"])
        except Exception as e:  # noqa: BLE001
            log(f"{sym}: data error {e}")
            continue
        if len(df) < 100:
            log(f"{sym}: not enough data ({len(df)} candles)")
            continue
        sigs = [x for x in generate_signals(df, p) if x.bar == len(df) - 1]
        if not sigs:
            continue
        s = sigs[-1]
        bar_id = f"{sym}@{df.index[-1].isoformat()}"
        if bar_id in state.setdefault("done", []):
            continue
        state["done"] = (state["done"] + [bar_id])[-500:]
        log(f"{sym}: SIGNAL {s.side.upper()} entry {s.entry:.4f} SL {s.sl:.4f} TP {s.tp:.4f} "
            f"(RSI div: {'yes' if s.info['rsi_div'] else 'no'})")

        if order_sym.replace("/", "") in positions:
            log(f"{sym}: already have a position — skipped")
            continue
        if len(positions) >= cfg["max_open_positions"]:
            log(f"{sym}: max open positions reached — skipped")
            continue
        if kind in ("crypto", "saudi") and s.side == "sell":
            log(f"{sym}: short selling not available for {kind} — skipped")
            continue
        if kind == "stock" and not us_open:
            log(f"{sym}: US market closed — skipped")
            continue
        if kind == "saudi" and not saudi_market_open():
            log(f"{sym}: Saudi market closed — skipped")
            continue

        # Saudi prices are in riyals, account equity in dollars
        eq_local = equity * SAR_PER_USD if kind == "saudi" else equity
        risk_per_unit = abs(s.entry - s.sl)
        qty = eq_local * cfg["risk_percent"] / 100 / risk_per_unit
        qty = min(qty, eq_local * cfg["max_position_percent"] / 100 / s.entry)
        if kind == "crypto":
            qty = math.floor(qty * 1e6) / 1e6
            size_ok = qty * s.entry >= 1
        else:
            qty = math.floor(qty)               # whole shares
            size_ok = qty >= 1
        if not size_ok:
            log(f"{sym}: position size too small — skipped")
            continue

        side = "buy" if s.side == "buy" else "sell"
        try:
            if kind == "stock":
                api.order({
                    "symbol": order_sym, "qty": str(qty), "side": side, "type": "market", "time_in_force": "gtc",
                    "order_class": "bracket",
                    "take_profit": {"limit_price": f"{s.tp:.2f}"},
                    "stop_loss": {"stop_price": f"{s.sl:.2f}"},
                })
            else:
                api.order({"symbol": order_sym, "qty": str(qty), "side": side, "type": "market",
                           "time_in_force": "gtc" if kind == "crypto" else "day"})
                managed[sym] = {"sl": float(s.sl), "tp": float(s.tp), "kind": kind, "order_sym": order_sym}
            positions[order_sym.replace("/", "")] = {"symbol": order_sym}
            log(f"{sym}: ORDER SENT {side.upper()} {qty}")
        except Exception as e:  # noqa: BLE001
            log(f"{sym}: order failed — {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="run one check and exit")
    ap.add_argument("--check-markets", action="store_true",
                    help="list which exchanges your Alpaca account can trade (e.g. to see if Saudi/Tadawul is there)")
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
    if a.check_markets:
        assets = api._req("GET", f"{api.base}/v2/assets", params={"status": "active"})
        by_ex: dict[str, int] = {}
        for x in assets:
            if x.get("tradable"):
                by_ex[x.get("exchange", "?")] = by_ex.get(x.get("exchange", "?"), 0) + 1
        print("Tradable assets on your account by exchange:")
        for ex, n in sorted(by_ex.items(), key=lambda kv: -kv[1]):
            print(f"  {ex:12s} {n}")
        saudi = [x for x in assets if "TADAWUL" in str(x.get("exchange", "")).upper()
                 or str(x.get("symbol", "")).startswith("2222")]
        print("\nSaudi (Tadawul) stocks:", "YES — " + ", ".join(x["symbol"] for x in saudi[:10]) if saudi else "NOT available on this account")
        return
    state = load_json(STATE_FILE, {})
    state.pop("saudi_map", None)   # re-check which Saudi stocks are tradable every start
    minutes = TF[cfg["timeframe"]][1]
    log(f"Bot started — {cfg['timeframe']} candles, {len(cfg['stocks'])} US stocks, "
        f"{len(cfg.get('saudi', []))} Saudi, {len(cfg['crypto'])} crypto")

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
