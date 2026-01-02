#!/usr/bin/env python3
"""
Lightweight scraper pre vybrané parky (Kálnica, Jasenská).
Vytiahne otváracie hodiny, stav (ak sa dá) a cenník a zapíše do
assets/status/trail_status.json. Používa iba štandardnú knižnicu (urllib + re).

Spustenie:
  python scripts/fetch_trail_status.py
"""

import json
import re
import urllib.request
from pathlib import Path

OUT = Path("assets/status/trail_status.json")


def fetch(url: str) -> str:
  with urllib.request.urlopen(url, timeout=20) as resp:
    return resp.read().decode("utf-8", errors="ignore")


def kalnica():
  html = fetch("https://www.bikeparkkalnica.sk/sk/")
  hours = _first_match(r"([0-9]{1,2}:[0-9]{2}\s*-\s*[0-9]{1,2}:[0-9]{2})", html)
  # Status heuristika: ak vidíme "zatvoren", označ ako False, inak neznáme.
  closed = re.search(r"zatvoren", html, re.IGNORECASE) is not None
  pricing = []
  for m in re.finditer(r"BIKEPASS[^<]*?([0-9]{1,3})\s*€", html, re.IGNORECASE):
    pricing.append(f"Bikepass: {m.group(1)} €")
  return {
    "openingHours": hours or "10:00 - 18:00",
    "seasonNote": "Obvykle marec - december, piatok a víkend; mimo otváracích hodín zatvorené.",
    "isOpenNow": False if closed else None,
    "statusText": "Pozri web/IG pre aktuálny stav; obvykle 10:00-18:00 piatok-víkend.",
    "pricing": pricing or [
      "Bikepass: 30 € (štandard), 25 € (do 12 r), 20 € (do 8 r)",
      "Vstup pumptracky: 10 € / 8 € (do 12 r) / 6 € (do 8 r)",
      "Permanentky: 5 vstupov +1 zdarma 150/125/100 €, 10 vstupov +3 zdarma 300/250/200 €",
      "Individuálna rezervácia: 2h/4 jazdci 150 €, 4h/8 jazdcov 300 €, 8h/12 jazdcov 450 € (každý navyše +40 €)",
    ],
    "infoNotes": [
      "Individuálne rezervácie dohodnúť min. 48 hodín vopred.",
    ],
  }


def jasenska():
  html_hours = fetch("https://www.bikeparkjasenska.sk/otvaracie-hodiny/")
  html_pricing = fetch("https://www.bikeparkjasenska.sk/cennik/")
  hours = _first_match(r"([0-9]{1,2}:[0-9]{2}\s*-\s*[0-9]{1,2}:[0-9]{2})", html_hours)
  # Status: ak meta/obsah obsahuje "zatvorené", nastav False; inak neznáme.
  closed = re.search(r"zatvoren", html_hours, re.IGNORECASE) is not None
  prices = []
  for label in [
      r"celodenn[ýy][^0-9]*?dospel[ýy]:\s*([0-9]{1,3})\s*€",
      r"celodenn[ýy][^0-9]*?15[^0-9r]*:\s*([0-9]{1,3})\s*€",
      r"4\s*hodi[^0-9]*?dospel[ýy]:\s*([0-9]{1,3})\s*€",
      r"4\s*hodi[^0-9]*?15[^0-9r]*:\s*([0-9]{1,3})\s*€",
    ]:
    m = re.search(label, html_pricing, re.IGNORECASE)
    if m:
      prices.append(m.group(0).replace("\n", " ").strip())
  return {
    "openingHours": hours or "Sobota, nedeľa, sviatky 10:00 - 16:30",
    "seasonNote": "Pri nepriaznivom počasí zatvorené. Sleduj IG pre aktuálny stav.",
    "isOpenNow": False if closed else None,
    "statusText": "Bežne sobota/nedeľa/sviatky 10:00-16:30; zatvorené pri zlom počasí.",
    "pricing": prices or [
      "Bikepass celodenný: 18 € (dospelý), 15 € (do 15 r)",
      "Bikepass 4-hodinový: 15 € (dospelý), 13 € (do 15 r)",
    ],
    "infoNotes": [],
  }


def _first_match(pattern: str, text: str) -> str | None:
  m = re.search(pattern, text, re.IGNORECASE)
  if m:
    return m.group(1)
  return None


def main():
  data = {
    "Bikepark Kálnica": kalnica(),
    "Bikepark Jasenská": jasenska(),
    # Oko Trails nemá na webe hodiny/cenník, nechávame default/ručne zadané.
  }
  OUT.parent.mkdir(parents=True, exist_ok=True)
  OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
  print(f"Saved {len(data)} status entries to {OUT}")


if __name__ == "__main__":
  main()
