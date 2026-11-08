"""
Backtest the SMC + RSI strategy on historical candles.

    python backtest.py --source kraken --symbol XBTUSD --tf 1h
    python backtest.py --source yahoo  --symbol AAPL   --tf 1h
    python backtest.py --source yahoo  --symbol 2222.SR --tf 1d --no-rsi-div

One position at a time. Entry on the close of the signal candle. If a candle touches
both SL and TP, the SL is assumed first (conservative). Fees are charged per side.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd

from data import load
from strategy import Params, generate_signals


def backtest(df: pd.DataFrame, p: Params, fee: float = 0.001, risk_pct: float = 1.0):
    h, l = df["high"].to_numpy(), df["low"].to_numpy()
    sigs = generate_signals(df, p)
    trades, busy_until = [], -1
    for s in sigs:
        if s.bar <= busy_until:
            continue
        res, exit_bar = None, len(df) - 1
        for t in range(s.bar + 1, len(df)):
            if s.side == "sell":
                if h[t] >= s.sl: res, exit_px = "SL", s.sl
                elif l[t] <= s.tp: res, exit_px = "TP", s.tp
            else:
                if l[t] <= s.sl: res, exit_px = "SL", s.sl
                elif h[t] >= s.tp: res, exit_px = "TP", s.tp
            if res:
                exit_bar = t
                break
        if res is None:
            res, exit_px = "OPEN", df["close"].iloc[-1]
        risk = abs(s.entry - s.sl)
        pnl = (exit_px - s.entry) * (1 if s.side == "buy" else -1)
        fees = fee * (s.entry + exit_px)
        r_mult = (pnl - fees) / risk
        trades.append(dict(time=df.index[s.bar], side=s.side, entry=s.entry, sl=s.sl, tp=s.tp,
                           exit=exit_px, result=res, R=round(r_mult, 2),
                           rsi_div=s.info["rsi_div"], bars=exit_bar - s.bar))
        busy_until = exit_bar
    tr = pd.DataFrame(trades)
    if tr.empty:
        return tr, {"trades": 0}
    closed = tr[tr.result != "OPEN"]
    equity = np.cumprod(1 + closed["R"].to_numpy() * risk_pct / 100)
    peak = np.maximum.accumulate(equity)
    stats = {
        "trades": len(closed),
        "win_rate_%": float(round(100 * (closed.R > 0).mean(), 1)) if len(closed) else 0,
        "total_R": round(closed.R.sum(), 2),
        "avg_R": round(closed.R.mean(), 2) if len(closed) else 0,
        f"return_%_at_{risk_pct}%_risk": round(100 * (equity[-1] - 1), 1) if len(closed) else 0,
        "max_drawdown_%": round(100 * (1 - equity / peak).max(), 1) if len(closed) else 0,
        "open": int((tr.result == "OPEN").sum()),
    }
    return tr, stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="kraken", help="kraken | yahoo | path/to/file.csv")
    ap.add_argument("--symbol", default="XBTUSD")
    ap.add_argument("--tf", default="1h")
    ap.add_argument("--rr", type=float, default=2.0)
    ap.add_argument("--swing", type=int, default=3)
    ap.add_argument("--no-rsi-div", action="store_true", help="don't require RSI divergence (video 1 filter off)")
    ap.add_argument("--no-bos", action="store_true", help="enter after CHoCH without waiting for BOS")
    ap.add_argument("--fee", type=float, default=0.001)
    ap.add_argument("--trades", action="store_true", help="print every trade")
    a = ap.parse_args()

    df = load(a.source, a.symbol, a.tf)
    p = Params(swing_len=a.swing, rr=a.rr, require_rsi_div=not a.no_rsi_div, require_bos=not a.no_bos)
    tr, stats = backtest(df, p, fee=a.fee)
    print(f"{a.symbol} {a.tf}  {df.index[0]:%Y-%m-%d} -> {df.index[-1]:%Y-%m-%d}  ({len(df)} candles)")
    print({k: (round(float(v), 2) if not isinstance(v, int) else v) for k, v in stats.items()})
    if a.trades and not tr.empty:
        print(tr.to_string(index=False))


if __name__ == "__main__":
    main()
