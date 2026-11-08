//+------------------------------------------------------------------+
//|                                                  SMC_RSI_Bot.mq5 |
//|  Trading bot for MetaTrader 5: stocks, forex, gold, crypto       |
//|                                                                  |
//|  Strategy 1 - Smart Money + RSI (videos 1 and 2):                |
//|    1) Liquidity sweep: wick above a swing high, close below it   |
//|    2) CHoCH: close below the protected low (alert only)          |
//|    3) BOS: lower high, then close below the new low              |
//|    4) FVG left by the drop                                       |
//|    5) Price returns to the FVG, rejects it, closes below = ENTRY |
//|    6) SL above the sweep wick, TP = R:R (default 1:2)            |
//|    7) Close above the FVG = idea cancelled                       |
//|    RSI: above 70 alone is NOT a sell. Optional filter: require   |
//|    divergence (price higher high, RSI lower high) at the sweep.  |
//|    Buys use the exact mirror of these rules.                     |
//|                                                                  |
//|  Strategy 2 - Grid (video 3): buy/sell limit orders spaced like  |
//|    a ladder with a fixed distance between orders.                |
//|                                                                  |
//|  Panel: Start / Stop buttons, lot size, distance between orders. |
//|  WARNING: trading is risky. Test in Strategy Tester and on a     |
//|  DEMO account first. No profit is guaranteed.                    |
//+------------------------------------------------------------------+
#property copyright "oncoal"
#property version   "1.00"

#include <Trade/Trade.mqh>

enum ENUM_BOT_STRATEGY
  {
   STRAT_SMC_RSI = 0,   // Smart Money + RSI
   STRAT_GRID    = 1    // Grid
  };

//--- general
input ENUM_BOT_STRATEGY InpStrategy      = STRAT_SMC_RSI; // Strategy
input bool              InpStartActive   = false;         // Start trading immediately (else press START)
input ulong             InpMagic         = 26110801;      // Magic number
input double            InpLots          = 0.01;          // Lot size (used when risk % = 0)
input double            InpRiskPercent   = 0.0;           // Risk % of balance per trade (SMC only, 0 = fixed lot)
input int               InpOrderDistance = 300;           // Distance between orders (points)
input int               InpMaxPositions  = 1;             // Max open positions (SMC)
input double            InpMaxDrawdownPct= 10.0;          // Emergency stop: close all at this equity drawdown %
input bool              InpCloseOnStop   = false;         // Close open positions when STOP is pressed
//--- Smart Money + RSI
input int               InpSwingLen      = 3;             // Swing length (bars each side)
input int               InpRSILen        = 14;            // RSI period
input bool              InpRequireRSIDiv = true;          // Require RSI divergence at the sweep (video 1)
input bool              InpRequireBOS    = true;          // Wait for BOS after CHoCH (video 2)
input double            InpRR            = 2.0;           // Reward : Risk
input double            InpSLBufferATR   = 0.10;          // Extra SL beyond the sweep wick (x ATR)
input int               InpMaxSetupBars  = 60;            // Setup expires after N bars
input double            InpMaxRiskATR    = 6.0;           // Skip if SL wider than N x ATR
input int               InpATRLen        = 14;            // ATR period
input int               InpLookbackBars  = 500;           // Bars scanned each new candle
input bool              InpAllowBuy      = true;          // Allow buys
input bool              InpAllowSell     = true;          // Allow sells
//--- Grid
input int               InpGridLevels    = 5;             // Grid: levels on each side
input int               InpGridTPPoints  = 0;             // Grid: take profit (points, 0 = distance)
input int               InpGridSLPoints  = 0;             // Grid: stop loss (points, 0 = none)
input bool              InpGridBuy       = true;          // Grid: buy limits below price
input bool              InpGridSell      = true;          // Grid: sell limits above price

//--- state
CTrade   trade;
bool     g_running      = false;
double   g_lots         = 0.01;
int      g_distance     = 300;
int      g_rsiHandle    = INVALID_HANDLE;
int      g_atrHandle    = INVALID_HANDLE;
datetime g_lastBar      = 0;
datetime g_lastSignalBar= 0;
double   g_gridBase     = 0.0;
double   g_startEquity  = 0.0;
string   g_lastMsg      = "-";

#define PFX "SMCBOT_"

//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagic);
   trade.SetDeviationInPoints(30);
   trade.SetTypeFillingBySymbol(_Symbol);

   g_lots     = InpLots;
   g_distance = InpOrderDistance;
   g_running  = InpStartActive || (bool)MQLInfoInteger(MQL_TESTER); // buttons don't work in the tester

   g_rsiHandle = iRSI(_Symbol, _Period, InpRSILen, PRICE_CLOSE);
   g_atrHandle = iATR(_Symbol, _Period, InpATRLen);
   if(g_rsiHandle == INVALID_HANDLE || g_atrHandle == INVALID_HANDLE)
     {
      Print("Failed to create indicators");
      return INIT_FAILED;
     }
   g_startEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   CreatePanel();
   UpdatePanel();
   EventSetTimer(1);
   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   EventKillTimer();
   ObjectsDeleteAll(0, PFX);
   if(g_rsiHandle != INVALID_HANDLE) IndicatorRelease(g_rsiHandle);
   if(g_atrHandle != INVALID_HANDLE) IndicatorRelease(g_atrHandle);
  }

//+------------------------------------------------------------------+
void OnTimer() { UpdatePanel(); }

//+------------------------------------------------------------------+
void OnTick()
  {
   if(!g_running) return;
   if(CheckDrawdown()) return;

   if(InpStrategy == STRAT_GRID)
     {
      ManageGrid();
      return;
     }

   datetime bar = iTime(_Symbol, _Period, 0);
   if(bar == g_lastBar) return;          // run once per new candle (on closed candles)
   g_lastBar = bar;
   RunSMC();
  }

//==================================================================//
//                    SMART MONEY + RSI ENGINE                      //
//==================================================================//

// Runs the SELL rules on the given arrays (oldest bar first).
// Returns true if an entry is triggered on the last (just closed) bar.
// The BUY side is obtained by calling this with mirrored arrays.
bool ScanBearish(const double &o[], const double &h[], const double &l[], const double &c[],
                 const double &r[], const double &a[], const int n,
                 double &entry, double &sl, double &tp, bool &divOut)
  {
   int k = InpSwingLen;
   if(n < 2 * k + 5) return false;

   int    shI[], slI[];
   double shP[], slP[];
   ArrayResize(shI, n); ArrayResize(shP, n);
   ArrayResize(slI, n); ArrayResize(slP, n);
   int shN = 0, slN = 0;

   int    phase = 0;            // 0 none, 1 swept, 2 choch, 3 find fvg, 4 armed
   int    start = 0, chochBar = 0, bosBar = 0, armedBar = 0;
   double sweepHi = 0, protLow = 0, fvgBot = 0, fvgTop = 0;
   bool   rdiv = false;

   for(int t = 2 * k; t < n; t++)
     {
      //--- confirm the swing that is k bars old (no look-ahead)
      int j = t - k;
      double mx = h[j], mn = l[j];
      for(int m = j - k; m <= j + k; m++)
        {
         if(h[m] > mx) mx = h[m];
         if(l[m] < mn) mn = l[m];
        }
      if(h[j] >= mx && h[j] > h[j - 1]) { shI[shN] = j; shP[shN] = h[j]; shN++; }
      if(l[j] <= mn && l[j] < l[j - 1]) { slI[slN] = j; slP[slN] = l[j]; slN++; }

      if(phase == 0)
        {
         //--- 1) liquidity sweep of the latest unbroken swing high
         if(shN == 0 || slN == 0) continue;
         int    si = shI[shN - 1];
         double sh = shP[shN - 1];
         if(h[t] > sh && c[t] < sh)
           {
            bool d = (r[t] < r[si]);         // price higher high, RSI lower high
            shN--;                            // level consumed
            if(InpRequireRSIDiv && !d) continue;
            phase = 1; start = t; sweepHi = h[t]; protLow = slP[slN - 1]; rdiv = d;
           }
         else if(c[t] > sh)
            shN--;                            // real break of structure upward
         continue;
        }

      if(t - start > InpMaxSetupBars) { phase = 0; continue; }
      if(c[t] > sweepHi)              { phase = 0; continue; }

      if(phase == 1)
        {
         sweepHi = MathMax(sweepHi, h[t]);
         if(c[t] < protLow)                   // 2) CHoCH
           {
            phase = 2; chochBar = t;
            if(!InpRequireBOS) { phase = 3; bosBar = t; }
           }
         else continue;
        }

      if(phase == 2 && t > chochBar)
        {
         //--- 3) BOS: lower high after CHoCH, then close below the leg low
         int lhI = -1;
         for(int q = shN - 1; q >= 0; q--)
           {
            if(shI[q] <= chochBar) break;
            if(shP[q] < sweepHi) { lhI = shI[q]; break; }
           }
         if(lhI >= 0)
           {
            double ref = l[start];
            for(int m = start; m <= lhI; m++) if(l[m] < ref) ref = l[m];
            if(c[t] < ref) { phase = 3; bosBar = t; }
           }
        }

      if(phase == 3)
        {
         //--- 4) most recent bearish FVG in the impulsive leg
         bool found = false;
         for(int i = bosBar; i > start + 1; i--)
           {
            if(l[i - 2] > h[i]) { fvgBot = h[i]; fvgTop = l[i - 2]; found = true; break; }
           }
         if(!found) { phase = 0; continue; }
         phase = 4; armedBar = t;
         continue;
        }

      if(phase == 4 && t > armedBar)
        {
         if(c[t] > fvgTop) { phase = 0; continue; }   // 7) closed above the gap
         //--- 5) back into the gap, rejected, closed below it
         if(h[t] >= fvgBot && c[t] < fvgBot && c[t] < o[t])
           {
            double e = c[t];
            double s = sweepHi + InpSLBufferATR * a[t];   // 6) stop above the sweep wick
            double risk = s - e;
            phase = 0;
            if(risk <= 0 || risk > InpMaxRiskATR * a[t]) continue;
            if(t == n - 1)
              {
               entry = e; sl = s; tp = e - InpRR * risk; divOut = rdiv;
               return true;
              }
           }
        }
     }
   return false;
  }

//+------------------------------------------------------------------+
void RunSMC()
  {
   int n = InpLookbackBars;
   MqlRates rates[];
   double rsi[], atr[];
   ArraySetAsSeries(rates, false);
   ArraySetAsSeries(rsi, false);
   ArraySetAsSeries(atr, false);
   // start at shift 1 = only closed candles, oldest first
   if(CopyRates(_Symbol, _Period, 1, n, rates) != n) return;
   if(CopyBuffer(g_rsiHandle, 0, 1, n, rsi) != n)  return;
   if(CopyBuffer(g_atrHandle, 0, 1, n, atr) != n)  return;

   double o[], h[], l[], c[], r[];
   double mo[], mh[], ml[], mc[], mr[];
   ArrayResize(o, n); ArrayResize(h, n); ArrayResize(l, n); ArrayResize(c, n); ArrayResize(r, n);
   ArrayResize(mo, n); ArrayResize(mh, n); ArrayResize(ml, n); ArrayResize(mc, n); ArrayResize(mr, n);
   for(int i = 0; i < n; i++)
     {
      o[i] = rates[i].open; h[i] = rates[i].high; l[i] = rates[i].low; c[i] = rates[i].close; r[i] = rsi[i];
      // mirrored chart: a bullish setup is a bearish setup upside-down
      mo[i] = -o[i]; mh[i] = -l[i]; ml[i] = -h[i]; mc[i] = -c[i]; mr[i] = 100.0 - r[i];
     }

   datetime sigBar = rates[n - 1].time;
   if(sigBar == g_lastSignalBar) return;

   double entry, sl, tp; bool div;
   if(InpAllowSell && ScanBearish(o, h, l, c, r, atr, n, entry, sl, tp, div))
     {
      g_lastSignalBar = sigBar;
      OpenSMC(ORDER_TYPE_SELL, sl, tp, div);
     }
   else if(InpAllowBuy && ScanBearish(mo, mh, ml, mc, mr, atr, n, entry, sl, tp, div))
     {
      g_lastSignalBar = sigBar;
      OpenSMC(ORDER_TYPE_BUY, -sl, -tp, div);
     }
  }

//+------------------------------------------------------------------+
void OpenSMC(ENUM_ORDER_TYPE type, double sl, double tp, bool div)
  {
   if(CountPositions() >= InpMaxPositions)
     { g_lastMsg = "Signal skipped: max positions"; Print(g_lastMsg); return; }

   double price = (type == ORDER_TYPE_BUY) ? SymbolInfoDouble(_Symbol, SYMBOL_ASK)
                                           : SymbolInfoDouble(_Symbol, SYMBOL_BID);
   if(HasPositionNear(price, g_distance))
     { g_lastMsg = "Signal skipped: too close to another order"; Print(g_lastMsg); return; }

   // signal was computed on the candle close; re-check against the live price
   if(type == ORDER_TYPE_SELL && (sl <= price || tp >= price)) { g_lastMsg = "Signal skipped: price moved"; return; }
   if(type == ORDER_TYPE_BUY  && (sl >= price || tp <= price)) { g_lastMsg = "Signal skipped: price moved"; return; }

   double stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;
   if(MathAbs(price - sl) < stopLevel || MathAbs(tp - price) < stopLevel)
     { g_lastMsg = "Signal skipped: stops too close"; return; }

   sl = NormalizeDouble(sl, _Digits);
   tp = NormalizeDouble(tp, _Digits);
   double lots = CalcLots(MathAbs(price - sl));
   string cmt  = div ? "SMC+RSIdiv" : "SMC";

   bool ok = (type == ORDER_TYPE_BUY) ? trade.Buy(lots, _Symbol, 0, sl, tp, cmt)
                                      : trade.Sell(lots, _Symbol, 0, sl, tp, cmt);
   g_lastMsg = StringFormat("%s %s %.2f lots  SL %s  TP %s  %s",
                            ok ? "OPENED" : "FAILED",
                            type == ORDER_TYPE_BUY ? "BUY" : "SELL", lots,
                            DoubleToString(sl, _Digits), DoubleToString(tp, _Digits),
                            ok ? "" : trade.ResultRetcodeDescription());
   Print(g_lastMsg);
  }

//==================================================================//
//                            GRID                                  //
//==================================================================//
void ManageGrid()
  {
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double step = g_distance * _Point;
   if(step <= 0) return;
   if(g_gridBase == 0.0) g_gridBase = NormalizeDouble((ask + bid) / 2.0, _Digits);

   double tpDist = (InpGridTPPoints > 0 ? InpGridTPPoints : g_distance) * _Point;
   double slDist = InpGridSLPoints * _Point;
   double stopLevel = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL) * _Point;

   for(int i = 1; i <= InpGridLevels; i++)
     {
      if(InpGridBuy)
        {
         double p = NormalizeDouble(g_gridBase - i * step, _Digits);
         if(ask - p > stopLevel && !LevelBusy(p, true))
           {
            double tp = NormalizeDouble(p + tpDist, _Digits);
            double sl = slDist > 0 ? NormalizeDouble(p - slDist, _Digits) : 0.0;
            trade.BuyLimit(g_lots, p, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "GRID");
           }
        }
      if(InpGridSell)
        {
         double p = NormalizeDouble(g_gridBase + i * step, _Digits);
         if(p - bid > stopLevel && !LevelBusy(p, false))
           {
            double tp = NormalizeDouble(p - tpDist, _Digits);
            double sl = slDist > 0 ? NormalizeDouble(p + slDist, _Digits) : 0.0;
            trade.SellLimit(g_lots, p, _Symbol, sl, tp, ORDER_TIME_GTC, 0, "GRID");
           }
        }
     }
  }

// true if this grid level already has a pending order or an open position
bool LevelBusy(double price, bool isBuy)
  {
   double tol = g_distance * _Point * 0.4;
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) != _Symbol || OrderGetInteger(ORDER_MAGIC) != (long)InpMagic) continue;
      ENUM_ORDER_TYPE t = (ENUM_ORDER_TYPE)OrderGetInteger(ORDER_TYPE);
      bool buyType = (t == ORDER_TYPE_BUY_LIMIT || t == ORDER_TYPE_BUY_STOP);
      if(buyType == isBuy && MathAbs(OrderGetDouble(ORDER_PRICE_OPEN) - price) < tol) return true;
     }
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != (long)InpMagic) continue;
      bool buyPos = (PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY);
      if(buyPos == isBuy && MathAbs(PositionGetDouble(POSITION_PRICE_OPEN) - price) < tol) return true;
     }
   return false;
  }

//==================================================================//
//                         HELPERS                                  //
//==================================================================//
int CountPositions()
  {
   int cnt = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == (long)InpMagic) cnt++;
     }
   return cnt;
  }

bool HasPositionNear(double price, int points)
  {
   if(points <= 0) return false;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) != _Symbol || PositionGetInteger(POSITION_MAGIC) != (long)InpMagic) continue;
      if(MathAbs(PositionGetDouble(POSITION_PRICE_OPEN) - price) < points * _Point) return true;
     }
   return false;
  }

double NormalizeLots(double lots)
  {
   double step = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double vmin = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double vmax = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);
   if(step > 0) lots = MathFloor(lots / step) * step;
   lots = MathMax(vmin, MathMin(vmax, lots));
   return NormalizeDouble(lots, 2);
  }

double CalcLots(double slDistance)
  {
   if(InpRiskPercent <= 0 || slDistance <= 0) return NormalizeLots(g_lots);
   double tickVal  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tickVal <= 0 || tickSize <= 0) return NormalizeLots(g_lots);
   double riskMoney   = AccountInfoDouble(ACCOUNT_BALANCE) * InpRiskPercent / 100.0;
   double lossPerLot  = slDistance / tickSize * tickVal;
   return NormalizeLots(riskMoney / lossPerLot);
  }

void DeletePendings()
  {
   for(int i = OrdersTotal() - 1; i >= 0; i--)
     {
      ulong tk = OrderGetTicket(i);
      if(tk == 0) continue;
      if(OrderGetString(ORDER_SYMBOL) == _Symbol && OrderGetInteger(ORDER_MAGIC) == (long)InpMagic)
         trade.OrderDelete(tk);
     }
  }

void CloseAll()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == (long)InpMagic)
         trade.PositionClose(tk);
     }
  }

bool CheckDrawdown()
  {
   if(InpMaxDrawdownPct <= 0 || g_startEquity <= 0) return false;
   double eq = AccountInfoDouble(ACCOUNT_EQUITY);
   if((g_startEquity - eq) / g_startEquity * 100.0 >= InpMaxDrawdownPct)
     {
      CloseAll();
      DeletePendings();
      g_running = false;
      g_lastMsg = "EMERGENCY STOP: max drawdown reached";
      Print(g_lastMsg);
      UpdatePanel();
      return true;
     }
   return false;
  }

void StartBot()
  {
   g_running     = true;
   g_gridBase    = 0.0;
   g_startEquity = AccountInfoDouble(ACCOUNT_EQUITY);
   g_lastMsg     = "Bot started";
   Print(g_lastMsg);
  }

void StopBot()
  {
   g_running = false;
   DeletePendings();
   if(InpCloseOnStop) CloseAll();
   g_lastMsg = "Bot stopped";
   Print(g_lastMsg);
  }

//==================================================================//
//                          PANEL                                   //
//==================================================================//
void MakeLabel(string name, int x, int y, string text, color clr, int size = 9)
  {
   string n = PFX + name;
   if(ObjectFind(0, n) < 0) ObjectCreate(0, n, OBJ_LABEL, 0, 0, 0);
   ObjectSetInteger(0, n, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, n, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, n, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, n, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, n, OBJPROP_FONTSIZE, size);
   ObjectSetString(0, n, OBJPROP_FONT, "Arial");
   ObjectSetString(0, n, OBJPROP_TEXT, text);
   ObjectSetInteger(0, n, OBJPROP_SELECTABLE, false);
  }

void MakeButton(string name, int x, int y, int w, int hgt, string text, color bg)
  {
   string n = PFX + name;
   if(ObjectFind(0, n) < 0) ObjectCreate(0, n, OBJ_BUTTON, 0, 0, 0);
   ObjectSetInteger(0, n, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, n, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, n, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, n, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, n, OBJPROP_YSIZE, hgt);
   ObjectSetInteger(0, n, OBJPROP_BGCOLOR, bg);
   ObjectSetInteger(0, n, OBJPROP_COLOR, clrWhite);
   ObjectSetInteger(0, n, OBJPROP_FONTSIZE, 10);
   ObjectSetString(0, n, OBJPROP_TEXT, text);
   ObjectSetInteger(0, n, OBJPROP_STATE, false);
   ObjectSetInteger(0, n, OBJPROP_SELECTABLE, false);
  }

void MakeEdit(string name, int x, int y, int w, int hgt, string text)
  {
   string n = PFX + name;
   if(ObjectFind(0, n) < 0) ObjectCreate(0, n, OBJ_EDIT, 0, 0, 0);
   ObjectSetInteger(0, n, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, n, OBJPROP_XDISTANCE, x);
   ObjectSetInteger(0, n, OBJPROP_YDISTANCE, y);
   ObjectSetInteger(0, n, OBJPROP_XSIZE, w);
   ObjectSetInteger(0, n, OBJPROP_YSIZE, hgt);
   ObjectSetInteger(0, n, OBJPROP_BGCOLOR, clrWhite);
   ObjectSetInteger(0, n, OBJPROP_COLOR, clrBlack);
   ObjectSetInteger(0, n, OBJPROP_ALIGN, ALIGN_CENTER);
   ObjectSetString(0, n, OBJPROP_TEXT, text);
   ObjectSetInteger(0, n, OBJPROP_SELECTABLE, false);
  }

void CreatePanel()
  {
   string bg = PFX + "bg";
   if(ObjectFind(0, bg) < 0) ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
   ObjectSetInteger(0, bg, OBJPROP_CORNER, CORNER_LEFT_UPPER);
   ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, 10);
   ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, 25);
   ObjectSetInteger(0, bg, OBJPROP_XSIZE, 290);
   ObjectSetInteger(0, bg, OBJPROP_YSIZE, 215);
   ObjectSetInteger(0, bg, OBJPROP_BGCOLOR, C'24,28,40');
   ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
   ObjectSetInteger(0, bg, OBJPROP_COLOR, C'70,80,110');
   ObjectSetInteger(0, bg, OBJPROP_SELECTABLE, false);

   MakeLabel("title", 22, 33, InpStrategy == STRAT_GRID ? "BOT PANEL - GRID" : "BOT PANEL - SMC + RSI", clrGold, 11);
   MakeButton("start", 22, 60, 125, 30, "START", C'22,160,90');
   MakeButton("stop", 160, 60, 125, 30, "STOP", C'200,50,60');
   MakeLabel("lotsL", 22, 105, "Lot size", clrSilver);
   MakeEdit("lots", 160, 102, 125, 22, DoubleToString(g_lots, 2));
   MakeLabel("distL", 22, 135, "Distance between orders (pts)", clrSilver);
   MakeEdit("dist", 220, 132, 65, 22, IntegerToString(g_distance));
   MakeLabel("status", 22, 165, "", clrWhite);
   MakeLabel("pnl", 22, 185, "", clrWhite);
   MakeLabel("msg", 22, 210, "", clrSilver, 8);
  }

void UpdatePanel()
  {
   ObjectSetString(0, PFX + "status", OBJPROP_TEXT, g_running ? "Status: RUNNING" : "Status: STOPPED");
   ObjectSetInteger(0, PFX + "status", OBJPROP_COLOR, g_running ? clrLime : clrTomato);

   double pnl = 0; int cnt = 0;
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      ulong tk = PositionGetTicket(i);
      if(tk == 0) continue;
      if(PositionGetString(POSITION_SYMBOL) == _Symbol && PositionGetInteger(POSITION_MAGIC) == (long)InpMagic)
        { pnl += PositionGetDouble(POSITION_PROFIT) + PositionGetDouble(POSITION_SWAP); cnt++; }
     }
   ObjectSetString(0, PFX + "pnl", OBJPROP_TEXT, StringFormat("Positions: %d   P/L: %.2f %s", cnt, pnl,
                   AccountInfoString(ACCOUNT_CURRENCY)));
   ObjectSetInteger(0, PFX + "pnl", OBJPROP_COLOR, pnl >= 0 ? clrLime : clrTomato);
   ObjectSetString(0, PFX + "msg", OBJPROP_TEXT, g_lastMsg);
   ChartRedraw();
  }

void OnChartEvent(const int id, const long &lparam, const double &dparam, const string &sparam)
  {
   if(id == CHARTEVENT_OBJECT_CLICK)
     {
      if(sparam == PFX + "start") { ObjectSetInteger(0, sparam, OBJPROP_STATE, false); StartBot(); }
      if(sparam == PFX + "stop")  { ObjectSetInteger(0, sparam, OBJPROP_STATE, false); StopBot(); }
      UpdatePanel();
     }
   if(id == CHARTEVENT_OBJECT_ENDEDIT)
     {
      if(sparam == PFX + "lots")
        {
         double v = StringToDouble(ObjectGetString(0, sparam, OBJPROP_TEXT));
         if(v > 0) g_lots = NormalizeLots(v);
         ObjectSetString(0, sparam, OBJPROP_TEXT, DoubleToString(g_lots, 2));
         g_lastMsg = "Lot size = " + DoubleToString(g_lots, 2);
        }
      if(sparam == PFX + "dist")
        {
         int v = (int)StringToInteger(ObjectGetString(0, sparam, OBJPROP_TEXT));
         if(v > 0)
           {
            g_distance = v;
            if(InpStrategy == STRAT_GRID) { DeletePendings(); g_gridBase = 0.0; } // rebuild the grid
           }
         ObjectSetString(0, sparam, OBJPROP_TEXT, IntegerToString(g_distance));
         g_lastMsg = "Distance = " + IntegerToString(g_distance) + " pts";
        }
      UpdatePanel();
     }
  }
//+------------------------------------------------------------------+
