import datetime as dt
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'news'))
import fetch_news

RSS=b"""<?xml version="1.0"?><rss><channel><item><title>Crypto market announces an important update</title><link>https://decrypt.co/test-news</link><pubDate>Tue, 17 Nov 2026 12:30:00 GMT</pubDate></item><item><title>Injected link is rejected by publisher allowlist</title><link>https://malicious.example/track</link><pubDate>Tue, 17 Nov 2026 12:30:00 GMT</pubDate></item></channel></rss>"""
class Tests(unittest.TestCase):
    def test_parse_safe_recent_headline(self):
        items=fetch_news.parse_feed(RSS,'Decrypt','decrypt.co',dt.datetime(2026,11,17,13,tzinfo=dt.timezone.utc))
        self.assertEqual(len(items),1)
        self.assertEqual(items[0]['source'],'Decrypt')
    def test_reject_fake_domain(self):
        self.assertIsNone(fetch_news.valid_link('https://decrypt.co.evil.example/news','decrypt.co'))
        self.assertIsNone(fetch_news.valid_link('javascript:alert(1)','decrypt.co'))
    def test_old_news_filtered(self):
        items=fetch_news.parse_feed(RSS,'Decrypt','decrypt.co',dt.datetime(2026,12,1,tzinfo=dt.timezone.utc))
        self.assertEqual(items,[])
    def test_html_tags_stripped(self):
        self.assertEqual(fetch_news.clean('BTC <b>rises</b> &amp; ETH'), 'BTC rises & ETH')
if __name__=='__main__':unittest.main()
