"""Signal computation and conservative, candle-based backtest. No trading code."""
from __future__ import annotations
import math
import numpy as np
import pandas as pd

INTERVAL_MS = {"15m": 900_000, "1h": 3_600_000, "4h": 14_400_000}

def candles_frame(rows, now_ms: int) -> pd.DataFrame:
    """Discard still-forming candles to prevent lookahead and unstable alerts."""
    cols = ["open_time", "open", "high", "low", "close", "volume", "close_time"]
    values = [[int(x[0]), *[float(x[j]) for j in (1, 2, 3, 4, 5)], int(x[6])] for x in rows if int(x[6]) < now_ms]
    frame = pd.DataFrame(values, columns=cols)
    if len(frame) < 70:
        raise ValueError("Không đủ ít nhất 70 nến đã đóng")
    return frame.sort_values("open_time").drop_duplicates("open_time").reset_index(drop=True)

def indicators(frame: pd.DataFrame) -> pd.DataFrame:
    df = frame.copy()
    c = df.close
    df["ema20"] = c.ewm(span=20, adjust=False).mean()
    df["ema50"] = c.ewm(span=50, adjust=False).mean()
    d = c.diff()
    gain = d.clip(lower=0).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = gain / loss.replace(0, np.nan)
    df["rsi"] = (100 - 100/(1 + rs)).fillna(50)
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    df["macd_hist"] = macd - macd.ewm(span=9, adjust=False).mean()
    true_range = pd.concat([(df.high-df.low), (df.high-c.shift()).abs(), (df.low-c.shift()).abs()], axis=1).max(axis=1)
    df["atr"] = true_range.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    df["vol_ratio"] = df.volume / df.volume.shift(1).rolling(20).mean().replace(0, np.nan)
    return df

def at_row(df: pd.DataFrame, i: int) -> dict:
    """Score directional confluence and only emit on a fresh MACD crossover.
    Score is a heuristic, not a calibrated probability of profit.
    """
    if i < 55:
        return {"signal": "WAIT", "score": 0, "reason": "Khởi tạo dữ liệu"}
    r, p = df.iloc[i], df.iloc[i-1]
    if any(not math.isfinite(float(r[k])) for k in ["ema20","ema50","rsi","macd_hist","atr","vol_ratio"]):
        return {"signal":"WAIT","score":0,"reason":"Dữ liệu chỉ báo chưa đầy đủ"}
    bullish = r.close > r.ema20 > r.ema50
    bearish = r.close < r.ema20 < r.ema50
    upcross = p.macd_hist <= 0 < r.macd_hist
    downcross = p.macd_hist >= 0 > r.macd_hist
    long_ok = bullish and upcross and (48 <= r.rsi <= 70) and r.vol_ratio >= 1.05
    short_ok = bearish and downcross and (30 <= r.rsi <= 52) and r.vol_ratio >= 1.05
    signal = "LONG" if long_ok else "SHORT" if short_ok else "WAIT"
    if signal == "WAIT":
        return {"signal":signal,"score":0,"reason":"Chưa đồng thuận xu hướng, động lượng, RSI và khối lượng"}
    # Score merely ranks strength of the qualifying setup, not win-rate.
    score = min(95, int(60 + min(15, (r.vol_ratio-1)*20) + min(12, abs(r.macd_hist)/r.close*40000) + min(8, abs(r.ema20-r.ema50)/r.close*1000)))
    return {"signal":signal,"score":score,"reason":"EMA20/50 + giao cắt MACD + RSI + khối lượng"}

def build_signal(symbol: str, frame: pd.DataFrame, interval: str):
    df = indicators(frame)
    r = df.iloc[-1]
    result = at_row(df, len(df)-1)
    entry = float(r.close)
    atr = float(r.atr)
    if result["signal"] == "WAIT" or not math.isfinite(atr) or atr <= 0:
        return {"symbol":symbol,"interval":interval,"signal":"WAIT","score":0,"price":entry,"entry":None,"sl":None,"tp":None,"rr":None,"rsi":round(float(r.rsi),1),"volume_ratio":round(float(r.vol_ratio),2) if math.isfinite(float(r.vol_ratio)) else None,"close_time":int(r.close_time),"reason":result["reason"]}
    direction = 1 if result["signal"] == "LONG" else -1
    sl = entry - direction*1.5*atr
    tp = entry + direction*3.0*atr
    return {"symbol":symbol,"interval":interval,"signal":result["signal"],"score":result["score"],"price":entry,"entry":entry,"sl":sl,"tp":tp,"rr":2.0,"rsi":round(float(r.rsi),1),"volume_ratio":round(float(r.vol_ratio),2),"close_time":int(r.close_time),"reason":result["reason"]}

def backtest(frame:pd.DataFrame, fee_bps:float=5, slippage_bps:float=2, max_hold:int=12):
    """Next-bar open fills; TP/SL using subsequent OHLC; worst-case SL if both touched.
    One trade at a time. Uses only prior confirmed bars to decide. Approximation,
    not a substitute for full event-driven paper trading/funding calculations.
    """
    df = indicators(frame)
    trades=[]
    i=70
    while i < len(df)-1:
        setup=at_row(df,i)
        side=setup["signal"]
        if side == "WAIT" or not math.isfinite(float(df.iloc[i].atr)):
            i+=1; continue
        direction = 1 if side=="LONG" else -1
        entry=float(df.iloc[i+1].open)*(1+direction*slippage_bps/10000)
        atr=float(df.iloc[i].atr)
        if atr <= 0: i+=1;continue
        stop=entry-direction*1.5*atr
        target=entry+direction*3*atr
        final=min(i+max_hold,len(df)-1)
        exit_price=None; reason="TIME"
        for j in range(i+1,final+1):
            bar=df.iloc[j]
            stop_hit=bar.low<=stop if direction==1 else bar.high>=stop
            target_hit=bar.high>=target if direction==1 else bar.low<=target
            # Pessimistic fill for gaps across stop; conflicting candle exits at stop.
            if stop_hit:
                exit_price=min(float(bar.open),stop) if direction==1 else max(float(bar.open),stop)
                reason="SL";final=j;break
            if target_hit:
                exit_price=target;reason="TP";final=j;break
        if exit_price is None: exit_price=float(df.iloc[final].close)
        exit_price *= 1-direction*slippage_bps/10000
        net_pct=direction*(exit_price/entry-1)*100 - 2*fee_bps/100
        trades.append({"time":int(df.iloc[i].close_time),"side":side,"entry":round(entry,8),"exit":round(exit_price,8),"return_pct":round(net_pct,3),"exit_reason":reason})
        i=final+1
    if not trades:
        return {"trades":0,"win_rate":None,"average_return_pct":None,"total_compounded_pct":None,"max_drawdown_pct":None,"sample":[],"note":"Chưa đủ giao dịch để đánh giá"}
    returns=np.array([t["return_pct"]/100 for t in trades])
    curve=np.cumprod(1+returns)
    peaks=np.maximum.accumulate(np.r_[1.,curve])[1:]
    drawdowns=(curve/peaks-1)*100
    return {"trades":len(trades),"win_rate":round(100*float((returns>0).mean()),1),"average_return_pct":round(100*float(returns.mean()),3),"total_compounded_pct":round(100*float(curve[-1]-1),2),"max_drawdown_pct":round(float(drawdowns.min()),2),"sample":trades[-12:],"note":"Kiểm định lịch sử gần đây, không phải kết quả giao dịch thật; chưa tính funding/liquidation, không có ý nghĩa dự báo chắc chắn."}
