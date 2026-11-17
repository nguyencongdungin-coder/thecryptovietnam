"""Free scheduled scanner for Binance USD-M Futures; no exchange credentials/trading."""
from __future__ import annotations
import argparse
import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx
from engine import candles_frame, build_signal, backtest

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'ai-signal' / 'data'
BASE = os.environ.get('BINANCE_BASE_URL', 'https://fapi.binance.com').rstrip('/')
INTERVALS = ('15m','1h','4h')
MAX_ALERT_AGE_MS = 20 * 60 * 1000

async def fetch(client, url, params=None):
    resp=await client.get(BASE+url, params=params)
    resp.raise_for_status()
    return resp.json()

async def top20(client):
    info,tickers=await asyncio.gather(fetch(client,'/fapi/v1/exchangeInfo'),fetch(client,'/fapi/v1/ticker/24hr'))
    eligible={s['symbol'] for s in info['symbols'] if s.get('status')=='TRADING' and s.get('contractType')=='PERPETUAL' and s.get('quoteAsset')=='USDT' and s.get('marginAsset')=='USDT'}
    pool=(t for t in tickers if t.get('symbol') in eligible)
    return [{'symbol':t['symbol'], 'quote_volume_24h':float(t.get('quoteVolume') or 0),'change_pct_24h':float(t.get('priceChangePercent') or 0)} for t in sorted(pool,key=lambda t:float(t.get('quoteVolume') or 0),reverse=True)[:20]]

async def scan_one(client, sem, item, interval, now_ms):
    async with sem:
        rows=await fetch(client,'/fapi/v1/klines',{'symbol':item['symbol'],'interval':interval,'limit':260})
    frame=candles_frame(rows,now_ms)
    signal=build_signal(item['symbol'],frame,interval)
    signal.update(item)
    return signal

async def notify(client, token, chat, signal):
    fmt=lambda x: format(x,'.8g')
    msg=(f"TCV AI SIGNAL | {signal['signal']} | {signal['symbol']} | {signal['interval']}\n"
         f"Nến đóng: {datetime.fromtimestamp(signal['close_time']/1000,timezone.utc):%Y-%m-%d %H:%M} UTC\n"
         f"Giá tham chiếu: {fmt(signal['entry'])} USDT\n"
         f"SL: {fmt(signal['sl'])} | TP: {fmt(signal['tp'])}\n"
         f"Điểm bộ lọc: {signal['score']}/100 (KHÔNG phải tỷ lệ thắng)\n"
         "Nghiên cứu, không phải khuyến nghị; Futures có rủi ro thanh lý.")
    response=await client.post(f'https://api.telegram.org/bot{token}/sendMessage',json={'chat_id':chat,'text':msg})
    response.raise_for_status()
    if not response.json().get('ok'):
        raise RuntimeError('Telegram rejected message')

async def run(args):
    DATA.mkdir(parents=True,exist_ok=True)
    prev_path=DATA/'latest.json'
    if prev_path.exists():
        try: previous=json.loads(prev_path.read_text(encoding='utf8'))
        except (OSError,ValueError): previous={}
    else: previous={}
    sent_path=DATA/'sent.json'
    if sent_path.exists():
        try: sent=json.loads(sent_path.read_text(encoding='utf8'))
        except (OSError,ValueError): sent={}
    else:sent={}
    now_ms=int(time.time()*1000)
    errors=[]
    async with httpx.AsyncClient(timeout=25.0,headers={'User-Agent':'TCV-AI-Signal/Free'}) as client:
        symbols=await top20(client)
        if len(symbols)!=20: raise RuntimeError(f'Expected Top 20, got {len(symbols)}')
        sem=asyncio.Semaphore(4)
        outputs=await asyncio.gather(*(scan_one(client,sem,s,iv,now_ms) for s in symbols for iv in INTERVALS),return_exceptions=True)
        signals=[]
        for out in outputs:
            if isinstance(out,Exception):errors.append(str(out))
            else:signals.append(out)
        if len(signals)<40:
            raise RuntimeError(f'Too many failed scans: {len(signals)}/60 completed; keep old data, no false success')
        token=os.environ.get('TELEGRAM_BOT_TOKEN','')
        chat=os.environ.get('TELEGRAM_CHAT_ID','')
        fresh=[]
        for s in signals:
            if s['signal']=='WAIT' or not 0 <= now_ms-s['close_time'] <= MAX_ALERT_AGE_MS:continue
            key=f"{s['symbol']}:{s['interval']}:{s['close_time']}:{s['signal']}"
            if key in sent:continue
            fresh.append((key,s))
        # Dedupe alerts persistently across scheduled runs. Only mark successful deliveries.
        # Avoid accidental historical alerts on first run before users opt in.
        sent_count=0
        if token and chat and args.telegram:
            for key,s in fresh[:15]:
                try:
                    await notify(client,token,chat,s)
                    sent[key]=now_ms
                    sent_count+=1
                except Exception as e:errors.append('Telegram: '+str(e))
        # Keep only 14 days of deduplication keys.
        sent={k:v for k,v in sent.items() if isinstance(v,int) and now_ms-v<14*86400_000}
        # Write latest atomically after all core scans finish; never publish fake values.
        payload={'status':'live' if not errors else 'partial','source':'Binance USD-M Futures REST','generated_at':now_ms,'scan_minutes':15,
                 'ranking_method':'USDT quoteVolume 24h, perpetual USDT margined, TRADING','symbols':symbols,
                 'signals':signals,'errors':errors[:4],'telegram_sent_this_run':sent_count,
                 'disclaimer':'Rule-based heuristic, not machine-learning AI or financial advice.'}
        write_json(DATA/'latest.json',payload)
        # Radar shares the same verified Top 20 + closed 15m bars. No extra API calls.
        radar_coins=[]
        by_symbol={s['symbol']:s for s in signals if s.get('interval')=='15m'}
        for item in symbols:
            s15=by_symbol.get(item['symbol'])
            ratio=s15.get('volume_ratio') if s15 else None
            ratio=ratio if isinstance(ratio,(float,int)) and 0 <= ratio < 1e5 else None
            change=item['change_pct_24h']
            # Transparent heuristic only, capped to 100. NOT predictive or probability.
            anomaly=min(100,round(min(abs(change),20)*3 + min(max((ratio or 1)-1,0),4)*10))
            radar_coins.append({**item,'volume_ratio_15m':ratio,
                                'volume_alert':bool(ratio is not None and ratio>=2),
                                'anomaly_score':anomaly,
                                'signal_15m':s15['signal'] if s15 else None})
        write_json(ROOT/'market-radar'/'data'/'latest.json',{
            'status':payload['status'], 'generated_at':now_ms,
            'source':'Binance USD-M Futures REST',
            'ranking_method':payload['ranking_method'],
            'metric':'24h price change, 24h quote volume, closed 15m volume / preceding 20 closed candles',
            'coins':radar_coins, 'note':'Rules-based anomaly score; not a probability or advice.'})

        write_json(sent_path,sent)
        print(f"Scanned {len(signals)} candles sets; {len(errors)} errors; {sent_count} Telegram sends")
        if args.backtest:
            # Lightweight sample: 5 symbols on 1h, explicit limitations.
            tests=[]
            for t in symbols[:5]:
                try:
                    rows=await fetch(client,'/fapi/v1/klines',{'symbol':t['symbol'],'interval':'1h','limit':1000})
                    frame=candles_frame(rows,now_ms)
                    result=backtest(frame)
                    tests.append({'symbol':t['symbol'],'interval':'1h','from':int(frame.iloc[0].open_time),'to':int(frame.iloc[-1].close_time),'assumptions':{'fee_bps_each_side':5,'slippage_bps_each_side':2,'funding_included':False},**result})
                except Exception as e:tests.append({'symbol':t['symbol'],'error':str(e)})
            write_json(DATA/'backtests.json',{'generated_at':now_ms,'sample':tests})


def write_json(path:Path,data):
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    temp.replace(path)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--telegram',action='store_true',help='Send new alerts, only when secrets configured')
    p.add_argument('--backtest',action='store_true')
    asyncio.run(run(p.parse_args()))
