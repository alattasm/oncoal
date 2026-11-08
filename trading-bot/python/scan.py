"""
Signal scanner: checks a watchlist of stocks / crypto and prints the latest setups.
No orders are sent — it only tells you where the strategy fired.

    python scan.py                       # default watchlist, 1h
    python scan.py --tf 1d --bars 5      # signals in the last 5 daily candles
    python scan.py --yahoo AAPL NVDA 2222.SR 1120.SR --kraken XBTUSD ETHUSD
"""
from __future__ import annotations

import argparse

from data import kraken, yahoo
from strategy import Params, generate_signals

DEFAULT_YAHOO = ["AAPL", "NVDA", "TSLA", "MSFT", "2222.SR", "1120.SR", "GC=F", "EURUSD=X"]
DEFAULT_KRAKEN = ["XBTUSD", "ETHUSD", "SOLUSD", "XRPUSD"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tf", default="1h")
    ap.add_argument("--bars", type=int, default=3, help="show signals from the last N candles")
    ap.add_argument("--yahoo", nargs="*", default=DEFAULT_YAHOO)
    ap.add_argument("--kraken", nargs="*", default=DEFAULT_KRAKEN)
    ap.add_argument("--no-rsi-div", action="store_true")
    a = ap.parse_args()
    p = Params(require_rsi_div=not a.no_rsi_div)

    jobs = [("yahoo", s) for s in a.yahoo] + [("kraken", s) for s in a.kraken]
    found = 0
    for src, sym in jobs:
        try:
            df = yahoo(sym, a.tf) if src == "yahoo" else kraken(sym, a.tf)
        except Exception as e:  # noqa: BLE001
            print(f"{sym:10s} data error: {e}")
            continue
        recent = [s for s in generate_signals(df, p) if s.bar >= len(df) - a.bars]
        for s in recent:
            found += 1
            print(f"{sym:10s} {df.index[s.bar]:%Y-%m-%d %H:%M}  {s.side.upper():4s}  "
                  f"entry {s.entry:.4f}  SL {s.sl:.4f}  TP {s.tp:.4f}  "
                  f"RSI-div {'yes' if s.info['rsi_div'] else 'no'}")
        if not recent:
            print(f"{sym:10s} no setup (last close {df['close'].iloc[-1]:.4f})")
    print(f"\n{found} signal(s). Not financial advice — confirm on the chart and use a demo account first.")


if __name__ == "__main__":
    main()
