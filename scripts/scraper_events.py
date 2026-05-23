#!/usr/bin/env python3
"""
Scraper des événements spéciaux des cinémas indépendants.
Pour l'instant : La Clef (laclefrevival.org) uniquement.
Produit : events.json (à la racine du repo)
"""
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = ROOT / "events.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
    ),
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}

DATE_PATTERN = re.compile(r"(\d{2})/(\d{2})/(\d{4})\s*@\s*(\d{1,2}):(\d{2})")


def fetch(url, retries=3):
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            if resp.status_code == 200:
                return resp.text
            print(f"  HTTP {resp.status_code} on {url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  Erreur ({attempt+1}/{retries}): {e}", file=sys.stderr)
        time.sleep(2 ** attempt)
    return None


def parse_laclef_events(html, base="https://laclefrevival.org"):
    soup = BeautifulSoup(html, "lxml")
    events = []
    for h2 in soup.find_all(["h2", "h3"]):
        link = h2.find("a", href=re.compile(r"/project/"))
        if not link:
            continue
        title = link.get_text(strip=True)
        url = link["href"]
        if not url.startswith("http"):
            url = base + url

        prev_text = ""
        node = h2
        for _ in range(6):
            node = node.previous_element
            if node is None:
                break
            t = node.get_text() if hasattr(node, "get_text") else str(node)
            prev_text = (t or "") + " " + prev_text
        m = DATE_PATTERN.search(prev_text)
        if not m:
            continue
        dd, mm, yyyy, hh, mn = m.groups()
        date_str = f"{yyyy}-{mm}-{dd}"
        hour, minute = int(hh), int(mn)

        director = ""
        nxt = h2.next_sibling
        for _ in range(4):
            if nxt is None:
                break
            t = (nxt.get_text(strip=True) if hasattr(nxt, "get_text") else str(nxt)).strip()
            if t.startswith(("de ", "d'", "d\u2019")):
                director = re.sub(r"^d[e']\s*|^d[\u2019]", "", t).strip()
                break
            nxt = nxt.next_sibling

        description = ""
        nxt = h2.next_sibling
        for _ in range(6):
            if nxt is None:
                break
            if hasattr(nxt, "name") and nxt.name == "p":
                description = nxt.get_text(strip=True)[:300]
                break
            nxt = nxt.next_sibling

        poster = ""
        node = h2
        for _ in range(12):
            node = node.previous_element
            if node is None:
                break
            if hasattr(node, "name") and node.name == "img":
                src = node.get("src", "")
                if "wp-content/uploads" in src and not src.startswith("data:"):
                    poster = src
                    break

        events.append({
            "cinema_id": "laClef",
            "date": date_str,
            "hour": hour,
            "minute": minute,
            "title": title,
            "director": director,
            "description": description,
            "poster": poster,
            "url": url,
        })
    return events


def main():
    print("\u2192 Scraping \u00e9v\u00e9nements La Clef\u2026", file=sys.stderr)
    all_events = []
    for page in [1, 2]:
        url = ("https://laclefrevival.org/tout-le-programme/" if page == 1
               else f"https://laclefrevival.org/tout-le-programme/page/{page}/")
        html = fetch(url)
        if not html:
            continue
        evs = parse_laclef_events(html)
        print(f"  page {page}: {len(evs)} \u00e9v\u00e9nements", file=sys.stderr)
        all_events.extend(evs)
        time.sleep(1)

    seen = set()
    unique = []
    for e in all_events:
        if e["url"] not in seen:
            seen.add(e["url"])
            unique.append(e)

    today = date.today()
    horizon = today + timedelta(days=60)
    upcoming = []
    for e in unique:
        try:
            d = date.fromisoformat(e["date"])
            if today <= d <= horizon:
                upcoming.append(e)
        except ValueError:
            pass

    upcoming.sort(key=lambda e: (e["date"], e["hour"], e["minute"]))

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "Sites officiels des cin\u00e9mas",
        "events": upcoming,
    }
    OUTPUT_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n\u2713 {len(upcoming)} \u00e9v\u00e9nements \u00e0 venir \u00e9crits dans {OUTPUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
