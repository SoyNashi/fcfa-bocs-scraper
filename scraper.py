import requests
from bs4 import BeautifulSoup
import json
import re

URLS = {
    "Lliga Senior": "https://fcfa.cat/lliga-catalana-de-futbol-america-25-26/",
    "Lliga Junior": "https://fcfa.cat/lliga-catalana-de-futbol-america-junior-25-26/",
    "Lliga Cadet":  "https://fcfa.cat/lliga-catalana-de-futbol-america-cadet-25-26/",
    "Copa Senior":  "https://fcfa.cat/copa-catalana-de-futbol-america-senior-25-26/",
    "Copa Cadet":   "https://fcfa.cat/copa-catalana-de-futbol-america-cadet-25-26/",
}

KEYWORDS = ["bocs", "argentona", "pagesos"]

def es_nuestro(texto, categoria):
    t = texto.lower()
    is_senior = "senior" in categoria.lower()

    if is_senior:
        return "bocs" in t   # senior SOLO bocs
    else:
        return "bocs" in t or "argentona" in t  # junior/cadet conjunto

def main():
    partidos = []

    for categoria, url in URLS.items():
        r = requests.get(url, timeout=20)
        soup = BeautifulSoup(r.text, "html.parser")

        for block in soup.find_all(["div", "p", "li"]):
            text = " ".join(block.get_text(" ", strip=True).split())
            if len(text) < 40:
                continue

            if not es_nuestro(text, categoria):
                continue

            partidos.append({
                "categoria": categoria,
                "texto": text
            })

    with open("partidos.json", "w", encoding="utf-8") as f:
        json.dump(partidos, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
