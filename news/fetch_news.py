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
    return successful,unique[:18]

def main():
    success,items=collect()
    if not items:
        print('No recent verified headlines; preserving previous feed file, no fabricated news')
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
