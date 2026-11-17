"""TCV research scanner: OKX V5 public USDT-margined perpetual SWAP data.
No orders, account authentication or synthetic signals. Fails closed if inaccessible.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path
import httpx
from engine import candles_frame, build_signal, backtest

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'ai-signal' / 'data'
BASE = 'https://www.okx.com'
INTERVALS = ('15m', '1h', '4h')
OKX_INTERVALS = {'15m': '15m', '1h': '1H', '4h': '4H'}
INTERVAL_MS = {'15m': 900_000, '1h': 3_600_000, '4h': 14_400_000}
MAX_ALERT_AGE_MS = 20 * 60 * 1000

async def fetch(client, endpoint, params=None):
    try:
        response = await client.get(BASE + endpoint, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(f'OKX market API HTTP {exc.response.status_code}; keep last valid data') from exc
    except (httpx.RequestError, ValueError) as exc:
        raise RuntimeError(f'OKX connection/data error: {type(exc).__name__}') from exc
    if not isinstance(payload, dict) or payload.get('code') != '0':
        raise RuntimeError(f'OKX API rejected {endpoint}: {str(payload.get("msg") if isinstance(payload, dict) else payload)[:180]}')
    result = payload.get('data')
    if not isinstance(result, list):
        raise RuntimeError(f'OKX API missing data array in {endpoint}')
    return result

def okx_id(symbol):
    if not symbol.endswith('USDT'):
        raise ValueError('Invalid USDT symbol')
    return symbol[:-4] + '-USDT-SWAP'

def parse_market_instruments(instruments, tickers):
    eligible = {x.get('instId') for x in instruments if
                x.get('state') == 'live' and x.get('instType') == 'SWAP' and
                x.get('settleCcy') == 'USDT' and
                str(x.get('instId', '')).endswith('-USDT-SWAP')}
    pool=[]
    for t in tickers:
        inst=t.get('instId')
        if inst not in eligible:
            continue
        try:
            price=float(t['last']); old=float(t['open24h']); base_volume=float(t['volCcy24h'])
            if not (math.isfinite(price) and math.isfinite(old) and math.isfinite(base_volume)
                    and price>0 and old>0 and base_volume>=0):
                continue
            # For OKX derivatives, volCcy24h is base asset volume, NOT USDT.
            # Value is a current-price ESTIMATE of 24h quote volume, not exact turnover.
            volume=base_volume*price
            change=(price/old-1)*100
            if not -100<=change<=100000:
                continue
            symbol=inst.removesuffix('-SWAP').replace('-','')
            pool.append({'symbol':symbol,'quote_volume_24h':volume,'change_pct_24h':change})
        except (KeyError,TypeError,ValueError,OverflowError):
            continue
    return sorted(pool,key=lambda t:t['quote_volume_24h'],reverse=True)[:20]

async def top20(client):
    instruments, tickers = await asyncio.gather(
        fetch(client,'/api/v5/public/instruments',{'instType':'SWAP'}),
        fetch(client,'/api/v5/market/tickers',{'instType':'SWAP'}))
    return parse_market_instruments(instruments,tickers)

def parse_okx_candles(raw, interval, now_ms):
    rows=[]
    for c in raw:
        if not isinstance(c,list) or len(c)<9 or c[8]!='1':
            continue
        start=int(c[0]); close=start+INTERVAL_MS[interval]-1
        if close >= now_ms:
            continue
        # OKX array: ts,o,h,l,c,vol(contracts),volCcy(base),volCcyQuote(USDT),confirm.
        # Use quote volume for comparisons across differing contract sizes.
        rows.append([start,c[1],c[2],c[3],c[4],c[7],close])
    rows.sort(key=lambda r:r[0])
    return candles_frame(rows,now_ms)

async def get_candles(client, symbol, interval, limit, now_ms):
    # OKX most-recent candle endpoint supports max 300 observations.
    # Use <= 300 to avoid silent truncation; no invented candle history.
    raw = await fetch(client,'/api/v5/market/candles',{
        'instId':okx_id(symbol),'bar':OKX_INTERVALS[interval],'limit':min(300,limit)})
    return parse_okx_candles(raw,interval,now_ms)

async def scan_one(client, sem, item, interval, now_ms):
    async with sem:
        frame = await get_candles(client, item['symbol'], interval, 260, now_ms)
    signal = build_signal(item['symbol'], frame, interval)
    signal.update(item)
    return signal

async def notify(client, token, chat, signal):
    fmt = lambda x: format(x, '.8g')
    msg = (f"TCV AI SIGNAL | {signal['signal']} | {signal['symbol']} | {signal['interval']}\n"
           f"Nến đóng: {datetime.fromtimestamp(signal['close_time']/1000,timezone.utc):%Y-%m-%d %H:%M} UTC\n"
           f"Giá tham chiếu: {fmt(signal['entry'])} USDT\n"
           f"SL: {fmt(signal['sl'])} | TP: {fmt(signal['tp'])}\n"
           f"Điểm bộ lọc: {signal['score']}/100 (KHÔNG phải tỷ lệ thắng)\n"
           "Nghiên cứu, không phải khuyến nghị; Futures có rủi ro thanh lý.")
    response = await client.post(f'https://api.telegram.org/bot{token}/sendMessage', json={'chat_id': chat, 'text': msg})
    response.raise_for_status()
    if not response.json().get('ok'):
        raise RuntimeError('Telegram rejected message')

def read_json(path):
    try:
        return json.loads(path.read_text(encoding='utf8'))
    except (OSError, ValueError):
        return {}

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf8')
    temp.replace(path)

async def run(args):
    DATA.mkdir(parents=True, exist_ok=True)
    sent_path = DATA / 'sent.json'
    sent = read_json(sent_path)
    now_ms = int(time.time() * 1000)
    errors = []
    async with httpx.AsyncClient(timeout=30.0, headers={'User-Agent': 'TCV-Market-Research/1.0'}) as client:
        symbols = await top20(client)
        if len(symbols) != 20:
            raise RuntimeError(f'Expected 20 valid USDT linear perpetual tickers, got {len(symbols)}')
        sem = asyncio.Semaphore(4)
        outputs = await asyncio.gather(*(scan_one(client, sem, item, iv, now_ms)
            for item in symbols for iv in INTERVALS), return_exceptions=True)
        signals = []
        for out in outputs:
            if isinstance(out, Exception):
                errors.append(str(out))
            else:
                signals.append(out)
        if len(signals) < 40:
            raise RuntimeError(f'Too many failed scans: {len(signals)}/60; old published data remains unchanged')
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        chat = os.environ.get('TELEGRAM_CHAT_ID', '')
        fresh = []
        for s in signals:
            if s['signal'] == 'WAIT' or not 0 <= now_ms - s['close_time'] <= MAX_ALERT_AGE_MS:
                continue
            key = f"{s['symbol']}:{s['interval']}:{s['close_time']}:{s['signal']}"
            if key not in sent:
                fresh.append((key, s))
        sent_count = 0
        if token and chat and args.telegram:
            for key, s in fresh[:15]:
                try:
                    await notify(client, token, chat, s)
                    sent[key] = now_ms
                    sent_count += 1
                except Exception as exc:
                    errors.append('Telegram: ' + str(exc))
        sent = {k: v for k, v in sent.items() if isinstance(v, int) and now_ms - v < 14 * 86400_000}
        ranking = 'OKX live USDT-settled SWAP; ranked by estimated 24h USDT volume = base volume * latest price'
        payload = {'status': 'live' if not errors else 'partial',
                   'source': 'OKX V5 public SWAP market data — USDT settled (volume ranking is estimated)',
                   'generated_at': now_ms, 'scan_minutes': 15,
                   'ranking_method': ranking, 'symbols': symbols,
                   'signals': signals, 'errors': errors[:4],
                   'telegram_sent_this_run': sent_count,
                   'disclaimer': 'Rule-based technical analysis, not machine-learning AI or financial advice.'}
        # Build both outputs before writing; a failed scan must not produce fake/live data.
        radar_coins = []
        by_symbol = {s['symbol']: s for s in signals if s.get('interval') == '15m'}
        for item in symbols:
            s15 = by_symbol.get(item['symbol'])
            ratio = s15.get('volume_ratio') if s15 else None
            ratio = ratio if isinstance(ratio, (float, int)) and 0 <= ratio < 1e5 else None
            change = item['change_pct_24h']
            anomaly = min(100, round(min(abs(change), 20) * 3 + min(max((ratio or 1) - 1, 0), 4) * 10))
            radar_coins.append({**item, 'volume_ratio_15m': ratio,
                                'volume_alert': bool(ratio is not None and ratio >= 2),
                                'anomaly_score': anomaly,
                                'signal_15m': s15['signal'] if s15 else None})
        radar = {'status': payload['status'], 'generated_at': now_ms,
                 'source': payload['source'], 'ranking_method': ranking,
                 'metric': '24h price change, estimated 24h USDT notional, closed 15m USDT volume / previous 20',
                 'coins': radar_coins, 'note': 'Rules-based anomaly score; not a probability or advice.'}
        write_json(DATA / 'latest.json', payload)
        write_json(ROOT / 'market-radar' / 'data' / 'latest.json', radar)
        write_json(sent_path, sent)
        print(f'Scanned {len(signals)} candle sets; {len(errors)} errors; {sent_count} Telegram sends')
        if args.backtest:
            tests = []
            for t in symbols[:5]:
                try:
                    frame = await get_candles(client, t['symbol'], '1h', 300, now_ms)
                    result = backtest(frame)
                    tests.append({'symbol': t['symbol'], 'interval': '1h',
                                  'from': int(frame.iloc[0].open_time),
                                  'to': int(frame.iloc[-1].close_time),
                                  'assumptions': {'fee_bps_each_side': 5,
                                                  'slippage_bps_each_side': 2,
                                                  'funding_included': False}, **result})
                except Exception as exc:
                    tests.append({'symbol': t['symbol'], 'error': str(exc)})
            write_json(DATA / 'backtests.json', {'generated_at': now_ms, 'sample': tests,
                       'source': 'OKX V5 public market data'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--telegram', action='store_true')
    parser.add_argument('--backtest', action='store_true')
    asyncio.run(run(parser.parse_args()))
