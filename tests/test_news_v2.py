import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'news'))
import fetch_news as n
NOW=dt.datetime(2026,11,17,14,tzinfo=dt.timezone.utc)
def item(title,source='CoinDesk',hour=13):
 return {'title':title,'source':source,'url':'https://'+source.lower()+'.com/article/'+str(len(title)),'published_at':dt.datetime(2026,11,17,hour,tzinfo=dt.timezone.utc).isoformat()}
class Tests(unittest.TestCase):
 def test_news_classification(self):
  self.assertEqual(n.classify('SEC approves spot Bitcoin ETF')[0],'Pháp lý')
  self.assertEqual(n.classify('Ethereum upgrade draws developers')[0],'Ethereum')
 def test_generic_equities_rejected(self):
  rows=n.rank_articles([item('ARK sells Nvidia shares ahead of earnings')],NOW)
  self.assertEqual(rows,[])
 def test_crypto_ranks_above_unrelated(self):
  rows=n.rank_articles([item('ARK sells Nvidia shares ahead of earnings'),item('Bitcoin ETF records historic outflow')],NOW)
  self.assertEqual(len(rows),1)
  self.assertEqual(rows[0]['category'],'ETF & tổ chức')
 def test_diverse_first_three_sources(self):
  rows=n.rank_articles([item('Bitcoin ETF fund outflow hits record'),item('Ethereum validator update sparks debate'),item('Solana token hack drains crypto users','Decrypt')],NOW)
  self.assertEqual(len(rows),3)
  self.assertEqual({rows[0]['source'],rows[1]['source']},{'CoinDesk','Decrypt'})
 def test_no_fabricated_summary(self):
  rows=n.rank_articles([item('Bitcoin ETF fund outflow hits record')],NOW)
  self.assertNotIn('summary_vi',rows[0])
if __name__=='__main__':unittest.main()
