import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scan

class BybitAdapterTests(unittest.IsolatedAsyncioTestCase):
    async def test_top20_filters_real_perpetual_usdt_and_uses_turnover(self):
        instruments = {'list': [
            {'symbol':'BTCUSDT', 'status':'Trading','contractType':'LinearPerpetual','quoteCoin':'USDT','settleCoin':'USDT'},
            {'symbol':'ETHUSDC','status':'Trading','contractType':'LinearPerpetual','quoteCoin':'USDC','settleCoin':'USDC'},
            {'symbol':'FOOUSDT','status':'PreLaunch','contractType':'LinearPerpetual','quoteCoin':'USDT','settleCoin':'USDT'}
        ], 'nextPageCursor': ''}
        tickers = {'list': [
            {'symbol':'BTCUSDT','turnover24h':'1234567.89','price24hPcnt':'0.0175'},
            {'symbol':'ETHUSDC','turnover24h':'900000000','price24hPcnt':'0.01'}]}
        with patch.object(scan,'fetch', new=AsyncMock(side_effect=[instruments,tickers])):
            result = await scan.top20(None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['symbol'], 'BTCUSDT')
        self.assertAlmostEqual(result[0]['change_pct_24h'], 1.75)

    async def test_kline_converts_reverse_order_and_computes_close_time(self):
        candles=[]
        for i in range(100):
            candles.append([str(i*900000),'100','110','90','100','100','10000'])
        with patch.object(scan,'fetch',new=AsyncMock(return_value={'list': list(reversed(candles))})):
            df = await scan.get_candles(None,'BTCUSDT','15m',260, 100*900000-1)
        self.assertEqual(len(df), 99)
        self.assertEqual(df.iloc[0].open_time, 0)
        self.assertEqual(df.iloc[-1].close_time, 99*900000-1)

if __name__=='__main__':
    unittest.main()
