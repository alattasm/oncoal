#!/usr/bin/env python3
"""
بوت منهج "القراءة بثلاث أسئلة" — مبني على مفاهيم شرحها المحلل أسعد حمزة
(Assad Hamzeh) في قناته على يوتيوب. البوت غير تابع له ولا يمثله.

المنهج كما فهمناه من الفيديوهات:
  1. السوق إله 3 حالات بس: صاعد (قمم وقيعان أعلى) / هابط / عرضي.
  2. الأسئلة الثلاثة لأي شارت: مين الغالب؟ قديش غالب؟ هل الغلبة عم تتغير؟
  3. الاختراق: استنى إغلاق الشمعة، المقاومة "منطقة" مش خط، شوف وين سكّرت
     الشمعة مش وين وصلت، جسم كبير وإغلاق قرب القمة ≠ ذيل طويل.
  4. احسب الوقف أولاً (وين بتبطل الفكرة)، بعدين عدد الأسهم من مبلغ المخاطرة،
     الهدف = 2.5 ضعف المخاطرة، وإذا الوقف بعيد كثير: استنى الرجعة أو اترك الصفقة.
  5. فريمين: اليومي يحدد المنطقة والاتجاه، والساعة لشرط الدخول
     (يتجاوز آخر قمة صغيرة على الساعة ويسكر فوقها).
  6. الخروج المقسّم: نصف عند الهدف، والباقي وقف تحت آخر قاع أعلى.
  7. التكلفة والسيولة: الصفقة الصغيرة بتنضغط من التكلفة؛ المؤشرات ما انعملت للتنبؤ.

الاستخدام:
  python3 assad_bot.py IVN.TO
  python3 assad_bot.py CBLU.V --risk 50 --cost 0.06
  python3 assad_bot.py VWAV --risk 100 --cost 0.45 --shares 2000

هذا أداة تعليمية وليست توصية مالية.
"""
import argparse
import json
import sys
import urllib.request

import numpy as np
import pandas as pd

UA = {"User-Agent": "Mozilla/5.0"}


# ───────────────────────────── البيانات ─────────────────────────────
def fetch(ticker: str, rng: str, interval: str) -> pd.DataFrame:
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?range={rng}&interval={interval}")
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
        res = json.load(r)["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame(
        {"o": q["open"], "h": q["high"], "l": q["low"], "c": q["close"], "v": q["volume"]},
        index=pd.to_datetime(res["timestamp"], unit="s"),
    ).dropna()
    df.attrs["meta"] = res["meta"]
    return df


def atr(d: pd.DataFrame, n: int = 14) -> pd.Series:
    tr = pd.concat([d.h - d.l, (d.h - d.c.shift()).abs(), (d.l - d.c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def swings(d: pd.DataFrame, k: int = 3):
    """قمم وقيعان: شمعة أعلى/أدنى من k شموع على كل جهة."""
    hi, lo = [], []
    for i in range(k, len(d) - k):
        if d.h.iloc[i] == d.h.iloc[i - k:i + k + 1].max():
            hi.append((d.index[i], d.h.iloc[i]))
        if d.l.iloc[i] == d.l.iloc[i - k:i + k + 1].min():
            lo.append((d.index[i], d.l.iloc[i]))
    return hi, lo


def fmt(x: float) -> str:
    if x >= 100:
        return f"{x:,.2f}"
    if x >= 1:
        return f"{x:.2f}"
    return f"{x:.4f}".rstrip("0").rstrip(".")


# ─────────────────────── السؤال 1: مين الغالب؟ ───────────────────────
def q1_who_wins(hi, lo, close):
    if len(hi) < 2 or len(lo) < 2:
        return "عرضي", "ما في قمم وقيعان كافية للحكم"
    h1, h2 = hi[-2][1], hi[-1][1]
    l1, l2 = lo[-2][1], lo[-1][1]
    if h2 > h1 and l2 > l1:
        state, why = "صاعد", f"قمة أعلى ({fmt(h1)}→{fmt(h2)}) وقاع أعلى ({fmt(l1)}→{fmt(l2)}): درج طالع، التيران غالبة"
    elif h2 < h1 and l2 < l1:
        state, why = "هابط", f"قمة أوطى ({fmt(h1)}→{fmt(h2)}) وقاع أوطى ({fmt(l1)}→{fmt(l2)}): درج نازل، الدببة غالبة"
    else:
        state, why = "عرضي", f"القمم والقيعان مش متفقة ({fmt(l2)}–{fmt(h2)}): الحبل بالنص، قوتين متعادلتين وزمبرك عم ينضغط"
    # كسر حديث بعد آخر قمة/قاع يغيّر القراءة
    if close < lo[-1][1] and state != "هابط":
        state, why = "هابط", f"السعر سكّر تحت آخر قاع ({fmt(lo[-1][1])}): الدببة سحبت الحبل"
    elif close > hi[-1][1] and state != "صاعد":
        state, why = "صاعد", f"السعر سكّر فوق آخر قمة ({fmt(hi[-1][1])}): التيران سحبت الحبل"
    return state, why


# ─────────────────────── السؤال 2: قديش غالب؟ ───────────────────────
def q2_how_strong(d: pd.DataFrame, state: str):
    last = d.iloc[-20:]
    body = (last.c - last.o)
    rng = (last.h - last.l).replace(0, np.nan)
    up = body[body > 0].abs().mean() if (body > 0).any() else 0
    dn = body[body < 0].abs().mean() if (body < 0).any() else 0
    n_up, n_dn = int((body > 0).sum()), int((body < 0).sum())
    pos = ((last.c - last.l) / rng).mean()  # متوسط مكان الإغلاق داخل الشمعة
    s_up, s_dn = up * n_up, dn * n_dn  # مجموع خطوات كل فريق
    if state == "صاعد":
        score = (s_up / s_dn) if s_dn else np.inf
    elif state == "هابط":
        score = (s_dn / s_up) if s_up else np.inf
    else:
        score = 1.0
    if score >= 1.6:
        lvl = "غلبة ساحقة"
    elif score >= 1.15:
        lvl = "غلبة واضحة"
    else:
        lvl = "غلبة على الحفّة / متعادلة"
    why = (f"آخر 20 شمعة: {n_up} خضرا (متوسط جسم {fmt(up)}) مقابل {n_dn} حمرا (متوسط جسم {fmt(dn)})؛"
           f" الإغلاق بالمتوسط عند {pos*100:.0f}% من مدى الشمعة")
    return lvl, why


# ──────────────────── السؤال 3: هل الغلبة عم تتغير؟ ────────────────────
def q3_changing(d: pd.DataFrame, state: str, hi, lo):
    signs = []
    last = d.iloc[-10:]
    prev = d.iloc[-20:-10]
    b_last = (last.c - last.o).abs().mean()
    b_prev = (prev.c - prev.o).abs().mean()
    up_wick = (last.h - last[["o", "c"]].max(axis=1)).mean()
    lo_wick = (last[["o", "c"]].min(axis=1) - last.l).mean()
    fresh_low = state == "هابط" and d.c.iloc[-1] < lo[-1][1]
    fresh_high = state == "صاعد" and d.c.iloc[-1] > hi[-1][1]
    if fresh_low:
        signs_against = ["السعر عم يعمل قاع جديد هلق تحت آخر قاع (" + fmt(lo[-1][1]) + "): الدببة لسا عم تسحب"]
    elif fresh_high:
        signs_against = ["السعر عم يعمل قمة جديدة هلق فوق آخر قمة (" + fmt(hi[-1][1]) + "): التيران لسا عم تسحب"]
    else:
        signs_against = []
    if b_last < 0.7 * b_prev and b_prev > 0:
        signs.append("الخطوات زغرت (أجسام الشموع أصغر من قبل): الغالب عم يتعب")
    if state == "صاعد":
        if up_wick > 1.3 * lo_wick:
            signs.append("ذيول علوية أطول: في بيع عند كل طلعة")
        if not fresh_high and len(hi) >= 2 and hi[-1][1] - hi[-2][1] < 0.5 * max(1e-9, abs(hi[-2][1] - (hi[-3][1] if len(hi) > 2 else lo[-2][1]))):
            signs.append("آخر قمة بالكاد أعلى من اللي قبلها: الصعود عم يتباطأ")
    if state == "هابط":
        if lo_wick > 1.3 * up_wick:
            signs.append("ذيول سفلية أطول: في شراء عند كل نزلة")
        if not fresh_low and len(lo) >= 2 and lo[-2][1] - lo[-1][1] < 0.5 * max(1e-9, abs((lo[-3][1] if len(lo) > 2 else hi[-2][1]) - lo[-2][1])):
            signs.append("آخر قاع بالكاد أوطى من اللي قبله: النزول عم يتباطأ")
    if state == "عرضي":
        signs.append("السوق العرضي معركة متعادلة: استنى مين يغلب (إغلاق برا النطاق)")
    if state == "عرضي":
        verdict = "ما في غالب لسا"
    elif len(signs) >= 2 and not signs_against:
        verdict = "في إشارات تغيّر"
    elif signs:
        verdict = "إشارة تغيّر أولية بس، مش كافية"
    else:
        verdict = "ما في إشارات تغيّر واضحة"
    return verdict, signs_against + signs


# ────────────────────────── مناطق الدعم والمقاومة ──────────────────────────
def zones(hi, lo, a: float, price: float):
    pts = sorted([p for _, p in hi + lo])
    if not pts:
        return [], []
    width = 0.5 * a
    clusters = []
    for p in pts:
        if clusters and p - clusters[-1][-1] <= width:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    zs = [(min(c) - width / 2, max(c) + width / 2, len(c)) for c in clusters]
    res = sorted([z for z in zs if z[0] > price], key=lambda z: z[0])[:3]
    sup = sorted([z for z in zs if z[1] < price], key=lambda z: -z[1])[:3]
    return sup, res


# ─────────────────────────────── الاختراق ───────────────────────────────
def breakout_check(d: pd.DataFrame, res_zone, sup_zone):
    """يقرأ آخر شمعة مكتملة مقابل أقرب منطقة."""
    c = d.iloc[-1]
    if c.h - c.l <= 0:
        return ["شمعة بلا مدى (السعر ما تحرك أو صفقة وحدة) — ما في قراءة للشمعة، السيولة ضعيفة"], None
    rng = c.h - c.l
    body = abs(c.c - c.o)
    avg_body = (d.c - d.o).abs().iloc[-11:-1].mean()
    close_pos = (c.c - c.l) / rng
    notes = []
    # فحص اختراق منطقة مقاومة (أو فشله) — الشمعة اللي وصلت فوق المنطقة
    prev_top = None
    for z in ([res_zone] if res_zone else []):
        if c.h > z[1] and c.c <= z[1]:
            notes.append(f"⚠️ اختراق كاذب محتمل: الشمعة زارت فوق {fmt(z[1])} بس سكّرت تحتها — اللي فوق ذيل بس")
    if sup_zone and c.l < sup_zone[0] and c.c >= sup_zone[0]:
        notes.append(f"⚠️ كسر كاذب محتمل للدعم: نزلت تحت {fmt(sup_zone[0])} ورجعت سكّرت فوقه")
    # هل الشمعة الأخيرة اخترقت مقاومة سابقة بإغلاق؟
    prev = d.iloc[-2]
    hi, lo = swings(d.iloc[:-1])
    if hi:
        last_hi = hi[-1][1]
        if prev.c <= last_hi < c.c:
            strong = body > avg_body and close_pos >= 0.7
            notes.append(
                f"{'✅ اختراق بإغلاق قوي' if strong else '🟡 اختراق بإغلاق ضعيف'} فوق آخر قمة {fmt(last_hi)}"
                f" — جسم {'أكبر' if body > avg_body else 'أصغر'} من المتوسط، الإغلاق عند {close_pos*100:.0f}% من مدى الشمعة")
            prev_top = last_hi
    return notes, prev_top


# ─────────────────────── شرط الدخول على فريم الساعة ───────────────────────
def hourly_trigger(h: pd.DataFrame):
    if h is None or len(h) < 30:
        return None
    hi, lo = swings(h, k=2)
    if not hi or not lo:
        return None
    last_hi = hi[-1][1]
    trend = "نازل" if len(hi) > 1 and hi[-1][1] < hi[-2][1] and lo[-1][1] < lo[-2][1] else (
        "طالع" if len(hi) > 1 and hi[-1][1] > hi[-2][1] and lo[-1][1] > lo[-2][1] else "متذبذب")
    triggered = h.c.iloc[-1] > last_hi
    return {"trend": trend, "last_small_high": last_hi, "last_small_low": lo[-1][1], "triggered": triggered}


# ────────────────────────────── خطة الصفقة ──────────────────────────────
def trade_plan(price, stop, next_res, a, risk_amt, rr=2.5):
    risk_ps = price - stop
    if risk_ps <= 0:
        return None
    shares = int(risk_amt // risk_ps) if risk_amt else None
    target = price + rr * risk_ps
    warn = []
    if risk_ps > 2.5 * a:
        warn.append(f"الوقف بعيد ({fmt(risk_ps)} = {risk_ps/a:.1f}×ATR): استنى رجعة أو اترك الصفقة")
    if next_res and next_res[0] < target:
        warn.append(f"في مقاومة ({fmt(next_res[0])}–{fmt(next_res[1])}) قبل الهدف: المساحة للهدف ضيقة")
    return {"entry": price, "stop": stop, "risk_ps": risk_ps, "shares": shares,
            "cost": shares * price if shares else None, "target": target, "warn": warn}


# ──────────────────────────────── التقرير ────────────────────────────────
def analyze(ticker, risk_amt=None, cost=None, nshares=None):
    d = fetch(ticker, "2y", "1d")
    try:
        h = fetch(ticker, "60d", "1h")
    except Exception:
        h = None
    meta = d.attrs["meta"]
    cur = meta.get("currency", "")
    price = float(meta.get("regularMarketPrice") or d.c.iloc[-1])
    a = float(atr(d).iloc[-1])
    hi, lo = swings(d)
    out = []
    P = out.append

    P(f"═══ بوت منهج الأسئلة الثلاثة — {ticker} ═══")
    P(f"السعر: {fmt(price)} {cur}   |   ATR اليومي: {fmt(a)} ({a/price*100:.1f}%)")

    # السيولة والتكلفة
    dollar_vol = float((d.c * d.v).iloc[-50:].mean())
    zero_days = int((d.v.iloc[-60:] == 0).sum())
    if dollar_vol < 50_000 or zero_days > 5:
        P(f"⚠️ سيولة ضعيفة: متوسط قيمة التداول اليومي ≈ {dollar_vol:,.0f} {cur}، و{zero_days} يوم بلا تداول من آخر 60."
          " الفرق بين سعر الشراء والبيع والانزلاق ممكن ياكلوا الصفقة — احسب التكلفة قبل أي قرار.")

    # الأسئلة الثلاثة
    state, why1 = q1_who_wins(hi, lo, d.c.iloc[-1])
    lvl, why2 = q2_how_strong(d, state)
    verdict, signs = q3_changing(d, state, hi, lo)
    P("\n🔦 السؤال 1 — مين الغالب؟")
    P(f"   الحالة: {state}. {why1}")
    P("🔦 السؤال 2 — قديش غالب؟")
    P(f"   {lvl}. {why2}")
    P("🔦 السؤال 3 — هل الغلبة عم تتغير؟")
    P(f"   {verdict}" + ("" if not signs else ":"))
    for s in signs:
        P(f"   • {s}")

    # المناطق
    sup, res = zones(hi, lo, a, price)
    P("\n📍 المناطق (مناطق مش خطوط):")
    for z in reversed(res):
        P(f"   مقاومة {fmt(z[0])} – {fmt(z[1])}  (لمسها {z[2]} {'مرة' if z[2] == 1 or z[2] > 10 else 'مرات'})")
    P(f"   ── السعر {fmt(price)} ──")
    for z in sup:
        P(f"   دعم    {fmt(z[0])} – {fmt(z[1])}  (لمسها {z[2]} {'مرة' if z[2] == 1 or z[2] > 10 else 'مرات'})")
    if not sup:
        P("   ما في دعم تاريخي تحت السعر (قاع جديد) — ما في مكان واضح تبطل عنده الفكرة")

    # قراءة آخر شمعة
    notes, _ = breakout_check(d, res[0] if res else None, sup[0] if sup else None)
    if notes:
        P("\n🕯️ آخر شمعة يومية مكتملة:")
        for n in notes:
            P(f"   {n}")

    # فريم الساعة
    ht = hourly_trigger(h)
    if ht:
        P("\n⏱️ فريم الساعة (لشرط الدخول):")
        P(f"   الحركة الصغيرة {ht['trend']} | آخر قمة صغيرة {fmt(ht['last_small_high'])} | آخر قاع صغير {fmt(ht['last_small_low'])}")
        P("   الشرط: سعر بمنطقة على اليومي + إغلاق شمعة ساعة فوق آخر قمة صغيرة → "
          + ("✅ متحقق" if ht["triggered"] else "❌ مش متحقق — ما في دخول"))

    # القرار
    P("\n🧭 القرار حسب المنهج:")
    stop = (sup[0][0] - 0.1 * a) if sup else None
    changing = verdict == "في إشارات تغيّر"
    if state == "صاعد" and not changing:
        P("   الاتجاه صاعد والغلبة ثابتة: دوّر على دخول عند رجعة لمنطقة دعم مع شرط فريم الساعة، مش مطاردة السعر.")
    elif state == "صاعد":
        P("   صاعد بس في إشارات تعب: لا تدخل جديد؛ إذا داخل، ارفع الوقف تحت آخر قاع أعلى.")
    elif state == "هابط" and not changing:
        P("   الدببة غالبة وما في تغيّر مؤكد: لا شراء ولا تعديل متوسط. الدخول بس بعد إغلاق يومي فوق آخر قمة أوطى"
          + (f" ({fmt(hi[-1][1])})" if hi else "") + " + شرط فريم الساعة.")
    elif state == "هابط":
        P("   هابط بس الغلبة عم تضعف: راقب — الدخول بس بعد إغلاق فوق آخر قمة أوطى (تغيّر الحالة) + شرط الساعة.")
    else:
        P("   عرضي: لا تتوقع الاتجاه. استنى إغلاق برا النطاق، وبعدين قرر إذا تدخل بعد الإغلاق أو تستنى الرجعة.")

    # خطة صفقة افتراضية
    if stop and (ht is None or ht["triggered"] or state == "صاعد"):
        plan = trade_plan(price, stop, res[0] if res else None, a, risk_amt)
        if plan:
            P("\n🧮 حسبة صفقة (لو تحققت شروطك):")
            P(f"   دخول {fmt(plan['entry'])} | وقف {fmt(plan['stop'])} | مخاطرة/سهم {fmt(plan['risk_ps'])}")
            if plan["shares"] is not None:
                P(f"   مبلغ المخاطرة {risk_amt} ÷ {fmt(plan['risk_ps'])} = {plan['shares']:,} سهم (تكلفتها {plan['cost']:,.2f} {cur})")
            P(f"   الهدف الأول (2.5× المخاطرة): {fmt(plan['target'])} → بيع النصف، والباقي وقف تحت آخر قاع أعلى")
            for w in plan["warn"]:
                P(f"   ⚠️ {w}")

    # مراجعة مركز قائم
    if cost:
        P("\n💼 مركزك:")
        pnl = (price / cost - 1) * 100
        need = (cost / price - 1) * 100
        P(f"   سعر شرائك {fmt(cost)} → {'ربح' if pnl >= 0 else 'خسارة'} {abs(pnl):.1f}%"
          + (f"، والسعر يحتاج +{need:.0f}% ليرجع لسعرك" if pnl < 0 else ""))
        if nshares:
            P(f"   قيمة المركز الآن {nshares*price:,.2f} {cur} ({'+' if pnl>=0 else ''}{nshares*(price-cost):,.2f})")
        if stop:
            P(f"   وين بتبطل الفكرة؟ إغلاق تحت {fmt(stop)} (تحت أقرب منطقة دعم).")
        else:
            P("   ما في دعم تحت السعر: حدد مسبقاً المبلغ اللي بتقبل تخسره، لأنه الشارت ما بيعطيك مكان واضح.")
        overhead = [z for z in res if z[0] < cost]
        if pnl < 0 and overhead:
            P(f"   في {len(overhead)} منطقة مقاومة بين السعر وسعر شرائك — أول وحدة {fmt(overhead[0][0])}–{fmt(overhead[0][1])}:"
              " منطقة منطقية لتخفيف جزء إذا الحالة لسا هابطة.")
        P("   راجع القرار مش النتيجة: لو ما كنت داخل، هل كنت رح تشتري هون حسب شروطك؟")

    P("\n— أداة تعليمية مبنية على مفاهيم من قناة Assad Hamzeh، غير تابعة له. القرار بالسوق مسؤوليتك.")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description="بوت منهج الأسئلة الثلاثة")
    ap.add_argument("tickers", nargs="+", help="رمز السهم على Yahoo، مثل IVN.TO أو VWAV")
    ap.add_argument("--risk", type=float, help="المبلغ اللي بتقبل تخسره بالصفقة")
    ap.add_argument("--cost", type=float, help="سعر شرائك (لمراجعة مركز قائم)")
    ap.add_argument("--shares", type=int, help="عدد أسهمك")
    a = ap.parse_args()
    for t in a.tickers:
        try:
            print(analyze(t, a.risk, a.cost, a.shares))
        except Exception as e:  # noqa: BLE001
            print(f"{t}: تعذر التحليل ({e})", file=sys.stderr)
        print()


if __name__ == "__main__":
    main()
