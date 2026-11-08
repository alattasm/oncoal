"""
Strategy engine — rules extracted from the three videos.

Video 2 (Smart Money):
  1. Liquidity sweep: a candle trades above a swing high but CLOSES back below it
     (a wick alone = liquidity grab, a close above = real break of structure).
  2. CHoCH: price then closes below the "protected low" (the last swing low before the sweep).
     This is only an alert, not an entry.
  3. BOS: price makes a lower high and closes below the new low -> bearish break of structure.
  4. FVG: the strong drop leaves a fair value gap (low[i-2] > high[i]).
  5. Don't chase. Wait for price to return into the FVG, reject it and close below -> ENTRY.
  6. Stop above the sweep wick, target the liquidity below (default R:R 1:2).
  7. If price closes above the FVG the idea is cancelled.

Video 1 (RSI):
  - RSI > 70 alone is NOT a sell (it means strong momentum, not "expensive").
  - Useful as a warning: bearish divergence = price higher high, RSI lower high.
  - Even divergence is only a warning: wait for price confirmation (break of support).
    -> In this engine RSI is an optional filter: require divergence at the sweep.

Everything is coded for the SELL side. The BUY side is obtained by mirroring the
price series (high' = -low, low' = -high, RSI' = 100 - RSI) and running the same logic,
so both directions follow exactly the same rules.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd


@dataclass
class Params:
    swing_len: int = 3            # bars on each side to confirm a swing high/low
    rsi_len: int = 14
    require_rsi_div: bool = True   # video 1: require bearish/bullish RSI divergence at the sweep
    require_bos: bool = True       # video 2: CHoCH is only an alert, wait for BOS
    rr: float = 2.0                # risk:reward
    sl_buffer_atr: float = 0.10    # extra stop distance beyond the sweep wick (in ATR)
    max_setup_bars: int = 60       # setup expires after N bars
    max_risk_atr: float = 6.0      # skip trades whose stop is wider than N * ATR
    atr_len: int = 14


@dataclass
class Signal:
    bar: int            # index of the bar whose close triggers the entry
    side: str           # "sell" | "buy"
    entry: float
    sl: float
    tp: float
    info: dict = field(default_factory=dict)


def rsi(close: np.ndarray, n: int = 14) -> np.ndarray:
    delta = np.diff(close, prepend=close[0])
    up = np.where(delta > 0, delta, 0.0)
    dn = np.where(delta < 0, -delta, 0.0)
    out = np.full(len(close), 50.0)
    if len(close) <= n:
        return out
    au, ad = up[1:n + 1].mean(), dn[1:n + 1].mean()
    for i in range(n + 1, len(close)):
        au = (au * (n - 1) + up[i]) / n          # Wilder smoothing (same as MT5/TradingView)
        ad = (ad * (n - 1) + dn[i]) / n
        out[i] = 100.0 if ad == 0 else 100 - 100 / (1 + au / ad)
    return out


def atr(h, l, c, n=14):
    pc = np.roll(c, 1)
    pc[0] = c[0]
    tr = np.maximum(h - l, np.maximum(abs(h - pc), abs(l - pc)))
    out = np.zeros(len(c))
    out[0] = tr[0]
    for i in range(1, len(c)):
        out[i] = (out[i - 1] * (n - 1) + tr[i]) / n
    return out


def _bearish_signals(o, h, l, c, r, a, p: Params, side: str, sign: float):
    """Run the SELL state machine. `sign` converts prices back for reporting (-1 when mirrored)."""
    n = len(c)
    k = p.swing_len
    swing_highs: list[tuple[int, float]] = []   # confirmed (index, price)
    swing_lows: list[tuple[int, float]] = []
    signals: list[Signal] = []

    st = None   # current setup dict or None
    for t in range(2 * k, n):
        # --- confirm the swing that is now k bars old (no look-ahead) ---
        j = t - k
        if h[j] == h[j - k:j + k + 1].max() and h[j] > h[j - 1]:
            swing_highs.append((j, h[j]))
        if l[j] == l[j - k:j + k + 1].min() and l[j] < l[j - 1]:
            swing_lows.append((j, l[j]))

        if st is None:
            # --- 1. look for a liquidity sweep of the latest unbroken swing high ---
            if not swing_highs or not swing_lows:
                continue
            si, sh = swing_highs[-1]
            if si >= t:
                continue
            if h[t] > sh and c[t] < sh:
                prot = [x for x in swing_lows if x[0] < t]
                if not prot:
                    continue
                div = r[t] < r[si]      # price higher high, RSI lower high
                if p.require_rsi_div and not div:
                    swing_highs.pop()   # consumed
                    continue
                st = dict(phase="swept", start=t, sweep_hi=h[t], swing_hi=sh,
                          prot_low=prot[-1][1], rsi_div=bool(div),
                          rsi_at_sweep=float(r[t]))
                swing_highs.pop()
            elif c[t] > sh:
                swing_highs.pop()       # real bullish BOS, level consumed
            continue

        # --- setup in progress ---
        if t - st["start"] > p.max_setup_bars:
            st = None
            continue
        if c[t] > st["sweep_hi"]:       # closed above the sweep wick -> idea invalid
            st = None
            continue
        if st["phase"] == "swept":
            st["sweep_hi"] = max(st["sweep_hi"], h[t])   # track the full sweep wick
            if c[t] < st["prot_low"]:                    # 2. CHoCH
                st.update(phase="choch", choch_bar=t)
                if not p.require_bos:
                    st.update(phase="find_fvg", bos_bar=t)
            else:
                continue

        if st["phase"] == "choch" and t > st["choch_bar"]:
            # 3. BOS: a lower high confirmed after CHoCH, then close below the leg low
            lh = [x for x in swing_highs if x[0] > st["choch_bar"] and x[1] < st["sweep_hi"]]
            if lh:
                lh_i = lh[-1][0]
                ref_low = l[st["start"]:lh_i + 1].min()
                if c[t] < ref_low:
                    st.update(phase="find_fvg", bos_bar=t, lh_bar=lh_i)

        if st["phase"] == "find_fvg":
            # 4. most recent bearish FVG in the impulsive leg (sweep -> BOS)
            fvg = None
            for i in range(st["bos_bar"], st["start"] + 1, -1):
                if l[i - 2] > h[i]:
                    fvg = (h[i], l[i - 2])   # (bottom, top)
                    break
            if fvg is None:
                st = None
                continue
            st.update(phase="armed", fvg_bot=fvg[0], fvg_top=fvg[1], armed_bar=t)
            continue

        if st["phase"] == "armed" and t > st["armed_bar"]:
            if c[t] > st["fvg_top"]:                     # 7. closed above the gap -> cancelled
                st = None
                continue
            # 5. retrace into the gap, rejection, close back below it
            if h[t] >= st["fvg_bot"] and c[t] < st["fvg_bot"] and c[t] < o[t]:
                entry = c[t]
                sl = st["sweep_hi"] + p.sl_buffer_atr * a[t]
                risk = sl - entry
                if risk <= 0 or risk > p.max_risk_atr * a[t]:
                    st = None
                    continue
                tp = entry - p.rr * risk
                signals.append(Signal(
                    bar=t, side=side, entry=sign * entry, sl=sign * sl, tp=sign * tp,
                    info=dict(sweep_bar=st["start"], rsi_div=st["rsi_div"],
                              rsi_at_sweep=st["rsi_at_sweep"] if sign > 0 else 100 - st["rsi_at_sweep"],
                              fvg=(sign * st["fvg_bot"], sign * st["fvg_top"]))))
                st = None
    return signals


def generate_signals(df: pd.DataFrame, p: Params = Params()) -> list[Signal]:
    """df needs columns open, high, low, close. Returns buy & sell signals sorted by bar."""
    o, h, l, c = (df[x].to_numpy(float) for x in ("open", "high", "low", "close"))
    r = rsi(c, p.rsi_len)
    a = atr(h, l, c, p.atr_len)
    sells = _bearish_signals(o, h, l, c, r, a, p, "sell", 1.0)
    # mirror the chart: a bullish setup is a bearish setup upside-down
    buys = _bearish_signals(-o, -l, -h, -c, 100 - r, a, p, "buy", -1.0)
    return sorted(sells + buys, key=lambda s: s.bar)
