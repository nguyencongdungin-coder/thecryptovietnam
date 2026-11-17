"""TCV research scanner: Bybit V5 public USDT linear perpetual market data.
No trading/authentication. Fails closed when data is missing or inaccessible.
"""
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
BASE = 'https://api.bybit.com'
INTERVALS = ('15m', '1h', '4h')
BYBIT_INTERVALS = {'15m': '15', '1h': '60', '4h': '240'}
INTERVAL_MS = {'15m': 900_000, '1h': 3_600_000, '4h': 14_400_000}
MAX_ALERT_AGE_MS = 20 * 60 * 1000

async def fetch(client, endpoint, params=None):
    url = BASE + endpoint
    try:
        response = await client.get(url, params=params)
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as exc:
        status = exc.response.status_code
        raise RuntimeError(f'Bybit market API HTTP {status}; kiểm tra điều kiện truy cập và GitHub Actions, không dùng dữ liệu giả') from exc
    if not isinstance(payload, dict) or payload.get('retCode') != 0:
        raise RuntimeError(f'Bybit API rejected {endpoint}: {str(payload.get("retMsg") if isinstance(payload, dict) else payload)[:200]}')
    result = payload.get('result')
    if not isinstance(result, dict):
        raise RuntimeError(f'Bybit API missing result in {endpoint}')
    return result

async def top20(client):
    # Obtain all instruments: Bybit linear listings may exceed 500 instruments.
    eligible = set()
    cursor = None
    for _ in range(10):
        params = {'category': 'linear', 'limit': 1000}
        if cursor:
            params['cursor'] = cursor
        info = await fetch(client, '/v5/market/instruments-info', params)
        for s in info.get('list', []):
            if (s.get('status') == 'Trading' and s.get('contractType') == 'LinearPerpetual'
                    and s.get('quoteCoin') == 'USDT' and s.get('settleCoin') == 'USDT'):
                eligible.add(s.get('symbol'))
        next_cursor = info.get('nextPageCursor') or ''
        if not next_cursor:
            break
        if next_cursor == cursor:
            raise RuntimeError('Bybit instrument pagination repeated cursor')
        cursor = next_cursor
    else:
        raise RuntimeError('Bybit instrument pagination exceeded safety limit')
    tickers = await fetch(client, '/v5/market/tickers', {'category': 'linear'})
    pool = []
    for t in tickers.get('list', []):
        if t.get('symbol') not in eligible:
            continue
        try:
            volume = float(t['turnover24h'])
            change = float(t['price24hPcnt']) * 100.0
        except (KeyError, ValueError, TypeError):
            continue
        if not (volume >= 0 and -100 <= change <= 100000):
            continue
        pool.append({'symbol': t['symbol'], 'quote_volume_24h': volume,
                     'change_pct_24h': change})
    return sorted(pool, key=lambda t: t['quote_volume_24h'], reverse=True)[:20]

async def get_candles(client, symbol, interval, limit, now_ms):
    result = await fetch(client, '/v5/market/kline', {
        'category': 'linear', 'symbol': symbol, 'interval': BYBIT_INTERVALS[interval],
        'limit': limit})
    rows = []
    for c in result.get('list', []):
        # Bybit V5 returns newest first and no candle closeTime field.
        # Map to Binance-shaped array expected by engine.candles_frame().
        start = int(c[0])
        close = start + INTERVAL_MS[interval] - 1
        rows.append([start, c[1], c[2], c[3], c[4], c[5], close])
    rows.sort(key=lambda r: r[0])
    return candles_frame(rows, now_ms)

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
        ranking = 'Bybit linear USDT perpetual, Trading, ranked by turnover24h (USDT)'
        payload = {'status': 'live' if not errors else 'partial',
                   'source': 'Bybit V5 public market data — USDT linear perpetual',
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
                 'metric': '24h price change, 24h turnover, closed 15m candle volume / previous 20',
                 'coins': radar_coins, 'note': 'Rules-based anomaly score; not a probability or advice.'}
        write_json(DATA / 'latest.json', payload)
        write_json(ROOT / 'market-radar' / 'data' / 'latest.json', radar)
        write_json(sent_path, sent)
        print(f'Scanned {len(signals)} candle sets; {len(errors)} errors; {sent_count} Telegram sends')
        if args.backtest:
            tests = []
            for t in symbols[:5]:
                try:
                    frame = await get_candles(client, t['symbol'], '1h', 1000, now_ms)
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
                       'source': 'Bybit V5 public market data'})

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--telegram', action='store_true')
    parser.add_argument('--backtest', action='store_true')
    asyncio.run(run(parser.parse_args()))
