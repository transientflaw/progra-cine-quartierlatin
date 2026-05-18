#!/usr/bin/env python3
"""
Scraper offi.fr — Cinémas indépendants du Quartier latin.

Produit : public/data.json
Source  : https://www.offi.fr/cinema/{slug}.html
Lancé   : par GitHub Actions chaque nuit à 04:00 Europe/Paris.

Stratégie :
- Pour chaque cinéma, fetch la page offi.fr.
- Parse les onglets de date (#t_0, #t_1...) → liste de jours.
- Pour chaque jour, parse les blocs film (h5) + genre/durée/langue + heures.
- Filtre les séances pour ne garder que les 14 prochains jours.
- Tolère les pages obsolètes (offi.fr les indique parfois en cache).
"""

import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── Config ──────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
CINEMAS_FILE = ROOT / "scripts" / "cinemas.json"
OUTPUT_FILE = ROOT / "data.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,"
        "image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

MONTHS_FR = {
    "janvier": 1, "février": 2, "fevrier": 2, "mars": 3, "avril": 4,
    "mai": 5, "juin": 6, "juillet": 7, "août": 8, "aout": 8,
    "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12, "decembre": 12,
}

GENRE_PATTERN = re.compile(
    r"(Drame|Comédie dramatique|Comédie romantique|Comédie|Thriller|"
    r"Documentaire|Science-fiction|Animation|Historique|Action / Aventure|"
    r"Action|Romance|Polar|Film musical|Musical|Horreur|Western|Biopic|"
    r"Fantastique|Court-métrage|Guerre|Retransmission|Divers)",
    re.IGNORECASE,
)
DURATION_PATTERN = re.compile(r"(\d+h\d{2})")
LANG_PATTERN = re.compile(r"\b(VOST?F?|VO|VF)\b")
TIME_PATTERN = re.compile(r"\b(\d{1,2}:\d{2})\b")


def fetch(url: str, retries: int = 3) -> str | None:
    """Fetch URL with retries and exponential backoff."""
    import random
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
            print(f"  HTTP {resp.status_code} ({len(resp.text)} chars)", file=sys.stderr)
            if resp.status_code == 200:
                # Diagnostic: log first 200 chars to spot blocking pages
                snippet = resp.text[:200].replace("\n", " ").strip()
                print(f"  Début HTML: {snippet[:160]!r}", file=sys.stderr)
                return resp.text
            print(f"  ! HTTP {resp.status_code} on {url}", file=sys.stderr)
        except requests.RequestException as e:
            print(f"  Network error ({attempt + 1}/{retries}): {e}", file=sys.stderr)
        time.sleep(2 ** attempt + random.uniform(0, 1))
    return None


def parse_day_tabs(soup: BeautifulSoup) -> list[dict]:
    """Extract day tabs : anchor id → date object."""
    days = []
    today = date.today()
    current_year = today.year
    for tab in soup.find_all("a", href=re.compile(r"^#t_\d+$")):
        # The tab may contain <br>, <b>, etc. — flatten all text first
        txt = " ".join(tab.stripped_strings)
        # e.g. "Lundi 18 Mai" or "Lundi <br> 18 <br> Mai" → "Lundi 18 Mai"
        # Look separately for the day number and the month name
        day_match = re.search(r"\b(\d{1,2})\b", txt)
        month_match = re.search(r"\b([A-Za-zÀ-ÿ]{3,})\b", txt[day_match.end():] if day_match else txt)
        if not day_match or not month_match:
            continue
        day_num = int(day_match.group(1))
        month_name = month_match.group(1).lower()
        month_num = MONTHS_FR.get(month_name)
        if not month_num:
            continue
        # If month is in the past, assume next year
        year = current_year
        candidate = date(year, month_num, day_num)
        if candidate < today - timedelta(days=2):
            candidate = date(year + 1, month_num, day_num)
        days.append({"anchor": tab["href"][1:], "date": candidate})
    return days


def parse_section(section, day_date: date, cinema_id: str) -> list[dict]:
    """Extract screenings from one day-section."""
    screenings = []
    # Chaque film est dans un <div id="minifiche_XXX">
    fiches = section.find_all("div", id=re.compile(r"^minifiche_\d+$"))
    print(f"    [{day_date}] {len(fiches)} fiches film trouvées", file=sys.stderr)
    for fiche in fiches:
        h5 = fiche.find("h5")
        if not h5:
            continue
        title_link = h5.find("a")
        title = (title_link.get_text(strip=True) if title_link
                 else h5.get_text(strip=True))
        if not title:
            continue

        # Tout le texte de la fiche, balises aplaties
        blob = " ".join(fiche.stripped_strings)

        genre_match = GENRE_PATTERN.search(blob)
        genre = genre_match.group(1).title() if genre_match else ""
        duration_match = DURATION_PATTERN.search(blob)
        duration = duration_match.group(1) if duration_match else ""
        lang_match = LANG_PATTERN.search(blob)
        lang = "VO" if lang_match and "VO" in lang_match.group(1) else (
            "VF" if lang_match and lang_match.group(1) == "VF" else "")
        times = TIME_PATTERN.findall(blob)
        # Filter invalid hours, dedupe
        seen = set()
        valid_times = []
        for t in times:
            h, mn = t.split(":")
            if 0 <= int(h) <= 23 and 0 <= int(mn) <= 59 and t not in seen:
                seen.add(t)
                valid_times.append(t)

        for t in valid_times:
            h, mn = t.split(":")
            screenings.append({
                "cinema_id": cinema_id,
                "date": day_date.isoformat(),
                "hour": int(h),
                "minute": int(mn),
                "title": title,
                "genre": genre,
                "duration": duration,
                "lang": lang,
            })
    return screenings


def scrape_cinema(cinema: dict) -> list[dict]:
    """Scrape one cinema page and return its screenings."""
    url = f"https://www.offi.fr/cinema/{cinema['slug']}.html"
    print(f"→ {cinema['name']} ({cinema['slug']})", file=sys.stderr)
    html = fetch(url)
    if not html:
        print(f"  ! Échec de récupération", file=sys.stderr)
        return []
    soup = BeautifulSoup(html, "lxml")
    days = parse_day_tabs(soup)
    if not days:
        print(f"  ! Aucun jour identifié", file=sys.stderr)
        return []

    screenings = []
    for day_info in days:
        section = soup.find("div", id=day_info["anchor"])
        if not section:
            continue
        screenings.extend(parse_section(section, day_info["date"], cinema["id"]))

    # Filter : keep only screenings in [today-1, today+14]
    today = date.today()
    cutoff_low = today - timedelta(days=1)
    cutoff_high = today + timedelta(days=14)
    screenings = [
        s for s in screenings
        if cutoff_low <= date.fromisoformat(s["date"]) <= cutoff_high
    ]

    print(f"  ✓ {len(screenings)} séances", file=sys.stderr)
    return screenings


def main():
    cinemas = json.loads(CINEMAS_FILE.read_text(encoding="utf-8"))
    all_screenings = []
    cinemas_meta = []

    for cinema in cinemas:
        screenings = scrape_cinema(cinema)
        has_data = len(screenings) > 0
        meta = {k: v for k, v in cinema.items() if k != "slug"}
        meta["has_data"] = has_data
        cinemas_meta.append(meta)
        all_screenings.extend(screenings)
        import random; time.sleep(1.5 + random.uniform(0, 2.5))  # politesse + un peu aléatoire

    out = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source": "L'Officiel des spectacles (offi.fr)",
        "cinemas": cinemas_meta,
        "screenings": all_screenings,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(out, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        f"\n✓ {len(all_screenings)} séances totales — "
        f"{sum(1 for c in cinemas_meta if c['has_data'])}/{len(cinemas)} cinémas couverts",
        file=sys.stderr,
    )
    print(f"✓ Écrit dans {OUTPUT_FILE}", file=sys.stderr)


if __name__ == "__main__":
    main()
