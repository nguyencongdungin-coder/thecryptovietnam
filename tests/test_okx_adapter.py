import unittest
from scan import parse_market_instruments, parse_okx_candles, okx_id

class OKXAdapterTests(unittest.TestCase):
    def test_instruments_ranked_usdt_not_contracts(self):
        instruments=[{'instId':'BTC-USDT-SWAP','instType':'SWAP','state':'live','settleCcy':'USDT'},
                     {'instId':'ETH-USDT-SWAP','instType':'SWAP','state':'live','settleCcy':'USDT'},
                     {'instId':'BTC-USD-SWAP','instType':'SWAP','state':'live','settleCcy':'BTC'}]
        tickers=[{'instId':'BTC-USDT-SWAP','last':'100','open24h':'90','volCcy24h':'2','vol24h':'300000'},
                 {'instId':'ETH-USDT-SWAP','last':'20','open24h':'20','volCcy24h':'20','vol24h':'1'},
                 {'instId':'BTC-USD-SWAP','last':'100','open24h':'90','volCcy24h':'9999'}]
        got=parse_market_instruments(instruments,tickers)
        self.assertEqual([x['symbol'] for x in got],['ETHUSDT','BTCUSDT'])
        self.assertEqual(got[0]['quote_volume_24h'],400)
        self.assertAlmostEqual(got[1]['change_pct_24h'],100/90*100-100)
        self.assertEqual(okx_id('BTCUSDT'),'BTC-USDT-SWAP')

    def test_only_confirmed_candles_and_quote_volume(self):
        now=200*900000
        candles=[]
        for i in range(95):
            row=[str(i*900000),'1','2','0.5','1.5','999','20','45','1']
            candles.append(row)
        candles[-1][-1]='0'
        frame=parse_okx_candles(candles,'15m',now)
        self.assertEqual(len(frame),94)
        self.assertEqual(frame.iloc[0].volume,45)
        self.assertEqual(int(frame.iloc[-1].open_time),93*900000)

if __name__=='__main__':
    unittest.main()
