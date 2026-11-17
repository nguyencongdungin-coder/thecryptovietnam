import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from engine import candles_frame,indicators,build_signal,backtest
class TestSignal(unittest.TestCase):
    def test_discards_open_candle(self):
        rows=[[i*900000,'100','110','90','100','100',(i+1)*900000-1] for i in range(100)]
        df=candles_frame(rows,99*900000)
        self.assertEqual(len(df),99)
    def test_flat_series_wait(self):
        rows=[[i*900000,'100','101','99','100','100',(i+1)*900000-1] for i in range(120)]
        df=candles_frame(rows,121*900000)
        s=build_signal('BTCUSDT',df,'15m')
        self.assertEqual(s['signal'],'WAIT')
        bt=backtest(df)
        self.assertEqual(bt['trades'],0)
if __name__=='__main__':unittest.main()
