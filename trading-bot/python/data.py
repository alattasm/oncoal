"""Free OHLC data: Kraken (crypto, no key) and Yahoo Finance (stocks / forex / gold)."""
from __future__ import annotations

import time

import pandas as pd
import requests

UA = {"User-Agent": "Mozilla/5.0 (smc-rsi-bot)"}

KRAKEN_TF = {"1m": 1, "5m": 5, "15m": 15, "30m": 30, "1h": 60, "4h": 240, "1d": 1440}


def kraken(pair: str = "XBTUSD", tf: str = "1h") -> pd.DataFrame:
    """Last ~720 candles from Kraken public API. pair e.g. XBTUSD, ETHUSD, SOLUSD."""
    r = requests.get("https://api.kraken.com/0/public/OHLC",
                     params={"pair": pair, "interval": KRAKEN_TF[tf]}, headers=UA, timeout=20)
    r.raise_for_status()
    js = r.json()
    if js.get("error"):
        raise RuntimeError(js["error"])
    key = [k for k in js["result"] if k != "last"][0]
    df = pd.DataFrame(js["result"][key],
                      columns=["time", "open", "high", "low", "close", "vwap", "volume", "count"])
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df = df.set_index("time")[["open", "high", "low", "close", "volume"]].astype(float)
    return df.iloc[:-1]   # drop the still-forming candle


def yahoo(symbol: str = "AAPL", tf: str = "1h", rng: str = "730d") -> pd.DataFrame:
    """Yahoo chart API. symbol e.g. AAPL, TSLA, 2222.SR (Aramco), EURUSD=X, GC=F (gold)."""
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    for attempt in range(5):
        r = requests.get(url, params={"range": rng, "interval": tf}, headers=UA, timeout=20)
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        r.raise_for_status()
        break
    else:
        raise RuntimeError("Yahoo rate limit (429) — try again later")
    res = r.json()["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")},
                      index=pd.to_datetime(res["timestamp"], unit="s", utc=True))
    return df.dropna().astype(float)


def load(source: str, symbol: str, tf: str) -> pd.DataFrame:
    if source == "kraken":
        return kraken(symbol, tf)
    if source == "yahoo":
        return yahoo(symbol, tf)
    if source.endswith(".csv"):
        df = pd.read_csv(source, parse_dates=[0], index_col=0)
        df.columns = [c.lower() for c in df.columns]
        return df
    raise ValueError(source)
