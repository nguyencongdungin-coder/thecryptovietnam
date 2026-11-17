#!/usr/bin/env python3
"""TCV RSS headlines collector. No copied article bodies or invented summaries."""
import datetime as dt
import email.utils
import html
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BASE = pathlib.Path(__file__).resolve().parent
OUTPUT = BASE / "data" / "latest.json"
FEEDS = (
    ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml", "coindesk.com"),
    ("Decrypt", "https://decrypt.co/feed", "decrypt.co"),
    ("Cointelegraph", "https://cointelegraph.com/rss", "cointelegraph.com"),
)
USER_AGENT = "TheCryptoVietnam-Headlines/1.0 (+https://thecryptovietnam.com)"
MAX_AGE_HOURS = 72

# Chấm điểm theo tiêu đề RSS, KHÔNG suy diễn nội dung bài báo.
TOPICS = (
    ("Pháp lý", r"\b(regulat(?:ion|ory|or)|sec|cftc|law|bill|legislation|license|court|lawsuit|policy|ban|approval|approved|government|senate|congress|compliance)\b", 7),
    ("ETF & tổ chức", r"\b(etf|etps?|institutional|blackrock|grayscale|fidelity|inflow|outflow|fund flows?|treasury|holdings|whale|strategy)\b", 7),
    ("Bảo mật", r"\b(hack|hacker|exploit|breach|phish(?:ing)?|attack|stolen|scam|fraud|vulnerability|security)\b", 7),
    ("Bitcoin", r"\b(bitcoin|btc|satoshi|mining|miner|halving)\b", 5),
    ("Ethereum", r"\b(ethereum|ether|eth|layer.?2|rollups?|staking)\b", 5),
    ("Altcoin & DeFi", r"\b(sol(?:ana)?|xrp|bnb|altcoin|defi|stablecoin|usdt|usdc|token|blockchain|dex|dao|airdrop|onchain|on-chain)\b", 4),
    ("Sàn & giao dịch", r"\b(exchange|futures|perpetual|derivatives|trading|liquidation|leverage|binance|okx|bybit|coinbase|kraken)\b", 4),
)
CORE = re.compile(r"\b(bitcoin|btc|ethereum|ether|eth|crypto|cryptocurrency|blockchain|token|solana|defi|stablecoin|web3|digital assets?|on-chain|onchain|futures|perpetual|coinbase|binance|okx|bybit|xrp|etf)\b",re.I)
OFF_TOPIC = re.compile(r"\b(nvidia|semiconductor|chipmaker|earnings|football|celebrity|recipe|sports|dating|hollywood)\b",re.I)
PROMO = re.compile(r"\b(sponsored|advertorial|press release|giveaway|casino|betting|price prediction|100x|guaranteed returns?)\b",re.I)


def classify(title):
    matches=[(label,weight) for label,pattern,weight in TOPICS if re.search(pattern,title,re.I)]
    category = max(matches,key=lambda pair:pair[1])[0] if matches else "Thị trường"
    return category, max((score for _,score in matches),default=0)


def score_article(item, now):
    title=item['title']
    if PROMO.search(title):return -100
    category, weight=classify(title)
    age_hours=max(0.0,(now-pub_time(item['published_at'])).total_seconds()/3600)
    score=weight + (4 if CORE.search(title) else -7) - (11 if OFF_TOPIC.search(title) and not CORE.search(title) else 0)
    # Ưu tiên tính mới nhưng không lấn át hoàn toàn tin pháp lý/bảo mật.
    score+=max(0,4 - age_hours/12)
    return round(score,2)


def rank_articles(items, now, limit=18):
    # RSS có thể chứa tin công nghệ rộng. Loại tin không trực tiếp nói đến crypto.
    suitable=[]
    for item in items:
        score=score_article(item,now)
        if score<2:continue
        category,_=classify(item['title'])
        suitable.append({**item,'category':category,'priority':score})
    suitable.sort(key=lambda i:(-i['priority'],i['published_at']),reverse=False)
    # Chọn 3 vị trí đầu có nguồn đa dạng nếu có, để tránh một nhà xuất bản chiếm cả trang chủ.
    selected=[];pool=suitable.copy()
    while pool and len(selected)<min(3,limit):
        previous={v['source'] for v in selected}
        pick=next((i for i,x in enumerate(pool) if x['source'] not in previous),0)
        selected.append(pool.pop(pick))
    return (selected+pool)[:limit]


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value or ""))).strip()[:250]

def valid_link(raw, domain):
    url = urllib.parse.urlsplit((raw or "").strip())
    hostname = (url.hostname or "").lower()
    if url.scheme != "https" or not (hostname == domain or hostname.endswith("." + domain)):
        return None
    # Remove tracking fragments/query params; preserve path, some publisher URLs use query identifiers.
    return urllib.parse.urlunsplit((url.scheme, url.netloc, url.path, url.query, ""))

def pub_time(raw):
    if not raw:
        return None
    try:
        val = email.utils.parsedate_to_datetime(raw)
    except (ValueError, TypeError):
        try:
            val = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None
    if val.tzinfo is None:
        val = val.replace(tzinfo=dt.timezone.utc)
    return val.astimezone(dt.timezone.utc)

def inner_text(el, *names):
    for n in names:
        e = el.find(n)
        if e is not None and e.text:
            return e.text
    return ""

def parse_feed(blob, source, domain, now):
    root = ET.fromstring(blob)
    items = []
    rss = root.findall("./channel/item")
    atom = False
    if not rss:
        rss = root.findall("{http://www.w3.org/2005/Atom}entry")
        atom = True
    for item in rss:
        if atom:
            title = inner_text(item,"{http://www.w3.org/2005/Atom}title")
            links = item.findall("{http://www.w3.org/2005/Atom}link")
            href = next((el.attrib.get("href") for el in links if el.attrib.get("rel","alternate")=="alternate"), None)
            published = inner_text(item,"{http://www.w3.org/2005/Atom}published","{http://www.w3.org/2005/Atom}updated")
        else:
            title = inner_text(item,'title')
            href = inner_text(item,'link')
            published = inner_text(item,'pubDate','{http://purl.org/dc/elements/1.1/}date')
        title = clean(title)
        url = valid_link(href, domain)
        moment = pub_time(published)
        if not title or not url or not moment or len(title) < 12:
            continue
        age = now - moment
        if age > dt.timedelta(hours=MAX_AGE_HOURS) or age < dt.timedelta(minutes=-30):
            continue
        # Unaltered headline, never inferred Vietnamese translation.
        items.append({"title":title,"url":url,"source":source,"published_at":moment.isoformat(timespec='seconds').replace('+00:00','Z')})
    return items

def collect(fetcher=None, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if fetcher is None:
        def fetcher(url):
            req = urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/rss+xml, application/xml, text/xml"})
            with urllib.request.urlopen(req, timeout=18) as response:
                return response.read(2_000_000)
    all_items, successful = [], 0
    for source,url,domain in FEEDS:
        try:
            data = fetcher(url)
            articles = parse_feed(data,source,domain,now)
            print(f"{source}: {len(articles)} recent headlines")
            all_items.extend(articles)
            successful += 1
        except (OSError,urllib.error.URLError,ET.ParseError,ValueError) as exc:
            print(f"WARNING {source}: {type(exc).__name__}: {exc}",file=sys.stderr)
    seen_links, seen_titles, unique = set(),set(),[]
    for it in sorted(all_items,key=lambda i:i['published_at'],reverse=True):
        title_key = re.sub(r'\W+','',it['title'].casefold())
        if it['url'] in seen_links or title_key in seen_titles:
            continue
        seen_links.add(it['url']);seen_titles.add(title_key);unique.append(it)
    return successful,rank_articles(unique,now,limit=18)

def main():
    success,items=collect()
    if not items:
        print('No recent high-relevance headlines; preserving previous feed file, no fabricated news')
        return 0
    output={'updated_at':dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00','Z'), 'items':items}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    current = OUTPUT.read_text(encoding='utf8') if OUTPUT.exists() else ''
    # Avoid new commit/deploy when only checked_at changes: timestamps are refreshed only if data changed.
    try:
        previous=json.loads(current)
        if previous.get('items')==items:
            print('No news changes');return 0
    except (ValueError,TypeError):
        pass
    OUTPUT.write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(f'Wrote {len(items)} headline links; {success} RSS sources responded')
    return 0

if __name__=='__main__':raise SystemExit(main())
